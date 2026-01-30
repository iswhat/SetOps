@echo off

REM SetOps - 本地千万级数据交并差运算工具
REM =====================================

echo SetOps - 本地千万级数据交并差运算工具
echo =====================================
echo 正在启动...

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

REM 安装依赖
echo 正在安装依赖...
python -m pip install -r backend\requirements.txt
if %errorlevel% neq 0 (
    echo 错误: 依赖安装失败
pause
exit /b 1
)

REM 启动后端
echo 正在启动后端服务...
start "SetOps Backend" python backend\main.py

REM 等待后端启动
echo 等待后端服务启动...
timeout /t 3 /nobreak >nul

REM 检查是否有Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: 未找到Node.js，将使用内置的前端文件
echo 请在浏览器中打开 dist\index.html 进行操作
pause
exit /b 0
)

REM 启动前端开发服务器
echo 正在启动前端服务...
start "SetOps Frontend" npm run dev

REM 提示用户
echo 服务已启动，请打开浏览器访问 http://localhost:5173

pause
