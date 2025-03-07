import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import zipfile
import os
import subprocess
import time
import json
from datetime import datetime
import sys
import win32gui
import win32con
from tkinter import font
import ctypes

if sys.platform == 'win32':
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class LoadingSpinner(ttk.Label):
    def __init__(self, parent, size=30):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.canvas = tk.Canvas(self, width=size, height=size, bg='white', highlightthickness=0)
        self.canvas.pack()
        self.is_spinning = False
        self.draw_spinner()
    
    def draw_spinner(self):
        self.canvas.delete("spinner")
        x = self.size / 2
        y = self.size / 2
        r = self.size / 3
        start = self.angle
        extent = 300
        self.canvas.create_arc(x - r, y - r, x + r, y + r, 
                               start=start, extent=extent,
                               tags="spinner", outline='blue', width=4)
        
    def start(self):
        self.is_spinning = True
        self.spin()
        
    def stop(self):
        self.is_spinning = False
        
    def spin(self):
        if self.is_spinning:
            self.angle = (self.angle + 10) % 360
            self.draw_spinner()
            self.after(50, self.spin)

class MinecraftLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Minecraft 启动器")
        self.root.geometry("800x400")
        self.set_taskbar_icon()
        self.set_font()
        self.load_config()
        self.create_main_interface()

    def get_download_state_file(self):
        return "download_state.json"

    def save_download_state(self, downloaded_size, total_size, is_paused=False):
        state = {
            "file_url": "https://mcmods2333.flyqilai.top/0d00.zip",
            "downloaded_size": downloaded_size,
            "total_size": total_size,
            "timestamp": datetime.now().isoformat(),
            "is_paused": is_paused
        }
        try:
            with open(self.get_download_state_file(), 'w') as f:
                json.dump(state, f)
        except Exception as e:
            messagebox.showerror("错误", f"保存下载状态失败: {str(e)}")

    def load_download_state(self):
        try:
            if os.path.exists(self.get_download_state_file()):
                with open(self.get_download_state_file(), 'r') as f:
                    return json.load(f)
        except Exception as e:
            messagebox.showerror("错误", f"加载下载状态失败: {str(e)}")
        return None

    def clear_download_state(self):
        if os.path.exists(self.get_download_state_file()):
            os.remove(self.get_download_state_file())

    def set_taskbar_icon(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        
        icon_path = os.path.join(base_path, 'onimai.ico')
        
        try:
            self.root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error setting taskbar icon: {str(e)}")

    def set_font(self):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        
        font_path = os.path.join(base_path, 'font.otf')
        custom_font = font.Font(family=font_path, size=10)
        self.root.option_add('*Font', custom_font)

    def create_main_interface(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.create_buttons()
        
        self.news_frame = ttk.LabelFrame(self.main_frame, text="最新消息")
        self.news_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.news_scroll = ttk.Scrollbar(self.news_frame)
        self.news_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.news_text = tk.Text(self.news_frame, wrap=tk.WORD, state=tk.DISABLED,
                               yscrollcommand=self.news_scroll.set)
        self.news_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.news_scroll.config(command=self.news_text.yview)
        
        self.spinner = LoadingSpinner(self.root)
        self.spinner.place_forget()
        
        self.update_news()

    def run_process_with_window(self, command, window_title="进度输出"):
        output_window = tk.Toplevel(self.root)
        output_window.title(window_title)
        output_window.geometry("500x300")
        
        scroll = ttk.Scrollbar(output_window)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        output_text = tk.Text(output_window, wrap=tk.WORD, yscrollcommand=scroll.set)
        output_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=output_text.yview)
        
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        
        def update_output():
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_text.insert(tk.END, output)
                    output_text.see(tk.END)
                    output_window.update()
            
            output_window.after(1000, output_window.destroy)
        
        threading.Thread(target=update_output, daemon=True).start()
        return process

    def launch_game(self):
        def launch():
            self.show_loading()
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                
                subprocess.run(
                    ['00.bat'],
                    startupinfo=startupinfo
                )
                
                try:
                    with open('game/update_log.txt', 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            messagebox.showwarning("警告", "请先更新！")
                            self.hide_loading()
                            return
                except FileNotFoundError:
                    pass

                if not self.config.get('direct_launch'):
                    subprocess.Popen(['hmcl.exe'], startupinfo=startupinfo)
                else:
                    subprocess.Popen(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'start.ps1'], 
                                   startupinfo=startupinfo)
                                   
            except Exception as e:
                messagebox.showerror("错误", f"启动失败: {str(e)}")
            finally:
                self.hide_loading()
        
        threading.Thread(target=launch, daemon=True).start()

    def update_game(self):
        def run_update():
            self.show_loading()
            try:
                process = self.run_process_with_window(['00.bat'], "更新输出 - 第1步")
                process.wait()
                
                process = self.run_process_with_window(['01.bat'], "更新输出 - 第2步")
                process.wait()
                
                messagebox.showinfo("成功", "更新完成！")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {str(e)}")
            finally:
                self.hide_loading()
        
        threading.Thread(target=run_update, daemon=True).start()

    def install_game(self):
        def download_and_install():
            self.show_loading()
            download_state = self.load_download_state()
            downloaded = 0
            download_paused = False
            download_cancelled = False
            max_retries = 3
            retry_count = 0
            
            try:
                headers = {}
                if download_state:
                    resume = messagebox.askyesno("继续下载", 
                        f"发现未完成的下载（已下载: {download_state['downloaded_size'] / 1024 / 1024:.2f}MB / {download_state['total_size'] / 1024 / 1024:.2f}MB），是否继续？")
                    if resume:
                        downloaded = download_state['downloaded_size']
                        headers['Range'] = f'bytes={downloaded}-'
                    else:
                        self.clear_download_state()
                
                progress_window = tk.Toplevel(self.root)
                progress_window.title("下载进度")
                progress_window.geometry("300x150")
                
                progress = ttk.Progressbar(progress_window, length=250, mode='determinate')
                progress.pack(pady=20)
                
                status_label = ttk.Label(progress_window, text="")
                status_label.pack(pady=5)
                
                button_frame = ttk.Frame(progress_window)
                button_frame.pack(pady=5)
                
                def update_status():
                    speed = downloaded / (time.time() - start_time) / 1024 / 1024
                    status_label.config(text=f"下载速度: {speed:.2f}MB/s\n"
                                          f"已下载: {downloaded/1024/1024:.2f}MB / {total_size/1024/1024:.2f}MB")
                
                def toggle_pause():
                    nonlocal download_paused
                    download_paused = not download_paused
                    pause_button.config(text="继续下载" if download_paused else "暂停下载")
                    if download_paused:
                        self.save_download_state(downloaded, total_size, True)
                
                def cancel_download():
                    nonlocal download_cancelled
                    download_cancelled = True
                    result = messagebox.askyesno("取消下载", 
                        "是否保存下载进度？\n选择'是'可以在下次打开程序时继续下载。")
                    if not result:
                        self.clear_download_state()
                        if os.path.exists('game.zip'):
                            os.remove('game.zip')
                    progress_window.destroy()
                
                pause_button = ttk.Button(button_frame, text="暂停下载", command=toggle_pause)
                pause_button.pack(side=tk.LEFT, padx=5)
                
                cancel_button = ttk.Button(button_frame, text="取消下载", command=cancel_download)
                cancel_button.pack(side=tk.LEFT, padx=5)

                while retry_count < max_retries:
                    try:
                        session = requests.Session()
                        response = session.get('https://mcmods2333.flyqilai.top/0d00.zip', 
                                         stream=True, headers=headers, timeout=30)
                        
                        if response.status_code not in [200, 206]:
                            raise Exception(f"下载失败，服务器返回状态码: {response.status_code}")
                            
                        total_size = int(response.headers.get('content-length', 0)) + downloaded
                        mode = 'ab' if downloaded > 0 else 'wb'
                        start_time = time.time()
                        chunk_size = 1024 * 1024  # 1MB chunks
                        
                        with open('game.zip', mode) as f:
                            for data in response.iter_content(chunk_size):
                                if download_cancelled:
                                    return
                                
                                while download_paused:
                                    time.sleep(0.1)
                                    if download_cancelled:
                                        return
                                
                                if data:
                                    f.write(data)
                                    downloaded += len(data)
                                    progress['value'] = (downloaded / total_size) * 100
                                    update_status()
                                    progress_window.update()
                                    self.save_download_state(downloaded, total_size)
                                    
                                if downloaded >= total_size:
                                    break
                                    
                        if downloaded >= total_size:
                            break
                            
                    except (requests.exceptions.RequestException, IOError) as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            raise Exception(f"下载失败，已重试{max_retries}次: {str(e)}")
                        else:
                            time.sleep(2)
                            continue

                if not download_cancelled and downloaded >= total_size:
                    self.clear_download_state()
                    progress_window.destroy()
                    
                    try:
                        with zipfile.ZipFile('game.zip', 'r') as zip_ref:
                            zip_ref.extractall(r'game\gaymoo')
                        os.remove('game.zip')
                        messagebox.showinfo("成功", "游戏安装完成！")
                    except Exception as e:
                        messagebox.showerror("解压错误", 
                            f"下载完成但解压失败。错误信息：{str(e)}\n"
                            "请手动检查文件完整性或重新下载。")
                    
            except requests.exceptions.ConnectionError:
                messagebox.showerror("网络错误", 
                    "网络连接失败。\n已保存下载进度，您可以稍后重试。")
                self.save_download_state(downloaded, total_size)
            except Exception as e:
                messagebox.showerror("错误", 
                    f"下载过程中出现错误：{str(e)}\n"
                    "已保存下载进度，您可以稍后重试。")
                self.save_download_state(downloaded, total_size)
            finally:
                self.hide_loading()
        
        threading.Thread(target=download_and_install, daemon=True).start()

    def load_config(self):
        try:
            with open('launcher_config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                'direct_launch': False
            }

    def save_config(self):
        with open('launcher_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def create_buttons(self):
        self.launch_btn = ttk.Button(self.button_frame, 
                                   text="启动启动器" if not self.config.get('direct_launch') else "启动游戏",
                                   command=self.launch_game)
        self.launch_btn.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(self.button_frame, text="安装游戏", 
                  command=self.install_game).pack(fill=tk.X, pady=5)
        
        ttk.Button(self.button_frame, text="更新游戏", 
                  command=self.update_game).pack(fill=tk.X, pady=5)
        
        ttk.Button(self.button_frame, text="设置", 
                  command=self.show_settings).pack(fill=tk.X, pady=5, side=tk.BOTTOM)

    def show_loading(self):
        self.spinner.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.spinner.start()

    def hide_loading(self):
        self.spinner.stop()
        self.spinner.place_forget()

    def update_news(self):
        def fetch_news():
            try:
                headers = {
                    'Accept-Charset': 'utf-8',
                    'User-Agent': 'Mozilla/5.0'
                }
                response = requests.get('https://mc.lzyablo.top/news.txt', headers=headers)
                if response.status_code == 200:
                    encodings = ['utf-8', 'gb2312', 'gbk']
                    news_text = None
                    
                    for encoding in encodings:
                        try:
                            response.encoding = encoding
                            news_text = response.text
                            news_text.encode(encoding)
                            break
                        except UnicodeEncodeError:
                            continue
                    
                    if news_text:
                        self.news_text.configure(state=tk.NORMAL)
                        self.news_text.delete(1.0, tk.END)
                        self.news_text.insert(tk.END, news_text)
                        self.news_text.configure(state=tk.DISABLED)
                    else:
                        response.encoding = response.apparent_encoding
                        self.news_text.configure(state=tk.NORMAL)
                        self.news_text.delete(1.0, tk.END)
                        self.news_text.insert(tk.END, response.text)
                        self.news_text.configure(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("错误", f"获取新闻失败: {str(e)}")
        
        threading.Thread(target=fetch_news, daemon=True).start()

    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("设置")
        settings_window.geometry("300x200")
        
        ttk.Label(settings_window, 
                 text="您可以直接启动游戏无需启动器").pack(pady=20)
        
        def toggle_direct_launch():
            self.config['direct_launch'] = not self.config.get('direct_launch')
            self.launch_btn.configure(
                text="启动游戏" if self.config['direct_launch'] else "启动启动器"
            )
            self.save_config()
        
        ttk.Button(settings_window, text="切换启动方式", 
                  command=toggle_direct_launch).pack(pady=10)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MinecraftLauncher()
    app.run()
