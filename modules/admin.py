import tkinter as tk
import ttkbootstrap as tb
import numpy as np
from ttkbootstrap import Style
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
from .database import db

# 设置matplotlib支持中文显示
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Heiti TC', 'WenQuanYi Micro Hei', 'Arial Unicode MS', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False
plt.style.use('dark_background')  # 使用深色背景风格

# 定义全局颜色变量（从AccountFrame中复用）
UP_COLOR = "#ff4d4d"  # 上涨颜色(红色)
DOWN_COLOR = "#00e676"  # 下跌颜色(绿色)
TEXT_COLOR = "#ffffff"  # 白色文本

class AdminFrame(tb.Frame):
    """管理员页面框架"""
    
    def __init__(self, parent):
        super().__init__(parent, bootstyle="dark")
        
        # 创建标题
        self.title_label = tb.Label(self, text="管理员控制面板", font=("微软雅黑", 16, "bold"), bootstyle="inverse-dark")
        self.title_label.pack(pady=10, padx=10, anchor="w")
        
        # 创建选项卡
        self.notebook = tb.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建用户管理选项卡
        self.user_tab = tb.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.user_tab, text="用户管理")
        
        # 创建数据统计选项卡
        self.stats_tab = tb.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.stats_tab, text="数据统计")
        
        # 创建系统设置选项卡
        self.settings_tab = tb.Frame(self.notebook, bootstyle="dark")
        self.notebook.add(self.settings_tab, text="系统设置")
        
        # 初始化各选项卡内容
        self.init_user_tab()
        self.init_stats_tab()
        self.init_settings_tab()
        
        # 加载数据
        self.load_users()
    
    def init_user_tab(self):
        """初始化用户管理选项卡"""
        # 创建上部控制区域
        control_frame = tb.Frame(self.user_tab, bootstyle="dark")
        control_frame.pack(fill=tk.X, pady=10)
        
        # 添加用户按钮
        add_btn = tb.Button(control_frame, text="添加用户", command=self.show_add_user_dialog, bootstyle="success")
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # 编辑用户按钮
        self.edit_btn = tb.Button(control_frame, text="编辑用户", command=self.show_edit_user_dialog, bootstyle="info")
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.edit_btn.config(state=tk.DISABLED)
        
        # 删除用户按钮
        self.delete_btn = tb.Button(control_frame, text="删除用户", command=self.delete_user, bootstyle="danger")
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        self.delete_btn.config(state=tk.DISABLED)
        
        # 刷新按钮
        refresh_btn = tb.Button(control_frame, text="刷新", command=self.load_users, bootstyle="secondary")
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建用户列表
        self.create_user_list()
    
    def create_user_list(self):
        """创建用户列表"""
        # 创建用户列表框架
        list_frame = tb.Frame(self.user_tab, bootstyle="dark")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建用户列表
        columns = ('用户名', '类型', '余额', '持仓数量', '注册时间')
        self.user_tree = tb.Treeview(list_frame, columns=columns, show='headings', bootstyle="dark")
        
        # 设置列标题
        for col in columns:
            self.user_tree.heading(col, text=col)
        
        # 设置列宽
        self.user_tree.column('用户名', width=100)
        self.user_tree.column('类型', width=80)
        self.user_tree.column('余额', width=100)
        self.user_tree.column('持仓数量', width=80)
        self.user_tree.column('注册时间', width=150)
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.user_tree.yview, bootstyle="round-dark")
        self.user_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件和双击事件
        self.user_tree.bind("<<TreeviewSelect>>", self.on_user_select)
        self.user_tree.bind("<Double-1>", self.show_holdings_window)  # 新增双击事件
        
        # 创建用户详情框架
        self.detail_frame = tb.LabelFrame(self.user_tab, text="用户详情", bootstyle="info")
        self.detail_frame.pack(fill=tk.X, pady=10)
        
        # 用户名
        tb.Label(self.detail_frame, text="用户名:", bootstyle="light").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.detail_username_var = tk.StringVar()
        tb.Label(self.detail_frame, textvariable=self.detail_username_var, bootstyle="info").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 用户类型
        tb.Label(self.detail_frame, text="用户类型:", bootstyle="light").grid(row=0, column=2, sticky="w", padx=10, pady=5)
        self.detail_type_var = tk.StringVar()
        tb.Label(self.detail_frame, textvariable=self.detail_type_var, bootstyle="info").grid(row=0, column=3, sticky="w", padx=10, pady=5)
        
        # 账户余额
        tb.Label(self.detail_frame, text="账户余额:", bootstyle="light").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.detail_balance_var = tk.StringVar()
        tb.Label(self.detail_frame, textvariable=self.detail_balance_var, bootstyle="info").grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 持仓数量
        tb.Label(self.detail_frame, text="持仓数量:", bootstyle="light").grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.detail_holdings_var = tk.StringVar()
        tb.Label(self.detail_frame, textvariable=self.detail_holdings_var, bootstyle="info").grid(row=1, column=3, sticky="w", padx=10, pady=5)
        
        # 注册时间
        tb.Label(self.detail_frame, text="注册时间:", bootstyle="light").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.detail_created_var = tk.StringVar()
        tb.Label(self.detail_frame, textvariable=self.detail_created_var, bootstyle="info").grid(row=2, column=1, columnspan=3, sticky="w", padx=10, pady=5)
    
    def init_stats_tab(self):
        """初始化数据统计选项卡"""
        # 创建上部控制区域
        control_frame = tb.Frame(self.stats_tab, bootstyle="dark")
        control_frame.pack(fill=tk.X, pady=10)
        
        # 刷新按钮
        refresh_btn = tb.Button(control_frame, text="刷新统计", command=self.load_stats, bootstyle="info")
        refresh_btn.pack(side=tk.RIGHT, padx=5)
        
        # 创建统计图表区域
        charts_frame = tb.Frame(self.stats_tab, bootstyle="dark")
        charts_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建左右布局
        left_frame = tb.Frame(charts_frame, bootstyle="dark")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = tb.Frame(charts_frame, bootstyle="dark")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建用户资产分布图表
        self.create_user_assets_chart(left_frame)
        
        # 创建交易量统计图表
        self.create_transaction_stats_chart(right_frame)
    
    def create_user_assets_chart(self, parent):
        """创建用户资产分布图表"""
        # 创建标题
        chart_title = tb.Label(parent, text="用户资产分布", font=("微软雅黑", 12, "bold"), bootstyle="info")
        chart_title.pack(pady=5, anchor="w")
        
        # 创建图表框架
        self.assets_chart_frame = tb.Frame(parent, bootstyle="dark")
        self.assets_chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建图表
        self.assets_fig, self.assets_ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.assets_fig.patch.set_facecolor("#0d1926")  # 设置图表背景颜色
        self.assets_ax.set_facecolor("#142638")  # 设置坐标区域背景颜色
        self.assets_canvas = FigureCanvasTkAgg(self.assets_fig, master=self.assets_chart_frame)
        self.assets_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_transaction_stats_chart(self, parent):
        """创建交易量统计图表"""
        # 创建标题
        chart_title = tb.Label(parent, text="交易量统计", font=("微软雅黑", 12, "bold"), bootstyle="info")
        chart_title.pack(pady=5, anchor="w")
        
        # 创建图表框架
        self.trans_chart_frame = tb.Frame(parent, bootstyle="dark")
        self.trans_chart_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建图表
        self.trans_fig, self.trans_ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.trans_fig.patch.set_facecolor("#0d1926")  # 设置图表背景颜色
        self.trans_ax.set_facecolor("#142638")  # 设置坐标区域背景颜色
        self.trans_canvas = FigureCanvasTkAgg(self.trans_fig, master=self.trans_chart_frame)
        self.trans_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def init_settings_tab(self):
        """初始化系统设置选项卡"""
        # 创建设置框架
        settings_frame = tb.LabelFrame(self.settings_tab, text="系统设置", bootstyle="info")
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 初始资金设置
        tb.Label(settings_frame, text="新用户初始资金:", bootstyle="light").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        self.initial_balance_var = tk.StringVar(value="100000")
        tb.Entry(settings_frame, textvariable=self.initial_balance_var, width=15).grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        # 保存按钮
        save_btn = tb.Button(settings_frame, text="保存设置", command=self.save_settings, bootstyle="success")
        save_btn.grid(row=1, column=0, columnspan=2, pady=20)
    
    def load_users(self):
        """加载用户数据"""
        # 清空用户列表
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)
        
        # 获取所有用户
        users = db.get_users()
        
        # 添加到用户列表
        for username, user in users.items():
            user_type = user.get("type", "user")
            balance = user.get("balance", 0)
            holdings = user.get("holdings", {})
            created_at = user.get("created_at", "")
            
            # 插入数据
            self.user_tree.insert('', tk.END, values=(
                username,
                "管理员" if user_type == "admin" else "普通用户",
                f"{balance:.2f}",
                len(holdings),
                created_at
            ))
    
    def load_stats(self):
        """加载统计数据"""
        # 获取所有用户
        users = db.get_users()
        
        # 准备用户资产数据
        usernames = []
        balances = []
        holdings_values = []
        
        # 获取所有股票的当前价格
        stocks = db.get_stocks()
        
        for username, user in users.items():
            usernames.append(username)
            balance = user.get("balance", 0)
            balances.append(balance)
            
            # 计算持仓市值
            holdings = user.get("holdings", {})
            holdings_value = 0
            for code, holding in holdings.items():
                stock = stocks.get(code, {})
                quantity = holding.get("quantity", 0)
                price = stock.get("price", 0)
                holdings_value += quantity * price
            
            holdings_values.append(holdings_value)
        
        # 更新用户资产图表
        self.update_user_assets_chart(usernames, balances, holdings_values)
        
        # 准备交易统计数据
        # 这里简化处理，只统计每个用户的交易次数
        transaction_counts = {}
        for username in users.keys():
            transactions = db.get_user_transactions(username)
            transaction_counts[username] = len(transactions)
        
        # 更新交易统计图表
        self.update_transaction_stats_chart(transaction_counts)
    
    def update_user_assets_chart(self, usernames, balances, holdings_values):
        """更新用户资产分布图表"""
        # 清除图表
        self.assets_ax.clear()
        
        # 准备数据
        x = range(len(usernames))
        width = 0.35
        
        # 绘制柱状图
        self.assets_ax.bar(x, balances, width, label='可用资金')
        self.assets_ax.bar([i + width for i in x], holdings_values, width, label='持仓市值')
        
        # 设置标签和标题
        self.assets_ax.set_xlabel('用户')
        self.assets_ax.set_ylabel('金额')
        self.assets_ax.set_title('用户资产分布')
        self.assets_ax.set_xticks([i + width/2 for i in x])
        self.assets_ax.set_xticklabels(usernames)
        self.assets_ax.legend()
        
        # 自动调整布局
        self.assets_fig.tight_layout()
        
        # 刷新图表
        self.assets_canvas.draw()
    
    def update_transaction_stats_chart(self, transaction_counts):
        """更新交易统计图表"""
        # 清除图表
        self.trans_ax.clear()
        
        # 准备数据
        usernames = list(transaction_counts.keys())
        counts = list(transaction_counts.values())
        
        # 绘制柱状图
        self.trans_ax.bar(usernames, counts, color='skyblue')
        
        # 设置标签和标题
        self.trans_ax.set_xlabel('用户')
        self.trans_ax.set_ylabel('交易次数')
        self.trans_ax.set_title('用户交易次数统计')
        
        # 自动调整布局
        self.trans_fig.tight_layout()
        
        # 刷新图表
        self.trans_canvas.draw()
    
    def on_user_select(self, event):
        """处理用户选择事件"""
        selected_items = self.user_tree.selection()
        if not selected_items:
            # 禁用编辑和删除按钮
            self.edit_btn.config(state=tk.DISABLED)
            self.delete_btn.config(state=tk.DISABLED)
            return
        
        # 启用编辑和删除按钮
        self.edit_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)
        
        # 获取选中的用户
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        if not values:
            return
        
        # 获取用户名
        username = values[0]
        
        # 获取用户详情
        user = db.get_user(username)
        if not user:
            return
        
        # 更新用户详情
        self.detail_username_var.set(username)
        self.detail_type_var.set("管理员" if user.get("type") == "admin" else "普通用户")
        self.detail_balance_var.set(f"{user.get('balance', 0):.2f}")
        self.detail_holdings_var.set(str(len(user.get("holdings", {}))))
        self.detail_created_var.set(user.get("created_at", ""))
    
    def show_add_user_dialog(self):
        """显示添加用户对话框"""
        # 创建对话框
        dialog = tk.Toplevel(self)
        dialog.title("添加用户")
        dialog.geometry("300x250")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 创建表单
        tb.Label(dialog, text="用户名:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        username_var = tk.StringVar()
        tb.Entry(dialog, textvariable=username_var, width=20).grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        tb.Label(dialog, text="密码:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        password_var = tk.StringVar()
        tb.Entry(dialog, textvariable=password_var, show="*", width=20).grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        tb.Label(dialog, text="用户类型:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        type_var = tk.StringVar(value="user")
        tb.Radiobutton(dialog, text="普通用户", variable=type_var, value="user").grid(row=2, column=1, sticky="w", padx=10, pady=5)
        tb.Radiobutton(dialog, text="管理员", variable=type_var, value="admin").grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        tb.Label(dialog, text="初始资金:").grid(row=4, column=0, sticky="w", padx=10, pady=10)
        balance_var = tk.StringVar(value=self.initial_balance_var.get())
        tb.Entry(dialog, textvariable=balance_var, width=20).grid(row=4, column=1, sticky="w", padx=10, pady=10)
        
        # 按钮区域
        btn_frame = tb.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 确定按钮
        def on_confirm():
            # 获取表单数据
            username = username_var.get().strip()
            password = password_var.get().strip()
            user_type = type_var.get()
            
            try:
                balance = float(balance_var.get())
            except:
                messagebox.showerror("错误", "初始资金必须是数字")
                return
            
            if not username:
                messagebox.showerror("错误", "用户名不能为空")
                return
            
            if not password:
                messagebox.showerror("错误", "密码不能为空")
                return
            
            # 添加用户
            success, message = db.add_user(username, password, user_type, balance)
            
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                # 刷新用户列表
                self.load_users()
            else:
                messagebox.showerror("错误", message)
        
        tb.Button(btn_frame, text="确定", command=on_confirm).pack(side=tk.LEFT, padx=10)
        tb.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def show_edit_user_dialog(self):
        """显示编辑用户对话框"""
        # 获取选中的用户
        selected_items = self.user_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        if not values:
            return
        
        username = values[0]
        user = db.get_user(username)
        if not user:
            return
        
        # 创建对话框
        dialog = tk.Toplevel(self)
        dialog.title(f"编辑用户 - {username}")
        dialog.geometry("300x220")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        
        # 创建表单
        tb.Label(dialog, text="用户名:").grid(row=0, column=0, sticky="w", padx=10, pady=10)
        tb.Label(dialog, text=username).grid(row=0, column=1, sticky="w", padx=10, pady=10)
        
        tb.Label(dialog, text="新密码:").grid(row=1, column=0, sticky="w", padx=10, pady=10)
        password_var = tk.StringVar()
        tb.Entry(dialog, textvariable=password_var, show="*", width=20).grid(row=1, column=1, sticky="w", padx=10, pady=10)
        
        tb.Label(dialog, text="用户类型:").grid(row=2, column=0, sticky="w", padx=10, pady=10)
        type_var = tk.StringVar(value=user.get("type", "user"))
        tb.Radiobutton(dialog, text="普通用户", variable=type_var, value="user").grid(row=2, column=1, sticky="w", padx=10, pady=5)
        tb.Radiobutton(dialog, text="管理员", variable=type_var, value="admin").grid(row=3, column=1, sticky="w", padx=10, pady=5)
        
        tb.Label(dialog, text="账户余额:").grid(row=4, column=0, sticky="w", padx=10, pady=10)
        balance_var = tk.StringVar(value=str(user.get("balance", 0)))
        tb.Entry(dialog, textvariable=balance_var, width=20).grid(row=4, column=1, sticky="w", padx=10, pady=10)
        
        # 按钮区域
        btn_frame = tb.Frame(dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 确定按钮
        def on_confirm():
            # 获取表单数据
            password = password_var.get().strip()
            user_type = type_var.get()
            
            try:
                balance = float(balance_var.get())
            except:
                messagebox.showerror("错误", "账户余额必须是数字")
                return
            
            # 准备更新数据
            update_data = {
                "type": user_type,
                "balance": balance
            }
            
            # 如果输入了新密码，则更新密码
            if password:
                update_data["password"] = password
            
            # 更新用户
            success, message = db.update_user(username, update_data)
            
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                # 刷新用户列表
                self.load_users()
            else:
                messagebox.showerror("错误", message)
        
        tb.Button(btn_frame, text="确定", command=on_confirm).pack(side=tk.LEFT, padx=10)
        tb.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
    
    def delete_user(self):
        """删除用户"""
        # 获取选中的用户
        selected_items = self.user_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        values = self.user_tree.item(item, 'values')
        if not values:
            return
        
        username = values[0]
        
        # 确认删除
        if not messagebox.askyesno("确认", f"确定要删除用户 {username} 吗？"):
            return
        
        # 删除用户
        success, message = db.delete_user(username)
        
        if success:
            messagebox.showinfo("成功", message)
            # 刷新用户列表
            self.load_users()
        else:
            messagebox.showerror("错误", message)
    
    def save_settings(self):
        """保存系统设置"""
        try:
            initial_balance = float(self.initial_balance_var.get())
            if initial_balance <= 0:
                messagebox.showerror("错误", "初始资金必须大于0")
                return
            
            messagebox.showinfo("成功", "设置保存成功")
        except:
            messagebox.showerror("错误", "初始资金必须是数字")
    
    def show_holdings_window(self, event):
        """显示用户持仓窗口"""
        selected_items = self.user_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        username = self.user_tree.item(item, 'values')[0]
        user = db.get_user(username)
        if not user:
            messagebox.showwarning("警告", "用户数据不存在")
            return
        
        # 创建持仓显示窗口
        holdings_window = tb.Toplevel(self)
        holdings_window.title(f"用户 {username} 持仓信息")
        holdings_window.geometry("2000x1500") 
        holdings_window.resizable(True, True)
        
        # 创建主框架（左右布局）
        main_frame = tb.Frame(holdings_window, bootstyle="dark")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左侧：持仓表格
        left_frame = tb.Frame(main_frame, bootstyle="dark")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 右侧：资产分布图表
        right_frame = tb.Frame(main_frame, bootstyle="dark")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # === 左侧持仓表格 ===
        # 创建标题
        tb.Label(left_frame, text=f"{username} 持仓信息", font=("微软雅黑", 14, "bold"), 
                bootstyle="inverse-dark").pack(pady=10, anchor="w")
        
        # 创建账户概览
        overview_frame = tb.LabelFrame(left_frame, text="账户概览", bootstyle="info")
        overview_frame.pack(fill=tk.X, pady=5)
        
        # 获取用户持仓数据
        holdings = user.get("holdings", {})
        stocks = db.get_stocks()
        
        # 计算持仓市值
        holdings_value = 0
        stock_values = {}
        for code, holding in holdings.items():
            stock = stocks.get(code, {})
            current_price = stock.get("price", 0)
            quantity = holding.get("quantity", 0)
            value = current_price * quantity
            holdings_value += value
            stock_values[code] = value
        
        # 创建持仓列表
        columns = ('代码', '名称', '持仓', '成本价', '现价', '市值', '盈亏', '盈亏率')
        holdings_tree = tb.Treeview(left_frame, columns=columns, show='headings', bootstyle="dark")
        
        # 设置列标题和宽度
        for col in columns:
            holdings_tree.heading(col, text=col)
            if col == '标题':
                holdings_tree.column(col, width=400, anchor='w')
            else:
                holdings_tree.column(col, width=80, anchor='center')
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(left_frame, orient=tk.VERTICAL, command=holdings_tree.yview, 
                               bootstyle="round-dark")
        holdings_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        holdings_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 计算总盈亏
        total_profit = 0
        
        for code, holding in holdings.items():
            stock = stocks.get(code, {})
            name = holding.get("name", "")
            quantity = holding.get("quantity", 0)
            cost_price = holding.get("cost", 0)  # 成本价
            current_price = stock.get("price", 0)  # 现价
            market_value = quantity * current_price  # 市值 = 现价 * 持仓
            cost_value = quantity * cost_price  # 成本 = 成本价 * 持仓
            profit = market_value - cost_value  # 盈亏 = 市值 - 成本
            profit_rate = (profit / cost_value) * 100 if cost_value > 0 else 0  # 盈亏率
            
            total_profit += profit
            
            # 设置颜色标签
            tag = "profit" if profit > 0 else "loss" if profit < 0 else "flat"
            holdings_tree.insert('', tk.END, values=(
                code,
                name,
                quantity,
                f"{cost_price:.2f}",  # 显示成本价
                f"{current_price:.2f}",  # 显示现价
                f"{market_value:.2f}",  # 显示市值
                f"{profit:.2f}",
                f"{profit_rate:.2f}%"
            ), tags=(tag,))
        
        # 配置颜色
        holdings_tree.tag_configure('profit', foreground=UP_COLOR)  # 上涨红色
        holdings_tree.tag_configure('loss', foreground=DOWN_COLOR)  # 下跌绿色
        holdings_tree.tag_configure('flat', foreground=TEXT_COLOR)  # 白色
        
        # === 右侧资产分布饼图 ===
        # 创建标题
        tb.Label(right_frame, text=f"{username} 资产分布", font=("微软雅黑", 14, "bold"), 
                bootstyle="inverse-dark").pack(pady=10, anchor="w")
        
        # 创建图表框架
        chart_frame = tb.Frame(right_frame, bootstyle="dark")
        chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建饼图
        fig, ax = plt.subplots(figsize=(5, 4), dpi=100)
        fig.patch.set_facecolor("#0d1926")  # 设置图表背景颜色
        ax.set_facecolor("#142638")  # 设置坐标区域背景颜色
        
        # 准备数据
        labels = ['可用资金'] + list(stock_values.keys())
        sizes = [user.get('balance', 0)] + list(stock_values.values())
        # 颜色：可用资金为蓝色，股票部分用tab20c色系
        n_stocks = len(stock_values)
        stock_colors = plt.cm.tab20c(np.linspace(0, 1, max(n_stocks, 1)))
        colors = ['#66b3ff'] + [stock_colors[i] for i in range(n_stocks)]
        
        # 绘制饼图
        wedges, texts, autotexts = ax.pie(
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
        
        ax.axis('equal')  # 保持圆形
        ax.set_title("资产分布", color=TEXT_COLOR)
        
        # 添加图例
        total = sum(sizes)
        legend_labels = [f'{labels[i]}: {sizes[i]:,.2f}(元) ({sizes[i]/total*100:.1f}%)' for i in range(len(labels))]
        ax.legend(wedges, legend_labels, loc='upper center', bbox_to_anchor=(0.5, 0), 
                ncol=2, frameon=True, facecolor="#142638", edgecolor='white')
        
        # 创建图表画布
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)