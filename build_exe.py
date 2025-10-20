#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
番茄钟GUI程序打包脚本
使用PyInstaller将Python程序打包成exe文件
"""

import os
import sys
import subprocess
import shutil

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✅ PyInstaller安装成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller安装失败: {e}")
        print("\n🔧 手动解决方案:")
        print("1. 运行: pip install pyinstaller")
        print("2. 或者使用conda: conda install pyinstaller")
        return False

def build_exe():
    """构建exe文件"""
    print("开始打包番茄钟程序...")
    
    # PyInstaller命令参数
    cmd = [
        "pyinstaller",
        "--onefile",                    # 打包成单个exe文件
        "--windowed",                   # 不显示控制台窗口
        "--name=番茄钟",                # 设置exe文件名
        "--icon=tomato.ico",           # 图标文件（如果存在）
        "--add-data=pomodoro_config.json;.",  # 包含配置文件
        "--hidden-import=PIL._tkinter_finder",  # 隐式导入
        "--hidden-import=plyer.platforms.win.notification",
        "pomodoro_gui.py"
    ]
    
    try:
        # 如果没有图标文件，移除图标参数
        if not os.path.exists("tomato.ico"):
            cmd.remove("--icon=tomato.ico")
        
        # 如果没有配置文件，移除配置文件参数
        if not os.path.exists("pomodoro_config.json"):
            cmd.remove("--add-data=pomodoro_config.json;.")
        
        subprocess.check_call(cmd)
        print("✅ 打包成功！")
        
        # 检查生成的文件
        exe_path = os.path.join("dist", "番茄钟.exe")
        if os.path.exists(exe_path):
            file_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            print(f"📁 生成的exe文件: {exe_path}")
            print(f"📊 文件大小: {file_size:.1f} MB")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 打包失败: {e}")
        return False

def create_icon():
    """创建简单的图标文件"""
    try:
        from PIL import Image, ImageDraw
        
        # 创建32x32的图标
        img = Image.new('RGBA', (32, 32), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # 绘制番茄图标
        draw.ellipse([4, 4, 28, 28], fill='tomato')
        draw.ellipse([14, 2, 18, 8], fill='green')
        
        # 保存为ico文件
        img.save('tomato.ico', format='ICO')
        print("✅ 图标文件创建成功！")
        return True
        
    except Exception as e:
        print(f"⚠️ 图标创建失败: {e}")
        return False

def clean_build():
    """清理构建文件"""
    dirs_to_remove = ['build', '__pycache__']
    files_to_remove = ['番茄钟.spec']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"🗑️ 已清理: {dir_name}")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"🗑️ 已清理: {file_name}")

def main():
    """主函数"""
    print("🍅 番茄钟程序打包工具")
    print("=" * 40)
    
    # 检查是否在正确的目录
    if not os.path.exists("pomodoro_gui.py"):
        print("❌ 错误: 请在包含pomodoro_gui.py的目录中运行此脚本")
        return
    
    # 创建图标
    create_icon()
    
    # 安装PyInstaller
    if not install_pyinstaller():
        return
    
    # 构建exe
    if build_exe():
        print("\n🎉 打包完成！")
        print("📁 exe文件位置: dist/番茄钟.exe")
        print("\n💡 使用提示:")
        print("1. 可以直接运行dist/番茄钟.exe")
        print("2. 首次运行可能需要几秒钟启动时间")
        print("3. 可以将exe文件复制到任何位置使用")
        
        # 询问是否清理构建文件
        response = input("\n是否清理构建文件? (y/n): ")
        if response.lower() in ['y', 'yes', '是']:
            clean_build()
    
    print("\n按任意键退出...")
    input()

if __name__ == "__main__":
    main()