"""
客户管理工作流集成测试
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.services.customer_service import CustomerService
from src.schemas.customer import CustomerCreate, ContactInfo, CustomerProfile
from src.models.customer import CompanySize, CustomerStatus


class TestCustomerWorkflowIntegration:
    """客户管理工作流集成测试类"""
    
    @pytest.fixture
    def customer_service(self, db_session: AsyncSession):
        """客户服务实例"""
        return CustomerService(db_session)
    
    @pytest.fixture
    def complete_customer_data(self):
        """完整的客户数据"""
        return {
            "name": "集成测试客户",
            "company": "集成测试科技有限公司",
            "industry": "人工智能",
            "size": "large",
            "contact": {
                "phone": "13800138000",
                "email": "integration@test.com",
                "address": "北京市朝阳区测试大厦",
                "wechat": "integration_test"
            },
            "profile": {
                "decision_making_style": "数据驱动",
                "communication_preference": "邮件",
                "business_priorities": ["数字化转型", "降本增效", "业务创新"],
                "pain_points": ["系统集成复杂", "数据孤岛", "决策效率低"],
                "budget": {
                    "range": "100-500万",
                    "decision_cycle": "3-6个月"
                },
                "timeline": "2024年Q2实施",
                "influencers": ["CTO", "CFO", "业务部门负责人"]
            },
            "status": "qualified",
            "tags": ["重点客户", "AI行业", "大客户"],
            "notes": "通过行业峰会认识，对我们的AI解决方案很感兴趣"
        }
    
    @pytest.mark.asyncio
    async def test_complete_customer_lifecycle_api(self, sync_client: TestClient, complete_customer_data: dict):
        """测试完整的客户生命周期API流程"""
        
        # 1. 创建客户
        create_response = sync_client.post("/api/v1/customers/", json=complete_customer_data)
        assert create_response.status_code == 200
        
        created_customer = create_response.json()
        customer_id = created_customer["id"]
        
        # 验证创建结果
        assert created_customer["name"] == "集成测试客户"
        assert created_customer["company"] == "集成测试科技有限公司"
        assert created_customer["industry"] == "人工智能"
        assert created_customer["size"] == "large"
        assert created_customer["status"] == "qualified"
        assert len(created_customer["tags"]) == 3
        
        # 2. 获取客户详情
        get_response = sync_client.get(f"/api/v1/customers/{customer_id}")
        assert get_response.status_code == 200
        
        customer_detail = get_response.json()
        assert customer_detail["id"] == customer_id
        assert customer_detail["contact"]["phone"] == "13800138000"
        assert customer_detail["profile"]["decision_making_style"] == "数据驱动"
        
        # 3. 更新客户信息
        update_data = {
            "status": "customer",
            "notes": "已成功签约，进入实施阶段",
            "profile": {
                "decision_making_style": "数据驱动",
                "communication_preference": "电话",
                "business_priorities": ["数字化转型", "降本增效", "业务创新", "客户体验提升"],
                "pain_points": ["系统集成复杂", "数据孤岛"],
                "budget": {
                    "range": "200-300万",
                    "decision_cycle": "已确定"
                },
                "timeline": "2024年Q2实施",
                "influencers": ["CTO", "CFO", "业务部门负责人"]
            },
            "tags": ["重点客户", "AI行业", "大客户", "已签约"]
        }
        
        update_response = sync_client.put(f"/api/v1/customers/{customer_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_customer = update_response.json()
        assert updated_customer["status"] == "customer"
        assert updated_customer["notes"] == "已成功签约，进入实施阶段"
        assert len(updated_customer["tags"]) == 4
        assert "已签约" in updated_customer["tags"]
        
        # 4. 搜索客户
        search_response = sync_client.get("/api/v1/customers/?search=集成测试")
        assert search_response.status_code == 200
        
        search_results = search_response.json()
        assert len(search_results) >= 1
        assert any(customer["id"] == customer_id for customer in search_results)
        
        # 5. 按行业筛选
        industry_response = sync_client.get("/api/v1/customers/?industry=人工智能")
        assert industry_response.status_code == 200
        
        industry_results = industry_response.json()
        assert len(industry_results) >= 1
        assert all(customer["industry"] == "人工智能" for customer in industry_results)
        
        # 6. 删除客户
        delete_response = sync_client.delete(f"/api/v1/customers/{customer_id}")
        assert delete_response.status_code == 200
        
        # 7. 验证删除
        get_deleted_response = sync_client.get(f"/api/v1/customers/{customer_id}")
        assert get_deleted_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_customer_service_integration(self, customer_service: CustomerService, complete_customer_data: dict):
        """测试客户服务层集成"""
        
        # 转换为服务层数据格式
        customer_create = CustomerCreate(
            name=complete_customer_data["name"],
            company=complete_customer_data["company"],
            industry=complete_customer_data["industry"],
            size=CompanySize(complete_customer_data["size"]),
            contact=ContactInfo(**complete_customer_data["contact"]),
            profile=CustomerProfile(**complete_customer_data["profile"]),
            status=CustomerStatus(complete_customer_data["status"]),
            tags=complete_customer_data["tags"],
            notes=complete_customer_data["notes"]
        )
        
        # 1. 创建客户
        created_customer = await customer_service.create_customer(customer_create)
        assert created_customer.id is not None
        assert created_customer.name == "集成测试客户"
        
        # 2. 批量操作测试
        batch_customers = []
        for i in range(5):
            batch_data = CustomerCreate(
                name=f"批量客户{i}",
                company=f"批量公司{i}",
                industry="软件开发",
                size=CompanySize.MEDIUM
            )
            batch_customer = await customer_service.create_customer(batch_data)
            batch_customers.append(batch_customer)
        
        # 3. 分页查询测试
        page1 = await customer_service.get_customers(skip=0, limit=3)
        page2 = await customer_service.get_customers(skip=3, limit=3)
        
        assert len(page1) <= 3
        assert len(page2) <= 3
        
        # 验证分页数据不重复
        page1_ids = {customer.id for customer in page1}
        page2_ids = {customer.id for customer in page2}
        assert len(page1_ids.intersection(page2_ids)) == 0
        
        # 4. 复杂搜索测试
        search_results = await customer_service.search_customers("批量")
        assert len(search_results) >= 5
        
        # 5. 统计功能测试
        total_count = await customer_service.get_customers_count()
        assert total_count >= 6  # 1个主测试客户 + 5个批量客户
        
        industry_count = await customer_service.get_customers_count(industry="软件开发")
        assert industry_count >= 5  # 5个批量客户
    
    @pytest.mark.asyncio
    async def test_concurrent_customer_operations(self, sync_client: TestClient):
        """测试并发客户操作"""
        import asyncio
        import httpx
        
        async def create_customer(client: httpx.AsyncClient, index: int):
            """创建单个客户"""
            customer_data = {
                "name": f"并发客户{index}",
                "company": f"并发公司{index}",
                "industry": "软件开发",
                "size": "medium"
            }
            
            response = await client.post("/api/v1/customers/", json=customer_data)
            return response.status_code == 200, response.json() if response.status_code == 200 else None
        
        # 并发创建多个客户
        async with httpx.AsyncClient(app=sync_client.app, base_url="http://test") as client:
            tasks = [create_customer(client, i) for i in range(10)]
            results = await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        success_count = sum(1 for success, _ in results if success)
        assert success_count == 10
        
        # 验证创建的客户数据
        created_customers = [data for success, data in results if success and data]
        assert len(created_customers) == 10
        
        # 验证客户名称唯一性
        customer_names = {customer["name"] for customer in created_customers}
        assert len(customer_names) == 10
    
    @pytest.mark.asyncio
    async def test_customer_data_validation_integration(self, sync_client: TestClient):
        """测试客户数据验证集成"""
        
        # 测试各种无效数据
        invalid_cases = [
            # 缺少必填字段
            {"company": "测试公司"},  # 缺少name
            {"name": "测试客户"},     # 缺少company
            
            # 无效的枚举值
            {
                "name": "测试客户",
                "company": "测试公司",
                "size": "invalid_size"
            },
            {
                "name": "测试客户",
                "company": "测试公司",
                "status": "invalid_status"
            },
            
            # 无效的联系信息格式
            {
                "name": "测试客户",
                "company": "测试公司",
                "contact": {
                    "email": "invalid_email"  # 无效邮箱格式
                }
            },
            
            # 空字符串
            {
                "name": "",
                "company": "测试公司"
            },
            {
                "name": "测试客户",
                "company": ""
            }
        ]
        
        for invalid_data in invalid_cases:
            response = sync_client.post("/api/v1/customers/", json=invalid_data)
            assert response.status_code == 422, f"应该拒绝无效数据: {invalid_data}"
    
    @pytest.mark.asyncio
    async def test_customer_relationship_data_integrity(self, customer_service: CustomerService):
        """测试客户关系数据完整性"""
        
        # 创建主客户
        main_customer = await customer_service.create_customer(
            CustomerCreate(
                name="主要联系人",
                company="测试集团",
                industry="金融服务"
            )
        )
        
        # 创建关联客户
        related_customer = await customer_service.create_customer(
            CustomerCreate(
                name="次要联系人",
                company="测试集团子公司",
                industry="金融服务"
            )
        )
        
        # 验证客户创建成功
        assert main_customer.id != related_customer.id
        assert main_customer.company != related_customer.company
        
        # 测试按公司搜索能找到相关客户
        company_customers = await customer_service.search_customers("测试集团")
        assert len(company_customers) >= 2
        
        company_names = {customer.company for customer in company_customers}
        assert "测试集团" in company_names
        assert "测试集团子公司" in company_names