#!/usr/bin/env python3
"""
Qdrant连接测试脚本

测试6333 (HTTP) 和 6334 (gRPC) 端口的连接有效性
并进行基本的集合操作测试
"""

import asyncio
import sys
import socket
import time
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse
import numpy as np


class QdrantTester:
    """Qdrant连接测试器"""
    
    def __init__(self, host: str = "localhost"):
        self.host = host
        self.http_port = 6333
        self.grpc_port = 6334
        self.test_collection = "connection_test"
        
    def test_port_connectivity(self, port: int, timeout: int = 3) -> bool:
        """测试端口连通性"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((self.host, port))
            sock.close()
            return result == 0
        except Exception as e:
            print(f"   端口连通性测试异常: {e}")
            return False
    
    def create_test_client(self, port: int, use_grpc: bool = False) -> Optional[QdrantClient]:
        """创建测试客户端"""
        try:
            if use_grpc:
                # gRPC连接
                client = QdrantClient(
                    host=self.host,
                    port=port,
                    prefer_grpc=True,
                    timeout=10,
                    check_compatibility=False
                )
            else:
                # HTTP连接
                url = f"http://{self.host}:{port}"
                client = QdrantClient(
                    url=url,
                    timeout=10,
                    prefer_grpc=False,
                    check_compatibility=False
                )
            return client
        except Exception as e:
            print(f"   客户端创建失败: {e}")
            return None
    
    def test_basic_operations(self, client: QdrantClient, connection_type: str) -> Dict[str, Any]:
        """测试基本操作"""
        results = {
            "connection_type": connection_type,
            "get_collections": False,
            "create_collection": False,
            "insert_points": False,
            "search_points": False,
            "delete_collection": False,
            "errors": []
        }
        
        try:
            # 1. 测试获取集合列表
            print(f"   1. 测试获取集合列表...")
            collections = client.get_collections()
            results["get_collections"] = True
            print(f"      ✅ 成功，当前集合数量: {len(collections.collections)}")
            
        except Exception as e:
            results["errors"].append(f"获取集合失败: {e}")
            print(f"      ❌ 失败: {e}")
            return results
        
        try:
            # 2. 测试创建集合
            print(f"   2. 测试创建集合: {self.test_collection}")
            
            # 先删除可能存在的测试集合
            try:
                client.delete_collection(self.test_collection)
                print(f"      清理已存在的测试集合")
            except:
                pass
            
            # 创建新集合
            client.create_collection(
                collection_name=self.test_collection,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE)
            )
            results["create_collection"] = True
            print(f"      ✅ 集合创建成功")
            
        except Exception as e:
            results["errors"].append(f"创建集合失败: {e}")
            print(f"      ❌ 失败: {e}")
            return results
        
        try:
            # 3. 测试插入向量点
            print(f"   3. 测试插入向量点...")
            
            # 生成测试向量
            test_vectors = [
                np.random.rand(128).tolist(),
                np.random.rand(128).tolist(),
                np.random.rand(128).tolist()
            ]
            
            points = [
                PointStruct(
                    id=i + 1,  # 从1开始，避免0作为ID
                    vector=vector,
                    payload={"text": f"测试文档 {i+1}", "category": "test"}
                )
                for i, vector in enumerate(test_vectors)
            ]
            
            client.upsert(
                collection_name=self.test_collection,
                points=points
            )
            results["insert_points"] = True
            print(f"      ✅ 成功插入 {len(points)} 个向量点")
            
            # 等待索引更新
            time.sleep(1)
            
        except Exception as e:
            results["errors"].append(f"插入向量点失败: {e}")
            print(f"      ❌ 失败: {e}")
            return results
        
        try:
            # 4. 测试向量搜索
            print(f"   4. 测试向量搜索...")
            
            query_vector = np.random.rand(128).tolist()
            search_results = client.search(
                collection_name=self.test_collection,
                query_vector=query_vector,
                limit=2
            )
            
            results["search_points"] = True
            print(f"      ✅ 搜索成功，返回 {len(search_results)} 个结果")
            
            # 显示搜索结果
            for i, result in enumerate(search_results):
                print(f"         结果 {i+1}: ID={result.id}, 分数={result.score:.4f}")
            
        except Exception as e:
            results["errors"].append(f"向量搜索失败: {e}")
            print(f"      ❌ 失败: {e}")
            return results
        
        try:
            # 5. 测试删除集合
            print(f"   5. 测试删除集合...")
            client.delete_collection(self.test_collection)
            results["delete_collection"] = True
            print(f"      ✅ 集合删除成功")
            
        except Exception as e:
            results["errors"].append(f"删除集合失败: {e}")
            print(f"      ❌ 失败: {e}")
        
        return results
    
    def test_connection(self, port: int, use_grpc: bool = False) -> Dict[str, Any]:
        """测试指定端口的连接"""
        connection_type = "gRPC" if use_grpc else "HTTP"
        protocol = "gRPC" if use_grpc else "HTTP"
        
        print(f"\n🔍 测试 {protocol} 连接 (端口 {port})")
        print("-" * 50)
        
        # 1. 测试端口连通性
        print(f"   端口连通性测试...")
        if not self.test_port_connectivity(port):
            print(f"   ❌ 端口 {port} 不可访问")
            return {
                "port": port,
                "connection_type": connection_type,
                "port_accessible": False,
                "client_created": False,
                "operations": {}
            }
        
        print(f"   ✅ 端口 {port} 可访问")
        
        # 2. 创建客户端
        print(f"   创建 {protocol} 客户端...")
        client = self.create_test_client(port, use_grpc)
        if not client:
            return {
                "port": port,
                "connection_type": connection_type,
                "port_accessible": True,
                "client_created": False,
                "operations": {}
            }
        
        print(f"   ✅ {protocol} 客户端创建成功")
        
        # 3. 测试基本操作
        print(f"   执行基本操作测试...")
        operations_result = self.test_basic_operations(client, connection_type)
        
        return {
            "port": port,
            "connection_type": connection_type,
            "port_accessible": True,
            "client_created": True,
            "operations": operations_result
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """运行综合测试"""
        print("🚀 Qdrant 连接综合测试")
        print("=" * 60)
        print(f"测试目标: {self.host}")
        print(f"HTTP 端口: {self.http_port}")
        print(f"gRPC 端口: {self.grpc_port}")
        
        results = {
            "host": self.host,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "tests": {}
        }
        
        # 测试 gRPC 连接 (6334) - 主要连接方式
        results["tests"]["grpc"] = self.test_connection(self.grpc_port, use_grpc=True)
        
        # 测试 HTTP 连接 (6333) - 备用连接方式
        results["tests"]["http"] = self.test_connection(self.http_port, use_grpc=False)
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📋 测试总结")
        print("=" * 60)
        
        for test_name, test_result in results["tests"].items():
            connection_type = test_result["connection_type"]
            port = test_result["port"]
            
            print(f"\n🔌 {connection_type} 连接 (端口 {port}):")
            
            if not test_result["port_accessible"]:
                print(f"   ❌ 端口不可访问")
                continue
            
            if not test_result["client_created"]:
                print(f"   ❌ 客户端创建失败")
                continue
            
            operations = test_result["operations"]
            if not operations:
                print(f"   ❌ 未执行操作测试")
                continue
            
            # 统计成功的操作
            success_count = sum([
                operations.get("get_collections", False),
                operations.get("create_collection", False),
                operations.get("insert_points", False),
                operations.get("search_points", False),
                operations.get("delete_collection", False)
            ])
            
            total_operations = 5
            success_rate = (success_count / total_operations) * 100
            
            print(f"   📊 操作成功率: {success_count}/{total_operations} ({success_rate:.1f}%)")
            print(f"   ✅ 获取集合: {'成功' if operations.get('get_collections') else '失败'}")
            print(f"   ✅ 创建集合: {'成功' if operations.get('create_collection') else '失败'}")
            print(f"   ✅ 插入向量: {'成功' if operations.get('insert_points') else '失败'}")
            print(f"   ✅ 向量搜索: {'成功' if operations.get('search_points') else '失败'}")
            print(f"   ✅ 删除集合: {'成功' if operations.get('delete_collection') else '失败'}")
            
            if operations.get("errors"):
                print(f"   ❌ 错误信息:")
                for error in operations["errors"]:
                    print(f"      - {error}")
        
        # 总体建议
        print(f"\n💡 建议:")
        http_success = results["tests"]["http"]["client_created"] if "http" in results["tests"] else False
        grpc_success = results["tests"]["grpc"]["client_created"] if "grpc" in results["tests"] else False
        
        if http_success and grpc_success:
            print(f"   🎉 HTTP 和 gRPC 连接都可用")
            print(f"   📝 推荐使用 HTTP (6333) 进行开发，gRPC (6334) 用于高性能场景")
        elif http_success:
            print(f"   ✅ HTTP 连接可用，建议使用端口 6333")
            print(f"   ⚠️  gRPC 连接不可用，检查端口 6334 配置")
        elif grpc_success:
            print(f"   ✅ gRPC 连接可用，可以使用端口 6334")
            print(f"   ⚠️  HTTP 连接不可用，检查端口 6333 配置")
        else:
            print(f"   ❌ 所有连接都不可用")
            print(f"   🔧 请检查 Qdrant 服务是否正在运行")
            print(f"   📝 启动命令: docker-compose -f docker-compose.vector.yml up -d qdrant")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qdrant连接测试工具")
    parser.add_argument("--host", default="localhost", help="Qdrant服务器地址")
    parser.add_argument("--grpc-port", type=int, default=6334, help="gRPC端口 (主要)")
    parser.add_argument("--http-port", type=int, default=6333, help="HTTP端口 (备用)")
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = QdrantTester(host=args.host)
    tester.http_port = args.http_port
    tester.grpc_port = args.grpc_port
    
    try:
        # 运行测试
        results = tester.run_comprehensive_test()
        
        # 打印总结
        tester.print_summary(results)
        
        # 检查是否有任何成功的连接
        http_success = results["tests"]["http"]["client_created"] if "http" in results["tests"] else False
        grpc_success = results["tests"]["grpc"]["client_created"] if "grpc" in results["tests"] else False
        
        if http_success or grpc_success:
            print(f"\n🎉 测试完成，至少有一个连接可用")
            return 0
        else:
            print(f"\n❌ 测试完成，所有连接都不可用")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n⏹️  测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())