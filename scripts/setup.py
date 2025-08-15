#!/usr/bin/env python3
"""
项目设置脚本
使用 uv 进行项目初始化和配置
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """运行命令并返回结果"""
    print(f"执行: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"命令执行失败: {cmd}")
        print(f"错误输出: {result.stderr}")
        sys.exit(1)
    
    return result


def check_uv_installed():
    """检查 uv 是否已安装"""
    if not shutil.which("uv"):
        print("uv 未安装，正在安装...")
        install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        run_command(install_cmd)
        
        # 重新加载环境变量
        os.environ["PATH"] = f"{os.path.expanduser('~/.cargo/bin')}:{os.environ['PATH']}"
        
        if not shutil.which("uv"):
            print("uv 安装失败，请手动安装")
            sys.exit(1)
    
    print("✓ uv 已安装")


def setup_python_version():
    """设置 Python 版本"""
    print("设置 Python 版本...")
    run_command("uv python install 3.11")
    run_command("uv python pin 3.11")
    print("✓ Python 版本设置完成")


def install_dependencies():
    """安装项目依赖"""
    print("安装项目依赖...")
    run_command("uv sync --all-extras --dev")
    print("✓ 依赖安装完成")


def setup_pre_commit():
    """设置 pre-commit 钩子"""
    print("设置 pre-commit 钩子...")
    run_command("uv run pre-commit install")
    print("✓ pre-commit 钩子设置完成")


def create_env_file():
    """创建环境变量文件"""
    env_file = Path(".env")
    if not env_file.exists():
        print("创建 .env 文件...")
        env_content = """# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_db
REDIS_URL=redis://localhost:6379/0
RABBITMQ_URL=amqp://guest:guest@localhost:5672/

# 向量数据库
QDRANT_URL=http://localhost:6333

# AI 服务配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 中文模型配置（可选）
ZHIPU_API_KEY=your_zhipu_api_key_here
QWEN_API_KEY=your_qwen_api_key_here

# 应用配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 环境配置
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# 服务配置
HOST=0.0.0.0
PORT=8000
WORKERS=1

# 文件存储
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760  # 10MB
"""
        env_file.write_text(env_content)
        print("✓ .env 文件创建完成")
    else:
        print("✓ .env 文件已存在")


def setup_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "uploads",
        "data",
        "backups",
        "monitoring/prometheus",
        "monitoring/grafana/dashboards",
        "monitoring/grafana/datasources",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ 目录结构创建完成")


def check_services():
    """检查必要的服务是否运行"""
    services = {
        "PostgreSQL": ("pg_isready", "请启动 PostgreSQL 服务"),
        "Redis": ("redis-cli ping", "请启动 Redis 服务"),
    }
    
    print("检查服务状态...")
    for service, (cmd, msg) in services.items():
        result = run_command(cmd, check=False)
        if result.returncode == 0:
            print(f"✓ {service} 运行正常")
        else:
            print(f"⚠ {service} 未运行 - {msg}")


def main():
    """主函数"""
    print("🚀 开始设置 Conversational CRM 项目...")
    print("=" * 50)
    
    # 检查并安装 uv
    check_uv_installed()
    
    # 设置 Python 版本
    setup_python_version()
    
    # 安装依赖
    install_dependencies()
    
    # 创建环境文件
    create_env_file()
    
    # 设置目录结构
    setup_directories()
    
    # 设置 pre-commit
    setup_pre_commit()
    
    # 检查服务
    check_services()
    
    print("=" * 50)
    print("✅ 项目设置完成！")
    print()
    print("下一步:")
    print("1. 编辑 .env 文件，配置你的 API 密钥和数据库连接")
    print("2. 启动服务: make dev-services")
    print("3. 运行数据库迁移: make migrate")
    print("4. 初始化种子数据: make seed")
    print("5. 启动开发服务器: make run")
    print()
    print("更多命令请运行: make help")


if __name__ == "__main__":
    main()