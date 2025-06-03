"""
股票模拟交易系统模块包
"""

# 导出模块
from .database import db
from .stock_data import stock_manager
from .login import LoginFrame
from .market import MarketFrame
from .trading import TradingFrame
from .recommendation import RecommendationFrame, StockRecommendationEngine
from .news import NewsFrame
from .account import AccountFrame
from .admin import AdminFrame

__all__ = [
    'db', 'stock_manager', 'LoginFrame', 'MarketFrame', 
    'TradingFrame', 'RecommendationFrame', 'StockRecommendationEngine',
    'NewsFrame', 'AccountFrame', 'AdminFrame'
]