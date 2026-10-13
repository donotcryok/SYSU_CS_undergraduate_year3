"""
CIFAR-10 FixMatch Dataset Module
---------------------------------
- 本地读取 CIFAR-10，严禁网络下载
- 有标签数据: 标准弱增强
- 无标签数据: 弱增强（伪标签生成）+ 强增强（一致性训练）双路输出
"""

import os
import pickle
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image

# ── CIFAR-10 归一化参数 ──────────────────────────────────────────────
CIFAR10_MEAN = (0.4914, 0.4822, 0.4465)
CIFAR10_STD  = (0.2471, 0.2435, 0.2616)


def _unpickle(file: str):
    with open(file, 'rb') as fo:
        return pickle.load(fo, encoding='bytes')


def load_cifar10_numpy(data_root: str):
    """从本地 batch 文件加载 CIFAR-10，返回 (train_x, train_y, test_x, test_y)."""
    batch_dir = os.path.join(data_root, 'data', 'cifar-10-batches-py')

    train_images, train_labels = [], []
    for i in range(1, 6):
        batch = _unpickle(os.path.join(batch_dir, f'data_batch_{i}'))
        train_images.append(batch[b'data'])
        train_labels.extend(batch[b'labels'])

    train_images = np.concatenate(train_images)          # (50000, 3072)
    train_images = train_images.reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)  # HWC
    train_labels = np.array(train_labels, dtype=np.int64)

    test_batch = _unpickle(os.path.join(batch_dir, 'test_batch'))
    test_images = test_batch[b'data'].reshape(-1, 3, 32, 32).transpose(0, 2, 3, 1)
    test_labels = np.array(test_batch[b'labels'], dtype=np.int64)

    return train_images, train_labels, test_images, test_labels


# ── Strong Augmentation 辅助类 ───────────────────────────────────────

class CutoutDefault:
    """Cutout 数据增强: 随机遮挡 16x16 方块 (FixMatch 论文标准)."""

    def __init__(self, n_holes: int = 1, length: int = 16):
        self.n_holes = n_holes
        self.length = length

    def __call__(self, img: torch.Tensor) -> torch.Tensor:
        h, w = img.shape[1], img.shape[2]
        mask = np.ones((h, w), dtype=np.float32)
        for _ in range(self.n_holes):
            y = np.random.randint(h)
            x = np.random.randint(w)
            y1 = max(0, y - self.length // 2)
            y2 = min(h, y + self.length // 2)
            x1 = max(0, x - self.length // 2)
            x2 = min(w, x + self.length // 2)
            mask[y1:y2, x1:x2] = 0.0
        mask = torch.from_numpy(mask).expand_as(img)
        return img * mask


# ── Transform 构建 ───────────────────────────────────────────────────

def build_weak_transform() -> transforms.Compose:
    """弱增强: RandomCrop(4px padding) + RandomHorizontalFlip."""
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
    ])


def build_strong_transform() -> transforms.Compose:
    """强增强: RandomCrop + RandomHorizontalFlip + RandAugment + Cutout."""
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.RandomCrop(32, padding=4),
        transforms.RandomHorizontalFlip(),
        transforms.RandAugment(num_ops=2, magnitude=10),
        transforms.ToTensor(),
        CutoutDefault(n_holes=1, length=16),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
    ])


def build_test_transform() -> transforms.Compose:
    """测试集: 无增强, 仅归一化."""
    return transforms.Compose([
        transforms.ToPILImage(),
        transforms.ToTensor(),
        transforms.Normalize(CIFAR10_MEAN, CIFAR10_STD),
    ])


# ── 标签/无标签 Dataset 类 ───────────────────────────────────────────

class CIFAR10Labeled(Dataset):
    """有标签子集 —— 仅返回弱增强图像与标签."""

    def __init__(self, images: np.ndarray, labels: np.ndarray, indices: np.ndarray):
        self.images = images[indices]
        self.labels = labels[indices]
        self.transform = build_weak_transform()

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx]
        label = self.labels[idx]
        return self.transform(img), label


class CIFAR10Unlabeled(Dataset):
    """
    无标签子集 —— 同时返回:
      - weak_aug:  弱增强图像 (用于 Teacher 生成伪标签)
      - strong_aug: 强增强图像 (用于 Student 一致性训练)
    """

    def __init__(self, images: np.ndarray, indices: np.ndarray):
        self.images = images[indices]
        self.weak_transform = build_weak_transform()
        self.strong_transform = build_strong_transform()

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img = self.images[idx]                         # HWC uint8
        return self.weak_transform(img), self.strong_transform(img)


class CIFAR10Test(Dataset):
    """测试集."""

    def __init__(self, images: np.ndarray, labels: np.ndarray):
        self.images = images
        self.labels = labels
        self.transform = build_test_transform()

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        return self.transform(self.images[idx]), self.labels[idx]


# ── 数据划分逻辑 ─────────────────────────────────────────────────────

def split_labeled_unlabeled(
    train_labels: np.ndarray,
    num_labeled: int = 40,
    num_classes: int = 10,
    seed: int = 42,
):
    """
    每类选取 num_labeled 个样本作为有标签集, 其余为无标签集.
    使用固定 seed 保证可复现.
    """
    rng = np.random.RandomState(seed)
    labeled_indices = []
    unlabeled_indices = []

    for c in range(num_classes):
        class_idx = np.where(train_labels == c)[0]
        rng.shuffle(class_idx)
        labeled_indices.append(class_idx[:num_labeled])
        unlabeled_indices.append(class_idx[num_labeled:])

    labeled_indices = np.concatenate(labeled_indices)
    unlabeled_indices = np.concatenate(unlabeled_indices)

    # Shuffle
    rng.shuffle(labeled_indices)
    rng.shuffle(unlabeled_indices)

    return labeled_indices, unlabeled_indices


def build_dataloaders(
    data_root: str,
    batch_size: int = 64,
    mu: int = 7,
    num_labeled: int = 40,
    num_workers: int = 4,
    seed: int = 42,
):
    """
    构建三个 DataLoader:
      - loader_labeled:   有标签 (batch_size)
      - loader_unlabeled: 无标签 (batch_size * mu)
      - loader_test:      测试集 (batch_size)
    """
    train_images, train_labels, test_images, test_labels = load_cifar10_numpy(data_root)

    labeled_idx, unlabeled_idx = split_labeled_unlabeled(
        train_labels, num_labeled=num_labeled, seed=seed
    )

    labeled_set = CIFAR10Labeled(train_images, train_labels, labeled_idx)
    unlabeled_set = CIFAR10Unlabeled(train_images, unlabeled_idx)
    test_set = CIFAR10Test(test_images, test_labels)

    loader_labeled = DataLoader(
        labeled_set, batch_size=batch_size, shuffle=True,
        num_workers=num_workers, pin_memory=True, drop_last=True,
    )
    loader_unlabeled = DataLoader(
        unlabeled_set, batch_size=batch_size * mu, shuffle=True,
        num_workers=num_workers, pin_memory=True, drop_last=True,
    )
    loader_test = DataLoader(
        test_set, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=True,
    )

    return loader_labeled, loader_unlabeled, loader_test
