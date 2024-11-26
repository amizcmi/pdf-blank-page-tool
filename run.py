import webview
import sys
import os
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from app import app
import subprocess
import threading
import time
import requests

def get_port():
    """获取可用端口"""
    import socket
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

def resource_path(relative_path):
    """获取资源文件的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def wait_for_server(url, timeout=30):
    """等待服务器启动"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return True
        except:
            time.sleep(0.5)
    return False

def run_flask(port):
    """运行Flask应用"""
    try:
        # 设置端口号为全局变量，供app.py使用
        app.config['SERVER_PORT'] = port
        # 监听所有网络接口，而不是只监听localhost
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        messagebox.showerror("错误", f"服务启动失败：{str(e)}")

def open_browser(url):
    """打开默认浏览器"""
    try:
        # 等待一秒确保服务器完全启动
        time.sleep(1)
        webbrowser.open(url)
    except Exception as e:
        messagebox.showerror("错误", f"无法打开浏览器：{str(e)}")

# 获取本机IP地址
def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 不需要真正连接
        s.connect(('8.8.8.8', 1))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip

if __name__ == '__main__':
    try:
        # 设置模板文件夹路径
        app.template_folder = resource_path('templates')
        
        # 获取随机端口
        port = get_port()
        
        # 获取本机IP
        local_ip = get_local_ip()
        
        # 构建URL
        local_url = f'http://{local_ip}:{port}'
        localhost_url = f'http://localhost:{port}'
        
        # 创建并启动服务器线程
        server_thread = threading.Thread(target=lambda: run_flask(port))
        server_thread.daemon = True
        server_thread.start()
        
        # 等待服务器启动
        print(f"正在启动服务器...")
        print(f"本机访问地址: {localhost_url}")
        print(f"局域网访问地址: {local_url}")
        
        if wait_for_server(localhost_url):
            print("服务器启动成功，正在打开浏览器...")
            open_browser(localhost_url)
            
            # 显示访问地址
            messagebox.showinfo("服务已启动", 
                f"电脑访问地址：{localhost_url}\n" +
                f"手机访问地址：{local_url}\n\n" +
                "请确保手机和电脑在同一个局域网内")
            
            # 保持程序运行
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("程序正在关闭...")
        else:
            messagebox.showerror("错误", "服务器启动超时，请重试")
            sys.exit(1)
            
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败：{str(e)}")
        sys.exit(1) 