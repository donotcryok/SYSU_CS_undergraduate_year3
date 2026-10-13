# src/models.py
# 中文短新闻主题分类 — 双模型架构定义
#
# 流水线 A: BiLSTM + Bahdanau 注意力机制
# 流水线 B: Transformer Encoder + 均值池化分类器
#
# 所有模块均为纯手写实现, 不依赖 HuggingFace 等预训练权重。
# 所有张量操作显式管理 .to(device) 以确保 CUDA 加速。

import math
from typing import Tuple, Optional

import torch
import torch.nn as nn
import torch.nn.functional as F


# ======================== 模型 A: Bahdanau 注意力 ========================
class BahdanauAttention(nn.Module):
    """Bahdanau (加性) 注意力机制。

    数学原理:
        给定编码器隐状态序列 H = [h_1, ..., h_T] ∈ R^{T×2d} (BiLSTM 双向拼接),
        定义可学习查询向量 q ∈ R^{attn_dim}, 计算:

            u_i = tanh(W * h_i + b)          (非线性变换)
            α_i = softmax(u_i^T · q)          (注意力权重)
            c   = Σ α_i · h_i                 (上下文向量)

    其中 W ∈ R^{attn_dim × 2d}, b ∈ R^{attn_dim}, q ∈ R^{attn_dim} 均为可学习参数。
    """

    def __init__(self, hidden_dim: int, attn_dim: int = 128):
        """
        Args:
            hidden_dim: 编码器隐状态维度 (BiLSTM 为 2 * lstm_hidden_dim)
            attn_dim: 注意力空间的中间维度
        """
        super().__init__()
        self.attn_dim = attn_dim

        # 线性变换层 W
        self.W = nn.Linear(hidden_dim, attn_dim, bias=True)
        # 可学习查询向量 q (使用 Parameter 而非 Linear, 避免过参数化)
        self.query = nn.Parameter(torch.randn(attn_dim))

        self.reset_parameters()

    def reset_parameters(self):
        """Xavier 初始化参数。"""
        nn.init.xavier_uniform_(self.W.weight)
        nn.init.zeros_(self.W.bias)
        nn.init.normal_(self.query, mean=0.0, std=0.1)

    def forward(self, encoder_outputs: torch.Tensor,
                mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            encoder_outputs: (batch, seq_len, hidden_dim) 编码器所有时间步的输出
            mask: (batch, seq_len) 布尔掩码, True 表示有效位置

        Returns:
            context: (batch, hidden_dim) 上下文向量
            attn_weights: (batch, seq_len) 注意力权重分布
        """
        # u: (batch, seq_len, attn_dim)
        u = torch.tanh(self.W(encoder_outputs))

        # 注意力分数: (batch, seq_len)
        scores = torch.matmul(u, self.query)

        # 对 <PAD> 位置施加极大负值, 使其 softmax 后接近 0
        if mask is not None:
            scores = scores.masked_fill(~mask, -1e9)

        # 注意力权重: (batch, seq_len)
        attn_weights = F.softmax(scores, dim=-1)

        # 上下文向量: (batch, hidden_dim)
        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs).squeeze(1)

        return context, attn_weights


# ======================== 模型 A: BiLSTM + Attention ========================
class BiLSTMAttention(nn.Module):
    """BiLSTM + Bahdanau 注意力 文本分类网络。

    前向传播流程:
        token_ids → Embedding → BiLSTM(2层) → Bahdanau Attention → FC → Softmax

    架构参数:
        - 词嵌入维度: embed_dim (256)
        - LSTM 隐状态维度: hidden_dim (128, 双向拼接后为 256)
        - 注意力维度: attn_dim (128)
        - Dropout: 0.5 (嵌入层后 + 全连接层前)
    """

    def __init__(self,
                 vocab_size: int,
                 num_classes: int,
                 embed_dim: int = 256,
                 hidden_dim: int = 128,
                 attn_dim: int = 128,
                 num_layers: int = 2,
                 dropout: float = 0.5,
                 pad_idx: int = 0):
        """
        Args:
            vocab_size: 词表大小
            num_classes: 类别数
            embed_dim: 词嵌入维度
            hidden_dim: LSTM 单向隐状态维度 (双向拼接后为 2*hidden_dim)
            attn_dim: 注意力投影维度
            num_layers: BiLSTM 层数
            dropout: Dropout 比率
            pad_idx: <PAD> 标记的索引
        """
        super().__init__()
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        self.bidirectional_dim = hidden_dim * 2  # 双向拼接后维度
        self.pad_idx = pad_idx

        # 词嵌入层: (vocab_size, embed_dim)
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_idx)

        # BiLSTM: 输入 embed_dim, 每方向 hidden_dim
        self.bilstm = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        # Bahdanau 注意力
        self.attention = BahdanauAttention(self.bidirectional_dim, attn_dim)

        # 分类器: 上下文向量 → num_classes
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(self.bidirectional_dim, num_classes)

        self.reset_parameters()

    def reset_parameters(self):
        """初始化 Embedding 和 FC 层参数。"""
        nn.init.xavier_uniform_(self.embedding.weight)
        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

    def forward(self, input_ids: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Args:
            input_ids: (batch, seq_len) token ID 序列

        Returns:
            logits: (batch, num_classes) 未归一化的类别得分
            attn_weights: (batch, seq_len) 注意力权重 (仅用于分析)
        """
        # 构建 <PAD> 掩码
        mask = (input_ids != self.pad_idx)  # (batch, seq_len)

        # 词嵌入: (batch, seq_len, embed_dim)
        embedded = self.embedding(input_ids)
        embedded = self.dropout(embedded)

        # BiLSTM: (batch, seq_len, hidden_dim*2)
        lstm_out, _ = self.bilstm(embedded)

        # Bahdanau 注意力: context (batch, hidden_dim*2), attn (batch, seq_len)
        context, attn_weights = self.attention(lstm_out, mask)

        # Dropout + 分类
        context = self.dropout(context)
        logits = self.fc(context)

        return logits, attn_weights


# ======================== 模型 B: 位置编码 ========================
class PositionalEncoding(nn.Module):
    """正弦/余弦 位置编码。

    数学原理:
        对于位置 pos 和维度 i:
            PE(pos, 2i)   = sin(pos / 10000^{2i/d_model})
            PE(pos, 2i+1) = cos(pos / 10000^{2i/d_model})

    该编码与词嵌入相加, 为 Transformer 提供序列位置信息。
    """

    def __init__(self, d_model: int, max_len: int = 512, dropout: float = 0.1):
        """
        Args:
            d_model: 模型维度 (必须与词嵌入维度相同)
            max_len: 最大序列长度
            dropout: Dropout 比率
        """
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # PE: (max_len, d_model)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)  # (max_len, 1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )  # (d_model/2,)

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        # 注册为 buffer (不参与梯度计算, 但随模型移动到 GPU)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, d_model) 词嵌入输出

        Returns:
            (batch, seq_len, d_model) 加入位置编码后的张量
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


# ======================== 模型 B: Transformer 分类器 ========================
class TransformerClassifier(nn.Module):
    """Transformer Encoder + 均值池化 文本分类网络。

    前向传播流程:
        token_ids → Embedding + PositionalEncoding → TransformerEncoder(4层,8头)
        → Mean Pooling → FC → Softmax

    架构参数:
        - d_model: 256
        - nhead: 8
        - num_encoder_layers: 4
        - dim_feedforward: 1024
        - Dropout: 0.3
    """

    def __init__(self,
                 vocab_size: int,
                 num_classes: int,
                 d_model: int = 256,
                 nhead: int = 8,
                 num_encoder_layers: int = 4,
                 dim_feedforward: int = 1024,
                 dropout: float = 0.3,
                 max_len: int = 128,
                 pad_idx: int = 0):
        """
        Args:
            vocab_size: 词表大小
            num_classes: 类别数
            d_model: 模型维度
            nhead: 多头注意力头数
            num_encoder_layers: Transformer 编码器层数
            dim_feedforward: 前馈网络隐藏层维度
            dropout: Dropout 比率
            max_len: 最大序列长度 (用于位置编码)
            pad_idx: <PAD> 索引
        """
        super().__init__()
        self.d_model = d_model
        self.pad_idx = pad_idx

        # 词嵌入
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=pad_idx)

        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model, max_len, dropout)

        # Transformer 编码器层
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='gelu',        # GELU 在 Transformer 中通常优于 ReLU
            batch_first=True,         # 使用 (batch, seq, dim) 格式
            norm_first=True,          # Pre-LN 结构, 训练更稳定
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_encoder_layers,
        )

        # 分类器
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(d_model, num_classes)

        self.reset_parameters()

    def reset_parameters(self):
        """初始化参数。"""
        nn.init.xavier_uniform_(self.embedding.weight)
        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """
        Args:
            input_ids: (batch, seq_len) token ID 序列

        Returns:
            logits: (batch, num_classes) 类别 logits
        """
        # <PAD> 掩码: True 表示需要屏蔽的位置 (与 PyTorch Transformer API 一致)
        # PyTorch Transformer 中 src_key_padding_mask 的 True 表示屏蔽
        pad_mask = (input_ids == self.pad_idx)  # (batch, seq_len)

        # 词嵌入 + 位置编码: (batch, seq_len, d_model)
        embedded = self.embedding(input_ids) * math.sqrt(self.d_model)
        src = self.pos_encoder(embedded)

        # Transformer 编码器
        # src_key_padding_mask: (batch, seq_len), True 表示忽略该位置
        memory = self.transformer_encoder(
            src,
            src_key_padding_mask=pad_mask,
        )  # (batch, seq_len, d_model)

        # 均值池化: 仅对非 <PAD> 位置取平均
        # 创建掩码: (batch, seq_len, 1)
        valid_mask = (~pad_mask).float().unsqueeze(-1)  # True→1.0, False→0.0
        memory = memory * valid_mask
        pooled = memory.sum(dim=1) / valid_mask.sum(dim=1).clamp(min=1)  # (batch, d_model)

        # Dropout + 分类
        pooled = self.dropout(pooled)
        logits = self.fc(pooled)

        return logits


# ======================== 工厂函数 ========================
def create_model(model_type: str, vocab_size: int, num_classes: int,
                 **kwargs) -> nn.Module:
    """根据模型类型创建对应的网络。

    Args:
        model_type: 'bilstm' 或 'transformer'
        vocab_size: 词表大小
        num_classes: 类别数
        **kwargs: 传递给具体模型构造函数的额外参数

    Returns:
        nn.Module 子类实例
    """
    model_type = model_type.lower()
    if model_type == 'bilstm':
        return BiLSTMAttention(
            vocab_size=vocab_size,
            num_classes=num_classes,
            embed_dim=kwargs.get('embed_dim', 256),
            hidden_dim=kwargs.get('hidden_dim', 128),
            attn_dim=kwargs.get('attn_dim', 128),
            num_layers=kwargs.get('num_layers', 2),
            dropout=kwargs.get('dropout', 0.5),
        )
    elif model_type == 'transformer':
        return TransformerClassifier(
            vocab_size=vocab_size,
            num_classes=num_classes,
            d_model=kwargs.get('d_model', 256),
            nhead=kwargs.get('nhead', 8),
            num_encoder_layers=kwargs.get('num_encoder_layers', 4),
            dim_feedforward=kwargs.get('dim_feedforward', 1024),
            dropout=kwargs.get('dropout', 0.3),
            max_len=kwargs.get('max_len', 128),
        )
    else:
        raise ValueError(f"不支持的模型类型: {model_type}. 可选: 'bilstm', 'transformer'")


# ======================== 模块自检 ========================
if __name__ == "__main__":
    print("=" * 60)
    print("models.py 模块自检")
    print("=" * 60)

    # 模拟参数
    VOCAB_SIZE = 5000
    NUM_CLASSES = 15
    BATCH_SIZE = 8
    SEQ_LEN = 20

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"运行设备: {device}")

    # 构造假数据
    dummy_input = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LEN)).to(device)

    # ---- 测试模型 A: BiLSTM + Attention ----
    print("\n[自检] 模型 A: BiLSTM + Attention")
    model_a = BiLSTMAttention(
        vocab_size=VOCAB_SIZE,
        num_classes=NUM_CLASSES,
        embed_dim=256,
        hidden_dim=128,
    ).to(device)

    model_a.eval()
    with torch.no_grad():
        logits_a, attn_a = model_a(dummy_input)
    print(f"  输入: {dummy_input.shape}")
    print(f"  logits: {logits_a.shape}")
    print(f"  注意力权重: {attn_a.shape}")
    print(f"  参数量: {sum(p.numel() for p in model_a.parameters()):,}")

    # ---- 测试模型 B: Transformer ----
    print("\n[自检] 模型 B: Transformer Encoder")
    model_b = TransformerClassifier(
        vocab_size=VOCAB_SIZE,
        num_classes=NUM_CLASSES,
        d_model=256,
        nhead=8,
        num_encoder_layers=4,
    ).to(device)

    model_b.eval()
    with torch.no_grad():
        logits_b = model_b(dummy_input)
    print(f"  输入: {dummy_input.shape}")
    print(f"  logits: {logits_b.shape}")
    print(f"  参数量: {sum(p.numel() for p in model_b.parameters()):,}")

    # ---- 测试工厂函数 ----
    print("\n[自检] 工厂函数 create_model()")
    for mtype in ['bilstm', 'transformer']:
        m = create_model(mtype, VOCAB_SIZE, NUM_CLASSES).to(device)
        params = sum(p.numel() for p in m.parameters())
        print(f"  create_model('{mtype}') → {m.__class__.__name__}, 参数量={params:,}")

    print("\n[自检] ✅ 双模型定义与 GPU 传输验证通过！")
