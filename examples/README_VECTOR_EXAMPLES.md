# 向量数据库和嵌入服务使用示例

本目录包含了向量数据库和嵌入服务的完整使用示例，展示了如何使用BGE-M3嵌入模型、Qdrant向量数据库、混合搜索和中文语义搜索等功能。

## 📁 示例文件

### 1. `vector_database_examples.py` - 向量数据库服务示例
展示Qdrant向量数据库的基本操作和高级功能。

**主要功能:**
- 向量数据库初始化和配置
- 文档添加、更新、删除操作
- 向量搜索和过滤搜索
- 相似度计算和向量操作
- 集合管理和统计信息
- 性能测试和优化

**运行方式:**
```bash
# 运行所有示例
uv run python examples/vector_database_examples.py

# 运行特定示例 (1-9)
uv run python examples/vector_database_examples.py 3
```

### 2. `embedding_service_examples.py` - BGE-M3嵌入服务示例
展示BGE-M3多语言嵌入模型的使用方法。

**主要功能:**
- BGE-M3模型初始化和配置
- 单文本和批量文本编码
- 中英文文本相似度计算
- 重排序功能演示
- 缓存机制和性能优化
- 归一化对比和多语言支持

**运行方式:**
```bash
# 运行所有示例
uv run python examples/embedding_service_examples.py

# 运行特定示例 (1-9)
uv run python examples/embedding_service_examples.py 5
```

### 3. `hybrid_search_examples.py` - 混合搜索服务示例
展示如何结合向量搜索和BM25搜索实现混合检索。

**主要功能:**
- 混合搜索系统初始化
- 向量搜索、BM25搜索、混合搜索模式
- 自定义搜索权重配置
- 过滤搜索和语义搜索
- 性能对比和统计分析
- 搜索结果重排序

**运行方式:**
```bash
# 运行所有示例
uv run python examples/hybrid_search_examples.py

# 运行特定示例 (1-10)
uv run python examples/hybrid_search_examples.py 7
```

### 4. `chinese_search_examples.py` - 中文语义搜索示例
专门针对中文文本的语义搜索功能演示。

**主要功能:**
- 中文文本预处理和分词
- 中文停用词和同义词处理
- 中文语义搜索和意图分析
- 同义词扩展搜索对比
- 相似文档查找
- 搜索建议生成
- 中文搜索性能分析

**运行方式:**
```bash
# 运行所有示例
uv run python examples/chinese_search_examples.py

# 运行特定示例 (1-10)
uv run python examples/chinese_search_examples.py 4
```

## 🚀 快速开始

### 环境要求
- Python 3.11+
- Qdrant 向量数据库 (本地或远程)
- Elasticsearch (用于BM25搜索)
- 足够的内存运行BGE-M3模型

### 启动服务
1. **启动Qdrant:**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

2. **启动Elasticsearch:**
```bash
docker run -p 9200:9200 -e "discovery.type=single-node" elasticsearch:8.11.0
```

3. **安装依赖:**
```bash
uv sync
```

### 运行示例
```bash
# 基础向量数据库操作
uv run python examples/vector_database_examples.py

# BGE-M3嵌入服务功能
uv run python examples/embedding_service_examples.py

# 混合搜索功能
uv run python examples/hybrid_search_examples.py

# 中文语义搜索
uv run python examples/chinese_search_examples.py
```

## 📋 示例详情

### 向量数据库示例 (vector_database_examples.py)

| 示例 | 功能 | 描述 |
|------|------|------|
| 1 | 基本设置 | 初始化服务和创建集合 |
| 2 | 添加文档 | 批量添加向量文档 |
| 3 | 基本搜索 | 文本查询和向量搜索 |
| 4 | 过滤搜索 | 带条件的搜索查询 |
| 5 | 向量搜索 | 直接使用向量进行搜索 |
| 6 | 相似度计算 | 文本相似度和批量计算 |
| 7 | 文档管理 | 更新和删除文档 |
| 8 | 集合管理 | 集合操作和统计信息 |
| 9 | 性能测试 | 批量操作性能测试 |

### 嵌入服务示例 (embedding_service_examples.py)

| 示例 | 功能 | 描述 |
|------|------|------|
| 1 | 模型初始化 | BGE-M3和重排序模型加载 |
| 2 | 单文本编码 | 单个文本向量化 |
| 3 | 批量编码 | 多文本批量处理 |
| 4 | 相似度计算 | 文本对相似度计算 |
| 5 | 多相似度计算 | 一对多相似度计算 |
| 6 | 重排序功能 | 搜索结果重排序 |
| 7 | 缓存性能 | 缓存机制性能测试 |
| 8 | 归一化对比 | 归一化vs非归一化 |
| 9 | 多语言性能 | 中英文性能对比 |

### 混合搜索示例 (hybrid_search_examples.py)

| 示例 | 功能 | 描述 |
|------|------|------|
| 1 | 服务初始化 | 混合搜索系统启动 |
| 2 | 添加文档 | 文档同时添加到向量库和ES |
| 3 | 向量搜索 | 仅语义搜索模式 |
| 4 | BM25搜索 | 仅关键词搜索模式 |
| 5 | 混合搜索 | 语义+关键词混合模式 |
| 6 | 自定义权重 | 搜索权重配置 |
| 7 | 过滤搜索 | 带条件的混合搜索 |
| 8 | 语义搜索 | 高级语义搜索功能 |
| 9 | 性能对比 | 不同模式性能比较 |
| 10 | 统计信息 | 系统统计和监控 |

### 中文搜索示例 (chinese_search_examples.py)

| 示例 | 功能 | 描述 |
|------|------|------|
| 1 | 服务初始化 | 中文搜索服务启动 |
| 2 | 中文文档 | 添加中文测试文档 |
| 3 | 文本处理 | 中文预处理和分词 |
| 4 | 语义搜索 | 中文语义搜索 |
| 5 | 同义词扩展 | 同义词扩展搜索对比 |
| 6 | 自定义权重 | 中文搜索权重调整 |
| 7 | 意图分析 | 中文查询意图识别 |
| 8 | 相似文档 | 中文相似文档查找 |
| 9 | 搜索建议 | 中文搜索建议生成 |
| 10 | 性能分析 | 中文搜索性能测试 |

## 🔧 配置说明

### 环境变量配置
```bash
# Qdrant配置
QDRANT_URL=localhost:6334
QDRANT_API_KEY=  # 可选

# Elasticsearch配置  
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USERNAME=  # 可选
ELASTICSEARCH_PASSWORD=  # 可选

# BGE模型配置
BGE_MODEL_NAME=BAAI/bge-m3
BGE_RERANKER_MODEL=BAAI/bge-reranker-v2-m3
BGE_DEVICE=cpu  # 或 cuda
```

### 性能优化建议
1. **GPU加速**: 如有GPU，设置 `BGE_DEVICE=cuda`
2. **批量处理**: 使用批量操作提高效率
3. **缓存利用**: 重复查询会使用缓存加速
4. **连接池**: 服务会自动管理连接池
5. **内存管理**: 大批量操作时注意内存使用

## 🐛 故障排除

### 常见问题

1. **Qdrant连接失败**
   - 检查Qdrant服务是否启动
   - 确认端口配置 (6333 HTTP, 6334 gRPC)
   - 检查防火墙设置

2. **文档ID格式错误**
   - Qdrant要求使用UUID格式的文档ID
   - 示例已修复为使用 `str(uuid.uuid4())` 生成ID
   - 如遇到 "Unable to parse UUID" 错误，请检查ID格式

3. **Elasticsearch连接失败**
   - 确认ES服务运行在9200端口
   - 检查认证配置
   - 验证索引权限
   - 中文分析器可能需要安装IK插件

4. **BGE模型加载失败**
   - 确认网络连接可下载模型
   - 检查磁盘空间是否充足
   - 验证Python环境和依赖

5. **内存不足**
   - 减少批量处理大小
   - 使用CPU而非GPU (如内存不足)
   - 清理不必要的缓存

### 调试模式
```bash
# 启用详细日志
export PYTHONPATH=.
export LOG_LEVEL=DEBUG
uv run python examples/vector_database_examples.py
```

## 📊 性能基准

### 典型性能指标 (CPU环境)
- **文本编码**: ~50ms/文本 (单个), ~20ms/文本 (批量)
- **向量搜索**: ~10ms/查询 (1000文档)
- **混合搜索**: ~50ms/查询 (包含重排序)
- **中文处理**: ~30ms/查询 (包含预处理)

### 扩展性
- **文档数量**: 支持百万级文档
- **并发查询**: 支持多线程并发
- **内存使用**: ~2GB (BGE-M3模型)
- **存储需求**: ~1KB/文档 (向量+元数据)

## 🤝 贡献指南

欢迎提交问题和改进建议！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](../LICENSE) 文件了解详情。