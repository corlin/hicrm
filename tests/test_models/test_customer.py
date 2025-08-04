"""
客户模型测试
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from src.models.customer import Customer, CompanySize, CustomerStatus


class TestCustomerModel:
    """客户模型测试类"""
    
    @pytest.mark.asyncio
    async def test_create_customer(self, db_session: AsyncSession):
        """测试创建客户"""
        customer_data = {
            "name": "张三",
            "company": "ABC科技有限公司",
            "industry": "软件开发",
            "size": CompanySize.MEDIUM,
            "contact": {
                "phone": "13800138000",
                "email": "zhangsan@abc.com"
            },
            "profile": {
                "decision_making_style": "数据驱动",
                "business_priorities": ["降本增效", "数字化转型"]
            },
            "status": CustomerStatus.PROSPECT,
            "tags": ["重点客户", "技术型"],
            "notes": "通过展会认识的潜在客户"
        }
        
        customer = Customer(**customer_data)
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        assert customer.id is not None
        assert customer.name == "张三"
        assert customer.company == "ABC科技有限公司"
        assert customer.industry == "软件开发"
        assert customer.size == CompanySize.MEDIUM
        assert customer.status == CustomerStatus.PROSPECT
        assert customer.contact["phone"] == "13800138000"
        assert customer.profile["decision_making_style"] == "数据驱动"
        assert "重点客户" in customer.tags
        assert customer.created_at is not None
        assert customer.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_customer_repr(self, db_session: AsyncSession):
        """测试客户字符串表示"""
        customer = Customer(
            name="李四",
            company="XYZ公司",
            industry="制造业"
        )
        
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        repr_str = repr(customer)
        assert "Customer" in repr_str
        assert customer.name in repr_str
        assert customer.company in repr_str
        assert str(customer.id) in repr_str
    
    @pytest.mark.asyncio
    async def test_customer_enums(self):
        """测试枚举值"""
        # 测试公司规模枚举
        assert CompanySize.STARTUP == "startup"
        assert CompanySize.SMALL == "small"
        assert CompanySize.MEDIUM == "medium"
        assert CompanySize.LARGE == "large"
        assert CompanySize.ENTERPRISE == "enterprise"
        
        # 测试客户状态枚举
        assert CustomerStatus.PROSPECT == "prospect"
        assert CustomerStatus.QUALIFIED == "qualified"
        assert CustomerStatus.CUSTOMER == "customer"
        assert CustomerStatus.INACTIVE == "inactive"
    
    @pytest.mark.asyncio
    async def test_customer_minimal_data(self, db_session: AsyncSession):
        """测试最小数据创建客户"""
        customer = Customer(
            name="王五",
            company="最小数据公司"
        )
        
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        assert customer.id is not None
        assert customer.name == "王五"
        assert customer.company == "最小数据公司"
        assert customer.status == CustomerStatus.PROSPECT  # 默认状态
        assert customer.industry is None
        assert customer.size is None
        assert customer.contact is None
        assert customer.profile is None