@echo off
REM 从pip迁移到UV的Windows脚本

echo 🔄 开始迁移到UV包管理...

REM 检查UV是否安装
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ UV未安装，正在安装...
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo ❌ UV安装失败，请手动安装
        exit /b 1
    )
)

echo ✅ UV已安装

REM 备份现有的requirements.txt
if exist requirements.txt (
    echo 📦 备份现有的requirements.txt...
    copy requirements.txt requirements.txt.backup
)

REM 删除现有虚拟环境
if exist .venv (
    echo 🗑️  删除现有虚拟环境...
    rmdir /s /q .venv
)

if exist venv (
    echo 🗑️  删除现有虚拟环境...
    rmdir /s /q venv
)

REM 初始化UV项目（如果pyproject.toml不存在）
if not exist pyproject.toml (
    echo 📝 pyproject.toml已存在，跳过初始化...
) else (
    echo 📝 pyproject.toml已存在...
)

REM 同步依赖
echo 🔄 同步依赖...
uv sync --all-extras

REM 创建.python-version文件
echo 🐍 设置Python版本...
echo 3.11 > .python-version

REM 更新.gitignore
echo 📝 更新.gitignore...
if not exist .gitignore (
    echo # Python > .gitignore
    echo __pycache__/ >> .gitignore
    echo *.py[cod] >> .gitignore
    echo *$py.class >> .gitignore
    echo. >> .gitignore
    echo # Virtual Environment >> .gitignore
    echo .venv/ >> .gitignore
    echo venv/ >> .gitignore
    echo. >> .gitignore
    echo # UV >> .gitignore
    echo .uv-cache/ >> .gitignore
    echo. >> .gitignore
    echo # Environment variables >> .gitignore
    echo .env >> .gitignore
    echo .env.local >> .gitignore
)

REM 安装pre-commit hooks
if exist .pre-commit-config.yaml (
    echo 🪝 安装pre-commit hooks...
    uv run pre-commit install
)

REM 运行测试验证迁移
echo 🧪 运行测试验证迁移...
if exist tests\test_completed_tasks.py (
    uv run python tests\test_completed_tasks.py
) else (
    echo ⚠️  未找到测试文件，跳过测试验证
)

echo 🎉 迁移到UV完成！
echo.
echo 📋 迁移后的变化:
echo 1. ✅ 使用现有的pyproject.toml配置文件
echo 2. ✅ 使用UV管理依赖
echo 3. ✅ 创建了.venv虚拟环境
echo 4. ✅ 更新了.gitignore文件
echo.
echo 📚 常用UV命令:
echo   uv sync              # 同步依赖
echo   uv add ^<package^>     # 添加依赖
echo   uv remove ^<package^>  # 移除依赖
echo   uv run ^<command^>     # 运行命令
echo   uv lock --upgrade    # 更新锁文件
echo.
echo 🚀 下一步:
echo 1. 检查pyproject.toml中的依赖配置
echo 2. 运行 'uv run uvicorn src.main:app --reload' 启动开发服务器
echo 3. 运行 'uv run pytest' 执行测试