# HiCRM项目Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down

# 默认目标
help:
	@echo "HiCRM - 对话式智能CRM系统"
	@echo ""
	@echo "可用命令:"
	@echo "  install     安装项目依赖"
	@echo "  dev         启动开发服务器"
	@echo "  test        运行测试"
	@echo "  lint        代码质量检查"
	@echo "  format      代码格式化"
	@echo "  clean       清理临时文件"
	@echo "  docker-build 构建Docker镜像"
	@echo "  docker-up   启动Docker服务"
	@echo "  docker-down 停止Docker服务"

# 安装依赖
install:
	pip install -r requirements.txt
	pip install -e .

# 启动开发服务器
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 运行测试
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# 代码质量检查
lint:
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/

# 代码格式化
format:
	black src/ tests/
	isort src/ tests/

# 清理临时文件
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker相关命令
docker-build:
	docker build -t hicrm:latest .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# 数据库迁移
migrate:
	alembic upgrade head

# 创建新的数据库迁移
migration:
	alembic revision --autogenerate -m "$(msg)"

# 初始化数据库
init-db:
	python -c "from src.core.database import init_db; import asyncio; asyncio.run(init_db())"

# 验证配置
validate-config:
	python scripts/validate_config.py

# 检查环境
check-env:
	@echo "检查环境配置..."
	@python -c "from src.core.config import settings; print(f'应用: {settings.APP_NAME} v{settings.VERSION}'); print(f'环境: {'开发' if settings.DEBUG else '生产'}'); print(f'数据库: {settings.DATABASE_URL}'); print(f'LLM: {'已配置' if settings.openai_configured else '未配置'}')"