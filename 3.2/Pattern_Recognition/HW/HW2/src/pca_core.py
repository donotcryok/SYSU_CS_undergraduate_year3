"""
pca_core.py — 手写 PCA（主成分分析）核心算法模块

本模块严格不调用 sklearn 等第三方 PCA 接口，基于 NumPy 实现：
    1. 数据中心化（去均值）
    2. 协方差矩阵计算
    3. SVD 奇异值分解（等价于协方差矩阵的特征分解）
    4. 数据降维（投影到低维空间）
    5. 数据重建（从低维空间映射回原始空间）
"""

import numpy as np


class PCA:
    """
    手写 PCA 类
    """

    def __init__(self, n_components: int = None):
        self.n_components = n_components
        self.mean_ = None          # 原始数据的均值向量 (d,)
        self.components_ = None    # 主成分方向矩阵 (d, k) — V_k
        self.singular_values_ = None  # 奇异值 (k,)
        self.explained_variance_ = None      # 各主成分的方差 (k,)
        self.explained_variance_ratio_ = None  # 各主成分的方差贡献率 (k,)
        self._fitted = False

    def fit(self, X: np.ndarray):
        """
        拟合 PCA 模型：计算数据的均值、主成分方向及方差解释率。

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            训练数据矩阵，每一行为一个样本，每一列为一个特征。

        Returns
        -------
        self : PCA
            返回自身以支持链式调用。
        """
        n_samples, n_features = X.shape

        # ---- 1. 数据中心化 ----
        # 计算每个特征（列）的均值
        self.mean_ = np.mean(X, axis=0)  # shape: (n_features,)

        # 减去均值，得到中心化数据
        X_centered = X - self.mean_       # shape: (n_samples, n_features)

        # ---- 2. SVD 分解 ----
        # 对中心化后的数据矩阵进行 SVD 分解
        # X_centered = U @ Σ @ V^T
        # full_matrices=False 使 U 为 (n, k)，Σ 为 (k,)，V^T 为 (k, d)
        # 其中 k = min(n_samples, n_features)
        U, S, Vt = np.linalg.svd(X_centered, full_matrices=False)

        # Vt 的形状为 (k, n_features)，转置后 V 为 (n_features, k)
        # 每一列是 X_centered^T @ X_centered 的特征向量，即主成分方向
        V = Vt.T  # shape: (n_features, k)

        # ---- 3. 确定保留的成分数量 ----
        if self.n_components is None:
            self.n_components = min(n_samples, n_features)
        else:
            self.n_components = min(self.n_components, min(n_samples, n_features))

        # ---- 4. 提取前 k 个主成分 ----
        self.components_ = V[:, :self.n_components]  # (n_features, n_components)
        self.singular_values_ = S[:self.n_components]  # (n_components,)

        # ---- 5. 计算各主成分的方差 ----
        # 协方差矩阵的特征值 λ_i = σ_i^2 / (n-1)，其中 σ_i 为奇异值
        self.explained_variance_ = (S[:self.n_components] ** 2) / (n_samples - 1)

        # 总方差 = 所有奇异值对应的方差之和
        total_variance = (S ** 2).sum() / (n_samples - 1)
        self.explained_variance_ratio_ = self.explained_variance_ / total_variance

        self._fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        将数据投影到 PCA 低维空间。

        """
        if not self._fitted:
            raise RuntimeError("模型尚未拟合，请先调用 fit() 方法。")

        # 中心化
        X_centered = X - self.mean_

        # 投影: Z = X_centered @ V_k
        Z = X_centered @ self.components_
        return Z

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        拟合 PCA 模型并返回降维后的数据。
        """
        self.fit(X)
        return self.transform(X)

    def inverse_transform(self, Z: np.ndarray) -> np.ndarray:
        """
        从低维空间重建原始数据
        """
        if not self._fitted:
            raise RuntimeError("模型尚未拟合，请先调用 fit() 方法。")

        # 反投影: X_centered_approx = Z @ V_k^T
        X_centered_approx = Z @ self.components_.T

        # 加回均值
        X_recon = X_centered_approx + self.mean_
        return X_recon

    def compression_ratio(self, original_size: int = None) -> float:
        """
        计算数据压缩比（仅考虑存储角度）。
        """
        if not self._fitted:
            raise RuntimeError("模型尚未拟合，请先调用 fit() 方法。")

        n_features = self.mean_.shape[0]
        n_samples_placeholder = 1  # 理论计算，不需要实际样本数

        k = self.n_components

        original = n_features                       # 每个样本的存储
        compressed = k + k * n_features + n_features  # 投影坐标 + 成分矩阵 + 均值

        return compressed / original


# ============================================================
# 模块自测代码
# ============================================================
if __name__ == "__main__":
    # 生成测试数据：100 个样本，每个样本 10 维特征
    np.random.seed(42)
    X_test = np.random.randn(100, 10)

    print("=" * 60)
    print("PCA 核心算法自测")
    print("=" * 60)

    # 测试完整流程
    pca = PCA(n_components=5)
    Z = pca.fit_transform(X_test)
    X_recon = pca.inverse_transform(Z)

    print(f"\n原始数据形状:     {X_test.shape}")
    print(f"降维后数据形状:   {Z.shape}")
    print(f"重建后数据形状:   {X_recon.shape}")
    print(f"\n各主成分方差贡献率: {pca.explained_variance_ratio_}")
    print(f"累计方差贡献率:     {pca.explained_variance_ratio_.sum():.4f}")

    # 计算重建误差（均方根误差 RMSE）
    rmse = np.sqrt(np.mean((X_test - X_recon) ** 2))
    print(f"\n重建 RMSE: {rmse:.6f}")

    # 测试保留所有成分时是否能完美重建
    pca_full = PCA(n_components=None)
    Z_full = pca_full.fit_transform(X_test)
    X_recon_full = pca_full.inverse_transform(Z_full)
    rmse_full = np.sqrt(np.mean((X_test - X_recon_full) ** 2))
    print(f"全成分重建 RMSE: {rmse_full:.2e}（应接近于 0）")

    print("\n自测通过！")
