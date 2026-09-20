# -*- coding: utf-8 -*-
"""
生成 LPBF 增材制造熔池样例数据集（合成数据，供离线 demo 与自动化测试）
说明：本样例数据为程序合成的模拟数据，仅用于功能演示与单元测试，
     真实数据请按 data/README.md 中的说明从 NIST AM-Bench 等公开数据集获取。
"""
import os
import numpy as np
import pandas as pd

# 固定随机种子，保证可复现
RNG = np.random.default_rng(42)

# 图像合成单独用一条随机流：工艺参数/标签与图像形态互不干扰，
# 今后单独调整图像生成逻辑时，process_params.csv 与 sensor_timeseries.csv 不会再被连带改变。
IMG_RNG = np.random.default_rng(2024)

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
IMG_DIR = os.path.join(RAW_DIR, "images")
os.makedirs(IMG_DIR, exist_ok=True)

N = 200  # 样本数


def melt_pool_image(label, size=64):
    """合成一张熔池灰度图：椭圆亮斑 + 噪声，三类各有可辨识的形态特征。

    类别 0（致密）  ：规整椭圆亮斑，内部均匀；
    类别 1（气孔）  ：椭圆亮斑内部叠加数个暗色圆形气孔（气体在熔池内形成的球状孔洞）；
    类别 2（裂纹/未熔合）：亮斑更细长、不规则。
    """
    img = np.zeros((size, size), dtype=np.float32)
    cy, cx = size // 2 + IMG_RNG.uniform(-4, 4), size // 2 + IMG_RNG.uniform(-4, 4)
    a, b = IMG_RNG.uniform(14, 20), IMG_RNG.uniform(10, 16)
    if label == 2:  # 裂纹/未熔合：更细长、不规则
        a, b = IMG_RNG.uniform(6, 12), IMG_RNG.uniform(18, 26)
    yy, xx = np.mgrid[0:size, 0:size]
    e = ((xx - cx) / a) ** 2 + ((yy - cy) / b) ** 2
    img[e <= 1] = IMG_RNG.uniform(200, 255, size=int(np.sum(e <= 1)))

    if label == 1:  # 气孔：在熔池内部挖出若干暗色圆形孔洞
        for _ in range(IMG_RNG.integers(3, 7)):
            pr = IMG_RNG.uniform(1.5, 3.0)              # 气孔半径（像素）
            ang = IMG_RNG.uniform(0, 2 * np.pi)
            rad = IMG_RNG.uniform(0, 0.6)               # 归一化半径，保证孔洞落在熔池内
            hx = cx + rad * a * np.cos(ang)
            hy = cy + rad * b * np.sin(ang)
            img[((xx - hx) ** 2 + (yy - hy) ** 2) <= pr ** 2] = IMG_RNG.uniform(20, 60)

    img += IMG_RNG.normal(0, 6, img.shape)  # 高斯噪声
    img = np.clip(img, 0, 255).astype(np.uint8)
    return img


def save_png(img, path):
    try:
        from PIL import Image
        Image.fromarray(img, mode="L").save(path)
    except ImportError:
        np.save(path[:-4] + ".npy", img)  # 无 PIL 时退化为 npy


rows = []
labels = []
for i in range(N):
    # 工艺参数
    laser_power = RNG.uniform(180, 320)          # W
    scan_speed = RNG.uniform(600, 1200)          # mm/s
    layer_thickness = RNG.uniform(30, 60)        # um
    hatch_spacing = RNG.uniform(70, 120)         # um

    # 能量密度（体能量密度，J/mm^3）
    energy_density = laser_power / (scan_speed * layer_thickness * hatch_spacing * 1e-6)

    # 根据能量密度区间生成质量标签（带噪声）
    if 40 <= energy_density <= 120:
        label = RNG.choice([0, 1], p=[0.8, 0.2])  # 多数致密良好
    elif energy_density < 40:
        label = RNG.choice([2, 1], p=[0.7, 0.3])            # 低能量→未熔合/裂纹
    else:
        label = RNG.choice([1, 0], p=[0.7, 0.3])            # 高能量→气孔

    # 致密度（0~1），与标签相关
    density = {"0": RNG.uniform(0.995, 0.9999),
               "1": RNG.uniform(0.95, 0.99),
               "2": RNG.uniform(0.88, 0.95)}[str(label)]

    # 熔池图像（合成）
    img = melt_pool_image(label)
    img_path = os.path.join(IMG_DIR, f"sample_{i:03d}.png")
    save_png(img, img_path)

    rows.append({
        "sample_id": i,
        "laser_power_W": round(laser_power, 2),
        "scan_speed_mm_s": round(scan_speed, 2),
        "layer_thickness_um": round(layer_thickness, 2),
        "hatch_spacing_um": round(hatch_spacing, 2),
        "energy_density_J_mm3": round(energy_density, 4),
        "density": round(density, 4),
        "quality_label": label,   # 0=致密良好 1=气孔 2=裂纹/未熔合
    })
    labels.append(label)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(RAW_DIR, "process_params.csv"), index=False, encoding="utf-8-sig")

# 传感器时序数据：若干"打印任务"的熔池温度曲线（含异常段）
sensor_rows = []
for job in range(6):
    t = np.arange(100)
    base = 1500 + RNG.normal(0, 15, t.shape)          # 熔池温度 °C
    if job % 3 == 0:                                   # 注入异常（温度骤降/骤升，短时强尖峰）
        base[45:50] += RNG.choice([-600, 600])
    oxy = 500 + RNG.normal(0, 8, t.shape)             # 氧含量 ppm
    for k in range(100):
        sensor_rows.append({
            "job_id": job, "time_step": k,
            "melt_pool_temp_C": round(float(base[k]), 2),
            "oxygen_ppm": round(float(oxy[k]), 2),
        })
sdf = pd.DataFrame(sensor_rows)
sdf.to_csv(os.path.join(RAW_DIR, "sensor_timeseries.csv"), index=False, encoding="utf-8-sig")

print(f"生成完成：{N} 张图像、{len(df)} 条参数记录、{len(sdf)} 条传感器时序")
print("标签分布：", pd.Series(labels).value_counts().to_dict())
print("图像目录：", IMG_DIR)
