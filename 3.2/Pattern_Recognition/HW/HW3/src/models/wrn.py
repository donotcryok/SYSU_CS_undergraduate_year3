"""
WideResNet-28-2 Architecture
-----------------------------
深度=28, 宽度因子=2, Dropout=0.0, 分类头=10 (CIFAR-10).
参考: "Wide Residual Networks" (BMVC 2016)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init


def _conv3x3(in_planes: int, out_planes: int, stride: int = 1) -> nn.Conv2d:
    return nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=stride,
                     padding=1, bias=False)


class BasicBlock(nn.Module):
    """WRN 基础残差块: 两个 3×3 卷积 + shortcut."""

    expansion = 1

    def __init__(self, in_planes: int, out_planes: int, stride: int,
                 dropout: float = 0.0):
        super().__init__()
        self.bn1 = nn.BatchNorm2d(in_planes)
        self.conv1 = _conv3x3(in_planes, out_planes, stride)
        self.bn2 = nn.BatchNorm2d(out_planes)
        self.conv2 = _conv3x3(out_planes, out_planes, 1)
        self.dropout = nn.Dropout2d(p=dropout) if dropout > 0 else nn.Identity()

        self.shortcut = nn.Sequential()
        if stride != 1 or in_planes != out_planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, out_planes, kernel_size=1,
                          stride=stride, bias=False),
            )

    def forward(self, x):
        out = F.relu(self.bn1(x))
        shortcut = self.shortcut(out) if hasattr(self, 'shortcut') else x
        out = self.conv1(out)
        out = F.relu(self.bn2(out))
        out = self.dropout(out)
        out = self.conv2(out)
        out += shortcut
        return out


class NetworkBlock(nn.Module):
    """堆叠 num_blocks 个 BasicBlock."""

    def __init__(self, num_blocks: int, in_planes: int, out_planes: int,
                 block: nn.Module, stride: int, dropout: float = 0.0):
        super().__init__()
        layers = [block(in_planes, out_planes, stride, dropout)]
        for _ in range(1, num_blocks):
            layers.append(block(out_planes, out_planes, 1, dropout))
        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        return self.layers(x)


class WideResNet(nn.Module):
    """
    WideResNet 骨干网络.
    Args:
        depth:      网络深度 (如 28)
        widen_factor: 宽度因子 (如 2)
        num_classes: 分类数 (10)
        dropout:     Dropout 率 (0.0)
    """

    def __init__(self, depth: int = 28, widen_factor: int = 2,
                 num_classes: int = 10, dropout: float = 0.0):
        super().__init__()
        assert (depth - 4) % 6 == 0, f'depth must be 6n+4, got {depth}'
        n = (depth - 4) // 6                     # 每组的块数
        widths = [16, 16 * widen_factor, 32 * widen_factor, 64 * widen_factor]

        self.in_planes = widths[0]
        self.conv1 = _conv3x3(3, widths[0], 1)   # 输入 3 通道 RGB
        self.block1 = NetworkBlock(n, widths[0], widths[1], BasicBlock, 1, dropout)
        self.block2 = NetworkBlock(n, widths[1], widths[2], BasicBlock, 2, dropout)
        self.block3 = NetworkBlock(n, widths[2], widths[3], BasicBlock, 2, dropout)
        self.bn_final = nn.BatchNorm2d(widths[3])
        self.fc = nn.Linear(widths[3], num_classes)

        # 初始化
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                init.constant_(m.weight, 1)
                init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                init.normal_(m.weight, 0, 0.01)
                init.constant_(m.bias, 0)

    def forward(self, x):
        out = self.conv1(x)
        out = self.block1(out)
        out = self.block2(out)
        out = self.block3(out)
        out = F.relu(self.bn_final(out))
        out = F.adaptive_avg_pool2d(out, (1, 1))
        out = out.view(out.size(0), -1)
        return self.fc(out)


def build_wrn28_2(num_classes: int = 10, dropout: float = 0.0) -> WideResNet:
    """构建 WideResNet-28-2 的便捷函数."""
    return WideResNet(depth=28, widen_factor=2, num_classes=num_classes,
                      dropout=dropout)
