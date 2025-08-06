#!/usr/bin/env python3
"""
Qdrant快速连接测试

简单快速地测试Qdrant的6333和6334端口连接
"""

import socket
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.exceptions import UnexpectedResponse
except ImportError:
    print("❌ 请先安装 qdrant-client: pip install qdrant-client")
    sys.exit(1)


def test_port(host: str, port: int, timeout: int = 3) -> bool:
    """测试端口连通性"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False


def test_qdrant_connection(host: str, port: int, use_grpc: bool = None) -> dict:
    """测试Qdrant连接"""
    # 自动判断协议类型
    if use_grpc is None:
        use_grpc = (port == 6334)
    
    protocol = "gRPC" if use_grpc else "HTTP"
    
    result = {
        "port": port,
        "protocol": protocol,
        "port_open": False,
        "client_connected": False,
        "collections_accessible": False,
        "error": None
    }
    
    # 1. 测试端口
    print(f"🔍 测试 {protocol} 端口 {port}...", end=" ")
    if not test_port(host, port):
        print("❌ 端口不可访问")
        return result
    
    result["port_open"] = True
    print("✅ 端口可访问")
    
    # 2. 测试客户端连接
    print(f"🔌 测试 {protocol} 客户端连接...", end=" ")
    try:
        if use_grpc:
            client = QdrantClient(
                host=host,
                port=port,
                prefer_grpc=True,
                timeout=5,
                check_compatibility=False
            )
        else:
            client = QdrantClient(
                url=f"http://{host}:{port}",
                timeout=5,
                prefer_grpc=False,
                check_compatibility=False
            )
        
        result["client_connected"] = True
        print("✅ 客户端连接成功")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ 客户端连接失败: {e}")
        return result
    
    # 3. 测试基本API调用
    print(f"📋 测试获取集合列表...", end=" ")
    try:
        collections = client.get_collections()
        result["collections_accessible"] = True
        print(f"✅ 成功 (当前有 {len(collections.collections)} 个集合)")
        
        # 显示现有集合
        if collections.collections:
            print(f"   现有集合:")
            for collection in collections.collections:
                print(f"   - {collection.name}")
        
    except Exception as e:
        result["error"] = str(e)
        print(f"❌ API调用失败: {e}")
    
    return result


def main():
    """主函数"""
    host = "localhost"
    
    print("🚀 Qdrant 快速连接测试")
    print("=" * 40)
    print(f"目标主机: {host}")
    print()
    
    # 测试gRPC连接 (6334) - 主要连接方式
    print("📡 gRPC 连接测试 (端口 6334) - 主要连接")
    print("-" * 40)
    grpc_result = test_qdrant_connection(host, 6334, use_grpc=True)
    print()
    
    # 测试HTTP连接 (6333) - 备用连接方式
    print("📡 HTTP 连接测试 (端口 6333) - 备用连接")
    print("-" * 40)
    http_result = test_qdrant_connection(host, 6333, use_grpc=False)
    print()
    
    # 总结
    print("📋 测试总结")
    print("=" * 40)
    
    http_ok = http_result["collections_accessible"]
    grpc_ok = grpc_result["collections_accessible"]
    
    print(f"gRPC (6334):  {'✅ 完全可用' if grpc_ok else '❌ 不可用'} (主要)")
    print(f"HTTP (6333):  {'✅ 完全可用' if http_ok else '❌ 不可用'} (备用)")
    print()
    
    if grpc_ok or http_ok:
        print("🎉 至少有一个连接可用！")
        if grpc_ok and http_ok:
            print("💡 当前配置: 使用高性能gRPC连接 (端口6334)")
            print("💡 备用方案: HTTP连接也可用 (端口6333)")
        elif grpc_ok:
            print("💡 建议: 使用gRPC连接 (端口 6334) - 当前配置")
        else:
            print("💡 建议: 使用HTTP连接 (端口 6333) - gRPC不可用时的备用方案")
        return 0
    else:
        print("❌ 所有连接都不可用")
        print()
        print("🔧 故障排除:")
        print("1. 检查Qdrant服务是否运行:")
        print("   docker ps | grep qdrant")
        print()
        print("2. 启动Qdrant服务:")
        print("   docker-compose -f docker-compose.vector.yml up -d qdrant")
        print()
        print("3. 检查端口是否被占用:")
        print("   netstat -an | grep 6333")
        print("   netstat -an | grep 6334")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        sys.exit(1)