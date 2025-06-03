import tkinter as tk
import ttkbootstrap as tb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
from .stock_data import stock_manager
from .database import db
from ttkbootstrap import Style

# 定义颜色
UP_COLOR = "#ff4d4d"  # 涨用红色
DOWN_COLOR = "#00e676"  # 跌用绿色
TEXT_COLOR = "#ffffff"
BACKGROUND_COLOR = "#0d1926"
CHART_AREA_COLOR = "#142638"

class StockRecommendationEngine:
    """股票推荐引擎，使用技术分析指标"""
    
    def __init__(self):
        self.indicators_weights = {
            'ma_signal': 0.25,    # 移动平均线信号
            'rsi_signal': 0.20,   # RSI信号
            'volume_signal': 0.15, # 成交量信号
            'price_momentum': 0.25, # 价格动量
            'volatility_signal': 0.15  # 波动率信号
        }
    
    def calculate_ma_signal(self, df):
        """计算移动平均线信号"""
        if len(df) < 20:
            return 0
        
        # 计算5日和20日移动平均
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        current_price = df['close'].iloc[-1]
        ma5_current = df['ma5'].iloc[-1]
        ma20_current = df['ma20'].iloc[-1]
        
        # 信号计算
        if current_price > ma5_current > ma20_current:
            return 0.8  # 强烈看涨
        elif current_price > ma5_current:
            return 0.6  # 看涨
        elif current_price < ma5_current < ma20_current:
            return -0.8  # 强烈看跌
        elif current_price < ma5_current:
            return -0.6  # 看跌
        else:
            return 0  # 中性
    
    def calculate_rsi_signal(self, df):
        """计算RSI信号"""
        if len(df) < 15:
            return 0
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        if pd.isna(current_rsi):
            return 0
        
        # RSI信号判断
        if current_rsi < 30:
            return 0.7  # 超卖，看涨
        elif current_rsi > 70:
            return -0.7  # 超买，看跌
        elif current_rsi < 50:
            return 0.3  # 偏看涨
        else:
            return -0.3  # 偏看跌
    
    def calculate_volume_signal(self, df):
        """计算成交量信号"""
        if len(df) < 10 or 'volume' not in df.columns:
            return 0
        
        # 计算成交量移动平均
        df['volume_ma'] = df['volume'].rolling(window=10).mean()
        
        current_volume = df['volume'].iloc[-1]
        volume_ma = df['volume_ma'].iloc[-1]
        
        if pd.isna(volume_ma) or volume_ma == 0:
            return 0
        
        volume_ratio = current_volume / volume_ma
        
        # 结合价格变化判断
        price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
        
        if volume_ratio > 1.5 and price_change > 0:
            return 0.6  # 放量上涨
        elif volume_ratio > 1.5 and price_change < 0:
            return -0.6  # 放量下跌
        elif volume_ratio < 0.8:
            return -0.2  # 缩量，较弱信号
        else:
            return 0
    
    def calculate_price_momentum(self, df):
        """计算价格动量信号"""
        if len(df) < 5:
            return 0
        
        # 计算3日和5日收益率
        df['return_3d'] = df['close'].pct_change(3)
        df['return_5d'] = df['close'].pct_change(5)
        
        return_3d = df['return_3d'].iloc[-1]
        return_5d = df['return_5d'].iloc[-1]
        
        if pd.isna(return_3d) or pd.isna(return_5d):
            return 0
        
        # 动量信号
        momentum_score = (return_3d * 0.6 + return_5d * 0.4) * 10
        return np.clip(momentum_score, -1, 1)
    
    def calculate_volatility_signal(self, df):
        """计算波动率信号"""
        if len(df) < 10:
            return 0
        
        # 计算10日波动率
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].rolling(window=10).std()
        current_volatility = volatility.iloc[-1]
        
        if pd.isna(current_volatility):
            return 0
        
        # 波动率过高给予负分，适中给予正分
        if current_volatility > 0.05:  # 5%以上波动率
            return -0.4
        elif current_volatility < 0.02:  # 2%以下波动率
            return 0.2
        else:
            return 0.1
    
    def analyze_stock(self, code):
        """分析单只股票，返回推荐信号"""
        try:
            # 获取30天历史数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            df = stock_manager.get_stock_data(code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                return 0, "数据不足"
            
            # 计算各项技术指标
            ma_signal = self.calculate_ma_signal(df.copy())
            rsi_signal = self.calculate_rsi_signal(df.copy())
            volume_signal = self.calculate_volume_signal(df.copy())
            momentum_signal = self.calculate_price_momentum(df.copy())
            volatility_signal = self.calculate_volatility_signal(df.copy())
            
            # 计算综合得分
            total_score = (
                ma_signal * self.indicators_weights['ma_signal'] +
                rsi_signal * self.indicators_weights['rsi_signal'] +
                volume_signal * self.indicators_weights['volume_signal'] +
                momentum_signal * self.indicators_weights['price_momentum'] +
                volatility_signal * self.indicators_weights['volatility_signal']
            )
            
            # 转换为概率（-1到1转换为0%到100%）
            probability = (total_score + 1) * 50
            probability = np.clip(probability, 0, 100)
            
            # 生成推荐理由
            reasons = []
            if abs(ma_signal) > 0.5:
                reasons.append(f"均线{'看涨' if ma_signal > 0 else '看跌'}")
            if abs(rsi_signal) > 0.5:
                reasons.append(f"RSI{'超卖' if rsi_signal > 0 else '超买'}")
            if abs(volume_signal) > 0.4:
                reasons.append(f"成交量{'放大' if volume_signal > 0 else '萎缩'}")
            
            reason = ", ".join(reasons) if reasons else "综合技术指标分析"
            
            return probability, reason
            
        except Exception as e:
            print(f"分析股票 {code} 时出错: {e}")
            return 50, "分析出错"
    
    def get_all_recommendations(self):
        """获取所有股票的推荐"""
        stocks = db.get_stocks()
        recommendations = {}
        
        for code, stock_info in stocks.items():
            probability, reason = self.analyze_stock(code)
            recommendations[code] = {
                'name': stock_info.get('name', ''),
                'current_price': stock_info.get('price', 0),
                'probability': probability,
                'reason': reason,
                'direction': 'up' if probability > 50 else 'down',
                'confidence': abs(probability - 50) * 2  # 0-100的置信度
            }
        
        return recommendations

class RecommendationFrame(tb.Frame):
    """股票推荐页面框架"""
    
    def __init__(self, parent, username):
        super().__init__(parent, bootstyle="dark")
        self.username = username
        self.recommendation_engine = StockRecommendationEngine()
        self.recommendations = {}
        
        # 创建标题
        self.title_label = tb.Label(self, text="股票推荐", font=("微软雅黑", 16, "bold"), 
                                   bootstyle="inverse-dark")
        self.title_label.pack(pady=10, padx=10, anchor="w")
        
        # 创建控制按钮框架
        self.control_frame = tb.Frame(self, bootstyle="dark")
        self.control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 刷新按钮
        self.refresh_btn = tb.Button(self.control_frame, text="刷新推荐", 
                                   command=self.refresh_recommendations, 
                                   bootstyle="info-outline")
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="点击刷新获取推荐")
        self.status_label = tb.Label(self.control_frame, textvariable=self.status_var, 
                                   bootstyle="secondary")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 创建主框架（左右分布）
        self.main_frame = tb.Frame(self, bootstyle="dark")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧股票推荐列表
        self.create_stock_list()
        
        # 创建右侧排行榜
        self.create_ranking_panel()
    
    def create_stock_list(self):
        """创建股票推荐列表"""
        # 左侧框架
        self.left_frame = tb.Frame(self.main_frame, bootstyle="dark")
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 标题
        list_title = tb.Label(self.left_frame, text="股票推荐列表", 
                            font=("微软雅黑", 12, "bold"), bootstyle="info")
        list_title.pack(pady=5, anchor="w")
        
        # 创建列表框架
        self.stock_list_frame = tb.Frame(self.left_frame, bootstyle="dark")
        self.stock_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ('代码', '名称', '当前价格', '涨跌概率', '置信度', '推荐理由')
        self.stock_tree = tb.Treeview(self.stock_list_frame, columns=columns, 
                                    show='headings', bootstyle="dark")
        
        # 设置列标题和宽度
        self.stock_tree.heading('代码', text='代码')
        self.stock_tree.heading('名称', text='名称')
        self.stock_tree.heading('当前价格', text='当前价格')
        self.stock_tree.heading('涨跌概率', text='涨跌概率')
        self.stock_tree.heading('置信度', text='置信度')
        self.stock_tree.heading('推荐理由', text='推荐理由')
        
        self.stock_tree.column('代码', width=80)
        self.stock_tree.column('名称', width=100)
        self.stock_tree.column('当前价格', width=80)
        self.stock_tree.column('涨跌概率', width=100)
        self.stock_tree.column('置信度', width=80)
        self.stock_tree.column('推荐理由', width=200)
        
        # 添加滚动条
        scrollbar_left = tb.Scrollbar(self.stock_list_frame, orient=tk.VERTICAL, 
                                    command=self.stock_tree.yview, bootstyle="round-dark")
        self.stock_tree.configure(yscrollcommand=scrollbar_left.set)
        
        # 布局
        self.stock_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_left.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_ranking_panel(self):
        """创建排行榜面板"""
        # 右侧框架
        self.right_frame = tb.Frame(self.main_frame, bootstyle="dark")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 标题
        ranking_title = tb.Label(self.right_frame, text="涨跌排行榜", 
                               font=("微软雅黑", 12, "bold"), bootstyle="info")
        ranking_title.pack(pady=5, anchor="w")
        
        # 看涨排行榜
        self.up_frame = tb.LabelFrame(self.right_frame, text="看涨前五", 
                                    bootstyle="success", padding=10)
        self.up_frame.pack(fill=tk.X, pady=5)
        
        self.up_list = tb.Treeview(self.up_frame, columns=('股票', '概率'), 
                                 show='headings', height=5, bootstyle="dark")
        self.up_list.heading('股票', text='股票')
        self.up_list.heading('概率', text='涨概率')
        self.up_list.column('股票', width=120)
        self.up_list.column('概率', width=80)
        self.up_list.pack(fill=tk.X)
        
        # 看跌排行榜
        self.down_frame = tb.LabelFrame(self.right_frame, text="看跌前五", 
                                      bootstyle="danger", padding=10)
        self.down_frame.pack(fill=tk.X, pady=5)
        
        self.down_list = tb.Treeview(self.down_frame, columns=('股票', '概率'), 
                                   show='headings', height=5, bootstyle="dark")
        self.down_list.heading('股票', text='股票')
        self.down_list.heading('概率', text='跌概率')
        self.down_list.column('股票', width=120)
        self.down_list.column('概率', width=80)
        self.down_list.pack(fill=tk.X)
        
        # 算法说明
        info_frame = tb.LabelFrame(self.right_frame, text="算法说明", 
                                 bootstyle="info", padding=10)
        info_frame.pack(fill=tk.X, pady=10)
        
        info_text = """基于技术分析指标：
• 移动平均线 (25%):分析5日和20日均线趋势(5日线上穿20日线是强烈买入信号)
• RSI指标 (20%): 判断超买超卖状态(RSI<30为超卖，RSI>70为超买)
• 成交量分析 (15%): 结合价格变化分析量价关系(成交量放大，价格上涨是强烈买入信号)
• 价格动量 (25%): 计算短期价格动量(短期价格动量越大，上涨或下跌趋势越明显)
• 波动率分析 (15%): 分析价格波动率(波动率越大，价格波动越大，风险越高)

概率>50%为看涨
概率<50%为看跌
置信度越高越可靠"""
        
        info_label = tb.Label(info_frame, text=info_text, justify=tk.LEFT, 
                            font=("微软雅黑", 8), bootstyle="light")
        info_label.pack(anchor="w")
    
    def refresh_recommendations(self):
        """刷新推荐数据"""
        self.status_var.set("正在分析股票数据...")
        self.refresh_btn.config(state=tk.DISABLED)
        
        def do_analysis():
            try:
                # 获取推荐数据
                self.recommendations = self.recommendation_engine.get_all_recommendations()
                
                # 更新界面
                self.after(0, self.update_display)
                
            except Exception as e:
                print(f"分析股票数据时出错: {e}")
                self.after(0, lambda: self.status_var.set(f"分析失败: {e}"))
            finally:
                self.after(0, lambda: self.refresh_btn.config(state=tk.NORMAL))
        
        # 在后台线程中进行分析
        threading.Thread(target=do_analysis, daemon=True).start()
    
    def update_display(self):
        """更新显示"""
        # 清空列表
        for item in self.stock_tree.get_children():
            self.stock_tree.delete(item)
        for item in self.up_list.get_children():
            self.up_list.delete(item)
        for item in self.down_list.get_children():
            self.down_list.delete(item)
        
        if not self.recommendations:
            self.status_var.set("无推荐数据")
            return
        
        # 更新主列表
        for code, rec in self.recommendations.items():
            probability = rec['probability']
            confidence = rec['confidence']
            
            # 格式化显示
            prob_text = f"{probability:.1f}%"
            conf_text = f"{confidence:.1f}%"
            price_text = f"{rec['current_price']:.2f}"
            
            # 设置颜色标签
            if probability > 60:
                tag = "strong_up"
            elif probability > 50:
                tag = "up"
            elif probability < 40:
                tag = "strong_down"
            else:
                tag = "down"
            
            self.stock_tree.insert('', tk.END, 
                                 values=(code, rec['name'], price_text, prob_text, 
                                        conf_text, rec['reason']), 
                                 tags=(tag,))
        
        # 设置颜色
        self.stock_tree.tag_configure('strong_up', foreground='#ff6b6b')
        self.stock_tree.tag_configure('up', foreground='#ffa8a8')
        self.stock_tree.tag_configure('strong_down', foreground='#51cf66')
        self.stock_tree.tag_configure('down', foreground='#8ce99a')
        
        # 更新排行榜
        self.update_rankings()
        
        self.status_var.set(f"分析完成，共{len(self.recommendations)}只股票")
    
    def update_rankings(self):
        """更新排行榜"""
        # 按涨跌概率排序
        sorted_stocks = sorted(self.recommendations.items(), 
                             key=lambda x: x[1]['probability'], reverse=True)
        
        # 看涨前五（概率最高的）
        up_stocks = [stock for stock in sorted_stocks if stock[1]['probability'] > 50][:5]
        for code, rec in up_stocks:
            stock_name = f"{rec['name']}({code})"
            prob_text = f"{rec['probability']:.1f}%"
            self.up_list.insert('', tk.END, values=(stock_name, prob_text))
        
        # 看跌前五（概率最低的）
        down_stocks = sorted([stock for stock in sorted_stocks if stock[1]['probability'] < 50], 
                           key=lambda x: x[1]['probability'])[:5]
        for code, rec in down_stocks:
            stock_name = f"{rec['name']}({code})"
            prob_text = f"{100 - rec['probability']:.1f}%"  # 显示跌的概率
            self.down_list.insert('', tk.END, values=(stock_name, prob_text)) 