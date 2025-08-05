# 向量数据库和嵌入服务设置指南

## 概述

本文档介绍如何设置和配置HiCRM系统的向量数据库和嵌入服务，包括Qdrant向量数据库、BGE-M3嵌入模型和Elasticsearch搜索引擎。

## 架构组件

### 1. Qdrant向量数据库
- **用途**: 存储和检索文档的向量表示
- **特点**: 高性能、支持过滤、实时更新
- **端口**: 6333 (HTTP), 6334 (gRPC)

### 2. BGE-M3嵌入模型
- **用途**: 将文本转换为向量表示
- **特点**: 多语言支持、中英文效果优异
- **模型**: BAAI/bge-m3, BAAI/bge-reranker-v2-m3

### 3. Elasticsearch
- **用途**: BM25文本搜索和关键词匹配
- **特点**: 全文搜索、高亮显示、聚合分析
- **端口**: 9200 (HTTP), 9300 (传输)

## 快速开始

### 1. 使用Docker Compose启动服务

```bash
# 启动向量数据库服务
docker-compose -f docker-compose.vector.yml up -d

# 查看服务状态
docker-compose -f docker-compose.vector.yml ps

# 查看日志
docker-compose -f docker-compose.vector.yml logs -f
```

### 2. 验证服务状态

```bash
# 检查Qdrant
curl http://localhost:6333/collections

# 检查Elasticsearch
curl http://localhost:9200/_cluster/health

# 检查Kibana (可选)
# 访问 http://localhost:5601
```

### 3. 配置环境变量

在`.env`文件中设置以下配置：

```env
# Qdrant配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # 可选，生产环境建议设置

# Elasticsearch配置
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USERNAME=  # 可选
ELASTICSEARCH_PASSWORD=  # 可选
ELASTICSEARCH_INDEX_PREFIX=hicrm

# BGE模型配置
BGE_MODEL_NAME=BAAI/bge-m3
BGE_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
BGE_DEVICE=cpu  # 或 cuda (如果有GPU)
```

## 服务详细配置

### Qdrant配置

```yaml
# docker-compose.vector.yml中的Qdrant配置
qdrant:
  image: qdrant/qdrant:v1.7.0
  ports:
    - "6333:6333"  # HTTP API
    - "6334:6334"  # gRPC API
  volumes:
    - qdrant_storage:/qdrant/storage
  environment:
    - QDRANT__SERVICE__HTTP_PORT=6333
    - QDRANT__SERVICE__GRPC_PORT=6334
```

**主要功能**:
- 向量存储和检索
- 相似度搜索
- 过滤和聚合
- 实时更新

### Elasticsearch配置

```yaml
# docker-compose.vector.yml中的Elasticsearch配置
elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
    - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
  ports:
    - "9200:9200"
    - "9300:9300"
```

**主要功能**:
- 全文搜索
- BM25评分
- 高亮显示
- 聚合分析

### BGE模型配置

BGE-M3模型会在首次使用时自动下载，需要确保网络连接正常。

**模型特点**:
- **BGE-M3**: 多语言嵌入模型，支持中英文
- **BGE-reranker-v2-m3**: 重排序模型，提高搜索精度
- **维度**: 1024维向量
- **语言**: 支持中文、英文等多种语言

## 使用示例

### 1. 基础向量搜索

```python
from src.services.vector_service import vector_service, VectorDocument

# 初始化服务
await vector_service.initialize()

# 添加文档
docs = [
    VectorDocument("doc1", "这是关于人工智能的文档", {"category": "AI"}),
    VectorDocument("doc2", "这是关于机器学习的文档", {"category": "ML"})
]
await vector_service.add_documents(docs)

# 搜索
results = await vector_service.search("人工智能", limit=5)
for result in results:
    print(f"{result.document.content} (分数: {result.score})")
```

### 2. 混合搜索

```python
from src.services.hybrid_search_service import hybrid_search_service, SearchMode

# 初始化服务
await hybrid_search_service.initialize()

# 添加文档
docs = [
    {
        "id": "doc1",
        "content": "人工智能技术的发展历程",
        "title": "AI发展史",
        "metadata": {"category": "AI"}
    }
]
await hybrid_search_service.add_documents(docs)

# 混合搜索
results = await hybrid_search_service.search(
    "人工智能", 
    mode=SearchMode.HYBRID,
    limit=10
)

for result in results:
    print(f"标题: {result.title}")
    print(f"向量分数: {result.vector_score}, BM25分数: {result.bm25_score}")
    print(f"混合分数: {result.hybrid_score}")
```

### 3. 嵌入服务使用

```python
from src.services.embedding_service import embedding_service

# 初始化服务
await embedding_service.initialize()

# 编码单个文本
embedding = await embedding_service.encode("这是测试文本")
print(f"向量维度: {len(embedding)}")

# 批量编码
texts = ["文本1", "文本2", "文本3"]
embeddings = await embedding_service.encode(texts)

# 计算相似度
similarity = await embedding_service.compute_similarity("人工智能", "机器学习")
print(f"相似度: {similarity}")

# 重排序
documents = ["文档1内容", "文档2内容", "文档3内容"]
ranked_results = await embedding_service.rerank("查询文本", documents)
```

## 测试

### 1. 单元测试

```bash
# 运行向量服务测试
uv run pytest tests/test_services/test_vector_service.py -v

# 运行嵌入服务测试
uv run pytest tests/test_services/test_embedding_service.py -v

# 运行混合搜索测试
uv run pytest tests/test_services/test_hybrid_search_service.py -v

# 运行Elasticsearch测试
uv run pytest tests/test_services/test_elasticsearch_service.py -v
```

### 2. 集成测试

```bash
# 确保服务已启动
docker-compose -f docker-compose.vector.yml up -d

# 运行集成测试
uv run pytest test_integration_vector.py -v -m integration

# 或直接运行集成测试脚本
uv run python test_integration_vector.py
```

### 3. 简单功能测试

```bash
# 运行基础功能测试
uv run pytest test_vector_simple.py -v
```

## 性能优化

### 1. Qdrant优化

```python
# 创建集合时的优化配置
await vector_service.create_collection(
    "optimized_collection",
    vector_size=1024,
    distance=Distance.COSINE,
    # 优化参数在vector_service.py中已配置
)
```

### 2. Elasticsearch优化

```yaml
# 在docker-compose.vector.yml中调整内存
environment:
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # 根据可用内存调整
```

### 3. BGE模型优化

```env
# 如果有GPU，设置使用CUDA
BGE_DEVICE=cuda

# 调整批处理大小
# 在代码中通过batch_size参数控制
```

## 监控和维护

### 1. 健康检查

```bash
# Qdrant健康检查
curl http://localhost:6333/collections

# Elasticsearch健康检查
curl http://localhost:9200/_cluster/health?pretty

# 查看集合/索引统计
curl http://localhost:6333/collections/hicrm_knowledge
curl http://localhost:9200/hicrm_knowledge/_stats?pretty
```

### 2. 数据备份

```bash
# Qdrant数据备份
docker-compose -f docker-compose.vector.yml exec qdrant \
  tar -czf /tmp/qdrant_backup.tar.gz /qdrant/storage

# Elasticsearch快照
curl -X PUT "localhost:9200/_snapshot/my_backup" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'
```

### 3. 日志监控

```bash
# 查看服务日志
docker-compose -f docker-compose.vector.yml logs qdrant
docker-compose -f docker-compose.vector.yml logs elasticsearch

# 实时监控
docker-compose -f docker-compose.vector.yml logs -f
```

## 故障排除

### 1. 常见问题

**Qdrant连接失败**:
```bash
# 检查端口是否被占用
netstat -an | grep 6333

# 检查Docker容器状态
docker ps | grep qdrant
```

**Elasticsearch内存不足**:
```bash
# 调整JVM堆内存
# 在docker-compose.vector.yml中修改ES_JAVA_OPTS
```

**BGE模型下载失败**:
```bash
# 检查网络连接
# 可以手动下载模型到本地缓存目录
```

### 2. 性能问题

**搜索速度慢**:
- 检查索引是否完成
- 调整批处理大小
- 考虑使用GPU加速

**内存使用过高**:
- 调整缓存大小
- 减少批处理大小
- 优化向量维度

## 生产环境部署

### 1. 安全配置

```env
# 启用Qdrant API密钥
QDRANT_API_KEY=your-secure-api-key

# 启用Elasticsearch安全
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-secure-password
```

### 2. 高可用配置

```yaml
# 多节点Elasticsearch集群
elasticsearch:
  environment:
    - cluster.name=hicrm-es-cluster
    - node.name=es-node-1
    - discovery.seed_hosts=es-node-2,es-node-3
    - cluster.initial_master_nodes=es-node-1,es-node-2,es-node-3
```

### 3. 资源限制

```yaml
# Docker资源限制
services:
  qdrant:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
  
  elasticsearch:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

## 总结

通过以上配置，您可以成功部署和使用HiCRM系统的向量数据库和嵌入服务。这个系统提供了：

1. **高性能向量搜索**: 基于Qdrant的语义搜索
2. **全文搜索**: 基于Elasticsearch的BM25搜索
3. **混合检索**: 结合向量和文本搜索的最佳效果
4. **中文优化**: 专门针对中文场景优化的嵌入模型
5. **可扩展性**: 支持大规模数据和高并发访问

如有问题，请参考故障排除部分或查看相关日志文件。