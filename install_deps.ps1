# SetOps - 依赖安装脚本
# ===============

Write-Host "SetOps - 依赖安装脚本"
Write-Host "==============="
Write-Host "正在安装依赖..."

# 检查是否有Python
try {
    $pythonVersion = python --version
    Write-Host "找到Python: $pythonVersion"
} catch {
    Write-Host "错误: 未找到Python，请先安装Python 3.8或更高版本" -ForegroundColor Red
    Write-Host "请访问 https://www.python.org/downloads/ 下载安装" -ForegroundColor Yellow
    Write-Host "安装时请勾选 'Add Python to PATH' 选项" -ForegroundColor Yellow
    Read-Host "按任意键退出..."
    exit 1
}

# 检查是否有pip
try {
    $pipVersion = python -m pip --version
    Write-Host "找到pip: $pipVersion"
} catch {
    Write-Host "错误: 未找到pip，请确保Python安装时包含pip" -ForegroundColor Red
    Write-Host "请重新安装Python并勾选 'Add Python to PATH' 选项" -ForegroundColor Yellow
    Read-Host "按任意键退出..."
    exit 1
}

# 升级pip
Write-Host "升级pip..."
try {
    python -m pip install --upgrade pip | Out-Null
    Write-Host "pip 升级成功"
} catch {
    Write-Host "警告: pip 升级失败，但将继续安装依赖" -ForegroundColor Yellow
}

# 安装依赖
Write-Host "安装项目依赖..."
try {
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Host "依赖安装成功！" -ForegroundColor Green
        Write-Host "现在可以运行 SetOpsUI.py 启动应用" -ForegroundColor Green
    } else {
        Write-Host "错误: 依赖安装失败" -ForegroundColor Red
        Write-Host "请检查网络连接并重试" -ForegroundColor Yellow
        Read-Host "按任意键退出..."
        exit 1
    }
} catch {
    Write-Host "错误: 依赖安装失败: $_" -ForegroundColor Red
    Read-Host "按任意键退出..."
    exit 1
}

Read-Host "按任意键退出..."
