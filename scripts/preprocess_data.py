import os
from PIL import Image
import pandas as pd

# 定义文件夹路径
raw_dir = "./data/raw"
processed_dir = "./data/processed"

# 如果processed文件夹不存在，就创建一个
if not os.path.exists(processed_dir):
    os.makedirs(processed_dir)

# 获取raw文件夹里所有图片的名字
image_files = [f for f in os.listdir(raw_dir) if f.endswith(('.tif', '.jpg', '.png'))]

# 这个列表用来记录每张图片的信息
records = []

# 对每张图片进行处理
for idx, filename in enumerate(image_files):
    # 打开图片
    img_path = os.path.join(raw_dir, filename)
    img = Image.open(img_path)
    
    # 把图片统一改成 224x224 的尺寸
    img_resized = img.resize((224, 224))
    
    # 保存处理后的图片，名字改为 "processed_0.jpg", "processed_1.jpg" 这种形式
    new_filename = f"processed_{idx}.jpg"
    save_path = os.path.join(processed_dir, new_filename)
    img_resized.convert('RGB').save(save_path, 'JPEG')
    
    # 根据原文件名猜它是"好"的还是"坏"的，用于以后做标签
    if 'defect' in filename.lower():
        label = 1  # 有缺陷
    elif 'ok' in filename.lower() or 'good' in filename.lower():
        label = 0  # 合格
    else:
        label = -1 # 未知
    
    # 记录这张图片的信息
    records.append({
        '原始文件名': filename,
        '处理后文件名': new_filename,
        '标签': label,
        '路径': save_path
    })

# 把所有图片的信息保存成一个索引表格（CSV文件）
df = pd.DataFrame(records)
df.to_csv(os.path.join(processed_dir, 'index.csv'), index=False)

print(f"搞定！一共处理了 {len(image_files)} 张图片。")