# 知识库管理系统使用指南
# Knowledge Management System Usage Guide

本指南详细介绍了知识库管理系统的功能、模型和使用方法。

## 📋 目录 (Table of Contents)

1. [系统概述](#系统概述)
2. [核心模型](#核心模型)
3. [主要功能](#主要功能)
4. [使用示例](#使用示例)
5. [API参考](#api参考)
6. [最佳实践](#最佳实践)
7. [故障排除](#故障排除)

## 🎯 系统概述

知识库管理系统是一个完整的企业知识管理解决方案，提供以下核心能力：

- **智能文档解析**: 自动分块和关键词提取
- **质量评估**: 多维度质量指标评估
- **语义搜索**: 基于向量的智能搜索
- **版本管理**: 完整的版本历史追踪
- **使用统计**: 详细的使用分析和统计
- **关系管理**: 知识间的关联关系管理

## 📊 核心模型

### 1. Knowledge (知识实体)

主要的知识实体模型，包含完整的知识信息。

```python
from src.models.knowledge import Knowledge, KnowledgeType, KnowledgeStatus

knowledge = Knowledge(
    title="知识标题",
    content="知识内容",
    type=KnowledgeType.DOCUMENT,
    status=KnowledgeStatus.PUBLISHED,
    metadata=metadata,
    quality=quality_metrics,
    usage=usage_statistics
)
```

**字段说明:**
- `title`: 知识标题
- `content`: 知识内容
- `type`: 知识类型 (DOCUMENT, FAQ, BEST_PRACTICE, TEMPLATE, CASE_STUDY, PROCESS, RULE)
- `status`: 状态 (DRAFT, REVIEW, APPROVED, PUBLISHED, ARCHIVED)
- `chunks`: 文档分块列表
- `metadata`: 元数据信息
- `quality`: 质量评估指标
- `usage`: 使用统计信息
- `relationships`: 关联关系列表
- `categories`: 分类标签
- `version_history`: 版本历史

### 2. KnowledgeMetadata (知识元数据)

存储知识的元信息。

```python
from src.models.knowledge import KnowledgeMetadata

metadata = KnowledgeMetadata(
    source="系统来源",
    author="作者",
    domain="领域分类",
    tags=["标签1", "标签2"],
    language="zh-CN",
    version="1.0",
    confidence=0.85,
    keywords=["关键词1", "关键词2"]
)
```

### 3. KnowledgeChunk (知识块)

文档分块信息，用于更精确的搜索和处理。

```python
from src.models.knowledge import KnowledgeChunk

chunk = KnowledgeChunk(
    content="块内容",
    chunk_index=0,
    start_position=0,
    end_position=100,
    embedding=[0.1, 0.2, 0.3],  # 向量嵌入
    metadata={"sentence_count": 5}
)
```

### 4. QualityMetrics (质量指标)

多维度的质量评估指标。

```python
from src.models.knowledge import QualityMetrics

quality = QualityMetrics(
    accuracy_score=0.85,      # 准确性
    completeness_score=0.90,  # 完整性
    relevance_score=0.80,     # 相关性
    freshness_score=0.95,     # 时效性
    usage_score=0.75,         # 使用频率
    overall_score=0.85,       # 综合评分
    last_evaluated=datetime.now()
)
```

### 5. UsageStatistics (使用统计)

详细的使用统计信息。

```python
from src.models.knowledge import UsageStatistics

usage = UsageStatistics(
    view_count=100,           # 查看次数
    search_count=50,          # 搜索命中次数
    reference_count=25,       # 被引用次数
    feedback_count=10,        # 反馈次数
    positive_feedback=8,      # 正面反馈
    negative_feedback=2,      # 负面反馈
    last_accessed=datetime.now()
)
```

## 🔧 主要功能

### 1. 知识创建

```python
from src.services.knowledge_service import KnowledgeService

service = KnowledgeService()

# 创建知识
knowledge = await service.create_knowledge(
    title="CRM系统使用指南",
    content="详细的CRM系统使用说明...",
    knowledge_type=KnowledgeType.DOCUMENT,
    metadata=metadata
)
```

### 2. 知识搜索

```python
# 语义搜索
results = await service.search_knowledge(
    query="CRM系统实施",
    limit=10
)

for result in results:
    print(f"标题: {result.knowledge.title}")
    print(f"相关性: {result.relevance:.2f}")
    print(f"摘要: {result.snippet}")
```

### 3. 知识更新

```python
from src.models.knowledge import KnowledgeUpdateRequest

update_request = KnowledgeUpdateRequest(
    title="更新后的标题",
    content="更新后的内容",
    status=KnowledgeStatus.PUBLISHED
)

updated_knowledge = await service.update_knowledge(
    knowledge_id="knowledge_id",
    update_request=update_request
)
```

### 4. 质量评估

```python
# 单个知识质量评估
quality = service.quality_assessor.assess_quality(knowledge)

# 批量质量评估
batch_results = await service.batch_quality_assessment()
```

### 5. 高级过滤

```python
from src.models.knowledge import KnowledgeSearchFilter

# 创建过滤器
filter_params = KnowledgeSearchFilter(
    types=[KnowledgeType.FAQ, KnowledgeType.BEST_PRACTICE],
    status=[KnowledgeStatus.PUBLISHED],
    tags=["重要", "常用"],
    min_quality_score=0.8
)

# 应用过滤器
filtered_knowledge = service.list_knowledge(
    filter_params=filter_params,
    limit=20
)
```

## 💡 使用示例

### 完整示例运行

```bash
# 运行完整的知识管理演示
python examples/knowledge_management_examples.py

# 运行模型测试
python examples/knowledge_model_tests.py
```

### 基本使用流程

```python
import asyncio
from src.services.knowledge_service import KnowledgeService
from src.models.knowledge import *

async def basic_usage():
    service = KnowledgeService()
    
    # 1. 创建知识
    metadata = KnowledgeMetadata(
        source="user_input",
        author="张三",
        domain="销售管理"
    )
    
    knowledge = await service.create_knowledge(
        title="销售技巧总结",
        content="有效的销售技巧包括...",
        knowledge_type=KnowledgeType.BEST_PRACTICE,
        metadata=metadata
    )
    
    # 2. 搜索知识
    results = await service.search_knowledge("销售技巧")
    
    # 3. 更新使用统计
    service.update_usage_statistics(knowledge.id, "reference")
    
    # 4. 获取统计信息
    stats = service.get_knowledge_statistics()
    print(f"总知识数: {stats['total_knowledge']}")

# 运行示例
asyncio.run(basic_usage())
```

## 📚 API参考

### KnowledgeService 主要方法

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `create_knowledge()` | 创建知识 | title, content, type, metadata | Knowledge |
| `update_knowledge()` | 更新知识 | knowledge_id, update_request | Knowledge |
| `delete_knowledge()` | 删除知识 | knowledge_id | bool |
| `get_knowledge()` | 获取知识 | knowledge_id | Knowledge |
| `list_knowledge()` | 列出知识 | filter_params, limit, offset | List[Knowledge] |
| `search_knowledge()` | 搜索知识 | query, filter_params, limit | List[KnowledgeSearchResult] |
| `batch_quality_assessment()` | 批量质量评估 | - | Dict[str, QualityMetrics] |
| `get_knowledge_statistics()` | 获取统计信息 | - | Dict[str, Any] |

### DocumentParser 方法

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `parse_text()` | 文本分块 | content, chunk_size, overlap | List[KnowledgeChunk] |
| `extract_keywords()` | 关键词提取 | content, max_keywords | List[str] |

### QualityAssessment 方法

| 方法 | 描述 | 参数 | 返回值 |
|------|------|------|--------|
| `assess_quality()` | 质量评估 | knowledge | QualityMetrics |

## 🎯 最佳实践

### 1. 知识创建最佳实践

- **标题规范**: 使用清晰、描述性的标题
- **内容结构**: 保持良好的内容结构和格式
- **元数据完整**: 填写完整的元数据信息
- **分类标准**: 使用统一的分类标准

```python
# 好的实践
metadata = KnowledgeMetadata(
    source="official_docs",
    author="产品团队",
    domain="产品使用",
    tags=["官方", "指南", "必读"],
    confidence=0.95,
    keywords=["产品", "使用", "指南"]
)
```

### 2. 搜索优化

- **关键词优化**: 使用相关的关键词
- **内容质量**: 保持高质量的内容
- **定期更新**: 及时更新过时的信息

### 3. 质量管理

- **定期评估**: 定期进行质量评估
- **用户反馈**: 收集和处理用户反馈
- **持续改进**: 基于评估结果持续改进

### 4. 版本管理

- **版本记录**: 详细记录版本变更
- **向后兼容**: 保持版本间的兼容性
- **变更说明**: 提供清晰的变更说明

## 🔧 故障排除

### 常见问题

1. **创建知识失败**
   - 检查必填字段是否完整
   - 验证数据格式是否正确
   - 确认服务依赖是否正常

2. **搜索结果不准确**
   - 检查关键词是否合适
   - 验证内容质量
   - 调整搜索参数

3. **质量评分异常**
   - 检查内容完整性
   - 验证元数据信息
   - 确认使用统计数据

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查知识状态
knowledge = service.get_knowledge(knowledge_id)
print(f"状态: {knowledge.status}")
print(f"质量: {knowledge.quality}")
print(f"使用统计: {knowledge.usage}")
```

## 📞 支持

如有问题或建议，请：

1. 查看示例代码: `examples/knowledge_management_examples.py`
2. 运行模型测试: `examples/knowledge_model_tests.py`
3. 查看测试用例: `tests/test_knowledge_service.py`
4. 提交Issue或联系开发团队

---

**版本**: 1.0  
**更新时间**: 2025-01-08  
**维护者**: 知识管理系统开发团队