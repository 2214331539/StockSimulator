import tkinter as tk
import ttkbootstrap as tb
from ttkbootstrap import Style
import re
from .database import db

class LoginFrame(tb.Frame):
    """登录框架"""
    
    def __init__(self, parent, callback=None):
        super().__init__(parent, bootstyle="dark")
        
        self.callback = callback  # 登录成功后的回调函数
        
        # 创建登录框架
        content_frame = tb.Frame(self, bootstyle="dark")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建欢迎标题
        welcome_label = tb.Label(content_frame, text="股票模拟交易系统", font=("微软雅黑", 20, "bold"), bootstyle="inverse-dark")
        welcome_label.pack(pady=(50, 30))
        
        # 创建表单框架
        form_frame = tb.Frame(content_frame, bootstyle="dark")
        form_frame.pack(pady=20)
        
        # 用户名
        username_label = tb.Label(form_frame, text="用户名:", font=("微软雅黑", 12), bootstyle="light")
        username_label.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        
        self.username_var = tk.StringVar()
        username_entry = tb.Entry(form_frame, textvariable=self.username_var, width=25, font=("微软雅黑", 12))
        username_entry.grid(row=0, column=1, padx=10, pady=10)
        username_entry.focus()
        
        # 密码
        password_label = tb.Label(form_frame, text="密码:", font=("微软雅黑", 12), bootstyle="light")
        password_label.grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.password_var = tk.StringVar()
        password_entry = tb.Entry(form_frame, textvariable=self.password_var, width=25, font=("微软雅黑", 12), show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 登录和注册按钮框架
        button_frame = tb.Frame(form_frame, bootstyle="dark")
        button_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        # 登录按钮
        login_button = tb.Button(button_frame, text="登录", command=self.login, width=15, bootstyle="success")
        login_button.pack(side=tk.LEFT, padx=10)
        
        # 注册按钮
        register_button = tb.Button(button_frame, text="注册", command=self.show_register, width=15, bootstyle="secondary")
        register_button.pack(side=tk.LEFT, padx=10)
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_label = tb.Label(content_frame, textvariable=self.status_var, bootstyle="warning")
        self.status_label.pack(pady=10)
        
        # 初始化注册框架
        self.register_frame = None
    
    def login(self):
        """处理登录逻辑"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            self.status_var.set("用户名和密码不能为空")
            return
        
        # 验证用户
        user = db.validate_user(username, password)
        if user:
            if self.callback:
                self.callback(user)  # 调用回调函数，传递用户信息
        else:
            self.status_var.set("用户名或密码错误")
    
    def show_register(self):
        """显示注册界面"""
        if self.register_frame:
            self.register_frame.destroy()
        
        self.register_frame = RegisterFrame(self, self.register_callback)
        self.register_frame.place(relx=0.5, rely=0.5, anchor="center")
    
    def register_callback(self, success, message):
        """注册回调函数"""
        if success:
            if self.register_frame:
                self.register_frame.destroy()
                self.register_frame = None
            self.status_var.set(message)
        else:
            # 在注册框架中显示错误消息
            if self.register_frame:
                self.register_frame.show_error(message)

class RegisterFrame(tb.Frame):
    """注册框架"""
    
    def __init__(self, parent, callback=None):
        super().__init__(parent, bootstyle="dark")
        
        self.callback = callback
        
        # 创建内容框架
        content_frame = tb.LabelFrame(self, text="新用户注册", bootstyle="info")
        content_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # 用户名
        username_label = tb.Label(content_frame, text="用户名:", bootstyle="light")
        username_label.grid(row=0, column=0, sticky="e", padx=10, pady=10)
        
        self.username_var = tk.StringVar()
        username_entry = tb.Entry(content_frame, textvariable=self.username_var, width=20)
        username_entry.grid(row=0, column=1, padx=10, pady=10)
        username_entry.focus()
        
        # 密码
        password_label = tb.Label(content_frame, text="密码:", bootstyle="light")
        password_label.grid(row=1, column=0, sticky="e", padx=10, pady=10)
        
        self.password_var = tk.StringVar()
        password_entry = tb.Entry(content_frame, textvariable=self.password_var, width=20, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 确认密码
        confirm_label = tb.Label(content_frame, text="确认密码:", bootstyle="light")
        confirm_label.grid(row=2, column=0, sticky="e", padx=10, pady=10)
        
        self.confirm_var = tk.StringVar()
        confirm_entry = tb.Entry(content_frame, textvariable=self.confirm_var, width=20, show="*")
        confirm_entry.grid(row=2, column=1, padx=10, pady=10)
        
        # 用户类型
        type_label = tb.Label(content_frame, text="用户类型:", bootstyle="light")
        type_label.grid(row=3, column=0, sticky="e", padx=10, pady=10)
        
        self.type_var = tk.StringVar(value="普通用户")
        type_combobox = tb.Combobox(content_frame, textvariable=self.type_var, width=17, values=["普通用户", "管理员"], state="readonly")
        type_combobox.grid(row=3, column=1, padx=10, pady=10)
        
        # 按钮框架
        button_frame = tb.Frame(content_frame, bootstyle="dark")
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        # 注册按钮
        register_button = tb.Button(button_frame, text="注册", command=self.register, bootstyle="success")
        register_button.pack(side=tk.LEFT, padx=10)
        
        # 取消按钮
        cancel_button = tb.Button(button_frame, text="取消", command=self.destroy, bootstyle="secondary")
        cancel_button.pack(side=tk.LEFT, padx=10)
        
        # 错误消息标签
        self.error_var = tk.StringVar()
        self.error_label = tb.Label(content_frame, textvariable=self.error_var, bootstyle="danger")
        self.error_label.grid(row=5, column=0, columnspan=2, pady=10)
    
    def register(self):
        """处理注册逻辑"""
        username = self.username_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()
        user_type = self.type_var.get()
        
        # 验证输入
        if not username or not password or not confirm:
            self.show_error("所有字段都必须填写")
            return
        
        if len(username) < 3:
            self.show_error("用户名至少需要3个字符")
            return
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            self.show_error("用户名只能包含字母、数字和下划线")
            return
        
        if len(password) < 6:
            self.show_error("密码至少需要6个字符")
            return
        
        if password != confirm:
            self.show_error("两次输入的密码不一致")
            return
        
        # 检查用户名是否已存在
        if db.user_exists(username):
            self.show_error(f"用户名 '{username}' 已被使用")
            return
        
        # 注册用户
        success = db.register_user(username, password, user_type)
        if success:
            if self.callback:
                self.callback(True, f"用户 '{username}' 注册成功，现在可以登录")
        else:
            self.show_error("注册失败，请稍后再试")
    
    def show_error(self, message):
        """显示错误消息"""
        self.error_var.set(message) 