import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, scrolledtext
import threading
import webbrowser

# 设置控制台输出编码
sys.stdout.reconfigure(encoding='utf-8')

class StockNewsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("股票新闻爬取与展示")
        self.root.geometry("900x600")
        self.root.resizable(True, True)
        
        # 设置样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", background="#4CAF50", foreground="black", font=("微软雅黑", 10))
        self.style.configure("TLabel", background="#f0f0f0", font=("微软雅黑", 10))
        self.style.configure("Header.TLabel", font=("微软雅黑", 12, "bold"))
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建控制面板
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=10)
        
        # 创建爬取按钮
        self.fetch_btn = ttk.Button(self.control_frame, text="爬取新闻", command=self.fetch_news_thread)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建状态标签
        self.status_label = ttk.Label(self.control_frame, text="状态: 准备就绪")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # 创建进度条
        self.progress = ttk.Progressbar(self.control_frame, orient=tk.HORIZONTAL, length=200, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, padx=5)
        
        # 创建新闻列表框架
        self.news_frame = ttk.Frame(self.main_frame)
        self.news_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建新闻列表
        self.columns = ('标题', '时间', '链接')
        self.news_tree = ttk.Treeview(self.news_frame, columns=self.columns, show='headings')
        
        # 设置列标题
        for col in self.columns:
            self.news_tree.heading(col, text=col)
            
        # 设置列宽
        self.news_tree.column('标题', width=400, anchor='w')
        self.news_tree.column('时间', width=150, anchor='center')
        self.news_tree.column('链接', width=300, anchor='w')
        
        # 添加滚动条
        self.scrollbar_y = ttk.Scrollbar(self.news_frame, orient=tk.VERTICAL, command=self.news_tree.yview)
        self.news_tree.configure(yscrollcommand=self.scrollbar_y.set)
        
        self.scrollbar_x = ttk.Scrollbar(self.news_frame, orient=tk.HORIZONTAL, command=self.news_tree.xview)
        self.news_tree.configure(xscrollcommand=self.scrollbar_x.set)
        
        # 布局
        self.news_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 绑定双击事件
        self.news_tree.bind("<Double-1>", self.show_news_content)
        
        # 创建新闻内容框架
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建新闻内容标题
        self.content_title = ttk.Label(self.content_frame, text="新闻内容", style="Header.TLabel")
        self.content_title.pack(anchor='w', pady=5)
        
        # 创建新闻内容文本框
        self.content_text = scrolledtext.ScrolledText(self.content_frame, wrap=tk.WORD, height=10)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        
        # 存储新闻数据
        self.news_data = []
        
    def fetch_news_thread(self):
        """在单独的线程中爬取新闻，避免界面卡顿"""
        self.fetch_btn.config(state=tk.DISABLED)
        self.status_label.config(text="状态: 正在爬取...")
        self.progress.start()
        
        # 创建并启动线程
        thread = threading.Thread(target=self.fetch_news)
        thread.daemon = True
        thread.start()
    
    def fetch_news(self):
        """爬取新闻的主函数"""
        try:
            # 清空现有数据
            for item in self.news_tree.get_children():
                self.news_tree.delete(item)
            
            self.news_data = []
            
            # 获取新闻
            news_list = self.get_stock_news()
            
            # 检查是否获取到数据
            if not news_list:
                self.update_status("未获取到任何新闻数据，请检查网络连接或网页结构")
                return
            
            # 过滤掉标题太短的项目（可能是广告或导航）
            filtered_news = [news for news in news_list if len(news['标题']) > 5]
            
            # 存储新闻数据
            self.news_data = filtered_news
            
            # 更新界面
            for i, news in enumerate(filtered_news):
                self.news_tree.insert('', tk.END, values=(news['标题'], news['时间'], news['链接']))
            
            self.update_status(f"成功获取 {len(filtered_news)} 条新闻")
            
        except Exception as e:
            self.update_status(f"爬取过程中出错: {str(e)}")
        finally:
            # 恢复界面状态
            self.root.after(0, self.stop_progress)
    
    def update_status(self, message):
        """更新状态信息（线程安全）"""
        self.root.after(0, lambda: self.status_label.config(text=f"状态: {message}"))
    
    def stop_progress(self):
        """停止进度条并恢复按钮状态"""
        self.progress.stop()
        self.fetch_btn.config(state=tk.NORMAL)
    
    def show_news_content(self, event):
        """显示选中新闻的内容"""
        selected_item = self.news_tree.selection()[0]
        if not selected_item:
            return
        
        # 获取选中的新闻
        values = self.news_tree.item(selected_item, 'values')
        if not values or len(values) < 3:
            return
        
        title, _, url = values
        
        # 更新内容标题
        self.content_title.config(text=title)
        
        # 清空内容
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, "正在加载新闻内容，请稍候...\n")
        
        # 在新线程中获取内容
        thread = threading.Thread(target=self.fetch_content, args=(url, title))
        thread.daemon = True
        thread.start()
    
    def fetch_content(self, url, title):
        """获取新闻内容"""
        try:
            content = self.get_news_content(url)
            
            # 更新内容（线程安全）
            self.root.after(0, lambda: self.update_content(title, content, url))
        except Exception as e:
            self.root.after(0, lambda: self.content_text.insert(tk.END, f"获取内容出错: {str(e)}"))
    
    def update_content(self, title, content, url):
        """更新新闻内容"""
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(tk.END, f"标题: {title}\n\n")
        self.content_text.insert(tk.END, f"内容: \n{content}\n\n")
        self.content_text.insert(tk.END, f"原文链接: {url}\n")
        
        # 添加可点击的链接
        self.content_text.insert(tk.END, "点击打开原文网页")
        self.content_text.tag_add("link", "end-19c", "end")
        self.content_text.tag_config("link", foreground="blue", underline=1)
        self.content_text.tag_bind("link", "<Button-1>", lambda e: webbrowser.open(url))
    
    def get_stock_news(self):
        """
        爬取新浪财经股票新闻
        :return: 新闻列表
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 使用新浪财经的股票新闻页面
        url = "https://finance.sina.com.cn/stock/"
        
        try:
            self.update_status("正在请求网页...")
            response = requests.get(url, headers=headers)
            response.encoding = 'utf-8'  # 确保使用UTF-8编码
            
            if response.status_code != 200:
                self.update_status(f"请求失败: {response.status_code}")
                return []
            
            self.update_status("正在解析网页...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种可能的选择器
            news_items = []
            selectors = [
                'ul.list01 li',  # 新浪财经常用的新闻列表选择器
                '.news-list li',
                '.main-content .news-item',
                '.box-list li',
                'div.zq_content li'  # 股票区域的内容
            ]
            
            for selector in selectors:
                items = soup.select(selector)
                if items:
                    self.update_status(f"找到匹配的元素: {len(items)} 个")
                    news_items = items
                    break
            
            if not news_items:
                # 如果上面的选择器都没找到，尝试获取所有链接
                self.update_status("尝试获取所有新闻链接...")
                all_links = soup.select('a')
                # 过滤掉非新闻链接
                news_items = [link for link in all_links if 'news' in link.get('href', '') or 'finance' in link.get('href', '')]
                self.update_status(f"找到可能的新闻链接: {len(news_items)} 个")
            
            results = []
            
            for item in news_items:
                try:
                    # 如果是li元素，查找其中的a标签
                    if item.name == 'li':
                        link = item.select_one('a')
                    else:
                        link = item  # 如果直接是a标签
                    
                    if link and link.has_attr('href'):
                        title = link.text.strip()
                        url = link['href']
                        
                        # 过滤掉空标题或非http开头的链接
                        if title and (url.startswith('http') or url.startswith('/')):
                            # 处理相对URL
                            if url.startswith('/'):
                                url = 'https://finance.sina.com.cn' + url
                            
                            # 新浪财经页面可能没有明确的时间，使用当前时间
                            current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                            
                            news = {
                                '标题': title,
                                '链接': url,
                                '时间': current_time
                            }
                            results.append(news)
                except Exception as e:
                    print(f"解析新闻项时出错: {str(e)}")
                    continue
            
            return results
        except Exception as e:
            self.update_status(f"请求页面出错: {str(e)}")
            return []

    def get_news_content(self, url):
        """
        获取新闻内容
        :param url: 新闻链接
        :return: 新闻内容
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'  # 确保使用UTF-8编码
            
            if response.status_code != 200:
                return "获取内容失败"
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试多种可能的内容选择器
            content_selectors = [
                'div.article-content', 'div#artibody', 'div.article', 'div.content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # 移除脚本和样式
                    for script in content_div.find_all(['script', 'style']):
                        script.decompose()
                    
                    # 获取文本
                    content = content_div.get_text(strip=True)
                    if content:
                        break
            
            return content if content else "未找到内容"
        except Exception as e:
            return f"获取内容出错: {str(e)}"

# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = StockNewsApp(root)
    root.mainloop()
