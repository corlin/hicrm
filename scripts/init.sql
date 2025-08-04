-- HiCRM数据库初始化脚本

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 创建数据库用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'hicrm_user') THEN
        CREATE ROLE hicrm_user WITH LOGIN PASSWORD 'hicrm_password';
    END IF;
END
$$;

-- 授予权限
GRANT ALL PRIVILEGES ON DATABASE hicrm TO hicrm_user;
GRANT ALL ON SCHEMA public TO hicrm_user;

-- 创建索引优化查询性能
-- 这些索引将在模型创建后自动生成，这里只是预留