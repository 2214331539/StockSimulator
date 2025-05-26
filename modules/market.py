import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import threading
import time
from datetime import datetime, timedelta
from .stock_data import stock_manager
from .database import db
import ttkbootstrap as tb
from ttkbootstrap import Style  # 显式导入Style

# 定义全局颜色变量
BACKGROUND_COLOR = "#0d1926"  # 深蓝色背景
TEXT_COLOR = "#ffffff"  # 白色文本
ACCENT_COLOR = "#1e90ff"  # 亮蓝色强调色
UP_COLOR = "#ff4d4d"  # 上涨颜色(红色)
DOWN_COLOR = "#00e676"  # 下跌颜色(绿色)
GRID_COLOR = "#1a3c5e"  # 网格线颜色
CHART_BG_COLOR = "#0d1926"  # 图表背景色
CHART_AREA_COLOR = "#142638"  # 图表区域色

class MarketFrame(tb.Frame):  # 使用ttkbootstrap美化界面
    """市场信息页面框架"""
    
    def __init__(self, parent, username):
        super().__init__(parent, bootstyle="dark")
        self.username = username
        self.update_running = False
        self.current_stock_code = None # 用于存储当前选中的股票代码
        self.current_stock_name = None # 用于存储当前选中的股票名称
        self.current_chart_period = "daily" #新增：追踪当前图表周期，默认为日线
        
        # 不使用background属性，使用bootstyle
        # self.configure(background=BACKGROUND_COLOR)
        
        # 创建标题
        self.title_label = tb.Label(self, text="市场行情", font=("微软雅黑", 16, "bold"), 
                                   bootstyle="inverse-dark")
        self.title_label.pack(pady=10, padx=10, anchor="w")
        
        # 创建上部框架，包含控制按钮和搜索框
        self.top_frame = tb.Frame(self, bootstyle="dark")
        # self.top_frame.configure(background=BACKGROUND_COLOR)
        self.top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 创建刷新按钮
        self.refresh_btn = tb.Button(self.top_frame, text="刷新行情", command=self.refresh_market, 
                                    bootstyle="info-outline")
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建自动刷新按钮
        self.auto_refresh_var = tk.BooleanVar(value=False)
        self.auto_refresh_btn = tb.Checkbutton(
            self.top_frame, 
            text="自动刷新", 
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh,
            bootstyle="info-round-toggle"
        )
        self.auto_refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建最后刷新时间标签
        self.last_refresh_var = tk.StringVar(value="未刷新")
        self.last_refresh_label = tb.Label(self.top_frame, text="最后刷新: ", 
                                         bootstyle="light")
        self.last_refresh_label.pack(side=tk.LEFT, padx=(20, 0))
        self.last_refresh_time = tb.Label(self.top_frame, textvariable=self.last_refresh_var, 
                                        bootstyle="info")
        self.last_refresh_time.pack(side=tk.LEFT, padx=(0, 20))
        
        # 创建搜索框
        tb.Label(self.top_frame, text="搜索股票:", bootstyle="light").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        self.search_entry = tb.Entry(self.top_frame, textvariable=self.search_var, width=20, 
                                   bootstyle="dark")
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_btn = tb.Button(self.top_frame, text="搜索", command=self.search_stock, 
                                  bootstyle="info-outline")
        self.search_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建主框架，分为左右两部分
        self.main_frame = tb.Frame(self, bootstyle="dark")
        # self.main_frame.configure(background=BACKGROUND_COLOR)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧股票列表框架
        self.left_frame = tb.Frame(self.main_frame, bootstyle="dark")
        # self.left_frame.configure(background=BACKGROUND_COLOR)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 创建股票列表
        self.create_stock_list()
        
        # 创建右侧图表框架
        self.right_frame = tb.Frame(self.main_frame, bootstyle="dark")
        # self.right_frame.configure(background=BACKGROUND_COLOR)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建图表
        self.create_chart()
        
        # 创建图表周期切换按钮
        self.create_chart_period_buttons()
        
        # 创建状态刷新指示器
        self.status_frame = tb.Frame(self, bootstyle="dark")
        # self.status_frame.configure(background=BACKGROUND_COLOR)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        self.status_label = tb.Label(self.status_frame, text="状态: 就绪", bootstyle="secondary")
        self.status_label.pack(side=tk.LEFT)
        
        self.refresh_indicator = tb.Label(self.status_frame, text="○", bootstyle="danger")
        self.refresh_indicator.pack(side=tk.RIGHT)
        
        # 初始加载数据
        self.load_market_data()
    
    def create_stock_list(self):
        """创建股票列表"""
        # 创建标题
        list_title = tb.Label(self.left_frame, text="股票列表", font=("微软雅黑", 12, "bold"), 
                            bootstyle="info")
        list_title.pack(pady=5, anchor="w")
        
        # 创建股票列表框架
        self.stock_frame = tb.Frame(self.left_frame, bootstyle="dark")
        self.stock_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建股票列表
        columns = ('代码', '名称', '价格', '涨跌幅')
        self.stock_tree = tb.Treeview(self.stock_frame, columns=columns, show='headings', bootstyle="dark")
        
        # 设置列标题
        for col in columns:
            self.stock_tree.heading(col, text=col)
        
        # 设置列宽
        self.stock_tree.column('代码', width=100)
        self.stock_tree.column('名称', width=100)
        self.stock_tree.column('价格', width=80)
        self.stock_tree.column('涨跌幅', width=100)  # 扩大涨跌幅列，以便显示更多信息
        
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
        scrollbar = tb.Scrollbar(self.stock_frame, orient=tk.VERTICAL, command=self.stock_tree.yview, 
                               bootstyle="round-dark")
        self.stock_tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 绑定选择事件
        self.stock_tree.bind("<<TreeviewSelect>>", self.on_stock_select)
    
    def create_chart(self):
        """创建图表"""
        # 创建标题
        chart_title_frame = tb.Frame(self.right_frame, bootstyle="dark")
        chart_title_frame.pack(fill=tk.X, pady=(5,0)) # pady只有top

        self.chart_title_var = tk.StringVar(value="请选择股票查看走势")
        chart_title_label = tb.Label(chart_title_frame, textvariable=self.chart_title_var, 
                                   font=("微软雅黑", 12, "bold"), bootstyle="info")
        chart_title_label.pack(side=tk.LEFT, anchor="w") # 左对齐
        
        # 图表周期切换按钮将放在这个标题下方的新Frame中
        self.chart_period_btn_frame_in_chart_area = tb.Frame(chart_title_frame, bootstyle="dark")
        self.chart_period_btn_frame_in_chart_area.pack(side=tk.RIGHT) # 右对齐

        # 创建图表框架
        self.chart_frame = tb.Frame(self.right_frame, bootstyle="dark")
        self.chart_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置图表风格为深色背景
        plt.style.use('dark_background')
        
        # 创建图表
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 初始化图表
        self.ax.set_title(self.chart_title_var.get(), color=TEXT_COLOR)
        self.ax.set_xlabel("日期", color=TEXT_COLOR)
        self.ax.set_ylabel("价格", color=TEXT_COLOR)
        self.ax.tick_params(colors=TEXT_COLOR)
        self.fig.patch.set_facecolor(CHART_BG_COLOR)  # 设置图表背景颜色
        self.ax.set_facecolor(CHART_AREA_COLOR)  # 设置坐标区域背景颜色
        
        # 设置网格线
        self.ax.grid(True, linestyle='--', alpha=0.3, color=GRID_COLOR)
        
        self.canvas.draw()
    
    def create_chart_period_buttons(self):
        """创建图表周期切换按钮，放在图表标题栏右侧"""
        # 使用 self.chart_period_btn_frame_in_chart_area 这个Frame
        parent_frame = self.chart_period_btn_frame_in_chart_area

        self.daily_chart_btn = tb.Button(parent_frame, text="日K", 
                                           command=self.set_daily_chart_period, 
                                           bootstyle="outline-info", width=5)
        self.daily_chart_btn.pack(side=tk.LEFT, padx=(0,5))

        self.hourly_chart_btn = tb.Button(parent_frame, text="时K", 
                                            command=self.set_hourly_chart_period, 
                                            bootstyle="outline-info", width=5)
        self.hourly_chart_btn.pack(side=tk.LEFT, padx=0)
        
        # 初始化时，根据默认周期更新按钮状态
        self.update_period_button_states()

    def set_daily_chart_period(self):
        """设置图表周期为日线并刷新"""
        if self.current_chart_period != "daily":
            self.current_chart_period = "daily"
            self.update_period_button_states()
            if self.current_stock_code and self.current_stock_name:
                self.update_chart(self.current_stock_code, self.current_stock_name)
            else:
                 # 如果还没有选中的股票，只更新标题
                self.ax.clear()
                self.chart_title_var.set("请选择股票查看日K线走势")
                self.ax.set_title(self.chart_title_var.get(), color=TEXT_COLOR)
                self.canvas.draw()

    def set_hourly_chart_period(self):
        """设置图表周期为小时线并刷新"""
        if self.current_chart_period != "hourly":
            self.current_chart_period = "hourly"
            self.update_period_button_states()
            if self.current_stock_code and self.current_stock_name:
                self.update_chart(self.current_stock_code, self.current_stock_name)
            else:
                self.ax.clear()
                self.chart_title_var.set("请选择股票查看近24小时走势")
                self.ax.set_title(self.chart_title_var.get(), color=TEXT_COLOR)
                self.canvas.draw()

    def update_period_button_states(self):
        """根据当前选择的周期更新按钮的样式 (例如，选中的按钮为实心)"""
        if self.current_chart_period == "daily":
            self.daily_chart_btn.config(bootstyle="info") # 实心
            self.hourly_chart_btn.config(bootstyle="outline-info") # 空心
        elif self.current_chart_period == "hourly":
            self.daily_chart_btn.config(bootstyle="outline-info")
            self.hourly_chart_btn.config(bootstyle="info")

    def load_market_data(self):
        """加载市场数据"""
        # 更新状态
        self.status_label.config(text="状态: 正在加载数据...", bootstyle="warning")
        self.refresh_indicator.config(text="●", bootstyle="warning")
        
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        
        # 获取股票数据
        stocks = db.get_stocks()
        
        # 扩大涨跌幅列，以便显示更多信息
        self.stock_tree.column('涨跌幅', width=100)
        
        # 添加到列表
        for code, info in stocks.items():
            name = info.get("name", "")
            price = info.get("price", 0)
            change = info.get("change", 0)
            
            # 根据涨跌幅设置颜色标签
            if change > 0:
                tag = "up"
                change_str = f"+{change:.2f}%"
            elif change < 0:
                tag = "down"
                change_str = f"{change:.2f}%"
            else:
                tag = "flat"
                change_str = f"{change:.2f}%"
            
            # 添加数据获取时间标记
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 插入数据
            self.stock_tree.insert('', tk.END, values=(code, name, f"{price:.2f}", change_str), tags=(tag,))
        
        # 设置颜色
        self.stock_tree.tag_configure('up', foreground=UP_COLOR)  # 鲜艳的红色
        self.stock_tree.tag_configure('down', foreground=DOWN_COLOR)  # 鲜艳的绿色
        self.stock_tree.tag_configure('flat', foreground=TEXT_COLOR)  # 白色
        
        # 更新最后刷新时间
        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_refresh_var.set(current_time)
        
        # 更新状态
        self.status_label.config(text=f"状态: 数据加载完成，显示价格为实时价格", bootstyle="success")
        self.refresh_indicator.config(text="●", bootstyle="success")
        
        # 3秒后恢复状态指示器
        self.after(3000, lambda: self.refresh_indicator.config(text="○", bootstyle="secondary"))
    
    def refresh_market(self):
        """刷新市场数据"""
        # 更新状态
        self.status_label.config(text="状态: 正在刷新实时数据...", bootstyle="warning")
        self.refresh_indicator.config(text="●", bootstyle="warning")
        self.refresh_btn.config(state=tk.DISABLED)
        
        def do_refresh():
            # 先同步价格数据（确保数据库中的价格与实际价格一致）
            stock_manager.sync_stock_prices()
            
            # 更新股票价格
            stock_manager.update_stock_prices()
            
            # 重新加载数据
            self.load_market_data()
            
            # 如果有选中的股票，重新加载图表
            selected_items = self.stock_tree.selection()
            if selected_items:
                item = selected_items[0]
                values = self.stock_tree.item(item, 'values')
                if values:
                    code = values[0]
                    name = values[1]
                    self.update_chart(code, name)
            
            # 恢复按钮状态
            self.refresh_btn.config(state=tk.NORMAL)
        
        # 使用线程进行刷新，避免界面卡顿
        threading.Thread(target=do_refresh, daemon=True).start()
    
    def toggle_auto_refresh(self):
        """切换自动刷新状态"""
        if self.auto_refresh_var.get():
            # 启动自动刷新
            self.update_running = True
            self.status_label.config(text="状态: 自动刷新已启动", bootstyle="success")
            self.auto_refresh_thread = threading.Thread(target=self.auto_refresh_task)
            self.auto_refresh_thread.daemon = True
            self.auto_refresh_thread.start()
        else:
            # 停止自动刷新
            self.update_running = False
            self.status_label.config(text="状态: 自动刷新已停止", bootstyle="secondary")
    
    def auto_refresh_task(self):
        """自动刷新任务"""
        while self.update_running:
            # 刷新数据
            self.after(0, self.refresh_market)
            # 等待30秒（模拟实时行情的刷新间隔）
            time.sleep(30)
    
    def search_stock(self):
        """搜索股票"""
        keyword = self.search_var.get().strip()
        if not keyword:
            messagebox.showinfo("提示", "请输入搜索关键词")
            return
        
        # 更新状态
        self.status_label.config(text=f"状态: 正在搜索 '{keyword}'...", bootstyle="info")
        
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
                change_str = f"+{change:.2f}%"
            elif change < 0:
                tag = "down"
                change_str = f"{change:.2f}%"
            else:
                tag = "flat"
                change_str = f"{change:.2f}%"
            
            # 插入数据
            self.stock_tree.insert('', tk.END, values=(code, name, f"{price:.2f}", change_str), tags=(tag,))
        
        # 更新状态
        if results:
            self.status_label.config(text=f"状态: 找到 {len(results)} 个匹配结果", bootstyle="success")
        else:
            self.status_label.config(text=f"状态: 未找到匹配结果", bootstyle="danger")
            messagebox.showinfo("提示", f"未找到与 '{keyword}' 相关的股票")
    
    def on_stock_select(self, event):
        """处理股票选择事件"""
        selected_items = self.stock_tree.selection()
        if not selected_items:
            self.current_stock_code = None # 清除当前选中的股票
            self.current_stock_name = None
            return
        
        item = selected_items[0]
        values = self.stock_tree.item(item, 'values')
        if not values:
            self.current_stock_code = None
            self.current_stock_name = None
            return
        
        code = values[0]
        name = values[1]

        self.current_stock_code = code # 保存当前选中的股票
        self.current_stock_name = name
        
        self.status_label.config(text=f"状态: 正在加载 {name}({code}) 图表...", bootstyle="info")
        self.update_chart(code, name) # update_chart会根据current_chart_period选择数据源
    
    def update_chart(self, code, name):
        """根据当前选择的周期更新图表"""
        self.ax.clear() # 清除旧图
        df = pd.DataFrame()

        if self.current_chart_period == "daily":
            self.chart_title_var.set(f"{name} ({code}) - 日K线")
            # 计算60天前的日期和今天的日期
            end_date_daily = datetime.now().strftime("%Y-%m-%d")
            start_date_daily = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
            df = stock_manager.get_stock_data(code, start_date=start_date_daily, end_date=end_date_daily)
        elif self.current_chart_period == "hourly":
            self.chart_title_var.set(f"{name} ({code}) - 近24小时")
            df = stock_manager.get_stock_hourly_data(code, lookback_hours=24)
        
        self.ax.set_title(self.chart_title_var.get(), color=TEXT_COLOR)

        if df.empty:
            msg = f"未找到 {code} 的 {self.current_chart_period} 数据"
            messagebox.showinfo("提示", msg)
            self.status_label.config(text=f"状态: {msg}", bootstyle="danger")
            self.ax.text(0.5, 0.5, msg, horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR, transform=self.ax.transAxes)
            self.canvas.draw()
            return

        # 确保 'date' 和 'close' 列存在
        if 'date' not in df.columns or 'close' not in df.columns:
            msg = f"{code} 返回的数据缺少 'date' 或 'close' 列 ({self.current_chart_period} 周期)"
            messagebox.showerror("数据错误", msg)
            self.status_label.config(text=f"状态: {msg}", bootstyle="danger")
            self.ax.text(0.5, 0.5, "数据格式错误", horizontalalignment='center', verticalalignment='center', color=TEXT_COLOR, transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # 'date' 列对于小时数据已经是 datetime 对象，对于日线数据是 YYYY-MM-DD 字符串
        # Matplotlib 可以处理这两种情况，但为了统一和更好的格式化，我们转换为 datetime
        try:
            df['date'] = pd.to_datetime(df['date'])
        except Exception as e:
            print(f"转换日期列失败: {e}")
            messagebox.showerror("数据错误", f"日期格式无法解析: {e}")
            # Fallback or return
            self.canvas.draw()
            return

        self.ax.plot(df['date'], df['close'], marker='.', linestyle='-', color=ACCENT_COLOR, linewidth=1.5)
        
        self.ax.set_xlabel("时间", color=TEXT_COLOR)
        self.ax.set_ylabel("价格", color=TEXT_COLOR)
        self.ax.tick_params(axis='x', colors=TEXT_COLOR, labelrotation=45)
        self.ax.tick_params(axis='y', colors=TEXT_COLOR)
        self.ax.grid(True, linestyle='--', alpha=0.3, color=GRID_COLOR)
        self.fig.patch.set_facecolor(CHART_BG_COLOR)
        self.ax.set_facecolor(CHART_AREA_COLOR)

        # 设置X轴日期格式和定位器
        import matplotlib.dates as mdates
        if self.current_chart_period == "daily":
            date_format = mdates.DateFormatter('%Y-%m-%d')
            # 自动选择最优的日期刻度定位器，同时限制刻度数量
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=5, maxticks=10, tz=None))
            self.ax.xaxis.set_minor_locator(mdates.DayLocator()) # 以天为次刻度单位
        elif self.current_chart_period == "hourly":
            date_format = mdates.DateFormatter('%m-%d %H:%M')
            # 对于小时图，可以更密集一些，比如每隔几个小时一个主刻度
            # AutoDateLocator 仍然可用，或者指定 HourLocator
            self.ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=8, tz=None))
            # self.ax.xaxis.set_major_locator(mdates.HourLocator(interval=4)) # 例如每4小时一个主刻度
            self.ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6))) # 每6小时一个次刻度
        
        self.ax.xaxis.set_major_formatter(date_format)
        self.fig.autofmt_xdate(rotation=30, ha='right') # 自动格式化X轴日期，旋转并右对齐

        # 标注逻辑 (图表最后一个数据点)
        if (self.current_chart_period == "daily" or self.current_chart_period == "hourly") and not df.empty:
            last_date = df['date'].iloc[-1]
            last_price = df['close'].iloc[-1]
            self.ax.scatter([last_date], [last_price], color='red', s=50, zorder=5) # zorder确保点在最上层
            self.ax.annotate(f'{last_price:.2f}', (last_date, last_price),
                             xytext=(5, 5), textcoords='offset points',
                             color=TEXT_COLOR, bbox=dict(boxstyle="round,pad=0.2", fc=CHART_AREA_COLOR, alpha=0.7))

        self.fig.tight_layout() # 自动调整布局以适应旋转的标签
        self.canvas.draw()
        self.status_label.config(text=f"状态: {name}({code}) {self.current_chart_period} 图表已加载", bootstyle="success")
    
    def sync_and_refresh(self):
        """同步股票价格数据并刷新显示"""
        # 禁用按钮，防止重复点击
        if hasattr(self, 'sync_btn'):
            self.sync_btn.configure(state=tk.DISABLED)
        self.refresh_btn.configure(state=tk.DISABLED)
        
        # 更新状态
        self.status_label.config(text="状态: 正在同步价格数据...", bootstyle="warning")
        self.refresh_indicator.config(text="●", bootstyle="warning")
        
        def do_sync():
            # 同步价格数据
            stock_manager.sync_stock_prices()
            
            # 刷新市场数据
            self.load_market_data()
            
            # 如果有选中的股票，重新加载图表
            selected_items = self.stock_tree.selection()
            if selected_items:
                item = selected_items[0]
                values = self.stock_tree.item(item, 'values')
                if values:
                    code = values[0]
                    name = values[1]
                    self.update_chart(code, name)
            
            # 恢复按钮状态
            self.refresh_btn.configure(state=tk.NORMAL)
            if hasattr(self, 'sync_btn'):
                self.sync_btn.configure(state=tk.NORMAL)
        
        # 使用线程进行同步，避免界面卡顿
        threading.Thread(target=do_sync, daemon=True).start()