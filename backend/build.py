from PyInstaller import __main__ as pyi


params = [
    # 打包为单文件
    '-F', 
    # static目录纳入打包
    '--add-data', 'static;static',
    # 每次打包前清楚build 和 dist目录    
    '--clean',
    # 无需用户确认
    '--noconfirm',
    'app.py'
]
# pyinstaller -F main.py
pyi.run(params)