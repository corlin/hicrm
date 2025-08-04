"""
客户服务层
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid
import logging

from src.models.customer import Customer
from src.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from src.core.database import get_db

logger = logging.getLogger(__name__)


class CustomerService:
    """客户服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_customers(
        self, 
        skip: int = 0, 
        limit: int = 100,
        industry: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Customer]:
        """获取客户列表"""
        try:
            query = select(Customer)
            
            # 添加过滤条件
            if industry:
                query = query.where(Customer.industry == industry)
            if status:
                query = query.where(Customer.status == status)
            
            # 分页
            query = query.offset(skip).limit(limit)
            query = query.order_by(Customer.created_at.desc())
            
            result = await self.db.execute(query)
            customers = result.scalars().all()
            
            logger.info(f"获取客户列表成功，返回 {len(customers)} 条记录")
            return customers
            
        except Exception as e:
            logger.error(f"获取客户列表失败: {e}")
            raise
    
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        """根据ID获取客户"""
        try:
            # 验证UUID格式
            uuid.UUID(customer_id)
            
            query = select(Customer).where(Customer.id == customer_id)
            result = await self.db.execute(query)
            customer = result.scalar_one_or_none()
            
            if customer:
                logger.info(f"获取客户成功: {customer.name}")
            else:
                logger.warning(f"客户不存在: {customer_id}")
            
            return customer
            
        except ValueError:
            logger.error(f"无效的客户ID格式: {customer_id}")
            return None
        except Exception as e:
            logger.error(f"获取客户失败: {e}")
            raise
    
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """创建新客户"""
        try:
            # 转换Pydantic模型为字典
            customer_dict = customer_data.model_dump()
            
            # 处理嵌套对象
            if customer_dict.get('contact'):
                customer_dict['contact'] = customer_data.contact.model_dump() if customer_data.contact else None
            if customer_dict.get('profile'):
                customer_dict['profile'] = customer_data.profile.model_dump() if customer_data.profile else None
            
            # 创建客户实例
            customer = Customer(**customer_dict)
            
            # 保存到数据库
            self.db.add(customer)
            await self.db.commit()
            await self.db.refresh(customer)
            
            logger.info(f"创建客户成功: {customer.name} ({customer.id})")
            return customer
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"创建客户失败: {e}")
            raise
    
    async def update_customer(
        self, 
        customer_id: str, 
        customer_data: CustomerUpdate
    ) -> Optional[Customer]:
        """更新客户信息"""
        try:
            # 获取现有客户
            customer = await self.get_customer(customer_id)
            if not customer:
                return None
            
            # 更新字段
            update_data = customer_data.model_dump(exclude_unset=True)
            
            # 处理嵌套对象
            if 'contact' in update_data and update_data['contact']:
                update_data['contact'] = customer_data.contact.model_dump() if customer_data.contact else None
            if 'profile' in update_data and update_data['profile']:
                update_data['profile'] = customer_data.profile.model_dump() if customer_data.profile else None
            
            # 应用更新
            for field, value in update_data.items():
                setattr(customer, field, value)
            
            await self.db.commit()
            await self.db.refresh(customer)
            
            logger.info(f"更新客户成功: {customer.name} ({customer.id})")
            return customer
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"更新客户失败: {e}")
            raise
    
    async def delete_customer(self, customer_id: str) -> bool:
        """删除客户"""
        try:
            customer = await self.get_customer(customer_id)
            if not customer:
                return False
            
            await self.db.delete(customer)
            await self.db.commit()
            
            logger.info(f"删除客户成功: {customer.name} ({customer.id})")
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"删除客户失败: {e}")
            raise
    
    async def get_customers_count(
        self,
        industry: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """获取客户总数"""
        try:
            query = select(func.count(Customer.id))
            
            # 添加过滤条件
            if industry:
                query = query.where(Customer.industry == industry)
            if status:
                query = query.where(Customer.status == status)
            
            result = await self.db.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"获取客户总数失败: {e}")
            raise
    
    async def search_customers(
        self, 
        query: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[Customer]:
        """搜索客户"""
        try:
            # 使用PostgreSQL的全文搜索
            search_query = select(Customer).where(
                Customer.name.ilike(f"%{query}%") |
                Customer.company.ilike(f"%{query}%") |
                Customer.industry.ilike(f"%{query}%")
            ).offset(skip).limit(limit).order_by(Customer.created_at.desc())
            
            result = await self.db.execute(search_query)
            customers = result.scalars().all()
            
            logger.info(f"搜索客户成功，查询: '{query}'，返回 {len(customers)} 条记录")
            return customers
            
        except Exception as e:
            logger.error(f"搜索客户失败: {e}")
            raise