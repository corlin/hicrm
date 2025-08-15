# Conversational CRM - 智能对话式CRM系统

基于多Agent架构的智能客户关系管理平台，使用现代Python技术栈和AI技术构建。

## 🚀 特性

- **多Agent架构**: 销售、市场、产品、客户成功等专业Agent协作
- **智能对话**: 基于大语言模型的自然语言交互
- **知识增强**: RAG技术提供智能知识检索和问答
- **实时通信**: WebSocket支持的实时消息推送
- **工作流自动化**: 客户发现、线索管理、销售漏斗自动化
- **现代技术栈**: FastAPI + SQLAlchemy + PostgreSQL + Redis + Qdrant

## 🛠️ 技术栈

### 后端
- **Web框架**: FastAPI
- **数据库**: PostgreSQL + SQLAlchemy
- **缓存**: Redis
- **消息队列**: RabbitMQ
- **向量数据库**: Qdrant
- **AI框架**: LangChain + LangGraph
- **嵌入模型**: BGE-M3 (中英文)
- **重排序**: BGE-reranker-v2-m3

### 前端
- **框架**: React + TypeScript
- **样式**: Tailwind CSS
- **组件库**: Shadcn/ui
- **实时通信**: WebSocket

### 开发工具
- **包管理**: uv (超快的Python包管理器)
- **代码质量**: Black + isort + Ruff + MyPy
- **测试**: pytest + pytest-asyncio
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## 📋 系统要求

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (可选)

## 🚀 快速开始

### 1. 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用包管理器
brew install uv  # macOS
pip install uv   # 任何平台
```

### 2. 克隆项目

```bash
git clone https://github.com/company/conversational-crm.git
cd conversational-crm
```

### 3. 自动化设置

```bash
# 运行设置脚本（推荐）
python scripts/setup.py

# 或手动设置
make init
```

### 4. 配置环境变量

编辑 `.env` 文件，配置你的API密钥和数据库连接：

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/crm_db

# AI服务配置
OPENAI_API_KEY=your_openai_api_key_here
# 或使用中文模型
ZHIPU_API_KEY=your_zhipu_api_key_here
QWEN_API_KEY=your_qwen_api_key_here
```

### 5. 启动服务

```bash
# 启动所有依赖服务
make dev-services

# 运行数据库迁移
make migrate

# 初始化种子数据
make seed

# 启动开发服务器
make run
```

### 6. 访问应用

- **API文档**: http://localhost:8000/docs
- **应用界面**: http://localhost:8000
- **Grafana监控**: http://localhost:3000 (admin/admin)
- **RabbitMQ管理**: http://localhost:15672 (guest/guest)

## 🔧 开发指南

### 使用 uv 管理依赖

```bash
# 安装依赖
uv sync                    # 生产依赖
uv sync --dev             # 包含开发依赖
uv sync --all-extras      # 包含所有可选依赖

# 添加新依赖
uv add fastapi            # 添加生产依赖
uv add --dev pytest       # 添加开发依赖
uv add --optional prod gunicorn  # 添加可选依赖

# 更新依赖
uv sync --upgrade         # 更新所有依赖
uv add --upgrade fastapi  # 更新特定依赖

# 运行命令
uv run python script.py   # 在虚拟环境中运行
uv run pytest            # 运行测试
uv run uvicorn src.main:app --reload  # 启动服务器
```

### 常用命令

```bash
# 开发
make run                  # 启动开发服务器
make test                 # 运行测试
make test-cov            # 运行测试并生成覆盖率报告
make lint                # 代码检查
make format              # 代码格式化
make type-check          # 类型检查

# 数据库
make migrate             # 运行迁移
make migrate-create      # 创建新迁移
make seed                # 初始化种子数据

# Docker
make docker-build        # 构建镜像
make docker-run          # 运行容器
make dev-services        # 启动开发服务
make stop-services       # 停止服务

# 部署
make deploy-prep         # 生产部署准备
make ci                  # 完整CI检查
```

### 项目结构

```
conversational-crm/
├── src/                          # 源代码
│   ├── agents/                   # Agent实现
│   │   ├── base.py              # 基础Agent类
│   │   ├── professional/        # 专业Agent
│   │   ├── manager.py           # Agent管理器
│   │   └── communication.py     # Agent通信
│   ├── api/                     # API路由
│   ├── core/                    # 核心配置
│   ├── models/                  # 数据模型
│   ├── schemas/                 # Pydantic模式
│   ├── services/                # 业务服务
│   ├── workflows/               # 业务流程
│   ├── websocket/               # WebSocket支持
│   └── main.py                  # 应用入口
├── tests/                       # 测试代码
├── frontend/                    # 前端代码
├── alembic/                     # 数据库迁移
├── scripts/                     # 工具脚本
├── monitoring/                  # 监控配置
├── pyproject.toml              # 项目配置
├── uv.toml                     # uv配置
├── Makefile                    # 构建脚本
└── docker-compose.dev.yml      # 开发环境
```

## 🧪 测试

```bash
# 运行所有测试
make test

# 运行特定测试
uv run pytest tests/test_agents/ -v

# 运行集成测试
make test-integration

# 生成覆盖率报告
make test-cov

# 性能测试
make perf-test
```

## 📊 监控

项目集成了完整的监控栈：

- **Prometheus**: 指标收集
- **Grafana**: 可视化仪表板
- **Jaeger**: 分布式追踪
- **结构化日志**: 使用 structlog

## 🚀 部署

### Docker部署

```bash
# 构建镜像
make docker-build

# 运行容器
make docker-run
```

### Kubernetes部署

```bash
# 应用Kubernetes配置
kubectl apply -f k8s/
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

### 代码规范

项目使用以下工具确保代码质量：

- **Black**: 代码格式化
- **isort**: Import排序
- **Ruff**: 快速代码检查
- **MyPy**: 类型检查
- **pre-commit**: Git钩子

## 📝 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

- 📖 [文档](https://docs.crm.com)
- 🐛 [问题反馈](https://github.com/company/conversational-crm/issues)
- 💬 [讨论区](https://github.com/company/conversational-crm/discussions)

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [LangChain](https://langchain.com/) - AI应用开发框架
- [uv](https://github.com/astral-sh/uv) - 超快的Python包管理器
- [Qdrant](https://qdrant.tech/) - 向量数据库
- [React](https://reactjs.org/) - 前端框架

---

**使用 uv 构建，为现代Python开发而生 🚀**