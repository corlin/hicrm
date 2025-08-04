#!/bin/bash
# 从pip迁移到UV的脚本

set -e

echo "🔄 开始迁移到UV包管理..."

# 检查UV是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ UV未安装，正在安装..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

echo "✅ UV已安装"

# 备份现有的requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 备份现有的requirements.txt..."
    cp requirements.txt requirements.txt.backup
fi

# 如果存在虚拟环境，先删除
if [ -d ".venv" ]; then
    echo "🗑️  删除现有虚拟环境..."
    rm -rf .venv
fi

if [ -d "venv" ]; then
    echo "🗑️  删除现有虚拟环境..."
    rm -rf venv
fi

# 初始化UV项目（如果pyproject.toml不存在）
if [ ! -f "pyproject.toml" ]; then
    echo "📝 创建pyproject.toml..."
    uv init --lib
fi

# 从requirements.txt导入依赖（如果存在）
if [ -f "requirements.txt.backup" ]; then
    echo "📥 从requirements.txt导入依赖..."
    
    # 读取requirements.txt并添加到pyproject.toml
    while IFS= read -r line; do
        # 跳过注释和空行
        if [[ ! "$line" =~ ^[[:space:]]*# ]] && [[ -n "$line" ]]; then
            # 移除行内注释
            package=$(echo "$line" | sed 's/#.*//' | xargs)
            if [[ -n "$package" ]]; then
                echo "  添加包: $package"
                uv add "$package" || echo "    ⚠️  无法添加 $package，请手动检查"
            fi
        fi
    done < requirements.txt.backup
fi

# 同步依赖
echo "🔄 同步依赖..."
uv sync --all-extras

# 创建.python-version文件
echo "🐍 设置Python版本..."
echo "3.11" > .python-version

# 更新.gitignore
echo "📝 更新.gitignore..."
if [ -f ".gitignore" ]; then
    # 添加UV相关的忽略项
    if ! grep -q ".venv" .gitignore; then
        echo ".venv/" >> .gitignore
    fi
    if ! grep -q "uv.lock" .gitignore; then
        echo "# UV lock file is committed" >> .gitignore
    fi
    if ! grep -q ".uv-cache" .gitignore; then
        echo ".uv-cache/" >> .gitignore
    fi
else
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# UV
.uv-cache/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Environment variables
.env
.env.local

# Database
*.db
*.sqlite3

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Documentation
docs/_build/
EOF
fi

# 安装pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 安装pre-commit hooks..."
    uv run pre-commit install
fi

# 运行测试验证迁移
echo "🧪 运行测试验证迁移..."
if [ -f "tests/test_completed_tasks.py" ]; then
    uv run python tests/test_completed_tasks.py
else
    echo "⚠️  未找到测试文件，跳过测试验证"
fi

echo "🎉 迁移到UV完成！"
echo ""
echo "📋 迁移后的变化:"
echo "1. ✅ 创建了pyproject.toml配置文件"
echo "2. ✅ 使用UV管理依赖"
echo "3. ✅ 创建了.venv虚拟环境"
echo "4. ✅ 更新了.gitignore文件"
echo "5. ✅ 备份了原始requirements.txt"
echo ""
echo "📚 常用UV命令:"
echo "  uv sync              # 同步依赖"
echo "  uv add <package>     # 添加依赖"
echo "  uv remove <package>  # 移除依赖"
echo "  uv run <command>     # 运行命令"
echo "  uv lock --upgrade    # 更新锁文件"
echo ""
echo "🚀 下一步:"
echo "1. 检查pyproject.toml中的依赖配置"
echo "2. 运行 'uv run uvicorn src.main:app --reload' 启动开发服务器"
echo "3. 运行 'uv run pytest' 执行测试"
echo "4. 删除requirements.txt.backup（如果确认迁移成功）"