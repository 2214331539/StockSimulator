import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
from ttkbootstrap.dialogs import Messagebox
import sys
import os
from modules.login import LoginFrame
from modules.market import MarketFrame
from modules.trading import TradingFrame
from modules.news import NewsFrame
from modules.account import AccountFrame


class StockSimulationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股票模拟交易系统")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        # 设置ttkbootstrap暗色主题  
        self.style = Style(theme="darkly") 
        
        # 用户信息
        self.current_user = None        # 登录后赋值
        self.user_type = None           # "admin" 或 "user"
        
        # 创建登录框架
        self.login_frame = LoginFrame(self.root, self.handle_login_success)
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建主内容框架（初始隐藏）
        self.main_frame = tb.Frame(self.root, bootstyle="dark")
        
        # 创建导航栏
        self.nav_frame = tb.Frame(self.main_frame, bootstyle="dark")
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建内容区域
        self.content_frame = tb.Frame(self.main_frame, bootstyle="dark")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 存储各个页面框架
        self.frames = {}
        
    def handle_login_success(self, user):
        """登录回调函数"""
        self.current_user = user["username"]
        self.user_type = user["type"]
        
        # 隐藏登录框架
        self.login_frame.pack_forget()
        
        # 显示主框架
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建导航按钮
        self.create_navigation()
        
        # 初始化各个页面
        self.initialize_frames()
        
        # 默认显示市场页面
        self.show_frame("market")
    
    def create_navigation(self):
        """创建导航栏"""
        # 清空导航栏
        for widget in self.nav_frame.winfo_children():
            widget.destroy()
        
        # 添加用户信息
        user_info = tb.Label(self.nav_frame, text=f"用户: {self.current_user}", bootstyle="inverse-dark", font=("微软雅黑", 12, "bold"))
        user_info.pack(pady=10, padx=10, fill=tk.X)
        
        # 添加导航按钮
        nav_buttons = [
            ("市场信息", "market", self.show_market, "outline-info"),
            ("交易操作", "trading", self.show_trading, "outline-success"),
            ("股票推荐", "recommendation", self.show_recommendation, "outline-warning"),
            ("新闻资讯", "news", self.show_news, "outline-secondary"),
            ("账户信息", "account", self.show_account, "outline-primary")
        ]
        
        # 如果是管理员，添加管理员页面
        if self.user_type == "admin":
            nav_buttons.append(("用户管理", "admin", self.show_admin, "outline-danger"))
        
        # 创建按钮
        for text, name, command, style in nav_buttons:
            btn = tb.Button(self.nav_frame, text=text, command=command, bootstyle=style, width=15)
            btn.pack(fill=tk.X, pady=5, padx=10)
        
        # 添加登出按钮
        logout_btn = tb.Button(self.nav_frame, text="退出登录", command=self.logout, bootstyle="outline-secondary", width=15)
        logout_btn.pack(fill=tk.X, pady=5, padx=10, side=tk.BOTTOM)
    
    def initialize_frames(self):
        """初始化各个页面框架"""
        # 市场信息页面
        self.frames["market"] = MarketFrame(self.content_frame, self.current_user)
        
        # 交易操作页面
        self.frames["trading"] = TradingFrame(self.content_frame, self.current_user)
        
        # 股票推荐页面
        from modules.recommendation import RecommendationFrame
        self.frames["recommendation"] = RecommendationFrame(self.content_frame, self.current_user)
        
        # 新闻资讯页面
        self.frames["news"] = NewsFrame(self.content_frame)
        
        # 账户信息页面
        self.frames["account"] = AccountFrame(self.content_frame, self.current_user)
        
        # 如果是管理员，创建管理员页面
        if self.user_type == "admin":
            from modules.admin import AdminFrame
            self.frames["admin"] = AdminFrame(self.content_frame)
    
    def show_frame(self, frame_name):
        """显示指定的页面"""
        # 隐藏所有页面
        for frame in self.frames.values():
            frame.pack_forget()
        
        # 显示指定页面
        self.frames[frame_name].pack(fill=tk.BOTH, expand=True)
    
    def show_market(self):
        """显示市场信息页面"""
        self.show_frame("market")
    
    def show_trading(self):
        """显示交易操作页面"""
        self.show_frame("trading")
    
    def show_recommendation(self):
        """显示股票推荐页面"""
        self.show_frame("recommendation")
    
    def show_news(self):
        """显示新闻资讯页面"""
        self.show_frame("news")
    
    def show_account(self):
        """显示账户信息页面"""
        self.show_frame("account")
    
    #此部分代码仅仅执行了显示admin的工作，没有处理其他页面，暂定，先看admin结果
    def show_admin(self):
        """显示管理员页面"""
        if self.user_type == "admin" and "admin" in self.frames:
            self.show_frame("admin")
        
    
    def logout(self):
        """退出登录"""
        # 确认是否退出
        if Messagebox.yesno("确认退出", "确定要退出登录吗？"):
            # 清理当前用户会话的框架
            for frame_name in list(self.frames.keys()): # 使用keys()的副本进行迭代
                if self.frames[frame_name] is not None:
                    self.frames[frame_name].destroy()
            self.frames.clear() # 清空框架字典

            # 额外确保content_frame被清空
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            
            # 清空用户信息
            self.current_user = None
            self.user_type = None
            
            # 隐藏主框架
            self.main_frame.pack_forget()
            
            # 显示登录框架
            self.login_frame.pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("data", exist_ok=True)
    
    # 启动应用
    root = tb.Window(themename="darkly")
    app = StockSimulationApp(root)
    root.mainloop() 