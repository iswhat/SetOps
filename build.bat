@echo off

REM SetOps - 打包脚本
REM ===============

echo SetOps - 打包脚本
echo ===============
echo 正在准备打包...

REM 检查是否有Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8或更高版本
    echo 请访问 https://www.python.org/downloads/ 下载安装
    pause
    exit /b 1
)

REM 检查是否有pip
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pip，请确保Python安装时包含pip
    echo 请重新安装Python并勾选"Add Python to PATH"选项
    pause
    exit /b 1
)

REM 检查是否有PyInstaller
python -m pip list | findstr pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装PyInstaller...
    python -m pip install pyinstaller
    if %errorlevel% neq 0 (
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
)

REM 开始打包
echo 正在打包应用...
python -m PyInstaller build.spec

if %errorlevel% neq 0 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo 打包完成！
echo 可执行文件已生成在 dist 目录中
echo 请运行 dist\SetOps.exe 启动应用

pause
