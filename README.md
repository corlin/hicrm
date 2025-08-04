# 对话式智能CRM系统 (HiCRM)

基于大语言模型(LLM)和检索增强生成(RAG)技术的智能客户关系管理平台，通过多专业Agent协作实现CRM全生命周期的智能化管理。

## 🚀 项目概述

HiCRM将传统CRM的数据管理能力与现代AI的理解、推理和生成能力深度融合，为用户提供自然语言交互界面，并在每个业务环节提供基于知识库和最佳实践的智能决策支持。

### 核心特性

- 🤖 **多专业Agent协作** - 8个专业AI助手覆盖销售、市场、产品、管理等领域
- 💬 **对话式交互** - 所有功能都通过自然语言对话实现
- 🧠 **智能决策支持** - 基于RAG技术的知识增强和最佳实践推荐
- 🎯 **中文优化** - 专门针对中文场景优化的AI模型和算法
- 📊 **全流程覆盖** - 从客户发现到客户成功的端到端智能化管理

## 🏗️ 技术架构

### 核心技术栈

- **后端**: Python 3.11+ + FastAPI + SQLAlchemy + Pydantic
- **AI/ML**: LangGraph + LangChain + BGE-M3 + BGE-reranker-v2-m3
- **LLM**: OpenAI兼容API (支持Qwen2.5、GLM-4、DeepSeek等中文模型)
- **向量数据库**: Qdrant
- **前端**: React 18 + TypeScript + Shadcn/ui + Tailwind CSS
- **基础设施**: Kubernetes + Kong + ELK + Prometheus

### 架构层次

```
用户交互层 (对话式UI + RESTful API + WebSocket)
    ↓
AI服务层 (LLM + NLU/NLG + RAG)
    ↓
Agent协作层 (8个专业Agent + 任务编排)
    ↓
知识管理层 (知识库 + 向量存储 + 嵌入服务)
    ↓
业务逻辑层 (客户管理 + 线索管理 + 机会管理)
    ↓
数据层 (PostgreSQL + Redis + 消息队列)
```

## 🎯 专业Agent体系

| Agent | 专业领域 | 核心能力 |
|-------|---------|---------|
| 销售Agent | 销售流程、客户关系、谈判技巧 | 客户开发、机会推进、成交管理 |
| 市场Agent | 市场分析、线索管理、营销策略 | 线索评估、市场洞察、竞争分析 |
| 产品Agent | 产品知识、技术方案、实施交付 | 方案匹配、技术支持、实施规划 |
| 销售管理Agent | 团队管理、绩效分析、资源配置 | 团队优化、目标管理、流程改进 |
| 客户成功Agent | 客户满意度、续约管理、价值实现 | 健康度监控、续约策略、价值挖掘 |
| 管理策略Agent | 战略分析、业务洞察、决策支持 | 数据分析、趋势预测、战略建议 |
| CRM专家Agent | CRM最佳实践、流程优化、知识管理 | 流程指导、知识整合、质量控制 |
| 系统管理Agent | 系统运维、安全管理、集成配置 | 系统监控、安全防护、集成管理 |

## 📋 功能特性

### 🔍 智能客户发现与接触管理
- 基于AI的潜在客户识别和筛选
- 个性化拜访计划和话术生成
- 多模态数据分析识别高价值客户

### 🎯 智能线索管理
- 多渠道线索自动收集和分析
- 基于LLM的智能评分和动态分配
- Agent协作的跨渠道线索整合

### 📈 销售漏斗智能管理
- 阶段化销售机会管理
- 基于最佳实践的推进策略
- 智能风险预警和突破建议

### 🤝 成交与交付协调
- 多Agent协作的成交管理
- 智能化交付方案生成
- 合同执行监控和问题处理

### 💎 客户成功与价值最大化
- 客户健康度实时监控
- 复购机会智能识别
- 个性化续约策略生成

### 💬 动态话术生成
- 实时个性化话术指导
- 基于客户画像的沟通策略
- 多Agent协作的全方位沟通支持

### 📊 智能业务分析
- 深度业务洞察和预测分析
- 根因分析和改进策略
- 团队优化和资源配置建议

## 📚 项目文档

- [需求文档](.kiro/specs/conversational-crm/requirements.md) - 11个核心需求和55个验收标准
- [设计文档](.kiro/specs/conversational-crm/design.md) - 完整的技术架构和组件设计
- [任务列表](.kiro/specs/conversational-crm/tasks.md) - 42个具体开发任务和实施计划
- [一致性检查](.kiro/specs/conversational-crm/consistency-review.md) - 文档质量保证报告

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker & Kubernetes (生产环境)

### 开发环境搭建

```bash
# 克隆项目
git clone https://github.com/corlin/hicrm.git
cd hicrm

# 后端环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 前端环境
cd frontend
npm install
npm run dev

# 启动服务
cd ..
uvicorn main:app --reload
```

### 配置说明

1. **LLM配置**: 配置OpenAI兼容API端点和密钥
2. **向量数据库**: 部署Qdrant实例并配置连接
3. **知识库**: 初始化CRM知识库和最佳实践库
4. **Agent配置**: 配置8个专业Agent的参数和知识库

## 🛣️ 开发路线图

### Phase 1: 基础架构 (1-2个月)
- [ ] 项目基础设施搭建
- [ ] 核心数据模型实现
- [ ] LLM服务集成
- [ ] RAG知识增强系统

### Phase 2: Agent系统 (2-3个月)
- [ ] 基础Agent架构
- [ ] 8个专业Agent实现
- [ ] Agent协作机制
- [ ] 对话式用户界面

### Phase 3: 业务集成 (2-3个月)
- [ ] 业务流程集成
- [ ] 数据分析报告
- [ ] 系统集成与安全
- [ ] 性能优化

### Phase 4: 部署上线 (1个月)
- [ ] 测试与质量保证
- [ ] 知识库初始化
- [ ] 用户培训与文档
- [ ] 生产环境部署

## 🤝 贡献指南

我们欢迎社区贡献！请查看以下指南：

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- 项目维护者: [corlin](https://github.com/corlin)
- 项目地址: [https://github.com/corlin/hicrm](https://github.com/corlin/hicrm)
- 问题反馈: [Issues](https://github.com/corlin/hicrm/issues)

---

⭐ 如果这个项目对你有帮助，请给我们一个星标！