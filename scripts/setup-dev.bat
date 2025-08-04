@echo off
REM Windows 开发环境设置脚本

echo 🚀 设置 HiCRM 开发环境...

REM 检查 UV 是否安装
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ UV 未安装，请先安装 UV:
    echo powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo 或者访问: https://docs.astral.sh/uv/getting-started/installation/
    exit /b 1
)

echo ✅ UV 已安装

REM 创建虚拟环境并安装依赖
echo 📦 创建虚拟环境并安装依赖...
uv sync --all-extras

REM 安装 pre-commit hooks
echo 🪝 安装 pre-commit hooks...
uv run pre-commit install

REM 创建必要的目录
echo 📁 创建必要的目录...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist uploads mkdir uploads
if not exist .uv-cache mkdir .uv-cache

REM 复制环境变量模板
if not exist .env (
    echo 📝 创建环境变量文件...
    copy .env.example .env
    echo ⚠️  请编辑 .env 文件配置必要的环境变量
)

REM 运行测试确保环境正常
echo 🧪 运行测试验证环境...
uv run pytest tests/test_completed_tasks.py -v

echo 🎉 开发环境设置完成！
echo.
echo 📋 下一步操作:
echo 1. 编辑 .env 文件配置环境变量
echo 2. 启动开发服务器: uv run uvicorn src.main:app --reload
echo 3. 运行测试: uv run pytest
echo 4. 代码格式化: uv run black src tests
echo 5. 类型检查: uv run mypy src
echo.
echo 📚 更多命令请查看 Makefile 或运行 make help