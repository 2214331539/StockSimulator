import os
import json
import pandas as pd
from datetime import datetime

class Database:
    """数据库类，用于管理用户数据和股票数据"""
    
    def __init__(self):
        """初始化数据库"""
        self.data_dir = "data"
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.stocks_file = os.path.join(self.data_dir, "stocks.json")
        self.transactions_dir = os.path.join(self.data_dir, "transactions")
        
        # 确保目录存在
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.transactions_dir, exist_ok=True)
        
        # 初始化数据文件
        self._initialize_data_files()
    
    def _initialize_data_files(self):
        """初始化数据文件"""
        # 初始化用户数据
        if not os.path.exists(self.users_file):
            default_users = {
                "admin": {
                    "password": "admin123",
                    "type": "admin",
                    "balance": 1000000.0,
                    "holdings": {},
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                "user": {
                    "password": "user123",
                    "type": "user",
                    "balance": 100000.0,
                    "holdings": {},
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(default_users, f, ensure_ascii=False, indent=4)
        
        # 初始化股票数据
        if not os.path.exists(self.stocks_file):
            # 使用更合理的涨跌幅初始值
            default_stocks = {
                "sh.000001": {"name": "上证指数", "price": 3369.24, "change": 0.82},
                "sh.600000": {"name": "浦发银行", "price": 11.71, "change": 0.43},
                "sh.601398": {"name": "工商银行", "price": 7.16, "change": -0.28},
                "sz.000001": {"name": "平安银行", "price": 11.16, "change": 1.73},
                "sz.000002": {"name": "万科A", "price": 6.85, "change": -1.15}
            }
            with open(self.stocks_file, "w", encoding="utf-8") as f:
                json.dump(default_stocks, f, ensure_ascii=False, indent=4)
    
    def get_users(self):
        """获取所有用户信息"""
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"获取用户信息出错: {e}")
            return {}
    
    def get_user(self, username):
        """获取指定用户信息"""
        users = self.get_users()
        return users.get(username)
    
    def authenticate_user(self, username, password):
        """验证用户登录"""
        user = self.get_user(username)
        if user and user.get("password") == password:
            return user
        return None
    
    def validate_user(self, username, password):
        """验证用户登录（与authenticate_user相同）"""
        user = self.authenticate_user(username, password)
        if user:
            # 添加username字段到用户信息中
            user_with_username = user.copy()
            user_with_username["username"] = username
            return user_with_username
        return None
    
    def user_exists(self, username):
        """检查用户名是否已存在"""
        users = self.get_users()
        return username in users
    
    def register_user(self, username, password, user_type="普通用户", initial_balance=100000.0):
        """注册新用户"""
        # 将"普通用户"转换为"user"，"管理员"转换为"admin"
        if user_type == "普通用户":
            user_type = "user"
        elif user_type == "管理员":
            user_type = "admin"
            
        return self.add_user(username, password, user_type, initial_balance)
    
    def add_user(self, username, password, user_type="user", initial_balance=100000.0):
        """添加用户"""
        users = self.get_users()
        if username in users:
            return False, "用户名已存在"
        
        users[username] = {
            "password": password,
            "type": user_type,
            "balance": initial_balance,
            "holdings": {},
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return True, "用户添加成功"
        except Exception as e:
            return False, f"添加用户出错: {e}"
    
    def update_user(self, username, data):
        """更新用户信息"""
        users = self.get_users()
        if username not in users:
            return False, "用户不存在"
        
        # 更新用户数据
        for key, value in data.items():
            users[username][key] = value
        
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return True, "用户信息更新成功"
        except Exception as e:
            return False, f"更新用户信息出错: {e}"
    
    def delete_user(self, username):
        """删除用户"""
        users = self.get_users()
        if username not in users:
            return False, "用户不存在"
        
        # 删除用户
        del users[username]
        
        try:
            with open(self.users_file, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=4)
            return True, "用户删除成功"
        except Exception as e:
            return False, f"删除用户出错: {e}"
    
    def get_stocks(self):
        """获取所有股票信息"""
        try:
            with open(self.stocks_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"获取股票信息出错: {e}")
            return {}
    
    def get_stock(self, code):
        """获取指定股票信息"""
        stocks = self.get_stocks()
        return stocks.get(code)
    
    def update_stock(self, code, data):
        """更新股票信息"""
        stocks = self.get_stocks()
        if code not in stocks:
            stocks[code] = {"name": data.get("name", code)}
        
        # 更新股票数据
        for key, value in data.items():
            stocks[code][key] = value
        
        try:
            with open(self.stocks_file, "w", encoding="utf-8") as f:
                json.dump(stocks, f, ensure_ascii=False, indent=4)
            return True, "股票信息更新成功"
        except Exception as e:
            return False, f"更新股票信息出错: {e}"
    
    def record_transaction(self, username, transaction_type, stock_code, stock_name, price, quantity, amount):
        """记录交易"""
        transaction = {
            "username": username,
            "type": transaction_type,  # "buy" 或 "sell"
            "stock_code": stock_code,
            "stock_name": stock_name,
            "price": price,
            "quantity": quantity,
            "amount": amount,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 用户交易记录文件
        user_transactions_file = os.path.join(self.transactions_dir, f"{username}_transactions.json")
        
        # 读取现有交易记录
        transactions = []
        if os.path.exists(user_transactions_file):
            try:
                with open(user_transactions_file, "r", encoding="utf-8") as f:
                    transactions = json.load(f)
            except:
                transactions = []
        
        # 添加新交易记录
        transactions.append(transaction)
        
        # 保存交易记录
        try:
            with open(user_transactions_file, "w", encoding="utf-8") as f:
                json.dump(transactions, f, ensure_ascii=False, indent=4)
            return True, "交易记录保存成功"
        except Exception as e:
            return False, f"保存交易记录出错: {e}"
    
    def get_user_transactions(self, username):
        """获取用户交易记录"""
        user_transactions_file = os.path.join(self.transactions_dir, f"{username}_transactions.json")
        
        if not os.path.exists(user_transactions_file):
            return []
        
        try:
            with open(user_transactions_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"获取用户交易记录出错: {e}")
            return []
    
    def execute_trade(self, username, transaction_type, stock_code, quantity):
        """执行交易"""
        user = self.get_user(username)
        stock = self.get_stock(stock_code)
        
        if not user:
            return False, "用户不存在"
        
        if not stock:
            return False, "股票不存在"
        
        price = stock["price"]
        amount = price * quantity
        
        if transaction_type == "buy":
            # 买入股票
            if user["balance"] < amount:
                return False, "余额不足"
            
            # 更新用户余额
            user["balance"] -= amount
            
            # 更新用户持仓
            if stock_code not in user["holdings"]:
                user["holdings"][stock_code] = {
                    "name": stock["name"],
                    "quantity": 0,
                    "cost": 0
                }
            
            # 计算新的持仓成本
            old_quantity = user["holdings"][stock_code]["quantity"]
            old_cost = user["holdings"][stock_code]["cost"]
            new_quantity = old_quantity + quantity
            new_cost = (old_cost * old_quantity + amount) / new_quantity if new_quantity > 0 else 0
            
            user["holdings"][stock_code]["quantity"] = new_quantity
            user["holdings"][stock_code]["cost"] = new_cost
            
        elif transaction_type == "sell":
            # 卖出股票
            if stock_code not in user["holdings"] or user["holdings"][stock_code]["quantity"] < quantity:
                return False, "持仓不足"
            
            # 更新用户余额
            user["balance"] += amount
            
            # 更新用户持仓
            user["holdings"][stock_code]["quantity"] -= quantity
            
            # 如果持仓为0，则删除该股票
            if user["holdings"][stock_code]["quantity"] == 0:
                del user["holdings"][stock_code]
        else:
            return False, "交易类型无效"
        
        # 更新用户信息
        success, message = self.update_user(username, user)
        if not success:
            return False, message
        
        # 记录交易
        success, message = self.record_transaction(
            username, transaction_type, stock_code, stock["name"], price, quantity, amount
        )
        if not success:
            return False, message
        
        return True, "交易成功"

# 创建数据库实例
db = Database() 