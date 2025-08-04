#!/bin/bash
# 开发环境设置脚本

set -e

echo "🚀 设置 HiCRM 开发环境..."

# 检查 UV 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ UV 未安装，请先安装 UV:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "或者访问: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "✅ UV 已安装"

# 创建虚拟环境并安装依赖
echo "📦 创建虚拟环境并安装依赖..."
uv sync --all-extras

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 安装 pre-commit hooks
echo "🪝 安装 pre-commit hooks..."
uv run pre-commit install

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p data
mkdir -p uploads
mkdir -p .uv-cache

# 复制环境变量模板
if [ ! -f .env ]; then
    echo "📝 创建环境变量文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置必要的环境变量"
fi

# 运行数据库迁移（如果需要）
echo "🗄️  初始化数据库..."
# uv run alembic upgrade head

# 运行测试确保环境正常
echo "🧪 运行测试验证环境..."
uv run pytest tests/test_completed_tasks.py -v

echo "🎉 开发环境设置完成！"
echo ""
echo "📋 下一步操作:"
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 启动开发服务器: uv run uvicorn src.main:app --reload"
echo "3. 运行测试: uv run pytest"
echo "4. 代码格式化: uv run black src tests"
echo "5. 类型检查: uv run mypy src"
echo ""
echo "📚 更多命令请查看 Makefile 或运行 make help"