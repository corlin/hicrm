# HiCRM 项目 Makefile
# 使用 UV 进行包管理

.PHONY: help install install-dev install-prod test test-unit test-integration test-performance
.PHONY: lint format type-check pre-commit clean build run dev docs docker-build docker-run
.PHONY: db-upgrade db-downgrade db-reset seed-data backup-db

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

help: ## 显示帮助信息
	@echo "$(BLUE)HiCRM 项目管理命令$(RESET)"
	@echo ""
	@echo "$(GREEN)环境管理:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(install|clean|setup)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)开发工具:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(test|lint|format|type|run|dev)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)数据库:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(db-|seed|backup)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)部署:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "(build|docker|docs)" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(RESET) %s\n", $$1, $$2}'

# 环境管理
install: ## 安装生产依赖
	@echo "$(GREEN)安装生产依赖...$(RESET)"
	uv sync --no-dev

install-dev: ## 安装开发依赖
	@echo "$(GREEN)安装开发依赖...$(RESET)"
	uv sync --all-extras

install-prod: ## 安装生产环境依赖
	@echo "$(GREEN)安装生产环境依赖...$(RESET)"
	uv sync --extra prod --no-dev

setup-dev: ## 设置开发环境
	@echo "$(GREEN)设置开发环境...$(RESET)"
	@if [ "$(OS)" = "Windows_NT" ]; then \
		scripts/setup-dev.bat; \
	else \
		chmod +x scripts/setup-dev.sh && scripts/setup-dev.sh; \
	fi

clean: ## 清理缓存和临时文件
	@echo "$(YELLOW)清理缓存和临时文件...$(RESET)"
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	rm -rf .uv-cache
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 测试
test: ## 运行所有测试
	@echo "$(GREEN)运行所有测试...$(RESET)"
	uv run pytest -v

test-unit: ## 运行单元测试
	@echo "$(GREEN)运行单元测试...$(RESET)"
	uv run pytest tests/test_models tests/test_services tests/test_core -v -m "not integration and not performance"

test-integration: ## 运行集成测试
	@echo "$(GREEN)运行集成测试...$(RESET)"
	uv run pytest tests/test_integration -v -m integration

test-performance: ## 运行性能测试
	@echo "$(GREEN)运行性能测试...$(RESET)"
	uv run pytest tests/test_performance -v -m performance -s

test-ai: ## 运行AI相关测试
	@echo "$(GREEN)运行AI相关测试...$(RESET)"
	uv run pytest -v -m ai

test-coverage: ## 运行测试并生成覆盖率报告
	@echo "$(GREEN)运行测试并生成覆盖率报告...$(RESET)"
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

test-watch: ## 监控文件变化并自动运行测试
	@echo "$(GREEN)监控测试...$(RESET)"
	uv run pytest-watch

# 代码质量
lint: ## 运行代码检查
	@echo "$(GREEN)运行代码检查...$(RESET)"
	uv run ruff check src tests
	uv run flake8 src tests

format: ## 格式化代码
	@echo "$(GREEN)格式化代码...$(RESET)"
	uv run black src tests
	uv run isort src tests
	uv run ruff format src tests

type-check: ## 类型检查
	@echo "$(GREEN)运行类型检查...$(RESET)"
	uv run mypy src

pre-commit: ## 运行pre-commit检查
	@echo "$(GREEN)运行pre-commit检查...$(RESET)"
	uv run pre-commit run --all-files

check-all: lint type-check test ## 运行所有检查

# 运行服务
run: ## 运行生产服务器
	@echo "$(GREEN)启动生产服务器...$(RESET)"
	uv run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker

dev: ## 运行开发服务器
	@echo "$(GREEN)启动开发服务器...$(RESET)"
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-debug: ## 运行调试模式开发服务器
	@echo "$(GREEN)启动调试模式开发服务器...$(RESET)"
	uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug

# 数据库管理
db-upgrade: ## 升级数据库到最新版本
	@echo "$(GREEN)升级数据库...$(RESET)"
	uv run alembic upgrade head

db-downgrade: ## 降级数据库一个版本
	@echo "$(YELLOW)降级数据库...$(RESET)"
	uv run alembic downgrade -1

db-reset: ## 重置数据库
	@echo "$(RED)重置数据库...$(RESET)"
	uv run alembic downgrade base
	uv run alembic upgrade head

db-revision: ## 创建新的数据库迁移
	@echo "$(GREEN)创建数据库迁移...$(RESET)"
	@read -p "迁移描述: " desc; \
	uv run alembic revision --autogenerate -m "$$desc"

seed-data: ## 填充测试数据
	@echo "$(GREEN)填充测试数据...$(RESET)"
	uv run python scripts/seed_data.py

backup-db: ## 备份数据库
	@echo "$(GREEN)备份数据库...$(RESET)"
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	uv run python scripts/backup_db.py backups/backup_$$timestamp.sql

# 构建和部署
build: ## 构建项目
	@echo "$(GREEN)构建项目...$(RESET)"
	uv build

docker-build: ## 构建Docker镜像
	@echo "$(GREEN)构建Docker镜像...$(RESET)"
	docker build -t hicrm:latest .

docker-run: ## 运行Docker容器
	@echo "$(GREEN)运行Docker容器...$(RESET)"
	docker-compose up -d

docker-dev: ## 运行开发环境Docker
	@echo "$(GREEN)运行开发环境Docker...$(RESET)"
	docker-compose -f docker-compose.dev.yml up

docker-stop: ## 停止Docker容器
	@echo "$(YELLOW)停止Docker容器...$(RESET)"
	docker-compose down

docker-logs: ## 查看Docker日志
	@echo "$(GREEN)查看Docker日志...$(RESET)"
	docker-compose logs -f

# 文档
docs: ## 构建文档
	@echo "$(GREEN)构建文档...$(RESET)"
	uv run mkdocs build

docs-serve: ## 启动文档服务器
	@echo "$(GREEN)启动文档服务器...$(RESET)"
	uv run mkdocs serve

docs-deploy: ## 部署文档
	@echo "$(GREEN)部署文档...$(RESET)"
	uv run mkdocs gh-deploy

# 安全检查
security-check: ## 运行安全检查
	@echo "$(GREEN)运行安全检查...$(RESET)"
	uv run safety check
	uv run bandit -r src

# 依赖管理
deps-update: ## 更新依赖
	@echo "$(GREEN)更新依赖...$(RESET)"
	uv lock --upgrade

deps-audit: ## 审计依赖安全性
	@echo "$(GREEN)审计依赖安全性...$(RESET)"
	uv run pip-audit

deps-tree: ## 显示依赖树
	@echo "$(GREEN)显示依赖树...$(RESET)"
	uv tree

# 性能分析
profile: ## 性能分析
	@echo "$(GREEN)运行性能分析...$(RESET)"
	uv run python -m cProfile -o profile.stats src/main.py

benchmark: ## 运行基准测试
	@echo "$(GREEN)运行基准测试...$(RESET)"
	uv run pytest tests/test_performance/test_load_testing.py -v --benchmark-only

# 版本管理
version-patch: ## 升级补丁版本
	@echo "$(GREEN)升级补丁版本...$(RESET)"
	uv run bump2version patch

version-minor: ## 升级次版本
	@echo "$(GREEN)升级次版本...$(RESET)"
	uv run bump2version minor

version-major: ## 升级主版本
	@echo "$(GREEN)升级主版本...$(RESET)"
	uv run bump2version major

# 快速命令别名
t: test ## 测试别名
f: format ## 格式化别名
l: lint ## 检查别名
d: dev ## 开发服务器别名
c: clean ## 清理别名