# -*- coding: utf-8 -*-
"""
pytest 根配置（conftest.py）。

作用：把项目根目录加入 sys.path，使测试文件里 `import src.xxx`、
`from src.algorithms...`、`from src.main import app` 都能正常解析到项目源码。
该文件位于项目根目录，pytest 收集用例时会最先加载，从而保证路径在导入前生效。
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
