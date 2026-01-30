# SetOps - 打包脚本
# ===============

Write-Host "SetOps - 打包脚本"
Write-Host "==============="
Write-Host "正在准备打包..."

# 检查是否有Python
try {
    python --version | Out-Null
    Write-Host "找到Python"
} catch {
    Write-Host "错误: 未找到Python，请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "请访问 https://www.python.org/downloads/ 下载安装"
    Read-Host "按任意键退出..."
    exit 1
}

# 检查是否有pip
try {
    python -m pip --version | Out-Null
    Write-Host "找到pip"
} catch {
    Write-Host "错误: 未找到pip，请确保Python安装时包含pip" -ForegroundColor Red
    Write-Host "请重新安装Python并勾选\"Add Python to PATH\"选项"
    Read-Host "按任意键退出..."
    exit 1
}

# 检查是否有PyInstaller
try {
    $pipList = python -m pip list
    if ($pipList -notlike "*pyinstaller*" -and $pipList -notlike "*PyInstaller*") {
        Write-Host "正在安装PyInstaller..."
        python -m pip install pyinstaller
        if ($LASTEXITCODE -ne 0) {
            Write-Host "错误: PyInstaller安装失败" -ForegroundColor Red
            Read-Host "按任意键退出..."
            exit 1
        }
        Write-Host "PyInstaller安装成功"
    } else {
        Write-Host "找到PyInstaller"
    }
} catch {
    Write-Host "错误: 检查PyInstaller失败" -ForegroundColor Red
    Read-Host "按任意键退出..."
    exit 1
}

# 开始打包
Write-Host "正在打包应用..."
try {
    python -m PyInstaller build.spec
    if ($LASTEXITCODE -ne 0) {
        Write-Host "错误: 打包失败" -ForegroundColor Red
        Read-Host "按任意键退出..."
        exit 1
    }
    Write-Host "打包完成！" -ForegroundColor Green
    Write-Host "可执行文件已生成在 dist 目录中"
    Write-Host "请运行 dist\SetOps.exe 启动应用"
} catch {
    Write-Host "错误: 打包过程中发生异常: $_" -ForegroundColor Red
    Read-Host "按任意键退出..."
    exit 1
}

Read-Host "按任意键退出..."
