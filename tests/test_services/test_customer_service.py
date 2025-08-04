"""
客户服务测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.services.customer_service import CustomerService
from src.schemas.customer import CustomerCreate, CustomerUpdate, ContactInfo, CustomerProfile
from src.models.customer import CompanySize, CustomerStatus


class TestCustomerService:
    """客户服务测试类"""
    
    @pytest.fixture
    def customer_service(self, db_session: AsyncSession):
        """客户服务实例"""
        return CustomerService(db_session)
    
    @pytest.fixture
    def sample_customer_data(self):
        """示例客户数据"""
        return CustomerCreate(
            name="测试客户",
            company="测试公司",
            industry="软件开发",
            size=CompanySize.MEDIUM,
            contact=ContactInfo(
                phone="13800138000",
                email="test@example.com"
            ),
            profile=CustomerProfile(
                decision_making_style="数据驱动",
                business_priorities=["降本增效"],
                pain_points=["效率低下"]
            ),
            tags=["测试", "重要"],
            notes="这是一个测试客户"
        )
    
    @pytest.mark.asyncio
    async def test_create_customer(self, customer_service: CustomerService, sample_customer_data: CustomerCreate):
        """测试创建客户"""
        customer = await customer_service.create_customer(sample_customer_data)
        
        assert customer.id is not None
        assert customer.name == "测试客户"
        assert customer.company == "测试公司"
        assert customer.industry == "软件开发"
        assert customer.size == CompanySize.MEDIUM
        assert customer.contact["phone"] == "13800138000"
        assert customer.profile["decision_making_style"] == "数据驱动"
        assert "测试" in customer.tags
        assert customer.notes == "这是一个测试客户"
    
    @pytest.mark.asyncio
    async def test_get_customer(self, customer_service: CustomerService, sample_customer_data: CustomerCreate):
        """测试获取客户"""
        # 创建客户
        created_customer = await customer_service.create_customer(sample_customer_data)
        
        # 获取客户
        customer = await customer_service.get_customer(str(created_customer.id))
        
        assert customer is not None
        assert customer.id == created_customer.id
        assert customer.name == "测试客户"
        assert customer.company == "测试公司"
    
    @pytest.mark.asyncio
    async def test_get_customer_not_found(self, customer_service: CustomerService):
        """测试获取不存在的客户"""
        non_existent_id = str(uuid.uuid4())
        customer = await customer_service.get_customer(non_existent_id)
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_get_customer_invalid_id(self, customer_service: CustomerService):
        """测试获取客户时使用无效ID"""
        customer = await customer_service.get_customer("invalid-id")
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_update_customer(self, customer_service: CustomerService, sample_customer_data: CustomerCreate):
        """测试更新客户"""
        # 创建客户
        created_customer = await customer_service.create_customer(sample_customer_data)
        
        # 更新数据
        update_data = CustomerUpdate(
            name="更新后的客户",
            industry="制造业",
            contact=ContactInfo(
                phone="13900139000",
                email="updated@example.com"
            )
        )
        
        # 执行更新
        updated_customer = await customer_service.update_customer(
            str(created_customer.id), 
            update_data
        )
        
        assert updated_customer is not None
        assert updated_customer.name == "更新后的客户"
        assert updated_customer.industry == "制造业"
        assert updated_customer.contact["phone"] == "13900139000"
        assert updated_customer.company == "测试公司"  # 未更新的字段保持不变
    
    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, customer_service: CustomerService):
        """测试更新不存在的客户"""
        non_existent_id = str(uuid.uuid4())
        update_data = CustomerUpdate(name="不存在的客户")
        
        result = await customer_service.update_customer(non_existent_id, update_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_customer(self, customer_service: CustomerService, sample_customer_data: CustomerCreate):
        """测试删除客户"""
        # 创建客户
        created_customer = await customer_service.create_customer(sample_customer_data)
        
        # 删除客户
        success = await customer_service.delete_customer(str(created_customer.id))
        
        assert success is True
        
        # 验证客户已被删除
        deleted_customer = await customer_service.get_customer(str(created_customer.id))
        assert deleted_customer is None
    
    @pytest.mark.asyncio
    async def test_delete_customer_not_found(self, customer_service: CustomerService):
        """测试删除不存在的客户"""
        non_existent_id = str(uuid.uuid4())
        success = await customer_service.delete_customer(non_existent_id)
        
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_customers_list(self, customer_service: CustomerService):
        """测试获取客户列表"""
        # 创建多个客户
        customers_data = [
            CustomerCreate(name=f"客户{i}", company=f"公司{i}", industry="软件开发")
            for i in range(5)
        ]
        
        for customer_data in customers_data:
            await customer_service.create_customer(customer_data)
        
        # 获取客户列表
        customers = await customer_service.get_customers(skip=0, limit=10)
        
        assert len(customers) >= 5
        assert all(customer.name.startswith("客户") for customer in customers[:5])
    
    @pytest.mark.asyncio
    async def test_get_customers_with_filters(self, customer_service: CustomerService):
        """测试带过滤条件的客户列表"""
        # 创建不同行业的客户
        await customer_service.create_customer(
            CustomerCreate(name="软件客户", company="软件公司", industry="软件开发")
        )
        await customer_service.create_customer(
            CustomerCreate(name="制造客户", company="制造公司", industry="制造业")
        )
        
        # 按行业过滤
        software_customers = await customer_service.get_customers(industry="软件开发")
        manufacturing_customers = await customer_service.get_customers(industry="制造业")
        
        assert len(software_customers) >= 1
        assert len(manufacturing_customers) >= 1
        assert all(c.industry == "软件开发" for c in software_customers)
        assert all(c.industry == "制造业" for c in manufacturing_customers)
    
    @pytest.mark.asyncio
    async def test_search_customers(self, customer_service: CustomerService):
        """测试搜索客户"""
        # 创建测试客户
        await customer_service.create_customer(
            CustomerCreate(name="张三", company="ABC科技", industry="软件开发")
        )
        await customer_service.create_customer(
            CustomerCreate(name="李四", company="XYZ制造", industry="制造业")
        )
        
        # 搜索客户
        results = await customer_service.search_customers("张三")
        assert len(results) >= 1
        assert any(customer.name == "张三" for customer in results)
        
        results = await customer_service.search_customers("ABC")
        assert len(results) >= 1
        assert any(customer.company == "ABC科技" for customer in results)
    
    @pytest.mark.asyncio
    async def test_get_customers_count(self, customer_service: CustomerService):
        """测试获取客户总数"""
        # 创建测试客户
        for i in range(3):
            await customer_service.create_customer(
                CustomerCreate(name=f"计数客户{i}", company=f"计数公司{i}")
            )
        
        count = await customer_service.get_customers_count()
        assert count >= 3