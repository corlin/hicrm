#!/usr/bin/env python3
"""
Qdrant集合操作测试

专门测试Qdrant的集合创建、操作和管理功能
"""

import sys
import time
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import (
        Distance, VectorParams, PointStruct, 
        Filter, FieldCondition, MatchValue
    )
except ImportError:
    print("❌ 请先安装 qdrant-client: pip install qdrant-client")
    sys.exit(1)


class QdrantCollectionTester:
    """Qdrant集合测试器"""
    
    def __init__(self, host: str = "localhost", port: int = 6334):
        self.host = host
        self.port = port
        self.client = None
        self.test_collections = []
        
    def connect(self) -> bool:
        """连接到Qdrant"""
        try:
            print(f"🔌 连接到 Qdrant ({self.host}:{self.port})...")
            if self.port == 6334:
                # gRPC连接
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    prefer_grpc=True,
                    timeout=10,
                    check_compatibility=False
                )
            else:
                # HTTP连接
                self.client = QdrantClient(
                    url=f"http://{self.host}:{self.port}",
                    timeout=10,
                    prefer_grpc=False,
                    check_compatibility=False
                )
            
            # 测试连接
            collections = self.client.get_collections()
            print(f"✅ 连接成功，当前有 {len(collections.collections)} 个集合")
            return True
            
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def cleanup_test_collections(self):
        """清理测试集合"""
        if not self.client:
            return
            
        print("🧹 清理测试集合...")
        for collection_name in self.test_collections:
            try:
                self.client.delete_collection(collection_name)
                print(f"   删除集合: {collection_name}")
            except:
                pass
        self.test_collections.clear()
    
    def test_basic_collection_operations(self) -> bool:
        """测试基本集合操作"""
        print("\n📁 测试基本集合操作")
        print("-" * 40)
        
        collection_name = "test_basic_collection"
        self.test_collections.append(collection_name)
        
        try:
            # 1. 创建集合
            print("1. 创建集合...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE)
            )
            print(f"   ✅ 集合 '{collection_name}' 创建成功")
            
            # 2. 获取集合信息
            print("2. 获取集合信息...")
            collection_info = self.client.get_collection(collection_name)
            print(f"   ✅ 向量维度: {collection_info.config.params.vectors.size}")
            print(f"   ✅ 距离度量: {collection_info.config.params.vectors.distance}")
            print(f"   ✅ 点数量: {collection_info.points_count}")
            
            # 3. 列出所有集合
            print("3. 列出所有集合...")
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            print(f"   ✅ 找到集合: {collection_names}")
            
            if collection_name not in collection_names:
                print(f"   ❌ 新创建的集合未在列表中找到")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ 基本操作失败: {e}")
            return False
    
    def test_vector_operations(self) -> bool:
        """测试向量操作"""
        print("\n🔢 测试向量操作")
        print("-" * 40)
        
        collection_name = "test_vector_collection"
        self.test_collections.append(collection_name)
        
        try:
            # 1. 创建集合
            print("1. 创建向量集合...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=256, distance=Distance.COSINE)
            )
            print(f"   ✅ 集合创建成功")
            
            # 2. 插入向量点
            print("2. 插入向量点...")
            points = []
            for i in range(10):
                vector = np.random.rand(256).tolist()
                point = PointStruct(
                    id=i + 1,  # 从1开始，避免0作为ID
                    vector=vector,
                    payload={
                        "text": f"测试文档 {i+1}",
                        "category": "test" if i % 2 == 0 else "demo",
                        "number": i + 1,
                        "is_even": i % 2 == 0
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            print(f"   ✅ 成功插入 {len(points)} 个向量点")
            
            # 等待索引更新
            time.sleep(1)
            
            # 3. 检查点数量
            print("3. 检查点数量...")
            collection_info = self.client.get_collection(collection_name)
            print(f"   ✅ 集合中有 {collection_info.points_count} 个点")
            
            # 4. 向量搜索
            print("4. 执行向量搜索...")
            query_vector = np.random.rand(256).tolist()
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=3
            )
            print(f"   ✅ 搜索返回 {len(search_results)} 个结果")
            
            for i, result in enumerate(search_results):
                payload = result.payload
                print(f"      结果 {i+1}: ID={result.id}, 分数={result.score:.4f}, 文本='{payload.get('text')}'")
            
            # 5. 带过滤的搜索
            print("5. 执行过滤搜索...")
            filtered_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[FieldCondition(key="category", match=MatchValue(value="test"))]
                ),
                limit=3
            )
            print(f"   ✅ 过滤搜索返回 {len(filtered_results)} 个结果")
            
            for i, result in enumerate(filtered_results):
                payload = result.payload
                print(f"      结果 {i+1}: ID={result.id}, 类别='{payload.get('category')}'")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 向量操作失败: {e}")
            return False
    
    def test_advanced_operations(self) -> bool:
        """测试高级操作"""
        print("\n⚙️ 测试高级操作")
        print("-" * 40)
        
        collection_name = "test_advanced_collection"
        self.test_collections.append(collection_name)
        
        try:
            # 1. 创建带优化配置的集合
            print("1. 创建高级配置集合...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=128, distance=Distance.DOT),
                optimizers_config=models.OptimizersConfigDiff(
                    default_segment_number=2,
                    indexing_threshold=1000
                ),
                hnsw_config=models.HnswConfigDiff(
                    m=16,
                    ef_construct=100
                )
            )
            print(f"   ✅ 高级配置集合创建成功")
            
            # 2. 批量插入
            print("2. 批量插入向量...")
            batch_size = 50
            points = []
            
            for i in range(batch_size):
                vector = np.random.rand(128).tolist()
                point = PointStruct(
                    id=i + 1,  # 从1开始，避免0作为ID
                    vector=vector,
                    payload={
                        "title": f"文档标题 {i+1}",
                        "content": f"这是第 {i+1} 个测试文档的内容",
                        "tags": ["tag1", "tag2"] if i % 3 == 0 else ["tag3"],
                        "score": float((i + 1) * 0.1),
                        "published": i % 5 == 0
                    }
                )
                points.append(point)
            
            # 分批插入
            batch_size_insert = 20
            for i in range(0, len(points), batch_size_insert):
                batch = points[i:i + batch_size_insert]
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                print(f"   插入批次 {i//batch_size_insert + 1}: {len(batch)} 个点")
            
            print(f"   ✅ 总共插入 {len(points)} 个向量点")
            
            # 等待索引更新
            time.sleep(2)
            
            # 3. 复杂过滤搜索
            print("3. 执行复杂过滤搜索...")
            query_vector = np.random.rand(128).tolist()
            
            # 多条件过滤
            complex_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="published", match=MatchValue(value=True)),
                        FieldCondition(
                            key="score",
                            range=models.Range(gte=0.0, lte=2.0)
                        )
                    ]
                ),
                limit=5
            )
            print(f"   ✅ 复杂过滤搜索返回 {len(complex_results)} 个结果")
            
            # 4. 获取特定点
            print("4. 获取特定点...")
            specific_points = self.client.retrieve(
                collection_name=collection_name,
                ids=[1, 5, 10],  # 使用从1开始的ID
                with_payload=True,
                with_vectors=False
            )
            print(f"   ✅ 获取到 {len(specific_points)} 个特定点")
            
            for point in specific_points:
                payload = point.payload
                print(f"      点 {point.id}: 标题='{payload.get('title')}'")
            
            # 5. 更新点
            print("5. 更新点数据...")
            self.client.set_payload(
                collection_name=collection_name,
                payload={"updated": True, "update_time": time.time()},
                points=[1, 2, 3]  # 使用从1开始的ID
            )
            print(f"   ✅ 更新了 3 个点的载荷数据")
            
            # 6. 删除点
            print("6. 删除特定点...")
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=[46, 47, 48, 49, 50]  # 调整ID范围
                )
            )
            print(f"   ✅ 删除了 5 个点")
            
            # 验证删除
            final_info = self.client.get_collection(collection_name)
            print(f"   ✅ 最终集合中有 {final_info.points_count} 个点")
            
            return True
            
        except Exception as e:
            print(f"   ❌ 高级操作失败: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 Qdrant 集合操作综合测试")
        print("=" * 50)
        
        if not self.connect():
            return {"connection": False}
        
        results = {"connection": True}
        
        try:
            # 清理可能存在的测试集合
            self.cleanup_test_collections()
            
            # 运行测试
            results["basic_operations"] = self.test_basic_collection_operations()
            results["vector_operations"] = self.test_vector_operations()
            results["advanced_operations"] = self.test_advanced_operations()
            
        finally:
            # 清理测试集合
            self.cleanup_test_collections()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """打印测试总结"""
        print("\n" + "=" * 50)
        print("📋 测试总结")
        print("=" * 50)
        
        total_tests = len(results) - 1  # 排除connection
        passed_tests = sum(1 for k, v in results.items() if k != "connection" and v)
        
        print(f"连接状态: {'✅ 成功' if results.get('connection') else '❌ 失败'}")
        
        if results.get("connection"):
            print(f"基本操作: {'✅ 通过' if results.get('basic_operations') else '❌ 失败'}")
            print(f"向量操作: {'✅ 通过' if results.get('vector_operations') else '❌ 失败'}")
            print(f"高级操作: {'✅ 通过' if results.get('advanced_operations') else '❌ 失败'}")
            
            print(f"\n📊 测试通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
            
            if passed_tests == total_tests:
                print("🎉 所有测试都通过了！Qdrant集合操作功能正常")
            else:
                print("⚠️  部分测试失败，请检查Qdrant配置和服务状态")
        else:
            print("❌ 无法连接到Qdrant，请检查服务是否运行")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Qdrant集合操作测试")
    parser.add_argument("--host", default="localhost", help="Qdrant主机地址")
    parser.add_argument("--port", type=int, default=6334, help="Qdrant端口 (默认6334 gRPC)")
    
    args = parser.parse_args()
    
    # 创建测试器
    tester = QdrantCollectionTester(host=args.host, port=args.port)
    
    try:
        # 运行测试
        results = tester.run_all_tests()
        
        # 打印总结
        tester.print_summary(results)
        
        # 返回适当的退出码
        if results.get("connection") and all(v for k, v in results.items() if k != "connection"):
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        tester.cleanup_test_collections()
        return 1
    except Exception as e:
        print(f"\n💥 测试异常: {e}")
        tester.cleanup_test_collections()
        return 1


if __name__ == "__main__":
    sys.exit(main())