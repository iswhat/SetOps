@echo off

REM SetOps - 打包脚本
REM ===============

echo SetOps - 打包脚本
echo ===============
echo 正在准备打包...

REM 创建输出目录
set OUTPUT_DIR=SetOpsApp
if exist "%OUTPUT_DIR%" (
    echo 清理旧的输出目录...
    rmdir /s /q "%OUTPUT_DIR%"
)

mkdir "%OUTPUT_DIR%"
echo 创建输出目录: %OUTPUT_DIR%

REM 复制必要的文件
echo 复制文件...

REM 复制前端文件
copy "demo.html" "%OUTPUT_DIR%\" >nul

REM 复制后端文件
mkdir "%OUTPUT_DIR%\backend" >nul 2>&1
copy "backend\*.py" "%OUTPUT_DIR%\backend\" >nul

REM 复制启动脚本
copy "StartSetOps.bat" "%OUTPUT_DIR%\SetOps.bat" >nul

REM 创建README文件
echo 创建README文件...
type nul > "%OUTPUT_DIR%\README.txt"
echo SetOps - 本地千万级数据交并差运算工具 >> "%OUTPUT_DIR%\README.txt"
echo =============================== >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 如何使用: >> "%OUTPUT_DIR%\README.txt"
echo 1. 双击运行 SetOps.bat 文件 >> "%OUTPUT_DIR%\README.txt"
echo 2. 浏览器会自动打开操作界面 >> "%OUTPUT_DIR%\README.txt"
echo 3. 拖拽文件到数据集区域 >> "%OUTPUT_DIR%\README.txt"
echo 4. 选择运算类型和输出设置 >> "%OUTPUT_DIR%\README.txt"
echo 5. 点击"开始处理"按钮执行运算 >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 支持的功能: >> "%OUTPUT_DIR%\README.txt"
echo • 处理千万级数据的交并差运算 >> "%OUTPUT_DIR%\README.txt"
echo • 多文件合并和去重 >> "%OUTPUT_DIR%\README.txt"
echo • 实时进度显示 >> "%OUTPUT_DIR%\README.txt"
echo • 批量输出防止内存溢出 >> "%OUTPUT_DIR%\README.txt"
echo • 支持CSV、Excel、TXT格式 >> "%OUTPUT_DIR%\README.txt"
echo. >> "%OUTPUT_DIR%\README.txt"
echo 系统要求: >> "%OUTPUT_DIR%\README.txt"
echo • Windows 7 或更高版本 >> "%OUTPUT_DIR%\README.txt"
echo • 现代浏览器 (Chrome、Firefox、Edge等) >> "%OUTPUT_DIR%\README.txt"
echo • 推荐配置: 4GB以上内存，双核CPU >> "%OUTPUT_DIR%\README.txt"

echo 打包完成！
echo 输出目录: %OUTPUT_DIR%
echo 请将整个目录复制到目标计算机上使用
echo 双击运行 SetOps.bat 启动应用

pause
