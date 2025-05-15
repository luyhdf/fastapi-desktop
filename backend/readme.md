python >= 3.10

# 创建虚拟环境
conda create -n fastapi-desktop python=3.10
conda activate fastapi-desktop

# 安装依赖
pip install -r requirements.txt

# 运行web
python src/web.py
# 运行app
python src/app.py

# 打包app
python build.py


