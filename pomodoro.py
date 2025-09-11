import argparse
import time
import os
import sys
from datetime import datetime, timedelta

def lock_screen():
    """锁定Windows屏幕"""
    try:
        os.system('rundll32.exe user32.dll,LockWorkStation')
        print("\n屏幕已锁定！")
    except Exception as e:
        print(f"\n锁屏失败: {e}")

def format_time(seconds):
    """格式化时间显示"""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"

def pomodoro_timer(duration_minutes):
    """番茄钟主函数"""
    total_seconds = duration_minutes * 60
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    print(f"\n🍅 番茄钟开始！")
    print(f"持续时间: {duration_minutes} 分钟")
    print(f"开始时间: {start_time.strftime('%H:%M:%S')}")
    print(f"结束时间: {end_time.strftime('%H:%M:%S')}")
    print("\n按 Ctrl+C 可以提前结束\n")
    
    try:
        for remaining in range(total_seconds, 0, -1):
            # 清除当前行并显示倒计时
            print(f"\r⏰ 剩余时间: {format_time(remaining)}", end="", flush=True)
            time.sleep(1)
        
        # 时间到了
        print("\n\n🎉 番茄钟时间到！")
        print("正在锁定屏幕...")
        lock_screen()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  番茄钟已手动停止")
        elapsed = datetime.now() - start_time
        elapsed_minutes = int(elapsed.total_seconds() // 60)
        print(f"已完成: {elapsed_minutes} 分钟")
        sys.exit(0)

def main():
    """主程序入口"""
    parser = argparse.ArgumentParser(
        description='🍅 番茄钟程序 - 专注工作，提高效率',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""使用示例:
  python pomodoro.py           # 默认25分钟
  python pomodoro.py -t 30     # 30分钟番茄钟
  python pomodoro.py --time 45 # 45分钟番茄钟"""
    )
    
    parser.add_argument(
        '-t', '--time',
        type=int,
        default=25,
        help='番茄钟持续时间（分钟），默认25分钟'
    )
    
    args = parser.parse_args()
    
    # 验证输入
    if args.time <= 0:
        print("❌ 错误: 时间必须大于0分钟")
        sys.exit(1)
    
    if args.time > 180:  # 限制最大3小时
        print("❌ 错误: 时间不能超过180分钟")
        sys.exit(1)
    
    # 开始番茄钟
    pomodoro_timer(args.time)

if __name__ == "__main__":
    main()