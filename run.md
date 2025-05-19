# 使用python内置的venv模块创建名为.venv的新虚拟环境
python -m venv .venv

# 激活虚拟环境
.\.venv\Scripts\Activate

# 安装requirements.txt中列出的所有依赖
pip install -r requirements.txt

# 运行
python stock_simulation_system.py


