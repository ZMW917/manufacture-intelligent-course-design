# -*- coding: utf-8 -*-
"""
一键启动后端入口。

作用：以 uvicorn 启动 src.main:app，监听 0.0.0.0:8000。
顶部先做 sys.path 处理，把项目根目录加入导入路径，保证无论从哪个目录运行，
都能正确 import 到 src.main。

用法：python scripts/run_backend.py
"""
import sys
import os

# 项目根目录 = 本文件所在目录（scripts/）的上一级
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
