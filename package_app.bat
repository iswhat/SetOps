@echo off

REM SetOps - 打包脚本
REM ===============

echo SetOps - 打包脚本
echo ===============
echo 正在准备打包...

REM 创建输出目录
set OUTPUT_DIR=SetOps_App
if exist "%OUTPUT_DIR%" (
    echo 清理旧的输出目录...
    rmdir /s /q "%OUTPUT_DIR%"
)

mkdir "%OUTPUT_DIR%"
echo 创建输出目录: %OUTPUT_DIR%

REM 复制必要的文件
echo 复制文件...

REM 复制前端文件
copy "SetOpsUI.py" "%OUTPUT_DIR%\" >nul

REM 复制后端文件
mkdir "%OUTPUT_DIR%\backend" >nul 2>&1
copy "backend\*.py" "%OUTPUT_DIR%\backend\" >nul

REM 复制依赖文件
copy "requirements.txt" "%OUTPUT_DIR%\" >nul

REM 复制启动脚本
copy "install_deps.bat" "%OUTPUT_DIR%\install_deps.bat" >nul

REM 创建启动脚本
echo 创建启动脚本...
type nul > "%OUTPUT_DIR%\StartSetOps.bat"
echo @echo off >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo REM SetOps - 启动脚本 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo REM =============== >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo echo SetOps - 本地千万级数据交并差运算工具 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo echo =============== >> "%OUTPUT_DIR%\StartSetOps.bat"
echo echo 正在启动... >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo REM 检查是否有Python >> "%OUTPUT_DIR%\StartSetOps.bat"
echo python --version >nul 2>&1 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo if %%errorlevel%% neq 0 ( >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     echo 错误: 未找到Python，请先安装Python 3.8或更高版本 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     echo 请运行 install_deps.bat 安装依赖 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     pause >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     exit /b 1 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo ) >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo REM 检查是否有依赖 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo python -c "import PySide6" >nul 2>&1 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo if %%errorlevel%% neq 0 ( >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     echo 错误: 缺少依赖，请先运行 install_deps.bat 安装 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     pause >> "%OUTPUT_DIR%\StartSetOps.bat"
echo     exit /b 1 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo ) >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo REM 启动应用 >> "%OUTPUT_DIR%\StartSetOps.bat"
echo echo 启动应用... >> "%OUTPUT_DIR%\StartSetOps.bat"
echo python SetOpsUI.py >> "%OUTPUT_DIR%\StartSetOps.bat"
echo. >> "%OUTPUT_DIR%\StartSetOps.bat"
echo pause >> "%OUTPUT_DIR%\StartSetOps.bat"

REM 创建README文件
echo 创建README文件...
type nul > "%OUTPUT_DIR%\README.txt"
echo SetOps - 本地千万级数据交并差运算工具 >> "%OUTPUT_DIR%\README.txt"
echo =============================== >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 如何使用: >> "%OUTPUT_DIR%\README.txt"
echo 1. 首先运行 install_deps.bat 安装依赖 >> "%OUTPUT_DIR%\README.txt"
echo 2. 双击运行 StartSetOps.bat 启动应用 >> "%OUTPUT_DIR%\README.txt"
echo 3. 在应用中拖拽文件到数据集区域 >> "%OUTPUT_DIR%\README.txt"
echo 4. 选择运算类型和输出设置 >> "%OUTPUT_DIR%\README.txt"
echo 5. 点击"开始处理"按钮执行运算 >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 功能特点: >> "%OUTPUT_DIR%\README.txt"
echo • 处理千万级数据的交并差运算 >> "%OUTPUT_DIR%\README.txt"
echo • 多文件合并和去重 >> "%OUTPUT_DIR%\README.txt"
echo • 实时进度显示 >> "%OUTPUT_DIR%\README.txt"
echo • 批量输出防止内存溢出 >> "%OUTPUT_DIR%\README.txt"
echo • 支持CSV、Excel、TXT格式 >> "%OUTPUT_DIR%\README.txt"
echo • 支持拖拽文件上传 >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 系统要求: >> "%OUTPUT_DIR%\README.txt"
echo • Windows 7 或更高版本 >> "%OUTPUT_DIR%\README.txt"
echo • Python 3.8 或更高版本 >> "%OUTPUT_DIR%\README.txt"
echo • 至少 4GB 内存 >> "%OUTPUT_DIR%\README.txt"

REM 创建桌面快捷方式
echo 创建桌面快捷方式...
set SHORTCUT_NAME=SetOps.lnk
set DESKTOP_DIR=%USERPROFILE%\Desktop

REM 使用PowerShell创建快捷方式
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%DESKTOP_DIR%\%SHORTCUT_NAME%'); $s.TargetPath = '%CD%\%OUTPUT_DIR%\StartSetOps.bat'; $s.WorkingDirectory = '%CD%\%OUTPUT_DIR%'; $s.Save()"

if exist "%DESKTOP_DIR%\%SHORTCUT_NAME%" (
    echo 桌面快捷方式创建成功！
) else (
    echo 提示: 桌面快捷方式创建失败，您可以手动创建
)

echo 打包完成！
echo 输出目录: %OUTPUT_DIR%
echo 请按照 README.txt 中的说明使用

echo. 
echo 下一步操作:
echo 1. 打开 %OUTPUT_DIR% 目录
echo 2. 运行 install_deps.bat 安装依赖
echo 3. 运行 StartSetOps.bat 启动应用

pause
