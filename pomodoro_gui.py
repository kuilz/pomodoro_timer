import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import plyer

def lock_screen():
    """锁定Windows屏幕"""
    try:
        os.system('rundll32.exe user32.dll,LockWorkStation')
        print("屏幕已锁定！")
    except Exception as e:
        print(f"锁屏失败: {e}")

class PomodoroConfig:
    """番茄钟配置管理"""
    def __init__(self):
        self.config_file = "pomodoro_config.json"
        self.default_config = {
            "work_time": 25,      # 工作时间（分钟）
            "short_break": 5,     # 短休息时间（分钟）
            "long_break": 15,     # 长休息时间（分钟）
            "cycles": 4,          # 循环次数
            "auto_lock": True     # 工作结束后自动锁屏
        }
        self.config = self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return self.default_config.copy()
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

class PomodoroTimer:
    """番茄钟核心逻辑"""
    def __init__(self, config, callback=None):
        self.config = config
        self.callback = callback
        self.is_running = False
        self.is_paused = False
        self.current_session = 0  # 当前会话（0=工作，1=短休息，2=长休息）
        self.current_cycle = 0    # 当前循环次数
        self.remaining_time = 0   # 剩余时间（秒）
        self.timer_thread = None
        
    def start(self):
        """开始番茄钟"""
        if not self.is_running:
            self.is_running = True
            self.is_paused = False
            if self.remaining_time == 0:
                self.reset_session()
            self.timer_thread = threading.Thread(target=self._run_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
    
    def pause(self):
        """暂停/恢复番茄钟"""
        self.is_paused = not self.is_paused
    
    def stop(self):
        """停止番茄钟"""
        self.is_running = False
        self.is_paused = False
        self.remaining_time = 0
        self.current_session = 0
        self.current_cycle = 0
    
    def reset_session(self):
        """重置当前会话"""
        if self.current_session == 0:  # 工作时间
            self.remaining_time = self.config.config["work_time"] * 60
        elif self.current_session == 1:  # 短休息
            self.remaining_time = self.config.config["short_break"] * 60
        else:  # 长休息
            self.remaining_time = self.config.config["long_break"] * 60
    
    def _run_timer(self):
        """计时器主循环"""
        while self.is_running and self.remaining_time > 0:
            if not self.is_paused:
                self.remaining_time -= 1
                if self.callback:
                    self.callback(self.get_status())
            time.sleep(1)
        
        if self.is_running and self.remaining_time <= 0:
            self._session_complete()
    
    def _session_complete(self):
        """会话完成处理"""
        session_name = ["工作", "短休息", "长休息"][self.current_session]
        
        # 发送通知
        try:
            plyer.notification.notify(
                title="番茄钟提醒",
                message=f"{session_name}时间结束！",
                timeout=5
            )
        except Exception:
            pass
        
        # 如果是工作时间结束，执行锁屏
        if self.current_session == 0 and self.config.config.get("auto_lock", True):  # 工作时间结束且开启自动锁屏
            try:
                lock_screen()
            except Exception as e:
                print(f"锁屏失败: {e}")
        
        # 切换到下一个会话
        if self.current_session == 0:  # 工作完成
            # 工作完成后，增加循环次数
            self.current_cycle += 1
            # 检查是否需要进入长休息
            if self.current_cycle >= self.config.config["cycles"]:
                # 完成一轮循环，进入长休息
                self.current_session = 2
            else:
                # 进入短休息
                self.current_session = 1
        elif self.current_session == 1:  # 短休息完成，回到工作
            self.current_session = 0
            # 短休息完成后不改变循环次数，保持当前循环状态
        else:  # 长休息完成，回到工作并重置循环
            self.current_session = 0
            # 长休息后重新开始，循环次数重置为0
            self.current_cycle = 0
        
        # 自动开始下一个会话
        self.reset_session()
        if self.callback:
            self.callback(self.get_status())
        
        # 重新启动计时器线程以继续下一个会话
        if self.is_running:
            self.timer_thread = threading.Thread(target=self._run_timer)
            self.timer_thread.daemon = True
            self.timer_thread.start()
    
    def get_status(self):
        """获取当前状态"""
        session_names = ["🍅 工作中", "☕ 短休息", "🛌 长休息"]
        # 显示循环轮次：工作中显示当前轮次+1，休息时显示已完成的轮次
        if self.current_session == 0:  # 工作中
            display_cycle = self.current_cycle + 1
        else:  # 休息中，显示已完成的工作轮次
            display_cycle = self.current_cycle
        
        return {
            "session": session_names[self.current_session],
            "cycle": display_cycle,
            "total_cycles": self.config.config["cycles"],
            "remaining_time": self.remaining_time,
            "is_running": self.is_running,
            "is_paused": self.is_paused
        }
    
    def format_time(self, seconds):
        """格式化时间显示"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

class ConfigWindow:
    """配置窗口"""
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.window = None
    
    def show(self):
        """显示配置窗口"""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return
        
        self.window = tk.Toplevel(self.parent.root)
        self.window.title("番茄钟配置")
        self.window.geometry("310x280")
        self.window.resizable(False, False)

        # 让窗口网格扩展并居中内容
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(0, weight=1)
        
        # 配置项容器居中（不填充）
        frame = ttk.Frame(self.window, padding="10")
        frame.grid(row=0, column=0)
        
        # 工作时间
        ttk.Label(frame, text="工作时间 (分钟):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.work_var = tk.StringVar(value=str(self.config.config["work_time"]))
        ttk.Entry(frame, textvariable=self.work_var, width=10).grid(row=0, column=1, sticky=tk.E, pady=5)
        
        # 短休息时间
        ttk.Label(frame, text="短休息时间 (分钟):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.short_var = tk.StringVar(value=str(self.config.config["short_break"]))
        ttk.Entry(frame, textvariable=self.short_var, width=10).grid(row=1, column=1, sticky=tk.E, pady=5)
        
        # 长休息时间
        ttk.Label(frame, text="长休息时间 (分钟):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.long_var = tk.StringVar(value=str(self.config.config["long_break"]))
        ttk.Entry(frame, textvariable=self.long_var, width=10).grid(row=2, column=1, sticky=tk.E, pady=5)
        
        # 循环次数
        ttk.Label(frame, text="循环次数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.cycles_var = tk.StringVar(value=str(self.config.config["cycles"]))
        ttk.Entry(frame, textvariable=self.cycles_var, width=10).grid(row=3, column=1, sticky=tk.E, pady=5)
        
        # 自动锁屏选项
        self.auto_lock_var = tk.BooleanVar(value=self.config.config.get("auto_lock", True))
        ttk.Checkbutton(frame, text="工作结束后自动锁屏", 
                       variable=self.auto_lock_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # 说明
        ttk.Label(frame, text="说明: 工作N次后进入长休息", 
                 font=("", 8)).grid(row=5, column=0, columnspan=2, pady=10)
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="保存", command=self.save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
        
        # 居中显示
        self.window.transient(self.parent.root)
        self.window.grab_set()
    
    def save_config(self):
        """保存配置"""
        try:
            work_time = int(self.work_var.get())
            short_break = int(self.short_var.get())
            long_break = int(self.long_var.get())
            cycles = int(self.cycles_var.get())
            auto_lock = self.auto_lock_var.get()
            
            if work_time <= 0 or short_break <= 0 or long_break <= 0 or cycles <= 0:
                raise ValueError("所有值必须大于0")
            
            self.config.config["work_time"] = work_time
            self.config.config["short_break"] = short_break
            self.config.config["long_break"] = long_break
            self.config.config["cycles"] = cycles
            self.config.config["auto_lock"] = auto_lock
            
            self.config.save_config()
            messagebox.showinfo("成功", "配置已保存！")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("错误", f"配置无效: {e}")

class PomodoroApp:
    """番茄钟主应用"""
    def __init__(self):
        self.config = PomodoroConfig()
        self.timer = PomodoroTimer(self.config, self.update_display)
        
        # 创建主窗口（隐藏）
        self.root = tk.Tk()
        self.root.title("番茄钟")
        self.root.geometry("310x200")
        self.root.withdraw()  # 隐藏主窗口
        self.root.attributes('-topmost', True)
        
        self.setup_ui()
        self.create_tray_icon()
        
    def setup_ui(self):
        """设置UI界面"""
        # 让根窗口网格扩展，并使内容居中
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # 主框架（不使用 sticky，默认在单元格居中）
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0)

        # 状态显示
        self.status_label = ttk.Label(main_frame, text="🍅 准备开始", font=("", 14))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # 时间显示
        self.time_label = ttk.Label(main_frame, text="25:00", font=("", 20, "bold"))
        self.time_label.grid(row=1, column=0, columnspan=3, pady=10)
        
        # 循环显示
        self.cycle_label = ttk.Label(main_frame, text="循环: 1/4")
        self.cycle_label.grid(row=2, column=0, columnspan=3, pady=5)
        
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="开始", command=self.toggle_timer)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="停止", command=self.stop_timer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="配置", command=self.show_config).pack(side=tk.LEFT, padx=5)
        
        # 初始化显示
        self.update_display(self.timer.get_status())
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建图标
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        # 绘制番茄形状的圆形
        draw.ellipse([8, 8, 56, 56], fill='tomato')
        # 绘制顶部的绿色叶子
        draw.ellipse([28, 4, 36, 16], fill='green')
        
        # 创建托盘菜单
        menu = pystray.Menu(
            item('显示', self.show_window),
            item('开始/暂停', self.toggle_timer),
            item('停止', self.stop_timer),
            pystray.Menu.SEPARATOR,
            item('配置', self.show_config),
            pystray.Menu.SEPARATOR,
            item('退出', self.quit_app)
        )
        
        self.tray_icon = pystray.Icon("pomodoro", image, "番茄钟", menu)
    
    def show_window(self, icon=None, item=None):
        """显示主窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.attributes('-topmost', True)
    
    def hide_window(self):
        """隐藏主窗口"""
        self.root.withdraw()
    
    def toggle_timer(self, icon=None, item=None):
        """切换计时器状态"""
        if self.timer.is_running:
            self.timer.pause()
            self.start_button.config(text="继续" if self.timer.is_paused else "暂停")
        else:
            self.timer.start()
            self.start_button.config(text="暂停")
    
    def stop_timer(self, icon=None, item=None):
        """停止计时器"""
        self.timer.stop()
        self.start_button.config(text="开始")
        self.update_display(self.timer.get_status())
    
    def show_config(self, icon=None, item=None):
        """显示配置窗口"""
        self.show_window()
        config_window = ConfigWindow(self, self.config)
        config_window.show()
    
    def update_display(self, status):
        """更新显示"""
        self.root.after(0, self._update_ui, status)
    
    def _update_ui(self, status):
        """在主线程中更新UI"""
        self.status_label.config(text=status["session"])
        self.time_label.config(text=self.timer.format_time(status["remaining_time"]))
        self.cycle_label.config(text=f"循环: {status['cycle']}/{status['total_cycles']}")
        
        # 更新托盘图标标题
        if hasattr(self, 'tray_icon'):
            time_str = self.timer.format_time(status["remaining_time"])
            self.tray_icon.title = f"番茄钟 - {status['session']} {time_str}"
    
    def on_closing(self):
        """窗口关闭事件"""
        self.hide_window()
    
    def quit_app(self, icon=None, item=None):
        """退出应用"""
        self.timer.stop()
        self.tray_icon.stop()
        self.root.quit()
    
    def run(self):
        """运行应用"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 在单独线程中运行托盘图标
        tray_thread = threading.Thread(target=self.tray_icon.run)
        tray_thread.daemon = True
        tray_thread.start()
        
        # 运行主循环
        self.root.mainloop()

if __name__ == "__main__":
    app = PomodoroApp()
    app.run()