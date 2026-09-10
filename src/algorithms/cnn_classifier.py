# -*- coding: utf-8 -*-
"""
LPBF 激光增材制造 · 熔池图像质量分类模块（深度学习 CNN，对应方案设计 3.5 节）

输入 → 处理 → 输出
==================
输入：
  - 训练：images_dir（熔池灰度图目录） + labels_csv（含 sample_id / quality_label 两列）
  - 预测：单张熔池图（H×W 或 H×W×3 的 numpy 数组，或图片文件路径）

处理：
  1) 顶层模型 = ResNet-18（torchvision.models.resnet18(weights=None)），离线随机初始化、
     不下载预训练权重；把第一层 conv1 改为 1 通道，最后一层 fc 改为 num_classes 输出
  2) 输入统一 resize 到 64×64 单通道、像素归一化到 [0,1]，再按均值/方差 0.5/0.5
     标准化到 [-1,1]（简化处理：不额外统计训练集均值方差，训练/预测共用同一常数）
  3) 训练：固定随机种子(42)，按 80/20 划分 train/val，CrossEntropyLoss + Adam，
     每个 epoch 打印 loss / train_acc / val_acc，并保存验证集最优的模型权重
  4) 推理：与训练一致的预处理后前向传播，softmax 得到三分类概率

输出：
  - train:  {'train_acc': float, 'val_acc': float, 'epochs': int}
  - predict: {'label': int, 'label_name': str, 'confidence': float,
              'probs': [float, float, float]}

依赖：torch / torchvision（离线）+ numpy / pandas / OpenCV，不联网可运行。
"""
import os
import re

import cv2
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset, Subset
from torchvision import models

from src.config import LABEL_NAMES, NUM_CLASSES

# 训练/预测共用的图像标准化常数（简化方案）：把 [0,1] 像素映射到 [-1,1]
NORM_MEAN = 0.5
NORM_STD = 0.5

# 支持的图片扩展名（训练时从 images_dir 里筛选）
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def _to_gray_uint8(image):
    """把任意输入图统一转换为 8-bit 单通道灰度图（与 image_preprocess 保持一致）。"""
    arr = np.asarray(image)
    if arr.ndim == 3:
        if arr.shape[2] == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        elif arr.shape[2] == 4:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGRA2GRAY)
        else:
            arr = arr[:, :, 0]
    elif arr.ndim != 2:
        raise ValueError("输入图像需为 H×W 或 H×W×3，实际维度: %d" % arr.ndim)

    if arr.dtype != np.uint8:
        arr = arr.astype(np.float32)
        if arr.max() <= 1.0:
            arr = arr * 255.0
        else:
            lo, hi = arr.min(), arr.max()
            arr = (arr - lo) / (hi - lo) * 255.0 if hi > lo else np.zeros_like(arr)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return arr


def _gray_to_tensor(gray, input_size):
    """8-bit 单通道灰度图 -> (1, H, W) 的 float32 tensor（已归一化到 [-1,1]）。"""
    gray = cv2.resize(gray, (input_size, input_size), interpolation=cv2.INTER_LINEAR)
    x = gray.astype(np.float32) / 255.0               # 归一化到 [0,1]
    x = (x - NORM_MEAN) / NORM_STD                    # 均值/方差 0.5/0.5 -> [-1,1]
    return torch.from_numpy(x).unsqueeze(0)           # 增加通道维 -> (1,H,W)


class _MeltPoolDataset(Dataset):
    """训练用数据集：根据 (图片路径, 标签) 逐条加载并做预处理。"""

    def __init__(self, image_paths, labels, input_size=64):
        self.image_paths = list(image_paths)
        self.labels = [int(l) for l in labels]
        self.input_size = input_size

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img = cv2.imread(self.image_paths[idx], cv2.IMREAD_GRAYSCALE)
        if img is None:
            # 读取失败时退化为全黑图，避免训练中断
            img = np.zeros((self.input_size, self.input_size), dtype=np.uint8)
        tensor = _gray_to_tensor(img, self.input_size)
        label = torch.tensor(self.labels[idx], dtype=torch.long)
        return tensor, label


class CNNClassifier:
    """基于 ResNet-18（1 通道，离线随机初始化）的熔池质量三分类器。"""

    def __init__(self, model_path=None, num_classes=3, input_size=64):
        self.num_classes = num_classes
        self.input_size = input_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._build_model(num_classes).to(self.device)
        self.model.eval()
        # 有模型权重文件时自动加载
        if model_path is not None and os.path.exists(model_path):
            self.load(model_path)

    # ------------------------------------------------------------------ #
    # 模型构造
    # ------------------------------------------------------------------ #
    def _build_model(self, num_classes):
        """构造 ResNet-18：conv1 改 1 通道，fc 改 num_classes，weights=None 离线可用。"""
        model = models.resnet18(weights=None)
        # 原 conv1 接受 3 通道，改为 1 通道（熔池灰度图）
        model.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False)
        # 全连接层输出维度改为 num_classes
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    # ------------------------------------------------------------------ #
    # 训练
    # ------------------------------------------------------------------ #
    def train(self, images_dir, labels_csv, epochs=8, batch_size=16, save_path=None):
        """训练 CNN 分类器。

        :param images_dir: 图像目录（文件名形如 sample_000.png）
        :param labels_csv: 标签 CSV 路径，需含 sample_id 与 quality_label 两列
        :param epochs: 训练轮数
        :param batch_size: 批大小
        :param save_path: 保存最优模型的路径（None 则不落盘）
        :return: {'train_acc': float, 'val_acc': float, 'epochs': int}
        """
        # 固定随机种子，保证可复现
        torch.manual_seed(42)
        np.random.seed(42)

        image_paths, labels = self._collect_samples(images_dir, labels_csv)
        if len(image_paths) == 0:
            raise ValueError("images_dir 与 labels_csv 未匹配到任何样本，无法训练")

        dataset = _MeltPoolDataset(image_paths, labels, self.input_size)

        # 80/20 划分 train/val（先打乱索引再切分，保证类别均衡近似）
        indices = np.random.permutation(len(dataset))
        split = int(0.8 * len(indices))
        train_loader = DataLoader(Subset(dataset, indices[:split]),
                                  batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(Subset(dataset, indices[split:]),
                                batch_size=batch_size, shuffle=False)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=1e-3)

        best_val_acc = 0.0
        last_train_acc = 0.0
        self.model.train()

        for epoch in range(1, epochs + 1):
            running_loss = 0.0
            correct = total = 0
            for images, targets in train_loader:
                images, targets = images.to(self.device), targets.to(self.device)
                optimizer.zero_grad()
                outputs = self.model(images)
                loss = criterion(outputs, targets)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * images.size(0)
                correct += (outputs.argmax(dim=1) == targets).sum().item()
                total += targets.size(0)

            last_train_acc = correct / total if total else 0.0
            val_acc = self._evaluate(val_loader)
            print("Epoch %d/%d  loss=%.4f  train_acc=%.4f  val_acc=%.4f"
                  % (epoch, epochs, running_loss / total, last_train_acc, val_acc))

            # 记录验证集最优模型
            if val_acc >= best_val_acc:
                best_val_acc = val_acc
                if save_path is not None:
                    self._save(save_path)

        self.model.eval()
        return {
            "train_acc": float(last_train_acc),
            "val_acc": float(best_val_acc),
            "epochs": int(epochs),
        }

    # ------------------------------------------------------------------ #
    # 预测
    # ------------------------------------------------------------------ #
    def predict(self, image):
        """对单张熔池图做三分类推理。

        :param image: H×W 或 H×W×3 的 numpy 数组，或图片文件路径
        :return: {'label': int, 'label_name': str, 'confidence': float,
                  'probs': [float, float, float]}
        """
        if isinstance(image, (str, os.PathLike)):
            img = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError("无法读取图片: %s" % image)
            gray = img
        else:
            gray = _to_gray_uint8(image)

        tensor = _gray_to_tensor(gray, self.input_size).unsqueeze(0)  # (1,1,H,W)
        tensor = tensor.to(self.device)

        self.model.eval()
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().numpy()

        label = int(np.argmax(probs))
        confidence = float(probs[label])
        return {
            "label": label,
            "label_name": LABEL_NAMES[label],
            "confidence": confidence,
            "probs": [float(p) for p in probs],
        }

    # ------------------------------------------------------------------ #
    # 持久化
    # ------------------------------------------------------------------ #
    def _save(self, path):
        """把模型权重连同超参存成 dict，便于后续 load 恢复。"""
        if os.path.dirname(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "num_classes": self.num_classes,
            "input_size": self.input_size,
        }, path)
        return path

    def load(self, path):
        """从 .pth 文件恢复模型权重。"""
        if not os.path.exists(path):
            raise FileNotFoundError("模型文件不存在: %s" % path)
        ckpt = torch.load(path, map_location="cpu")

        if isinstance(ckpt, dict) and "state_dict" in ckpt:
            num_classes = ckpt.get("num_classes", self.num_classes)
            input_size = ckpt.get("input_size", self.input_size)
            # 超参不一致时按存档重建模型结构
            if num_classes != self.num_classes or input_size != self.input_size:
                self.num_classes = num_classes
                self.input_size = input_size
                self.model = self._build_model(num_classes)
            state_dict = ckpt["state_dict"]
        else:
            state_dict = ckpt

        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        return self

    # ------------------------------------------------------------------ #
    # 工具
    # ------------------------------------------------------------------ #
    def _collect_samples(self, images_dir, labels_csv):
        """从 CSV 与图像目录收集 (路径, 标签) 对，按 sample_id 对齐。"""
        df = pd.read_csv(labels_csv)
        for col in ("sample_id", "quality_label"):
            if col not in df.columns:
                raise ValueError("labels_csv 缺少列: %s" % col)
        label_map = {int(r["sample_id"]): int(r["quality_label"])
                     for _, r in df.iterrows()}

        image_paths, labels = [], []
        files = sorted(f for f in os.listdir(images_dir)
                       if f.lower().endswith(_IMAGE_EXTS))
        for fname in files:
            sid = self._parse_sample_id(fname)
            if sid is None or sid not in label_map:
                continue
            image_paths.append(os.path.join(images_dir, fname))
            labels.append(label_map[sid])
        return image_paths, labels

    @staticmethod
    def _parse_sample_id(fname):
        """从 'sample_000.png' 之类的文件名解析出末尾数字作为 sample_id。"""
        stem = os.path.splitext(fname)[0]
        m = re.search(r"(\d+)\s*$", stem)
        return int(m.group(1)) if m else None

    def _evaluate(self, loader):
        """在给定 DataLoader 上计算分类准确率。"""
        self.model.eval()
        correct = total = 0
        with torch.no_grad():
            for images, targets in loader:
                images, targets = images.to(self.device), targets.to(self.device)
                outputs = self.model(images)
                correct += (outputs.argmax(dim=1) == targets).sum().item()
                total += targets.size(0)
        return correct / total if total else 0.0
