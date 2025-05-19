import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
import pandas as pd
from .database import db
from .stock_data import stock_manager

class TradingFrame(tb.Frame):
    """交易操作页面框架"""
    
    def __init__(self, parent, username):
        super().__init__(parent)
        self.username = username
        
        # 创建标题
        self.title_label = tb.Label(self, text="交易操作", style="Title.TLabel")
        self.title_label.pack(pady=10, padx=10, anchor="w")
        
        # 创建主框架
        self.main_frame = tb.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧股票列表框架
        self.left_frame = tb.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 创建右侧交易操作框架
        self.right_frame = tb.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建股票列表
        self.create_stock_list()
        
        # 创建交易表单
        self.create_trade_form()
        
        # 创建交易记录
        self.create_transaction_list()
        
        # 加载数据
        self.load_data()
    
    def create_stock_list(self):
        """创建股票列表"""
        # 创建标题
        list_title = tb.Label(self.left_frame, text="可交易股票", style="Header.TLabel")
        list_title.pack(pady=5, anchor="w")
        
        # 创建搜索框
        search_frame = tb.Frame(self.left_frame)
        search_frame.pack(fill=tk.X, pady=5)
        
        tb.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tb.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_btn = tb.Button(search_frame, text="搜索", command=self.search_stock)
        search_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建股票列表框架
        self.stock_frame = tb.Frame(self.left_frame)
        self.stock_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建股票列表
        columns = ('代码', '名称', '价格', '涨跌幅')
        self.stock_tree = tb.Treeview(self.stock_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.stock_tree.heading(col, text=col)
        
        # 设置列宽
        self.stock_tree.column('代码', width=80)
        self.stock_tree.column('名称', width=80)
        self.stock_tree.column('价格', width=80)
        self.stock_tree.column('涨跌幅', width=80)
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(self.stock_frame, orient=tk.VERTICAL, command=self.stock_tree.yview)
        self.stock_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.stock_tree.bind("<<TreeviewSelect>>", self.on_stock_select)
    
    def create_trade_form(self):
        """创建交易表单"""
        # 创建标题
        form_title = tb.Label(self.right_frame, text="交易操作", style="Header.TLabel")
        form_title.pack(pady=5, anchor="w")
        
        # 创建表单框架
        form_frame = tb.Frame(self.right_frame)
        form_frame.pack(fill=tk.X, pady=10)
        
        # 股票信息区域
        info_frame = tb.LabelFrame(form_frame, text="股票信息")
        info_frame.pack(fill=tk.X, pady=5)
        
        # 股票代码
        tb.Label(info_frame, text="代码:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.code_var = tk.StringVar()
        self.code_label = tb.Label(info_frame, textvariable=self.code_var)
        self.code_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 股票名称
        tb.Label(info_frame, text="名称:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.name_var = tk.StringVar()
        self.name_label = tb.Label(info_frame, textvariable=self.name_var)
        self.name_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 当前价格
        tb.Label(info_frame, text="当前价格:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.price_var = tk.StringVar()
        self.price_label = tb.Label(info_frame, textvariable=self.price_var)
        self.price_label.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        
        # 账户信息区域
        user_frame = tb.LabelFrame(form_frame, text="账户信息")
        user_frame.pack(fill=tk.X, pady=5)
        
        # 可用资金
        tb.Label(user_frame, text="可用资金:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.balance_var = tk.StringVar()
        self.balance_label = tb.Label(user_frame, textvariable=self.balance_var)
        self.balance_label.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        
        # 持仓数量
        tb.Label(user_frame, text="持仓数量:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.holding_var = tk.StringVar()
        self.holding_label = tb.Label(user_frame, textvariable=self.holding_var)
        self.holding_label.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 交易操作区域
        trade_frame = tb.LabelFrame(form_frame, text="交易操作")
        trade_frame.pack(fill=tk.X, pady=5)
        
        # 交易类型
        tb.Label(trade_frame, text="交易类型:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.trade_type_var = tk.StringVar(value="buy")
        buy_radio = tb.Radiobutton(trade_frame, text="买入", variable=self.trade_type_var, value="buy")
        buy_radio.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        sell_radio = tb.Radiobutton(trade_frame, text="卖出", variable=self.trade_type_var, value="sell")
        sell_radio.grid(row=0, column=2, sticky="w", padx=10, pady=5)
        
        # 交易数量
        tb.Label(trade_frame, text="数量:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.quantity_var = tk.StringVar()
        quantity_entry = tb.Entry(trade_frame, textvariable=self.quantity_var, width=10)
        quantity_entry.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        
        # 交易金额
        tb.Label(trade_frame, text="金额:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.amount_var = tk.StringVar()
        self.amount_label = tb.Label(trade_frame, textvariable=self.amount_var)
        self.amount_label.grid(row=2, column=1, columnspan=2, sticky="w", padx=10, pady=5)
        
        # 监听数量变化
        self.quantity_var.trace_add("write", self.update_amount)
        
        # 提交按钮
        self.submit_btn = tb.Button(form_frame, text="执行交易", command=self.execute_trade)
        self.submit_btn.pack(pady=10)
        self.submit_btn.config(state=tk.DISABLED)
    
    def create_transaction_list(self):
        """创建交易记录列表"""
        # 创建标题
        list_title = tb.Label(self.right_frame, text="最近交易记录", style="Header.TLabel")
        list_title.pack(pady=10, anchor="w")
        
        # 创建交易记录框架
        self.transaction_frame = tb.Frame(self.right_frame)
        self.transaction_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建交易记录列表
        columns = ('时间', '类型', '代码', '名称', '价格', '数量', '金额')
        self.transaction_tree = tb.Treeview(self.transaction_frame, columns=columns, show='headings')
        
        # 设置列标题
        for col in columns:
            self.transaction_tree.heading(col, text=col)
        
        # 设置列宽
        self.transaction_tree.column('时间', width=150)
        self.transaction_tree.column('类型', width=50)
        self.transaction_tree.column('代码', width=80)
        self.transaction_tree.column('名称', width=80)
        self.transaction_tree.column('价格', width=80)
        self.transaction_tree.column('数量', width=50)
        self.transaction_tree.column('金额', width=100)
        
        # 添加滚动条
        scrollbar = tb.Scrollbar(self.transaction_frame, orient=tk.VERTICAL, command=self.transaction_tree.yview)
        self.transaction_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.transaction_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_data(self):
        """加载市场数据"""
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 获取股票数据
        stocks = db.get_stocks()
        
        # 添加到列表
        for code, info in stocks.items():
            name = info.get("name", "")
            price = info.get("price", 0)
            change = info.get("change", 0)
            
            # 根据涨跌幅设置颜色标签
            if change > 0:
                tag = "up"
            elif change < 0:
                tag = "down"
            else:
                tag = "flat"
            
            # 插入数据
            self.stock_tree.insert('', tk.END, values=(code, name, f"{price:.2f}", f"{change:.2f}%"), tags=(tag,))
        
        # 设置颜色
        self.stock_tree.tag_configure('up', foreground='red')
        self.stock_tree.tag_configure('down', foreground='green')
        self.stock_tree.tag_configure('flat', foreground='black')
    
    def load_transactions(self):
        """加载交易记录"""
        # 清空列表
        for item in self.transaction_tree.get_children():
            self.transaction_tree.delete(item)
        
        # 获取交易记录
        transactions = db.get_user_transactions(self.username)
        
        # 添加到列表
        for transaction in transactions:
            # 交易类型
            trade_type = "买入" if transaction.get("type") == "buy" else "卖出"
            # 交易时间
            timestamp = transaction.get("timestamp", "")
            # 股票名称
            stock_name = transaction.get("stock_name", "")
            # 价格
            price = transaction.get("price", 0)
            # 数量
            quantity = transaction.get("quantity", 0)
            # 金额
            amount = transaction.get("amount", 0)
            
            # 设置颜色标签
            tag = "buy" if trade_type == "买入" else "sell"
            
            # 插入数据
            self.transaction_tree.insert('', 0, values=(timestamp, trade_type, stock_name, f"{price:.2f}", quantity, f"{amount:.2f}"), tags=(tag,))
        
        # 设置颜色
        self.transaction_tree.tag_configure('buy', foreground='red')
        self.transaction_tree.tag_configure('sell', foreground='green')
    
    def search_stock(self):
        """搜索股票"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入搜索关键词")
            return
        
        # 搜索股票
        results = stock_manager.search_stocks(keyword)
        
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 添加搜索结果
        for stock in results:
            code = stock.get("code", "")
            name = stock.get("name", "")
            price = stock.get("price", 0)
            change = stock.get("change", 0)
            
            # 根据涨跌幅设置颜色标签
            if change > 0:
                tag = "up"
            elif change < 0:
                tag = "down"
            else:
                tag = "flat"
            
            # 插入数据
            self.stock_tree.insert('', tk.END, values=(code, name, f"{price:.2f}", f"{change:.2f}%"), tags=(tag,))
        
        # 如果没有结果
        if not results:
            messagebox.showinfo("提示", f"未找到与 '{keyword}' 相关的股票")
    
    def on_stock_select(self, event):
        """处理股票选择事件"""
        selected_items = self.stock_tree.selection()
        if not selected_items:
            return
        
        # 获取选中的股票
        item = selected_items[0]
        values = self.stock_tree.item(item, 'values')
        if not values:
            return
        
        # 获取股票信息
        code = values[0]
        name = values[1]
        price = float(values[2])
        
        # 更新表单
        self.code_var.set(code)
        self.name_var.set(name)
        self.price_var.set(f"{price:.2f}")
        
        # 更新持仓数量
        self.update_holding_quantity(code)
        
        # 启用提交按钮
        self.submit_btn.config(state=tk.NORMAL)
    
    def update_user_info(self):
        """更新用户账户信息"""
        user = db.get_user(self.username)
        if user:
            balance = user.get("balance", 0)
            self.balance_var.set(f"{balance:.2f}")
    
    def update_holding_quantity(self, code):
        """更新持仓数量"""
        user = db.get_user(self.username)
        if user:
            holdings = user.get("holdings", {})
            if code in holdings:
                quantity = holdings[code].get("quantity", 0)
                self.holding_var.set(str(quantity))
            else:
                self.holding_var.set("0")
    
    def update_amount(self, *args):
        """更新交易金额"""
        try:
            quantity = int(self.quantity_var.get())
            price = float(self.price_var.get())
            amount = quantity * price
            self.amount_var.set(f"{amount:.2f}")
        except:
            self.amount_var.set("0.00")
    
    def execute_trade(self):
        """执行交易"""
        # 获取交易信息
        code = self.code_var.get()
        trade_type = self.trade_type_var.get()
        
        try:
            quantity = int(self.quantity_var.get())
            if quantity <= 0:
                messagebox.showerror("错误", "交易数量必须大于0")
                return
        except:
            messagebox.showerror("错误", "请输入有效的交易数量")
            return
        
        # 执行交易
        success, message = db.execute_trade(self.username, trade_type, code, quantity)
        
        if success:
            messagebox.showinfo("成功", message)
            # 更新用户信息
            self.update_user_info()
            # 更新持仓数量
            self.update_holding_quantity(code)
            # 更新交易记录
            self.load_transactions()
            # 清空数量
            self.quantity_var.set("")
        else:
            messagebox.showerror("错误", message) 