"""
性能和负载测试
"""

import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.customer_service import CustomerService
from src.schemas.customer import CustomerCreate
from src.models.customer import CompanySize


class TestPerformance:
    """性能测试类"""
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, sync_client: TestClient):
        """测试并发API请求性能"""
        
        async def make_request(client: AsyncClient, index: int):
            """发起单个API请求"""
            start_time = time.time()
            
            customer_data = {
                "name": f"性能测试客户{index}",
                "company": f"性能测试公司{index}",
                "industry": "软件开发"
            }
            
            response = await client.post("/api/v1/customers/", json=customer_data)
            end_time = time.time()
            
            return {
                "success": response.status_code == 200,
                "response_time": end_time - start_time,
                "index": index
            }
        
        # 并发请求数量
        concurrent_requests = 50
        
        start_time = time.time()
        
        # 使用AsyncClient进行并发测试
        async with AsyncClient(app=sync_client.app, base_url="http://test") as client:
            tasks = [make_request(client, i) for i in range(concurrent_requests)]
            results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 分析结果
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        response_times = [r["response_time"] for r in successful_requests]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        
        # 性能断言
        assert len(successful_requests) >= concurrent_requests * 0.95  # 95%成功率
        assert avg_response_time < 2.0  # 平均响应时间小于2秒
        assert max_response_time < 5.0  # 最大响应时间小于5秒
        assert total_time < 10.0  # 总时间小于10秒
        
        print(f"\n性能测试结果:")
        print(f"总请求数: {concurrent_requests}")
        print(f"成功请求数: {len(successful_requests)}")
        print(f"失败请求数: {len(failed_requests)}")
        print(f"成功率: {len(successful_requests)/concurrent_requests*100:.2f}%")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均响应时间: {avg_response_time:.3f}秒")
        print(f"最小响应时间: {min_response_time:.3f}秒")
        print(f"最大响应时间: {max_response_time:.3f}秒")
        print(f"QPS: {len(successful_requests)/total_time:.2f}")
    
    @pytest.mark.asyncio
    async def test_database_performance(self, db_session: AsyncSession):
        """测试数据库操作性能"""
        customer_service = CustomerService(db_session)
        
        # 批量创建客户数据
        batch_size = 100
        customers_data = [
            CustomerCreate(
                name=f"批量客户{i}",
                company=f"批量公司{i}",
                industry="软件开发",
                size=CompanySize.MEDIUM
            )
            for i in range(batch_size)
        ]
        
        # 测试批量创建性能
        start_time = time.time()
        
        created_customers = []
        for customer_data in customers_data:
            customer = await customer_service.create_customer(customer_data)
            created_customers.append(customer)
        
        create_time = time.time() - start_time
        
        # 测试批量查询性能
        start_time = time.time()
        
        all_customers = await customer_service.get_customers(limit=batch_size * 2)
        
        query_time = time.time() - start_time
        
        # 测试搜索性能
        start_time = time.time()
        
        search_results = await customer_service.search_customers("批量")
        
        search_time = time.time() - start_time
        
        # 性能断言
        assert create_time < 30.0  # 创建100个客户应在30秒内完成
        assert query_time < 2.0    # 查询应在2秒内完成
        assert search_time < 3.0   # 搜索应在3秒内完成
        assert len(created_customers) == batch_size
        assert len(search_results) >= batch_size
        
        print(f"\n数据库性能测试结果:")
        print(f"批量创建{batch_size}个客户耗时: {create_time:.2f}秒")
        print(f"平均创建时间: {create_time/batch_size:.3f}秒/个")
        print(f"批量查询耗时: {query_time:.3f}秒")
        print(f"搜索耗时: {search_time:.3f}秒")
        print(f"搜索结果数量: {len(search_results)}")
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, sync_client: TestClient):
        """测试负载下的内存使用情况"""
        import psutil
        import os
        
        # 获取当前进程
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 创建大量客户数据
        customer_count = 200
        
        for i in range(customer_count):
            customer_data = {
                "name": f"内存测试客户{i}",
                "company": f"内存测试公司{i}",
                "industry": "软件开发",
                "contact": {
                    "phone": f"1380013{i:04d}",
                    "email": f"test{i}@example.com"
                },
                "profile": {
                    "decision_making_style": "数据驱动",
                    "business_priorities": ["降本增效", "数字化转型"],
                    "pain_points": ["效率低下", "成本过高"]
                },
                "tags": [f"标签{i}", "测试标签"],
                "notes": f"这是第{i}个测试客户的详细描述信息" * 10  # 增加数据量
            }
            
            response = sync_client.post("/api/v1/customers/", json=customer_data)
            assert response.status_code == 200
            
            # 每50个客户检查一次内存
            if (i + 1) % 50 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                print(f"创建{i+1}个客户后，内存使用: {current_memory:.2f}MB, 增长: {memory_increase:.2f}MB")
                
                # 内存增长不应该过快（每50个客户增长不超过100MB）
                assert memory_increase < 100 * ((i + 1) // 50)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"\n内存使用测试结果:")
        print(f"初始内存: {initial_memory:.2f}MB")
        print(f"最终内存: {final_memory:.2f}MB")
        print(f"总内存增长: {total_memory_increase:.2f}MB")
        print(f"平均每个客户内存消耗: {total_memory_increase/customer_count:.3f}MB")
        
        # 总内存增长不应该超过500MB
        assert total_memory_increase < 500
    
    @pytest.mark.asyncio
    async def test_response_time_distribution(self, sync_client: TestClient):
        """测试响应时间分布"""
        
        response_times = []
        request_count = 100
        
        for i in range(request_count):
            customer_data = {
                "name": f"响应时间测试客户{i}",
                "company": f"响应时间测试公司{i}",
                "industry": "软件开发"
            }
            
            start_time = time.time()
            response = sync_client.post("/api/v1/customers/", json=customer_data)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append(end_time - start_time)
        
        # 计算统计信息
        response_times.sort()
        
        avg_time = sum(response_times) / len(response_times)
        median_time = response_times[len(response_times) // 2]
        p95_time = response_times[int(len(response_times) * 0.95)]
        p99_time = response_times[int(len(response_times) * 0.99)]
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"\n响应时间分布测试结果:")
        print(f"请求总数: {request_count}")
        print(f"平均响应时间: {avg_time:.3f}秒")
        print(f"中位数响应时间: {median_time:.3f}秒")
        print(f"95%响应时间: {p95_time:.3f}秒")
        print(f"99%响应时间: {p99_time:.3f}秒")
        print(f"最小响应时间: {min_time:.3f}秒")
        print(f"最大响应时间: {max_time:.3f}秒")
        
        # 性能要求
        assert avg_time < 1.0      # 平均响应时间小于1秒
        assert median_time < 0.8   # 中位数响应时间小于0.8秒
        assert p95_time < 2.0      # 95%响应时间小于2秒
        assert p99_time < 3.0      # 99%响应时间小于3秒
    
    @pytest.mark.asyncio
    async def test_database_connection_pool_performance(self, db_session: AsyncSession):
        """测试数据库连接池性能"""
        
        async def database_operation(index: int):
            """单个数据库操作"""
            customer_service = CustomerService(db_session)
            
            start_time = time.time()
            
            # 创建客户
            customer_data = CustomerCreate(
                name=f"连接池测试客户{index}",
                company=f"连接池测试公司{index}",
                industry="软件开发"
            )
            
            customer = await customer_service.create_customer(customer_data)
            
            # 查询客户
            retrieved_customer = await customer_service.get_customer(str(customer.id))
            
            end_time = time.time()
            
            return {
                "success": retrieved_customer is not None,
                "operation_time": end_time - start_time,
                "customer_id": str(customer.id)
            }
        
        # 并发数据库操作
        concurrent_operations = 20
        
        start_time = time.time()
        tasks = [database_operation(i) for i in range(concurrent_operations)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        successful_operations = [r for r in results if r["success"]]
        operation_times = [r["operation_time"] for r in successful_operations]
        
        avg_operation_time = sum(operation_times) / len(operation_times) if operation_times else 0
        
        print(f"\n数据库连接池性能测试结果:")
        print(f"并发操作数: {concurrent_operations}")
        print(f"成功操作数: {len(successful_operations)}")
        print(f"总耗时: {total_time:.2f}秒")
        print(f"平均单操作时间: {avg_operation_time:.3f}秒")
        print(f"操作吞吐量: {len(successful_operations)/total_time:.2f}ops/s")
        
        # 性能断言
        assert len(successful_operations) == concurrent_operations  # 所有操作都应该成功
        assert avg_operation_time < 1.0  # 平均操作时间小于1秒
        assert total_time < 10.0  # 总时间小于10秒