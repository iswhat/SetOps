#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SetOps - 打包脚本
"""

import os
import shutil
import sys

def main():
    """主函数"""
    print("SetOps - 打包脚本")
    print("===============")
    print("正在准备打包...")
    
    # 创建输出目录
    output_dir = "SetOps_App"
    if os.path.exists(output_dir):
        print(f"清理旧的输出目录: {output_dir}")
        shutil.rmtree(output_dir)
    
    print(f"创建输出目录: {output_dir}")
    os.makedirs(output_dir)
    
    # 复制必要的文件
    print("复制文件...")
    
    # 复制前端文件
    if os.path.exists("SetOpsUI.py"):
        shutil.copy("SetOpsUI.py", output_dir)
        print("复制 SetOpsUI.py")
    
    # 复制后端文件
    backend_dir = os.path.join(output_dir, "backend")
    os.makedirs(backend_dir)
    for file in os.listdir("backend"):
        if file.endswith(".py"):
            src = os.path.join("backend", file)
            dst = os.path.join(backend_dir, file)
            shutil.copy(src, dst)
            print(f"复制 backend/{file}")
    
    # 复制依赖文件
    if os.path.exists("requirements.txt"):
        shutil.copy("requirements.txt", output_dir)
        print("复制 requirements.txt")
    
    # 创建启动脚本
    print("创建启动脚本...")
    create_start_script(output_dir)
    
    # 创建依赖安装脚本
    print("创建依赖安装脚本...")
    create_install_script(output_dir)
    
    # 创建README文件
    print("创建README文件...")
    create_readme(output_dir)
    
    print("\n打包完成！")
    print(f"输出目录: {output_dir}")
    print("\n下一步操作:")
    print(f"1. 打开 {output_dir} 目录")
    print("2. 运行 install_deps.bat 安装依赖")
    print("3. 运行 StartSetOps.bat 启动应用")
    print("\n应用已准备就绪！")

def create_start_script(output_dir):
    """创建启动脚本"""
    script_path = os.path.join(output_dir, "StartSetOps.bat")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("\n")
        f.write("REM SetOps - 启动脚本\n")
        f.write("REM ===============\n")
        f.write("\n")
        f.write("echo SetOps - 本地千万级数据交并差运算工具\n")
        f.write("echo ===============\n")
        f.write("echo 正在启动...\n")
        f.write("\n")
        f.write("REM 检查是否有Python\n")
        f.write("python --version >nul 2>&1\n")
        f.write("if %errorlevel% neq 0 (\n")
        f.write("    echo 错误: 未找到Python，请先安装Python 3.8或更高版本\n")
        f.write("    echo 请运行 install_deps.bat 安装依赖\n")
        f.write("    pause\n")
        f.write("    exit /b 1\n")
        f.write(")\n")
        f.write("\n")
        f.write("REM 检查是否有依赖\n")
        f.write("python -c \"import PySide6\" >nul 2>&1\n")
        f.write("if %errorlevel% neq 0 (\n")
        f.write("    echo 错误: 缺少依赖，请先运行 install_deps.bat 安装\n")
        f.write("    pause\n")
        f.write("    exit /b 1\n")
        f.write(")\n")
        f.write("\n")
        f.write("REM 启动应用\n")
        f.write("echo 启动应用...\n")
        f.write("python SetOpsUI.py\n")
        f.write("\n")
        f.write("pause\n")

def create_install_script(output_dir):
    """创建依赖安装脚本"""
    script_path = os.path.join(output_dir, "install_deps.bat")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("\n")
        f.write("REM SetOps - 依赖安装脚本\n")
        f.write("REM ===============\n")
        f.write("\n")
        f.write("echo SetOps - 依赖安装脚本\n")
        f.write("echo ===============\n")
        f.write("echo 正在安装依赖...\n")
        f.write("\n")
        f.write("REM 检查是否有Python\n")
        f.write("python --version >nul 2>&1\n")
        f.write("if %errorlevel% neq 0 (\n")
        f.write("    echo 错误: 未找到Python，请先安装Python 3.8或更高版本\n")
        f.write("    echo 请访问 https://www.python.org/downloads/ 下载安装\n")
        f.write("    echo 安装时请勾选 Add Python to PATH 选项\n")
        f.write("    pause\n")
        f.write("    exit /b 1\n")
        f.write(")\n")
        f.write("\n")
        f.write("REM 检查是否有pip\n")
        f.write("python -m pip --version >nul 2>&1\n")
        f.write("if %errorlevel% neq 0 (\n")
        f.write("    echo 错误: 未找到pip，请确保Python安装时包含pip\n")
        f.write("    echo 请重新安装Python并勾选 Add Python to PATH 选项\n")
        f.write("    pause\n")
        f.write("    exit /b 1\n")
        f.write(")\n")
        f.write("\n")
        f.write("REM 升级pip\n")
        f.write("echo 升级pip...\n")
        f.write("python -m pip install --upgrade pip >nul 2>&1\n")
        f.write("\n")
        f.write("REM 安装依赖\n")
        f.write("echo 安装项目依赖...\n")
        f.write("python -m pip install -r requirements.txt\n")
        f.write("\n")
        f.write("if %errorlevel% neq 0 (\n")
        f.write("    echo 错误: 依赖安装失败\n")
        f.write("    echo 请检查网络连接并重试\n")
        f.write("    pause\n")
        f.write("    exit /b 1\n")
        f.write(")\n")
        f.write("\n")
        f.write("echo 依赖安装成功！\n")
        f.write("echo 现在可以运行 StartSetOps.bat 启动应用\n")
        f.write("pause\n")

def create_readme(output_dir):
    """创建README文件"""
    readme_path = os.path.join(output_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("SetOps - 本地千万级数据交并差运算工具\n")
        f.write("===============================\n")
        f.write("\n")
        f.write("如何使用:\n")
        f.write("1. 首先运行 install_deps.bat 安装依赖\n")
        f.write("2. 双击运行 StartSetOps.bat 启动应用\n")
        f.write("3. 在应用中拖拽文件到数据集区域\n")
        f.write("4. 选择运算类型和输出设置\n")
        f.write("5. 点击\"开始处理\"按钮执行运算\n")
        f.write("\n")
        f.write("功能特点:\n")
        f.write("• 处理千万级数据的交并差运算\n")
        f.write("• 多文件合并和去重\n")
        f.write("• 实时进度显示\n")
        f.write("• 批量输出防止内存溢出\n")
        f.write("• 支持CSV、Excel、TXT格式\n")
        f.write("• 支持拖拽文件上传\n")
        f.write("• 基于PySide6的现代界面\n")
        f.write("\n")
        f.write("系统要求:\n")
        f.write("• Windows 7 或更高版本\n")
        f.write("• Python 3.8 或更高版本\n")
        f.write("• 至少 4GB 内存\n")
        f.write("• 1GB 可用磁盘空间\n")

if __name__ == "__main__":
    main()
