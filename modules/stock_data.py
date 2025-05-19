import baostock as bs
import pandas as pd
import random
import time
import requests
from datetime import datetime, timedelta
from .database import db

class StockDataManager:
    """股票数据管理类，用于获取和更新股票数据"""
    
    def __init__(self):
        """初始化股票数据管理器"""
        self.logged_in = False
        self.login()
        # 初始化时同步一次数据库中的股票价格
        self.sync_stock_prices()
    
    def login(self):
        """登录BaoStock"""
        try:
            lg = bs.login()
            if lg.error_code == '0':
                self.logged_in = True
                print("BaoStock登录成功")
            else:
                print(f"BaoStock登录失败: {lg.error_msg}")
        except Exception as e:
            print(f"BaoStock登录异常: {e}")
    
    def logout(self):
        """登出BaoStock"""
        if self.logged_in:
            bs.logout()
            self.logged_in = False
    
    def sync_stock_prices(self):
        """同步数据库中的股票价格与baostock的实际价格"""
        print("正在同步股票价格数据...")
        stocks = db.get_stocks()
        if not stocks:
            print("数据库中没有股票数据")
            return
        
        # 获取所有股票代码
        codes = list(stocks.keys())
        
        for code in codes:
            try:
                # 获取最近一个交易日的收盘价
                today = datetime.now().strftime("%Y-%m-%d")
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                
                rs = bs.query_history_k_data_plus(
                    code,
                    "date,close",
                    start_date=(datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),  # 获取更多历史数据确保能计算涨跌幅
                    end_date=today,
                    frequency="d",
                    adjustflag="3"
                )
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                if data_list:
                    # 获取最新一条数据
                    latest_data = data_list[-1]
                    if len(latest_data) > 1 and latest_data[1]:
                        new_price = float(latest_data[1])
                        old_price = stocks[code].get("price", 0)
                        old_change = stocks[code].get("change", 0)
                        
                        # 获取昨日收盘价计算涨跌幅
                        calculated_change = 0
                        if len(data_list) > 1:
                            prev_data = data_list[-2]
                            prev_close = float(prev_data[1]) if prev_data and prev_data[1] else 0
                            calculated_change = round(((new_price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0
                            
                            # 如果计算出的涨跌幅为0但是有昨日价格，强制重新计算
                            if calculated_change == 0 and prev_close > 0 and abs(new_price - prev_close) > 0.000001:
                                calculated_change = round(((new_price - prev_close) / prev_close) * 100, 2)
                                print(f"重新计算{code}涨跌幅: ({new_price} - {prev_close}) / {prev_close} * 100 = {calculated_change}%")
                        
                        # 决定使用哪个涨跌幅值
                        if abs(new_price - old_price) < 0.001 and old_change != 0:
                            # 如果价格没有变化且原涨跌幅不为0，保留原有涨跌幅
                            change = old_change
                            print(f"价格未变化，保留原涨跌幅: {code} 价格: {new_price}, 涨跌幅: {change}%")
                        else:
                            # 价格有变化或原涨跌幅为0，使用计算的新涨跌幅
                            change = calculated_change if calculated_change != 0 else old_change
                            print(f"使用计算的涨跌幅: {code} 价格: {new_price}, 涨跌幅: {change}%")
                        
                        # 更新数据库
                        stock_info = {
                            "name": stocks[code].get("name", ""),
                            "price": new_price,
                            "change": change
                        }
                        db.update_stock(code, stock_info)
                        print(f"已更新 {code} 价格: {new_price}, 涨跌幅: {change}%")
            except Exception as e:
                print(f"同步 {code} 价格失败: {e}")
        
        print("股票价格同步完成")
    
    def get_stock_data(self, code, start_date=None, end_date=None, frequency="d", adjustflag="3"):
        """
        获取股票历史数据
        :param code: 股票代码，如"sh.600000"
        :param start_date: 开始日期，格式YYYY-MM-DD，默认为30天前
        :param end_date: 结束日期，格式YYYY-MM-DD，默认为今天
        :param frequency: 数据频率，d=日k线，w=周k线，m=月k线，默认为d
        :param adjustflag: 复权类型，1=前复权，2=后复权，3=不复权，默认为3
        :return: DataFrame格式的股票数据
        """
        if not self.logged_in:
            self.login()
            if not self.logged_in:
                return pd.DataFrame()
        
        # 设置默认日期
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # 查询股票数据
        try:
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,adjustflag",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjustflag
            )
            
            # 处理结果集
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            # 转换为DataFrame
            if data_list:
                result = pd.DataFrame(data_list, columns=rs.fields)
                # 转换数据类型
                for field in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                    if field in result.columns:
                        result[field] = pd.to_numeric(result[field], errors='coerce')
                return result
            else:
                print(f"未获取到股票 {code} 的数据")
                return pd.DataFrame()
            
        except Exception as e:
            print(f"获取股票数据异常: {e}")
            return pd.DataFrame()
    
    def get_stock_basic_info(self, code):
        """
        获取股票基本信息
        :param code: 股票代码，如"sh.600000"
        :return: 股票基本信息
        """
        if not self.logged_in:
            self.login()
            if not self.logged_in:
                return None
        
        try:
            rs = bs.query_stock_basic(code=code)
            if rs.error_code == '0' and rs.next():
                return rs.get_row_data()
            else:
                print(f"未获取到股票 {code} 的基本信息")
                return None
        except Exception as e:
            print(f"获取股票基本信息异常: {e}")
            return None
    
    def get_realtime_quotes(self, codes):
        """
        获取实时行情数据
        :param codes: 股票代码列表，如["sh.600000", "sh.601398"]
        :return: 实时行情数据字典
        """
        if not self.logged_in:
            self.login()
            if not self.logged_in:
                return {}
        
        result = {}
        
        try:
            # 获取当前日期
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            for code in codes:
                # 尝试以下方式获取最新价格
                price = None
                change = 0
                
                # 方法1: 使用当日K线数据
                try:
                    rs_day = bs.query_history_k_data_plus(
                        code,
                        "date,open,high,low,close",
                        start_date=today,
                        end_date=today
                    )
                    day_data_list = []
                    while (rs_day.error_code == '0') & rs_day.next():
                        day_data_list.append(rs_day.get_row_data())
                    
                    if day_data_list:
                        data = day_data_list[0]
                        if len(data) > 4 and data[4]:
                            price = float(data[4])  # 收盘价
                            print(f"获取到{code}当日K线数据价格: {price}")
                except Exception as e:
                    print(f"获取{code}当日K线数据失败: {e}")
                
                # 方法2: 尝试获取最近一个交易日的收盘价
                if price is None:
                    try:
                        # 获取最近的历史数据
                        rs_hist = bs.query_history_k_data_plus(
                            code,
                            "date,close",
                            start_date=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                            end_date=today
                        )
                        hist_data_list = []
                        while (rs_hist.error_code == '0') & rs_hist.next():
                            hist_data_list.append(rs_hist.get_row_data())
                        
                        if hist_data_list:
                            # 获取最新一条历史数据
                            latest_hist_data = hist_data_list[-1]
                            if len(latest_hist_data) > 1 and latest_hist_data[1]:
                                price = float(latest_hist_data[1])
                                print(f"获取到{code}最近历史数据价格: {price}, 日期: {latest_hist_data[0]}")
                    except Exception as e:
                        print(f"获取{code}历史数据失败: {e}")
                
                # 方法3: 如果以上都失败，获取数据库中的价格
                if price is None:
                    stock_info = db.get_stock(code)
                    if stock_info:
                        price = stock_info.get("price", 0)
                        change = stock_info.get("change", 0)
                        print(f"使用{code}数据库价格: {price}")
                
                # 如果获取到价格，计算涨跌幅(除非已经获取到)
                if price is not None and change == 0:
                    try:
                        # 获取昨日收盘价
                        rs_prev = bs.query_history_k_data_plus(
                            code,
                            "close",
                            start_date=yesterday,
                            end_date=yesterday
                        )
                        prev_close = None
                        if rs_prev.error_code == '0' and rs_prev.next():
                            prev_data = rs_prev.get_row_data()
                            if prev_data and prev_data[0]:
                                prev_close = float(prev_data[0])
                        
                        # 计算涨跌幅
                        if prev_close and prev_close > 0:
                            change = round(((price - prev_close) / prev_close) * 100, 2)
                            print(f"计算{code}涨跌幅: {change}%")
                    except Exception as e:
                        print(f"计算{code}涨跌幅失败: {e}")
                        
                    # 如果仍然无法计算涨跌幅，使用数据库中的涨跌幅
                    if change == 0:
                        stock_info = db.get_stock(code)
                        if stock_info:
                            db_change = stock_info.get("change", 0)
                            if db_change != 0:
                                change = db_change
                                print(f"使用数据库中的涨跌幅: {change}%")
                
                # 存储结果
                if price is not None:
                    result[code] = {
                        "price": price,
                        "change": change,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
        except Exception as e:
            print(f"获取实时行情异常: {e}")
        
        return result
    
    def search_stocks(self, keyword):
        """
        搜索股票
        :param keyword: 关键词，可以是股票代码或名称
        :return: 匹配的股票列表
        """
        stocks = db.get_stocks()
        results = []
        
        for code, info in stocks.items():
            if keyword.lower() in code.lower() or keyword.lower() in info.get("name", "").lower():
                results.append({
                    "code": code,
                    "name": info.get("name", ""),
                    "price": info.get("price", 0),
                    "change": info.get("change", 0)
                })
        
        return results
    
    def update_stock_prices(self):
        """使用baostock获取实时股票数据更新价格"""
        stocks = db.get_stocks()
        
        if not stocks:
            return {}
        
        # 获取所有股票代码
        codes = list(stocks.keys())
        
        # 获取实时行情
        realtime_data = self.get_realtime_quotes(codes)
        
        updated_stocks = {}
        
        for code, info in stocks.items():
            if code in realtime_data:
                # 使用实时数据
                real_info = realtime_data[code]
                new_price = real_info.get("price", 0)
                change = real_info.get("change", 0)
                
                # 如果新价格与旧价格相同，且没有获取到新的涨跌幅，则保留原有涨跌幅
                old_price = info.get("price", 0)
                old_change = info.get("change", 0)
                
                # 如果计算的涨跌幅为0但价格确实变化了，尝试重新计算
                if change == 0 and abs(new_price - old_price) > 0.001:
                    # 获取最近的股票数据来计算涨跌幅
                    try:
                        today = datetime.now().strftime("%Y-%m-%d")
                        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                        
                        rs = bs.query_history_k_data_plus(
                            code,
                            "date,close",
                            start_date=yesterday,
                            end_date=yesterday
                        )
                        if rs.error_code == '0' and rs.next():
                            prev_data = rs.get_row_data()
                            if prev_data and prev_data[1]:
                                prev_close = float(prev_data[1])
                                if prev_close > 0:
                                    change = round(((new_price - prev_close) / prev_close) * 100, 2)
                                    print(f"重新计算{code}涨跌幅: {change}%")
                    except Exception as e:
                        print(f"计算{code}涨跌幅失败: {e}")
                
                if change == 0 and old_change != 0 and abs(new_price - old_price) < 0.001:
                    # 如果价格没有明显变化，且原涨跌幅不为0，保留原有涨跌幅
                    change = old_change
                    print(f"价格未变化，保留原涨跌幅: {code} 价格: {new_price}, 涨跌幅: {change}%")
                elif change == 0 and old_change != 0:
                    # 如果仍然无法计算涨跌幅，但原来有值，保留原有涨跌幅
                    change = old_change
                    print(f"无法计算新涨跌幅，保留原涨跌幅: {code} 价格: {new_price}, 涨跌幅: {change}%")
                
                # 更新价格和涨跌幅
                updated_stocks[code] = {
                    "name": info.get("name", ""),
                    "price": new_price,
                    "change": change
                }
                
                # 更新数据库
                db.update_stock(code, updated_stocks[code])
            else:
                # 如果没有获取到实时数据，保持原价格和涨跌幅
                updated_stocks[code] = info
        
        return updated_stocks
    
    def get_index_data(self, index_code="sh.000001", days=7):
        """
        获取指数数据用于绘制图表
        :param index_code: 指数代码，默认为上证指数
        :param days: 获取天数
        :return: 指数数据
        """
        # 首先获取数据库中的价格
        stock_info = db.get_stock(index_code)
        current_price = stock_info.get("price", 0) if stock_info else 0
        
        # 获取历史数据
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        df = self.get_stock_data(index_code, start_date, end_date)
        
        # 如果获取到了历史数据，并且数据库中的价格与历史数据最后一条价格差异较大
        # 则更新最后一条数据的收盘价为数据库中的价格，确保图表与列表显示一致
        if not df.empty and current_price > 0:
            # 检查最后一条数据的收盘价与数据库价格的差异
            last_close = df['close'].iloc[-1]
            if abs((last_close - current_price) / current_price) > 0.01:  # 差异超过1%
                print(f"调整 {index_code} 图表数据: 历史收盘价 {last_close} -> 数据库价格 {current_price}")
                # 将最后一条数据的收盘价调整为数据库中的价格
                df.loc[df.index[-1], 'close'] = current_price
        
        return df

# 创建股票数据管理器实例
stock_manager = StockDataManager() 