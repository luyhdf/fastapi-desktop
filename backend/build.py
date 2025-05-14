import os
import sys
from PyInstaller import __main__ as pyi

# 获取 i2cpy 驱动路径
import i2cpy
i2cpy_path = os.path.dirname(i2cpy.__file__)

# 构建参数
params = [
    # 打包为单文件
    '-F',
    # 添加数据文件
    '--add-data', f'{os.path.join(i2cpy_path, "driver")};i2cpy/driver',
    '--add-data', 'static;static',
    # 每次打包前清除 build 和 dist 目录
    '--clean',
    # 无需用户确认
    '--noconfirm',
    # 添加必要的隐藏导入
    # '--hidden-import', 'i2cpy',
    # 主程序
    'app.py'
]

# 运行 PyInstaller
pyi.run(params)