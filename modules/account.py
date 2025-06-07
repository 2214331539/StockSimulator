import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style  # 显式导入Style
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
import matplotlib
from .database import db
from datetime import datetime

# 设置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Heiti TC', 'WenQuanYi Micro Hei', 'Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
# 设置matplotlib深色背景风格
plt.style.use('dark_background')

# 定义全局颜色变量
BACKGROUND_COLOR = "#0d1926"  # 深蓝色背景
TEXT_COLOR = "#ffffff"  # 白色文本
ACCENT_COLOR = "#1e90ff"  # 亮蓝色强调色
UP_COLOR = "#ff4d4d"  # 上涨颜色(红色)
DOWN_COLOR = "#00e676"  # 下跌颜色(绿色)
GRID_COLOR = "#1a3c5e"  # 网格线颜色
CHART_BG_COLOR = "#0d1926"  # 图表背景色
CHART_AREA_COLOR = "#142638"  # 图表区域色

class AccountFrame(tb.Frame):
    """账户信息页面框架"""
    
    def __init__(self, parent, username):
        super().__init__(parent, bootstyle="dark")
        self.username = username
        
        # 使用bootstyle而不是background
        # self.configure(background=BACKGROUND_COLOR)
        
        # 创建标题
        self.title_label = tb.Label(self, text="账户信息", font=("微软雅黑", 16, "bold"), 
                                  bootstyle="inverse-dark")
        self.title_label.pack(pady=10, padx=10, anchor="w")
        
        # 创建主框架，分为左右两部分
        self.main_frame = tb.Frame(self, bootstyle="dark")
        # self.main_frame.configure(background=BACKGROUND_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧账户信息框架
        self.left_frame = tb.Frame(self.main_frame, bootstyle="dark")
        # self.left_frame.configure(background=BACKGROUND_COLOR)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建右侧图表框架
        self.right_frame = tb.Frame(self.main_frame, bootstyle="dark")
        # self.right_frame.configure(background=BACKGROUND_COLOR)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建账户信息区域
        self.create_account_info()
        
        # 创建持仓信息区域
        self.create_holdings_info()
        
        # 创建图表区域
        self.create_charts()
        
        # 创建刷新按钮
        self.refresh_btn = tb.Button(self.left_frame, text="刷新账户数据", command=self.load_account_data, 
                                   bootstyle="info-outline")
        self.refresh_btn.pack(pady=10)
        
        # 创建状态栏
        self.status_frame = tb.Frame(self, bootstyle="dark")
        # self.status_frame.configure(background=BACKGROUND_COLOR)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = tb.Label(self.status_frame, textvariable=self.status_var, 
                                   bootstyle="info")
        self.status_label.pack(side=tk.LEFT, fill=tk.X, padx=10, pady=5)
        
        # 加载数据
        self.load_account_data()
    
    def create_account_info(self):
        """创建账户信息区域"""
        # 创建账户信息框架
        account_frame = tb.LabelFrame(self.left_frame, text="账户概览", bootstyle="info")
        # account_frame.configure(background=BACKGROUND_COLOR, foreground=TEXT_COLOR)
        account_frame.pack(fill=tk.X, pady=10)
        
        # 用户名
        tb.Label(account_frame, text="用户名:", bootstyle="light").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.username_var = tk.StringVar(value=self.username)
        tb.Label(account_frame, textvariable=self.username_var, bootstyle="info").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 账户余额
        tb.Label(account_frame, text="可用资金:", bootstyle="light").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.balance_var = tk.StringVar()
        tb.Label(account_frame, textvariable=self.balance_var, bootstyle="info").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 持仓市值
        tb.Label(account_frame, text="持仓市值:", bootstyle="light").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.holdings_value_var = tk.StringVar()
        tb.Label(account_frame, textvariable=self.holdings_value_var, bootstyle="info").grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # 账户总值
        tb.Label(account_frame, text="账户总值:", bootstyle="light").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.total_value_var = tk.StringVar()
        tb.Label(account_frame, textvariable=self.total_value_var, bootstyle="info").grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        # 总盈亏
        tb.Label(account_frame, text="总盈亏:", bootstyle="light").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.profit_var = tk.StringVar()
        self.profit_label = tb.Label(account_frame, textvariable=self.profit_var, bootstyle="light")
        self.profit_label.grid(row=4, column=1, sticky="w", padx=10, pady=5)
    
    def create_holdings_info(self):
        """创建持仓信息区域"""
        # 创建标题
        holdings_title = tb.Label(self.left_frame, text="持仓信息", font=("微软雅黑", 12, "bold"), 
                                bootstyle="info")
        holdings_title.pack(pady=10, anchor="w")
        
        # 创建持仓列表框架
        self.holdings_frame = tb.Frame(self.left_frame, bootstyle="dark")
        # self.holdings_frame.configure(background=BACKGROUND_COLOR)
        self.holdings_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建持仓列表
        columns = ('代码', '名称', '持仓', '成本价', '现价', '市值', '盈亏', '盈亏率')
        self.holdings_tree = tb.Treeview(self.holdings_frame, columns=columns, show='headings', bootstyle="dark")
        
        # 设置列标题
        for col in columns:
            self.holdings_tree.heading(col, text=col)
        
        # 设置列宽
        self.holdings_tree.column('代码', width=80)
        self.holdings_tree.column('名称', width=80)
        self.holdings_tree.column('持仓', width=60)
        self.holdings_tree.column('成本价', width=60)
        self.holdings_tree.column('现价', width=60)
        self.holdings_tree.column('市值', width=80)
        self.holdings_tree.column('盈亏', width=80)
        self.holdings_tree.column('盈亏率', width=60)
        
        # 设置表格样式
        style = Style()
        style.configure("Treeview", 
                      background=CHART_AREA_COLOR, 
                      foreground=TEXT_COLOR, 
                      fieldbackground=CHART_AREA_COLOR)
        style.configure("Treeview.Heading", 
                       background=BACKGROUND_COLOR, 
                       foreground=TEXT_COLOR)
        style.map('Treeview', 
                 background=[('selected', ACCENT_COLOR)],
                 foreground=[('selected', TEXT_COLOR)])
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(self.holdings_frame, orient=tk.VERTICAL, command=self.holdings_tree.yview, 
                               bootstyle="round-dark")
        self.holdings_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.holdings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_charts(self):
        """创建图表区域"""
        # 创建资产分布图表
        self.create_asset_distribution_chart()
        
        # 创建持仓分布图表
        self.create_holdings_distribution_chart()
    
    def create_asset_distribution_chart(self):
        """创建资产分布图表"""
        # 创建资产分布图表框架
        self.asset_chart_frame = tb.Frame(self.right_frame, bootstyle="dark")
        # self.asset_chart_frame.configure(background=BACKGROUND_COLOR)
        self.asset_chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建资产分布图表
        self.asset_fig, self.asset_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.asset_fig.subplots_adjust(bottom=0.25)  # 为图例腾出空间
        self.asset_ax.set_title("资产分布", color=TEXT_COLOR)
        
        # 设置图表背景
        self.asset_fig.patch.set_facecolor(CHART_BG_COLOR)
        self.asset_ax.set_facecolor(CHART_AREA_COLOR)
        
        # 创建资产分布图表画布
        self.asset_canvas = FigureCanvasTkAgg(self.asset_fig, master=self.asset_chart_frame)
        self.asset_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_holdings_distribution_chart(self):
        """创建持仓分布图表"""
        # 创建持仓分布图表框架
        self.holdings_chart_frame = tb.Frame(self.right_frame, bootstyle="dark")
        # self.holdings_chart_frame.configure(background=BACKGROUND_COLOR)
        self.holdings_chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建持仓分布图表
        self.holdings_fig, self.holdings_ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.holdings_fig.subplots_adjust(bottom=0.25)  # 为图例腾出空间
        self.holdings_ax.set_title("持仓分布", color=TEXT_COLOR)
        
        # 设置图表背景
        self.holdings_fig.patch.set_facecolor(CHART_BG_COLOR)
        self.holdings_ax.set_facecolor(CHART_AREA_COLOR)
        
        # 创建持仓分布图表画布
        self.holdings_canvas = FigureCanvasTkAgg(self.holdings_fig, master=self.holdings_chart_frame)
        self.holdings_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def load_account_data(self):
        """加载账户数据"""
        # 更新状态
        self.status_var.set("正在加载账户数据...")
        self.update_idletasks()
        
        # 获取用户信息
        user = db.get_user(self.username)
        if not user:
            from ttkbootstrap.dialogs import Messagebox
            Messagebox.show_error("无法获取用户信息", "错误")
            self.status_var.set("加载失败：无法获取用户信息")
            return
        
        # 获取用户余额
        balance = user.get("balance", 0)
        self.balance_var.set(f"{balance:.2f}")
        
        # 获取用户持仓
        holdings = user.get("holdings", {})
        
        # 计算持仓市值和盈亏
        holdings_value = 0
        total_profit = 0
        holdings_data = []
        
        # 清空持仓列表
        for item in self.holdings_tree.get_children():
            self.holdings_tree.delete(item)
        
        # 获取所有股票的当前价格
        stocks = db.get_stocks()
        
        # 处理每个持仓
        for code, holding in holdings.items():
            # 获取股票信息
            stock = stocks.get(code, {})
            name = holding.get("name", "")
            quantity = holding.get("quantity", 0)
            cost = holding.get("cost", 0)
            current_price = stock.get("price", 0)
            
            # 计算市值和盈亏
            market_value = quantity * current_price
            profit = market_value - (quantity * cost)
            profit_rate = (profit / (quantity * cost)) * 100 if cost > 0 and quantity > 0 else 0
            
            # 累计总市值和盈亏
            holdings_value += market_value
            total_profit += profit
            
            # 添加到持仓数据列表
            holdings_data.append({
                "code": code,
                "name": name,
                "quantity": quantity,
                "cost": cost,
                "current_price": current_price,
                "market_value": market_value,
                "profit": profit,
                "profit_rate": profit_rate,
                "value": market_value  # 用于图表
            })
            
            # 添加到持仓列表
            if profit > 0:
                tag = "profit"
            elif profit < 0:
                tag = "loss"
            else:
                tag = "flat"
            
            self.holdings_tree.insert('', tk.END, values=(
                code,
                name,
                quantity,
                f"{cost:.2f}",
                f"{current_price:.2f}",
                f"{market_value:.2f}",
                f"{profit:.2f}",
                f"{profit_rate:.2f}%"
            ), tags=(tag,))
        
        # 设置颜色
        self.holdings_tree.tag_configure('profit', foreground=UP_COLOR)  # 上涨红色
        self.holdings_tree.tag_configure('loss', foreground=DOWN_COLOR)  # 下跌绿色
        self.holdings_tree.tag_configure('flat', foreground=TEXT_COLOR)  # 白色
        
        # 更新账户总值和盈亏
        total_value = balance + holdings_value
        self.holdings_value_var.set(f"{holdings_value:.2f}")
        self.total_value_var.set(f"{total_value:.2f}")
        self.profit_var.set(f"{total_profit:.2f}")
        
        # 设置盈亏颜色
        if total_profit > 0:
            self.profit_label.config(bootstyle="danger", foreground=UP_COLOR)  # 红色
        elif total_profit < 0:
            self.profit_label.config(bootstyle="success", foreground=DOWN_COLOR)  # 绿色
        else:
            self.profit_label.config(bootstyle="light", foreground=TEXT_COLOR)  # 白色
        
        # 更新图表
        self.update_asset_chart(balance, holdings_value)
        self.update_holdings_chart(holdings_data)
        
        # 更新状态
        self.status_var.set(f"账户数据已更新 - {datetime.now().strftime('%H:%M:%S')}")
    
    def update_asset_chart(self, balance, holdings_value):
        """更新资产分布图表"""
        # 清除图表
        self.asset_ax.clear()
        
        # 准备数据
        labels = ['可用资金', '持仓市值']
        sizes = [balance, holdings_value]
        colors = ['#66b3ff', '#ff9999']
        
        # 绘制饼图
        wedges, texts, autotexts = self.asset_ax.pie(
            sizes, 
            labels=None,  # 移除标签，改为使用图例
            colors=colors, 
            autopct='%1.1f%%', 
            startangle=90,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1, 'alpha': 0.8}
        )
        
        # 设置自动文本颜色
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontweight('bold')
        
        self.asset_ax.axis('equal')  # 保持圆形
        self.asset_ax.set_title("资产分布", color=TEXT_COLOR)
        
        # 设置背景颜色
        self.asset_fig.patch.set_facecolor(CHART_BG_COLOR)
        self.asset_ax.set_facecolor(CHART_AREA_COLOR)
        
        # 添加图例
        total = sum(sizes)
        legend_labels = [f'{labels[i]}: {sizes[i]:,.2f}(元) ({sizes[i]/total*100:.1f}%)' for i in range(len(labels))]
        self.asset_ax.legend(legend_labels, loc='upper center', bbox_to_anchor=(0.5, 0), 
                           ncol=2, frameon=True, facecolor=CHART_AREA_COLOR, edgecolor='white')
        
        # 刷新图表，但不使用tight_layout，避免图表缩小
        # self.asset_fig.tight_layout()  # 移除这一行
        self.asset_canvas.draw()
    
    def update_holdings_chart(self, holdings_data):
        """更新持仓分布图表（改为柱状图）"""
        # 清除图表
        self.holdings_ax.clear()

        # 如果没有持仓，显示提示
        if not holdings_data:
            self.holdings_ax.text(0.5, 0.5, '暂无持仓', horizontalalignment='center', 
                                verticalalignment='center', color=TEXT_COLOR, fontsize=14)
            self.holdings_ax.axis('off')
            self.holdings_canvas.draw()
            return

        # 准备数据
        labels = [f"{h['name']}({h['code']})" for h in holdings_data]
        values = [h['value'] for h in holdings_data]
        colors = plt.cm.tab20c(np.linspace(0, 1, len(holdings_data)))

        # 绘制柱状图
        bars = self.holdings_ax.bar(labels, values, color=colors)
        self.holdings_ax.set_title("持仓分布（市值）", color=TEXT_COLOR)
        self.holdings_ax.set_ylabel("市值", color=TEXT_COLOR)
        self.holdings_ax.set_xlabel("股票", color=TEXT_COLOR)
        self.holdings_ax.tick_params(axis='x', colors=TEXT_COLOR, rotation=30)
        self.holdings_ax.tick_params(axis='y', colors=TEXT_COLOR)
        self.holdings_ax.set_facecolor(CHART_AREA_COLOR)
        self.holdings_fig.patch.set_facecolor(CHART_BG_COLOR)

        # 在柱子上标注市值
        for bar, value in zip(bars, values):
            self.holdings_ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{value:.2f}",
                                  ha='center', va='bottom', color=TEXT_COLOR, fontsize=9)

        self.holdings_fig.tight_layout()
        self.holdings_canvas.draw() 