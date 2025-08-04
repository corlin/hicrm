# UV 包管理命令参考

## 基础命令

### 项目初始化
```bash
# 初始化新项目
uv init hicrm

# 从现有项目初始化
uv init --lib hicrm
```

### 依赖管理
```bash
# 安装所有依赖
uv sync

# 安装开发依赖
uv sync --all-extras

# 安装特定额外依赖
uv sync --extra dev --extra test

# 只安装生产依赖
uv sync --no-dev

# 更新锁文件
uv lock

# 更新所有依赖到最新版本
uv lock --upgrade

# 更新特定包
uv lock --upgrade-package fastapi
```

### 包安装
```bash
# 添加新依赖
uv add fastapi

# 添加开发依赖
uv add --dev pytest

# 添加可选依赖
uv add --optional ai sentence-transformers

# 添加特定版本
uv add "fastapi>=0.104.0,<0.105.0"

# 从Git安装
uv add git+https://github.com/user/repo.git

# 移除依赖
uv remove fastapi
```

### 运行命令
```bash
# 运行Python脚本
uv run python src/main.py

# 运行模块
uv run -m pytest

# 运行已安装的命令
uv run uvicorn src.main:app --reload

# 运行带参数的命令
uv run pytest tests/ -v --cov=src
```

### 虚拟环境管理
```bash
# 创建虚拟环境
uv venv

# 指定Python版本创建
uv venv --python 3.11

# 激活虚拟环境 (Linux/Mac)
source .venv/bin/activate

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 查看虚拟环境信息
uv venv --show
```

## 高级用法

### 工作空间管理
```bash
# 在工作空间中同步所有项目
uv sync --workspace

# 构建工作空间中的所有包
uv build --workspace
```

### 缓存管理
```bash
# 清理缓存
uv cache clean

# 查看缓存大小
uv cache dir

# 清理特定包的缓存
uv cache clean fastapi
```

### 工具运行
```bash
# 运行一次性工具
uvx black src/

# 安装并运行工具
uvx --from black black src/

# 运行特定版本的工具
uvx --from "black==23.11.0" black src/
```

### 构建和发布
```bash
# 构建包
uv build

# 构建wheel
uv build --wheel

# 构建源码分发
uv build --sdist

# 发布到PyPI
uv publish

# 发布到测试PyPI
uv publish --repository testpypi
```

## 项目特定命令

### 开发环境
```bash
# 设置开发环境
make setup-dev
# 或
uv sync --all-extras && uv run pre-commit install

# 运行开发服务器
make dev
# 或
uv run uvicorn src.main:app --reload
```

### 测试
```bash
# 运行所有测试
make test
# 或
uv run pytest

# 运行特定测试
uv run pytest tests/test_models/

# 运行带覆盖率的测试
uv run pytest --cov=src --cov-report=html
```

### 代码质量
```bash
# 格式化代码
make format
# 或
uv run black src tests && uv run isort src tests

# 代码检查
make lint
# 或
uv run ruff check src tests

# 类型检查
make type-check
# 或
uv run mypy src
```

### 数据库操作
```bash
# 数据库迁移
uv run alembic upgrade head

# 创建迁移
uv run alembic revision --autogenerate -m "description"

# 回滚迁移
uv run alembic downgrade -1
```

## 配置文件

### pyproject.toml 配置
```toml
[tool.uv]
dev-dependencies = [
    "pytest>=7.4.3",
    "black>=23.11.0",
]

# 指定Python版本
python = ">=3.11"

# 索引配置
index-url = "https://pypi.org/simple"
```

### 环境变量
```bash
# 设置索引URL
export UV_INDEX_URL="https://pypi.org/simple"

# 设置缓存目录
export UV_CACHE_DIR=".uv-cache"

# 禁用缓存
export UV_NO_CACHE=1

# 设置并发数
export UV_CONCURRENT_DOWNLOADS=10
```

## 最佳实践

### 1. 依赖管理
- 使用 `uv.lock` 锁定依赖版本
- 定期运行 `uv lock --upgrade` 更新依赖
- 使用可选依赖组织不同环境的依赖

### 2. 开发工作流
```bash
# 每日开发流程
uv sync                    # 同步依赖
uv run pre-commit run --all-files  # 代码检查
uv run pytest            # 运行测试
uv run uvicorn src.main:app --reload  # 启动开发服务器
```

### 3. CI/CD 集成
```yaml
# GitHub Actions 示例
- name: Install uv
  uses: astral-sh/setup-uv@v1

- name: Install dependencies
  run: uv sync --all-extras

- name: Run tests
  run: uv run pytest
```

### 4. Docker 集成
```dockerfile
# 在Dockerfile中使用UV
FROM python:3.11-slim

# 安装UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制项目文件
COPY . /app
WORKDIR /app

# 安装依赖
RUN uv sync --no-dev

# 运行应用
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

## 故障排除

### 常见问题
1. **依赖冲突**: 使用 `uv lock --upgrade` 重新解析依赖
2. **缓存问题**: 使用 `uv cache clean` 清理缓存
3. **Python版本问题**: 检查 `.python-version` 文件
4. **权限问题**: 确保有写入 `.venv` 目录的权限

### 调试命令
```bash
# 显示详细信息
uv --verbose sync

# 显示依赖树
uv tree

# 检查项目配置
uv show

# 验证锁文件
uv lock --check
```