# Conversational CRM Makefile
# 使用 uv 进行 Python 项目管理

.PHONY: help install dev-install test lint format clean run docker-build docker-run

# 默认目标
help:
	@echo "Conversational CRM - 智能对话式CRM系统"
	@echo ""
	@echo "可用命令:"
	@echo "  install      - 安装生产依赖"
	@echo "  dev-install  - 安装开发依赖"
	@echo "  test         - 运行测试"
	@echo "  test-cov     - 运行测试并生成覆盖率报告"
	@echo "  lint         - 运行代码检查"
	@echo "  format       - 格式化代码"
	@echo "  type-check   - 运行类型检查"
	@echo "  clean        - 清理缓存和临时文件"
	@echo "  run          - 启动开发服务器"
	@echo "  run-prod     - 启动生产服务器"
	@echo "  docker-build - 构建Docker镜像"
	@echo "  docker-run   - 运行Docker容器"
	@echo "  migrate      - 运行数据库迁移"
	@echo "  seed         - 初始化种子数据"

# Python 和 uv 检查
check-uv:
	@which uv > /dev/null || (echo "请先安装 uv: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)

# 安装依赖
install: check-uv
	uv sync --frozen

# 安装开发依赖
dev-install: check-uv
	uv sync --all-extras --dev

# 运行测试
test: check-uv
	uv run pytest tests/ -v

# 运行测试并生成覆盖率报告
test-cov: check-uv
	uv run pytest tests/ --cov=src --cov-report=html --cov-report=term-missing -v

# 运行集成测试
test-integration: check-uv
	uv run pytest tests/ -m integration -v

# 运行单元测试
test-unit: check-uv
	uv run pytest tests/ -m "not integration" -v

# 代码检查
lint: check-uv
	uv run flake8 src tests
	uv run ruff check src tests

# 格式化代码
format: check-uv
	uv run black src tests
	uv run isort src tests
	uv run ruff format src tests

# 类型检查
type-check: check-uv
	uv run mypy src

# 代码质量检查（全套）
quality: format lint type-check test

# 清理缓存和临时文件
clean:
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 启动开发服务器
run: check-uv
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 启动生产服务器
run-prod: check-uv
	uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 数据库迁移
migrate: check-uv
	uv run alembic upgrade head

# 创建新的迁移
migrate-create: check-uv
	@read -p "迁移描述: " desc; \
	uv run alembic revision --autogenerate -m "$$desc"

# 初始化数据库
init-db: check-uv
	uv run python -m src.scripts.init_db

# 初始化种子数据
seed: check-uv
	uv run python -m src.scripts.seed_data

# 启动所有服务（开发环境）
dev-services:
	docker-compose -f docker-compose.dev.yml up -d

# 停止所有服务
stop-services:
	docker-compose -f docker-compose.dev.yml down

# 构建Docker镜像
docker-build:
	docker build -t conversational-crm:latest .

# 运行Docker容器
docker-run:
	docker run -p 8000:8000 --env-file .env conversational-crm:latest

# 生成API文档
docs: check-uv
	uv run mkdocs build

# 启动文档服务器
docs-serve: check-uv
	uv run mkdocs serve

# 安装pre-commit钩子
pre-commit-install: check-uv
	uv run pre-commit install

# 运行pre-commit检查
pre-commit: check-uv
	uv run pre-commit run --all-files

# 更新依赖
update: check-uv
	uv sync --upgrade

# 锁定依赖版本
lock: check-uv
	uv lock

# 导出requirements.txt（用于Docker等）
export-requirements: check-uv
	uv export --format requirements-txt --output-file requirements.txt
	uv export --format requirements-txt --all-extras --dev --output-file requirements-dev.txt

# 安全检查
security: check-uv
	uv run safety check
	uv run bandit -r src/

# 性能测试
perf-test: check-uv
	uv run locust -f tests/performance/locustfile.py --host=http://localhost:8000

# 完整的CI检查
ci: dev-install quality test-cov security

# 项目初始化（首次设置）
init: check-uv dev-install pre-commit-install init-db seed
	@echo "项目初始化完成！"
	@echo "运行 'make run' 启动开发服务器"

# 生产部署准备
deploy-prep: clean quality test export-requirements docker-build
	@echo "生产部署准备完成！"

# 显示项目信息
info:
	@echo "项目: Conversational CRM"
	@echo "Python版本: $(shell python --version)"
	@echo "UV版本: $(shell uv --version)"
	@echo "虚拟环境: $(shell uv venv list)"
	@echo "依赖数量: $(shell uv pip list | wc -l)"

# 健康检查
health:
	@curl -f http://localhost:8000/health || echo "服务未运行"

# 查看日志
logs:
	docker-compose -f docker-compose.dev.yml logs -f

# 进入容器shell
shell:
	docker-compose -f docker-compose.dev.yml exec app bash

# 数据库shell
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres -d crm_db