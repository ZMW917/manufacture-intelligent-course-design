# -*- coding: utf-8 -*-
"""
训练入口：命令行执行 `python -m src.train`。

输入 → 处理 → 输出：
  熔池图像(data/raw/images/) + 工艺参数(data/raw/process_params.csv)
  → 训练 CNN 分类器 + RF/SVR 回归模型
  → 保存到 config.CNN_MODEL_PATH / config.REGRESSOR_PATH，并打印训练指标

孤立森林为无监督算法，随用随拟合，无需训练产物。
"""
import os

from src.config import (
    ensure_dirs,
    IMAGES_DIR,
    RAW_DIR,
    NUM_CLASSES,
    CNN_MODEL_PATH,
    REGRESSOR_PATH,
)
from src.algorithms.cnn_classifier import CNNClassifier
from src.algorithms.regression import QualityRegressor


def main():
    # 确保 models/ 等目录存在
    ensure_dirs()

    # 工艺参数 CSV（CNN 训练从中读取 quality_label，回归从中读取特征与目标）
    params_csv = os.path.join(RAW_DIR, "process_params.csv")

    # ---- 1) 训练 CNN 熔池图像分类 ----
    print("[train] 开始训练 CNN 分类器 ...")
    cnn = CNNClassifier(model_path=None, num_classes=NUM_CLASSES, input_size=64)
    cnn_metrics = cnn.train(
        images_dir=IMAGES_DIR,
        labels_csv=params_csv,
        epochs=8,
        batch_size=16,
        save_path=CNN_MODEL_PATH,
    )
    print("[train] CNN 训练完成，指标：train_acc=%.4f val_acc=%.4f epochs=%d"
          % (cnn_metrics.get("train_acc", 0.0),
             cnn_metrics.get("val_acc", 0.0),
             cnn_metrics.get("epochs", 0)))
    print("[train] CNN 模型已保存到:", CNN_MODEL_PATH)

    # ---- 2) 训练回归模型（随机森林 + SVR）----
    print("[train] 开始训练回归模型（RF + SVR）...")
    # 注：train() 只返回指标，落盘需显式调用 save() 到 config.REGRESSOR_PATH
    regressor = QualityRegressor()
    reg_metrics = regressor.train(params_csv)
    regressor.save(REGRESSOR_PATH)
    print("[train] 回归训练完成，指标：rf_r2_density=%.4f svr_r2_density=%.4f"
          % (reg_metrics.get("rf_r2_density", 0.0),
             reg_metrics.get("svr_r2_density", 0.0)))
    print("[train] RF 特征重要性:", reg_metrics.get("rf_importances", {}))
    print("[train] 回归模型已保存到:", REGRESSOR_PATH)

    print("[train] 全部训练完成。")


if __name__ == "__main__":
    main()
