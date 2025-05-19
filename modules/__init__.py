# 股票模拟交易系统模块
# 此文件为模块初始化文件，确保模块可以正确导入

# 导出模块
from .database import db
from .stock_data import stock_manager
from .login import LoginFrame
from .market import MarketFrame
from .trading import TradingFrame
from .news import NewsFrame
from .account import AccountFrame
from .admin import AdminFrame