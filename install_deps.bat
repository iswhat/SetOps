@echo off

REM SetOps - 依赖安装脚本
REM ===============

echo SetOps - 依赖安装脚本
echo ===============
echo 正在安装依赖...

REM 检查是否有Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 请访问 https://www.python.org/downloads/ 下载安装
    echo 安装时请勾选 "Add Python to PATH" 选项
    pause
    exit /b 1
)

REM 检查是否有pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pip，请确保Python安装时包含pip
    echo 请重新安装Python并勾选 "Add Python to PATH" 选项
    pause
    exit /b 1
)

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip >nul 2>&1

REM 安装依赖
echo 安装项目依赖...
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败
    echo 请检查网络连接并重试
    pause
    exit /b 1
)

echo 依赖安装成功！
echo 现在可以运行 SetOps.exe 或 SetOpsUI.py 启动应用
pause
