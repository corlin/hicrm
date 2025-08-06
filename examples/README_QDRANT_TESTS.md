# Qdrant 测试脚本说明

本目录包含了多个Qdrant连接和功能测试脚本，用于验证Qdrant服务的可用性和功能完整性。

> 📡 **连接方式**: 本项目默认使用 **gRPC (端口6334)** 连接Qdrant，提供更高的性能和更低的延迟。

## 🛠️ 环境要求

本项目使用 [uv](https://docs.astral.sh/uv/) 作为Python包管理器和运行工具。

### 安装 uv
```bash
# macOS 和 Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip 安装
pip install uv
```

### 验证安装
```bash
uv --version
```

### 项目依赖
运行测试脚本前，uv会自动安装所需依赖，包括：
- `qdrant-client`: Qdrant Python客户端（支持gRPC连接）
- `numpy`: 数值计算库

### Qdrant连接配置
项目默认使用gRPC连接方式：
- **端口**: 6334 (gRPC)
- **协议**: gRPC (高性能二进制协议)
- **配置**: `QDRANT_URL=localhost:6334` 和 `QDRANT_USE_GRPC=true`

### uv 的优势
- ⚡ **快速**: 比pip快10-100倍的依赖解析和安装
- 🔒 **可靠**: 自动管理虚拟环境和依赖版本
- 🎯 **简单**: 无需手动创建虚拟环境，一条命令即可运行
- 🔄 **一致**: 确保所有开发者使用相同的依赖版本

### gRPC 连接的优势
- 🚀 **高性能**: 二进制协议，比HTTP REST更快
- 📦 **低延迟**: 减少网络开销和序列化时间
- 🔄 **流式传输**: 支持双向流和长连接
- 💪 **类型安全**: 强类型接口定义

## 📋 测试脚本概览

### 1. `qdrant_quick_test.py` - 快速连接测试
**用途**: 快速检查6333和6334端口的连接状态
**特点**: 
- 简单快速
- 测试gRPC (6334) 和 HTTP (6333) 端口连通性
- 验证基本API调用
- 适合日常检查

**使用方法**:
```bash
uv run examples/qdrant_quick_test.py
```

**输出示例**:
```
🚀 Qdrant 快速连接测试
========================================
目标主机: localhost

📡 gRPC 连接测试 (端口 6334)
------------------------------
🔍 测试 gRPC 端口 6334... ✅ 端口可访问
🔌 测试 gRPC 客户端连接... ✅ 客户端连接成功
📋 测试获取集合列表... ✅ 成功 (当前有 0 个集合)

📡 HTTP 连接测试 (端口 6333)
------------------------------
🔍 测试 HTTP 端口 6333... ✅ 端口可访问
🔌 测试 HTTP 客户端连接... ✅ 客户端连接成功
📋 测试获取集合列表... ✅ 成功 (当前有 0 个集合)

📋 测试总结
========================================
gRPC (6334):  ✅ 完全可用 (当前使用)
HTTP (6333):  ✅ 完全可用 (备用)

🎉 gRPC连接可用！
💡 当前配置: 使用高性能gRPC连接 (端口6334)
```

### 2. `qdrant_connection_test.py` - 综合连接测试
**用途**: 全面测试Qdrant连接和基本操作
**特点**:
- 详细的连接测试
- 完整的CRUD操作验证
- 支持自定义主机和端口
- 详细的错误报告

**使用方法**:
```bash
# 默认测试
uv run examples/qdrant_connection_test.py

# 自定义主机和端口
uv run examples/qdrant_connection_test.py --host 192.168.1.100 --http-port 6333 --grpc-port 6334
```

**测试内容**:
- 端口连通性检查
- 客户端创建和连接
- 获取集合列表
- 创建测试集合
- 插入向量点
- 执行向量搜索
- 删除集合

### 3. `qdrant_collection_test.py` - 集合操作测试
**用途**: 专门测试Qdrant的集合管理和向量操作功能
**特点**:
- 基本集合操作测试
- 向量插入和搜索测试
- 高级功能测试（批量操作、复杂过滤等）
- 自动清理测试数据

**使用方法**:
```bash
# 默认测试
uv run examples/qdrant_collection_test.py

# 自定义连接
uv run examples/qdrant_collection_test.py --host localhost --port 6333
```

**测试内容**:
- **基本操作**: 创建集合、获取信息、列出集合
- **向量操作**: 插入向量、向量搜索、过滤搜索
- **高级操作**: 批量插入、复杂过滤、点更新、点删除

## 🚀 快速开始

### 基本使用
```bash
# 快速检查连接
uv run examples/qdrant_quick_test.py

# 全面连接测试
uv run examples/qdrant_connection_test.py

# 集合功能测试
uv run examples/qdrant_collection_test.py
```

> 💡 **提示**: `uv run` 会自动：
> - 创建和管理虚拟环境
> - 安装项目依赖
> - 运行指定的Python脚本
> 
> 首次运行可能需要几秒钟来安装依赖，后续运行会很快。

## 🎯 使用场景

### 场景1: 首次部署验证
```bash
# 1. 启动Qdrant服务
docker-compose -f docker-compose.vector.yml up -d qdrant

# 2. 快速检查连接
uv run examples/qdrant_quick_test.py

# 3. 如果连接正常，运行完整测试
uv run examples/qdrant_connection_test.py
```

### 场景2: 功能完整性验证
```bash
# 运行集合操作测试
uv run examples/qdrant_collection_test.py
```

### 场景3: 故障排除
```bash
# 1. 快速诊断
uv run examples/qdrant_quick_test.py

# 2. 如果有问题，查看详细信息
uv run examples/qdrant_connection_test.py
```

### 场景4: 性能基准测试
```bash
# 运行高级操作测试，观察性能
uv run examples/qdrant_collection_test.py
```

## 📊 测试结果解读

### 成功状态
- ✅ **端口可访问**: 网络连接正常
- ✅ **客户端连接成功**: Qdrant服务响应正常
- ✅ **API调用成功**: 服务功能正常
- ✅ **操作完成**: 具体功能工作正常

### 失败状态
- ❌ **端口不可访问**: 服务未启动或网络问题
- ❌ **客户端连接失败**: 服务配置问题或版本不兼容
- ❌ **API调用失败**: 服务内部错误或权限问题
- ❌ **操作失败**: 具体功能异常

## 🔧 常见问题解决

### 问题1: 端口不可访问
```bash
# 检查服务状态
docker ps | grep qdrant

# 启动服务
docker-compose -f docker-compose.vector.yml up -d qdrant

# 检查gRPC端口 (主要)
netstat -an | grep 6334

# 检查HTTP端口 (备用)
netstat -an | grep 6333
```

### 问题2: gRPC客户端连接失败
- 检查Qdrant版本兼容性（确保支持gRPC）
- 确认gRPC端口6334是否开放
- 检查防火墙是否阻止gRPC连接
- 验证qdrant-client版本支持gRPC
- 如果gRPC有问题，可临时切换到HTTP模式

### 问题3: API调用失败
- 检查Qdrant服务日志
- 确认服务完全启动（可能需要等待几秒）
- 验证客户端库版本

### 问题4: uv相关问题
```bash
# 清理uv缓存
uv cache clean

# 重新安装依赖
uv sync --reinstall

# 查看uv版本
uv --version

# 手动安装依赖（如果需要）
uv add qdrant-client numpy
```

## 📝 测试脚本特点对比

| 脚本 | 速度 | 详细程度 | 功能覆盖 | 适用场景 |
|------|------|----------|----------|----------|
| `qdrant_quick_test.py` | 快 | 基础 | 连接测试 | 日常检查 |
| `qdrant_connection_test.py` | 中 | 详细 | 基本操作 | 部署验证 |
| `qdrant_collection_test.py` | 慢 | 全面 | 完整功能 | 功能测试 |

## 🎯 建议的测试流程

1. **开发环境设置**:
   ```bash
   uv run examples/qdrant_quick_test.py
   ```

2. **部署后验证**:
   ```bash
   uv run examples/qdrant_connection_test.py
   ```

3. **功能完整性检查**:
   ```bash
   uv run examples/qdrant_collection_test.py
   ```

4. **定期健康检查**:
   ```bash
   uv run examples/qdrant_quick_test.py
   ```

这些测试脚本可以帮助你快速诊断和验证Qdrant服务的状态，确保向量数据库功能正常工作。