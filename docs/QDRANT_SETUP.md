# Qdrant 向量数据库设置指南

## 问题解决

### 1. API Key 安全警告

**问题**: `Api key is used with an insecure connection`

**解决方案**:
- **开发环境**: 在 `.env` 文件中设置 `QDRANT_API_KEY=` (留空)
- **生产环境**: 使用 HTTPS 连接 `QDRANT_URL=https://your-domain:6333`

### 2. 服务器版本检查警告

**问题**: `Failed to obtain server version. Unable to check client-server compatibility`

**解决方案**: 已自动添加 `check_compatibility=False` 参数跳过版本检查

### 3. 502 Bad Gateway 错误

**问题**: Qdrant 服务未运行

**解决方案**:

#### 方法1: 使用 Docker Compose (推荐)
```bash
docker-compose up -d qdrant
```

#### 方法2: 直接使用 Docker
```bash
docker run -d --name qdrant-hicrm -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

#### 方法3: 使用向量服务配置
```bash
docker-compose -f docker-compose.vector.yml up -d qdrant
```

## 端口说明

- **6333**: HTTP REST API (推荐)
- **6334**: gRPC API (高性能)

## 配置建议

### 开发环境 (.env)
```env
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
DEBUG=true
```

### 生产环境 (.env)
```env
QDRANT_URL=https://your-qdrant-server:6333
QDRANT_API_KEY=your-secure-api-key
DEBUG=false
```

## 验证连接

```bash
# 检查服务状态
curl http://localhost:6333/collections

# 检查端口
telnet localhost 6333
```

## 故障排除

1. **检查 Docker 是否运行**
   ```bash
   docker --version
   docker ps
   ```

2. **检查端口占用**
   ```bash
   netstat -an | grep 6333
   ```

3. **查看 Qdrant 日志**
   ```bash
   docker logs qdrant-hicrm
   # 或
   docker-compose logs qdrant
   ```

4. **重启服务**
   ```bash
   docker restart qdrant-hicrm
   # 或
   docker-compose restart qdrant
   ```