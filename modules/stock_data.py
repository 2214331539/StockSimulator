import pandas as pd
import random
import time
import requests
from datetime import datetime, timedelta
from .database import db
import akshare as ak

class StockDataManager:
    """股票数据管理类，用于获取和更新股票数据"""
    
    def __init__(self):
        """初始化股票数据管理器"""
        # self.logged_in = False  # AKShare 通常不需要登录状态
        # self.login() # AKShare 通常不需要显式登录
        # 初始化时同步一次数据库中的股票价格
        self.hourly_period_minutes = 60 # 新增：初始化每小时图表的分钟数周期
        self.sync_stock_prices()
    
    # def login(self): # AKShare 通常不需要显式登录
    #     """登录BaoStock"""
    #     try:
    #         lg = bs.login()
    #         if lg.error_code == '0':
    #             self.logged_in = True
    #             print("BaoStock登录成功")
    #         else:
    #             print(f"BaoStock登录失败: {lg.error_msg}")
    #     except Exception as e:
    #         print(f"BaoStock登录异常: {e}")
    
    # def logout(self): # AKShare 通常不需要显式登录
    #     """登出BaoStock"""
    #     if self.logged_in:
    #         bs.logout()
    #         self.logged_in = False
    
    def sync_stock_prices(self):
        """使用 AKShare 同步数据库中的股票价格至最近的交易日收盘价，并计算涨跌幅"""
        print("AKShare: 正在同步数据库股票价格至最新收盘价...")
        all_db_stocks = db.get_stocks()
        if not all_db_stocks:
            print("AKShare: 数据库中没有股票数据可供同步")
            return

        # 获取今天和几天前的日期，用于查询历史数据
        today_dt = datetime.now()
        # 查询过去 N 天的数据，以确保能获取到最近的两个交易日用于计算涨跌幅
        # 如果今天是周一，只获取一天可能不够，需要往前找
        start_date_hist_dt = today_dt - timedelta(days=10) 
        today_str = today_dt.strftime("%Y-%m-%d")
        start_date_hist_str = start_date_hist_dt.strftime("%Y-%m-%d")

        for bs_code, db_stock_info in all_db_stocks.items():
            print(f"AKShare: 开始同步 {bs_code}...")
            try:
                # 使用 get_stock_data 获取最近的历史数据
                # adjustflag="2" (hfq, 后复权) 通常用于计算准确的连续价格变化
                # adjustflag="3" (不复权) 用于获取原始收盘价
                # 这里我们用不复权价格来获取特定日期的收盘价
                hist_df = self.get_stock_data(code=bs_code, 
                                              start_date=start_date_hist_str, 
                                              end_date=today_str,
                                              frequency="d",
                                              adjustflag="3")

                if hist_df is not None and not hist_df.empty and len(hist_df) >= 1:
                    # 获取最新的有效交易日数据作为 new_price
                    latest_trade_day_data = hist_df.iloc[-1]
                    new_price = float(latest_trade_day_data['close'])
                    new_price_date = latest_trade_day_data['date']
                    calculated_change = 0.0

                    # 如果有至少两个交易日的数据，计算涨跌幅
                    if len(hist_df) >= 2:
                        prev_trade_day_data = hist_df.iloc[-2]
                        prev_close = float(prev_trade_day_data['close'])
                        if prev_close > 0:
                            calculated_change = round(((new_price - prev_close) / prev_close) * 100, 2)
                        print(f"AKShare: {bs_code} - 最新收盘价: {new_price} ({new_price_date}), 前一收盘价: {prev_close}, 计算涨跌幅: {calculated_change}%")
                    else:
                        # 只有一个交易日的数据，无法计算涨跌幅，尝试使用数据库旧值或设为0
                        calculated_change = db_stock_info.get("change", 0.0)
                        print(f"AKShare: {bs_code} - 仅有1条历史数据，最新收盘价: {new_price} ({new_price_date}), 使用旧涨跌幅: {calculated_change}%")

                    stock_to_save = {
                        "name": db_stock_info.get("name", ""),
                        "price": new_price,
                        "change": calculated_change
                    }
                    db.update_stock(bs_code, stock_to_save)
                    print(f"AKShare: 已同步 {bs_code} 至数据库 - 价格: {new_price}, 涨跌幅: {calculated_change}%")
                else:
                    print(f"AKShare: 未能获取 {bs_code} 的有效历史数据进行同步，保留数据库原值。")
            except Exception as e:
                print(f"AKShare: 同步 {bs_code} 价格失败: {e}")
                import traceback
                traceback.print_exc()
        
        print("AKShare: 数据库股票价格同步完成 (基于最新收盘价)")
    
    def get_stock_hourly_data(self, code, lookback_hours=24):
        """
        获取股票或指数最近N个小时的60分钟线数据 (使用 AKShare)
        :param code: 股票或指数代码，如"sh.600000" 或 "sh.000001"
        :param lookback_hours: 希望回溯的小时数，将转换为数据点数量 (1小时1个点)
        :return: DataFrame格式的股票数据
        """
        original_code_str = str(code) 
        api_symbol_numeric = self._convert_bs_to_ak_code(original_code_str) 
        
        # 使用完整的代码（带前缀）来判断是否为我们关心的指数
        # 例如: 上证指数 "sh.000001", 深证成指 "sz.399001", 沪深300 "sh.000300", 创业板指 "sz.399006"
        known_full_index_codes = []
        is_index = original_code_str in known_full_index_codes

        end_date_dt = datetime.now()
        ak_end_date_str = end_date_dt.strftime('%Y-%m-%d %H:%M:%S')
        ak_start_date_str = (end_date_dt - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')

        df = None
        api_attempted_symbol = ""
        try:
            if is_index:
                api_attempted_symbol = original_code_str.replace('.', '')
                print(f"AKShare (Index): 获取 {api_attempted_symbol} ({original_code_str}) 60分钟线数据, 从 {ak_start_date_str} 到 {ak_end_date_str}")
                df = ak.index_zh_a_hist_min_em(symbol=api_attempted_symbol,
                                                start_date=ak_start_date_str, 
                                                end_date=ak_end_date_str, 
                                                period='60')
            else:
                api_attempted_symbol = api_symbol_numeric
                print(f"AKShare (Stock): 获取 {api_attempted_symbol} ({original_code_str}) 60分钟线数据, 从 {ak_start_date_str} 到 {ak_end_date_str}")
                df = ak.stock_zh_a_hist_min_em(symbol=api_attempted_symbol,
                                                start_date=ak_start_date_str, 
                                                end_date=ak_end_date_str, 
                                                period='60', 
                                                adjust='qfq')
            
            if df is None or df.empty:
                data_type = "指数" if is_index else "股票"
                print(f"AKShare: 未获取到{data_type} {original_code_str} 的60分钟线数据 ({api_attempted_symbol})，或返回为空/None。")
                return pd.DataFrame()

            rename_map = {
                "时间": "date", 
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount"
            }
            df.rename(columns=rename_map, inplace=True)

            if 'date' not in df.columns:
                print(f"AKShare: 60分钟数据缺少 '时间' ('date') 列 for {original_code_str} ({api_attempted_symbol})")
                return pd.DataFrame()
            df['date'] = pd.to_datetime(df['date'])
            
            required_plot_cols = ['date', 'open', 'high', 'low', 'close'] 
            if not all(col in df.columns for col in required_plot_cols):
                missing_cols = [col for col in required_plot_cols if col not in df.columns]
                print(f"错误: {original_code_str} ({api_attempted_symbol}) 的60分钟K线数据缺少绘图必要列: {missing_cols}。拥有列: {df.columns}")
                return pd.DataFrame()

            df.sort_values(by='date', inplace=True)

            if len(df) >= lookback_hours:
                df_filtered = df.tail(lookback_hours).copy()
            else:
                df_filtered = df.copy()
                print(f"AKShare: {original_code_str} ({api_attempted_symbol}) 60分钟数据不足 {lookback_hours} 条，返回实际获取的 {len(df_filtered)} 条")
            
            df_filtered.loc[:, 'code'] = original_code_str 

            final_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount']
            existing_final_columns = [col for col in final_columns if col in df_filtered.columns]
            df_to_return = df_filtered[existing_final_columns]

            print(f"AKShare: 成功获取并处理了 {original_code_str} 的 {len(df_to_return)} 条60分钟线数据")
            return df_to_return

        except Exception as e:
            data_type = "指数" if is_index else "股票"
            print(f"AKShare: 获取{data_type}60分钟线数据 {original_code_str} ({api_attempted_symbol}) 异常: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()

    def _convert_bs_to_ak_code(self, bs_code):
        """将BaoStock的股票代码 (如 sh.600000) 转换为AKShare的6位代码 (如 600000)"""
        if isinstance(bs_code, str) and '.' in bs_code:
            return bs_code.split('.')[1]
        return bs_code # 如果格式不符合预期，返回原值

    def _convert_ak_to_bs_code(self, ak_code, original_bs_code_prefix=None):
        """将AKShare的6位代码转换为BaoStock的股票代码，需要原始前缀辅助判断市场"""
        if len(ak_code) == 6 and ak_code.isdigit():
            if original_bs_code_prefix:
                 return f"{original_bs_code_prefix}.{ak_code}"
            # 如果没有前缀，尝试根据代码首位判断 (不完全可靠，但作为备选)
            if ak_code.startswith('6'): # 通常是沪市
                return f"sh.{ak_code}"
            elif ak_code.startswith('0') or ak_code.startswith('3'): # 通常是深市
                return f"sz.{ak_code}"
        return ak_code # 格式不对或无法判断则返回原值

    def get_stock_data(self, code, start_date=None, end_date=None, frequency="d", adjustflag="3"):
        """
        获取股票历史数据 (使用 AKShare)
        :param code: 股票代码，如"sh.600000"
        :param start_date: 开始日期，格式YYYY-MM-DD，默认为30天前
        :param end_date: 结束日期，格式YYYY-MM-DD，默认为今天
        :param frequency: 数据频率，d=日k线，w=周k线，m=月k线，默认为d
        :param adjustflag: 复权类型，1=前复权，2=后复权，3=不复权，默认为3
        :return: DataFrame格式的股票数据
        """
        ak_code = self._convert_bs_to_ak_code(code)
        original_bs_prefix = code.split('.')[0] if '.' in code else None

        # 设置默认日期
        if not end_date:
            end_date_dt = datetime.now()
            end_date = end_date_dt.strftime("%Y-%m-%d")
        else:
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        if not start_date:
            start_date_dt = datetime.now() - timedelta(days=30)
            start_date = start_date_dt.strftime("%Y-%m-%d")
        else:
            start_date_dt = datetime.strptime(start_date, "%Y-%m-%d")

        # AKShare 日期格式 YYYYMMDD
        ak_start_date = start_date_dt.strftime("%Y%m%d")
        ak_end_date = end_date_dt.strftime("%Y%m%d")

        # 转换 frequency
        ak_period_map = {"d": "daily", "w": "weekly", "m": "monthly"}
        ak_period = ak_period_map.get(frequency, "daily")

        # 转换 adjustflag
        ak_adjust_map = {"1": "qfq", "2": "hfq", "3": ""}
        ak_adjust = ak_adjust_map.get(str(adjustflag), "")

        try:
            print(f"AKShare: 获取 {ak_code} 从 {ak_start_date} 到 {ak_end_date}, period: {ak_period}, adjust: {ak_adjust}")
            df = ak.stock_zh_a_hist(symbol=ak_code,
                                     period=ak_period,
                                     start_date=ak_start_date,
                                     end_date=ak_end_date,
                                     adjust=ak_adjust)
            
            if df.empty:
                print(f"AKShare: 未获取到股票 {ak_code} 的数据")
                return pd.DataFrame()

            # 重命名列以匹配之前的格式 (baostock)
            # AKShare 列名: 日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
            rename_map = {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                # "涨跌幅": "pctChange", # baostock 没有直接的涨跌幅，通常是计算得到
                # "换手率": "turnoverRatio"
            }
            df.rename(columns=rename_map, inplace=True)

            # 添加原始的 'code' 和 'adjustflag' 列，保持与baostock输出的兼容性
            df['code'] = self._convert_ak_to_bs_code(ak_code, original_bs_prefix) 
            df['adjustflag'] = adjustflag 

            # 筛选我们需要的列，并确保数据类型正确
            required_columns = ['date', 'code', 'open', 'high', 'low', 'close', 'volume', 'amount', 'adjustflag']
            # 有些数据可能不存在，例如刚上市的股票可能没有成交额
            existing_required_columns = [col for col in required_columns if col in df.columns]
            df = df[existing_required_columns]

            for field in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                if field in df.columns:
                    df[field] = pd.to_numeric(df[field], errors='coerce')
            
            # 将 'date' 列转换为 YYYY-MM-DD 格式
            if 'date' in df.columns:
                 df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

            print(f"AKShare: 成功获取并处理了 {code} 的数据, 共 {len(df)} 条")
            return df

        except Exception as e:
            print(f"AKShare: 获取股票数据 {code} ({ak_code}) 异常: {e}")
            # 打印更详细的错误信息，比如AKShare可能的网络错误或API限制
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    # def get_stock_basic_info(self, code):
    #     """
    #     获取股票基本信息 (此方法暂时停用，可由AKShare其他函数替代)
    #     :param code: 股票代码，如"sh.600000"
    #     :return: 股票基本信息
    #     """
    #     # if not self.logged_in: # AKShare不需要登录状态
    #     #     self.login()
    #     #     if not self.logged_in:
    #     #         return None
    #     
    #     # try:
    #     #     # AKShare 对应功能可使用如 ak.stock_individual_info_em(symbol=self._convert_bs_to_ak_code(code))
    #     #     # rs = bs.query_stock_basic(code=code) # 原baostock调用
    #     #     # if rs.error_code == '0' and rs.next():
    #     #     #     return rs.get_row_data()
    #     #     # else:
    #     #     #     print(f"未获取到股票 {code} 的基本信息")
    #     #     #     return None
    #     #     print(f"get_stock_basic_info for {code} is currently disabled and needs AKShare equivalent.")
    #     #     return None 
    #     # except Exception as e:
    #     #     print(f"获取股票基本信息异常: {e}")
    #     #     return None
    
    def get_realtime_quotes(self, codes):
        """
        获取实时行情数据 (使用 AKShare)
        :param codes: 股票代码列表，如["sh.600000", "sh.601398"]
        :return: 实时行情数据字典
        """
        results = {}
        ak_all_spot_df = None
        try:
            # 尝试获取所有A股的实时行情数据
            ak_all_spot_df = ak.stock_zh_a_spot_em()
            # 将代码列设置为索引以便快速查找
            if ak_all_spot_df is not None and not ak_all_spot_df.empty and '代码' in ak_all_spot_df.columns:
                ak_all_spot_df.set_index('代码', inplace=True)
            else:
                print("AKShare: stock_zh_a_spot_em 未返回有效数据或缺少'代码'列")
                ak_all_spot_df = None # 确保后续不会使用无效的DataFrame
        except Exception as e:
            print(f"AKShare:调用 stock_zh_a_spot_em 获取所有股票实时行情失败: {e}")
            ak_all_spot_df = None

        for bs_code in codes:
            price = None
            change = 0.0 # 初始化为浮点数
            ak_code = self._convert_bs_to_ak_code(bs_code)

            # 方法1: 从 ak.stock_zh_a_spot_em() 的结果中查找
            if ak_all_spot_df is not None and ak_code in ak_all_spot_df.index:
                try:
                    stock_data = ak_all_spot_df.loc[ak_code]
                    price = stock_data.get('最新价', None)
                    change_pct = stock_data.get('涨跌幅', 0.0) # 直接获取百分比
                    
                    if price is not None:
                        price = float(price)
                        change = float(change_pct) # AKShare直接提供涨跌幅百分比
                        print(f"AKShare: 从stock_zh_a_spot_em获取到 {bs_code}({ak_code}) - 价格: {price}, 涨跌幅: {change}%")
                    else:
                        print(f"AKShare: stock_zh_a_spot_em 中 {ak_code} 的'最新价'为空")

                except Exception as e:
                    print(f"AKShare: 处理 stock_zh_a_spot_em 数据时出错 ({bs_code}): {e}")
            
            # 方法2: 如果AKShare实时行情获取失败或未找到该股票，尝试从历史数据获取最近价格
            # 注意：这通常不是"实时"的，但作为备用
            if price is None:
                print(f"AKShare: 无法从实时行情获取 {bs_code}, 尝试从历史数据获取最新收盘价")
                try:
                    # 获取最近一个交易日的数据
                    end_date_dt = datetime.now()
                    start_date_dt = end_date_dt - timedelta(days=5) # 查询最近5天的数据，确保能拿到一个交易日
                    
                    df_hist = self.get_stock_data(code=bs_code, 
                                                  start_date=start_date_dt.strftime("%Y-%m-%d"), 
                                                  end_date=end_date_dt.strftime("%Y-%m-%d"),
                                                  frequency="d",
                                                  adjustflag="3") # 通常用不复权看收盘价
                    
                    if not df_hist.empty:
                        latest_record = df_hist.iloc[-1]
                        price = float(latest_record['close'])
                        # 计算涨跌幅 (相对于前一个交易日)
                        if len(df_hist) > 1:
                            prev_close = float(df_hist.iloc[-2]['close'])
                            if prev_close > 0:
                                change = round(((price - prev_close) / prev_close) * 100, 2)
                        print(f"AKShare: 从历史数据获取到 {bs_code} - 价格: {price}, 计算涨跌幅: {change}%")
                    else:
                        print(f"AKShare: 历史数据也未找到 {bs_code}")
                except Exception as e:
                    print(f"AKShare: 从历史数据获取 {bs_code} 价格失败: {e}")

            # 方法3: 如果以上都失败，获取数据库中的价格和涨跌幅
            if price is None:
                stock_info_db = db.get_stock(bs_code)
                if stock_info_db:
                    price = stock_info_db.get("price")
                    change = stock_info_db.get("change", 0.0)
                    if price is not None:
                        print(f"AKShare: 使用数据库价格为 {bs_code} - 价格: {price}, 涨跌幅: {change}%")
                    else:
                         print(f"AKShare: 数据库中 {bs_code} 价格也为空")
                else:
                    print(f"AKShare: 数据库中未找到 {bs_code}")
            
            if price is not None:
                results[bs_code] = {
                    "price": float(price),
                    "change": float(change),
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                print(f"AKShare: 最终未能获取到 {bs_code} 的任何价格信息")

        return results
    
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
        """使用 AKShare 获取实时股票数据更新价格"""
        stocks = db.get_stocks()
        
        if not stocks:
            print("数据库中没有股票数据可供更新")
            return {}
        
        codes_to_update = list(stocks.keys())
        
        # 获取实时行情 (已经包含了备用逻辑)
        realtime_data = self.get_realtime_quotes(codes_to_update)
        
        updated_stocks_info = {}
        
        for code, current_db_info in stocks.items():
            if code in realtime_data:
                live_info = realtime_data[code]
                new_price = live_info.get("price")
                new_change = live_info.get("change") # AKShare 应该直接提供正确的涨跌幅

                if new_price is not None and new_change is not None:
                    stock_data_to_save = {
                        "name": current_db_info.get("name", ""), # 保留现有名称
                        "price": float(new_price),
                        "change": float(new_change)
                    }
                    db.update_stock(code, stock_data_to_save)
                    updated_stocks_info[code] = stock_data_to_save
                    print(f"AKShare: 更新数据库 {code} - 价格: {new_price}, 涨跌幅: {new_change}%")
                else:
                    # 未能从get_realtime_quotes获取有效价格或涨跌幅，保留数据库原样
                    updated_stocks_info[code] = current_db_info
                    print(f"AKShare: 未能获取 {code} 的有效实时数据，保留数据库原值")
            else:
                # get_realtime_quotes 未返回该股票信息，保留数据库原样
                updated_stocks_info[code] = current_db_info
                print(f"AKShare: get_realtime_quotes 未返回 {code} 的信息，保留数据库原值")
        
        return updated_stocks_info
    
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