"""
线索服务测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.lead_service import LeadService
from src.models.lead import Lead, LeadScore, LeadInteraction, LeadStatus, LeadSource
from src.schemas.lead import (
    LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    InteractionCreate, InteractionResponse, LeadStatistics,
    LeadAssignmentRequest, LeadAssignmentResponse,
    ContactInfo, CompanyInfo
)
from src.core.database import Base, engine


@pytest.fixture
async def db_session():
    """创建测试数据库会话"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    from src.core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def lead_service():
    """创建线索服务实例"""
    return LeadService()


@pytest.fixture
def sample_lead_create():
    """示例线索创建数据"""
    return LeadCreate(
        name="张三",
        company="测试科技有限公司",
        title="技术总监",
        industry="technology",
        contact=ContactInfo(
            email="zhangsan@test.com",
            phone="13800138000",
            wechat="zhangsan_wx"
        ),
        company_info=CompanyInfo(
            size="medium",
            revenue=50000000,
            employees=200,
            website="https://test.com"
        ),
        requirements="需要CRM系统来管理客户关系",
        budget=100000.0,
        timeline="3个月",
        source=LeadSource.WEBSITE,
        status=LeadStatus.NEW,
        tags=["高优先级", "技术决策者"],
        notes="通过官网表单提交的线索",
        custom_fields={"industry_segment": "SaaS"}
    )


@pytest.fixture
async def sample_lead_in_db(db_session: AsyncSession, sample_lead_create: LeadCreate):
    """在数据库中创建示例线索"""
    lead = Lead(
        name=sample_lead_create.name,
        company=sample_lead_create.company,
        title=sample_lead_create.title,
        industry=sample_lead_create.industry,
        contact=sample_lead_create.contact.dict(),
        company_info=sample_lead_create.company_info.dict(),
        requirements=sample_lead_create.requirements,
        budget=sample_lead_create.budget,
        timeline=sample_lead_create.timeline,
        source=sample_lead_create.source,
        status=sample_lead_create.status,
        tags=sample_lead_create.tags,
        notes=sample_lead_create.notes,
        custom_fields=sample_lead_create.custom_fields
    )
    
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)
    return lead


class TestLeadService:
    """线索服务测试类"""
    
    async def test_create_lead(
        self,
        lead_service: LeadService,
        db_session: AsyncSession,
        sample_lead_create: LeadCreate
    ):
        """测试创建线索"""
        # Mock评分服务以避免复杂的评分计算
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.5
            mock_score.return_value.confidence = 0.85
            
            response = await lead_service.create_lead(sample_lead_create, db_session)
        
        # 验证响应
        assert isinstance(response, LeadResponse)
        assert response.name == sample_lead_create.name
        assert response.company == sample_lead_create.company
        assert response.title == sample_lead_create.title
        assert response.industry == sample_lead_create.industry
        assert response.budget == sample_lead_create.budget
        assert response.timeline == sample_lead_create.timeline
        assert response.source == sample_lead_create.source
        assert response.status == sample_lead_create.status
        assert response.tags == sample_lead_create.tags
        assert response.notes == sample_lead_create.notes
        assert response.custom_fields == sample_lead_create.custom_fields
        assert response.id is not None
        assert response.created_at is not None
        assert response.updated_at is not None
        
        # 验证联系信息
        assert response.contact.email == sample_lead_create.contact.email
        assert response.contact.phone == sample_lead_create.contact.phone
        
        # 验证公司信息
        assert response.company_info.size == sample_lead_create.company_info.size
        assert response.company_info.revenue == sample_lead_create.company_info.revenue
    
    async def test_get_lead(
        self,
        lead_service: LeadService,
        db_session: AsyncSession,
        sample_lead_in_db: Lead
    ):
        """测试获取线索详情"""
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.5
            
            response = await lead_service.get_lead(str(sample_lead_in_db.id), db_session)
        
        assert response is not None
        assert isinstance(response, LeadResponse)
        assert response.id == str(sample_lead_in_db.id)
        assert response.name == sample_lead_in_db.name
        assert response.company == sample_lead_in_db.company
    
    async def test_get_lead_not_found(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试获取不存在的线索"""
        response = await lead_service.get_lead("non-existent-id", db_session)
        assert response is None
    
    async def test_update_lead(
        self,
        lead_service: LeadService,
        db_session: AsyncSession,
        sample_lead_in_db: Lead
    ):
        """测试更新线索"""
        update_data = LeadUpdate(
            name="李四",
            company="更新后的公司",
            budget=200000.0,
            status=LeadStatus.QUALIFIED,
            assigned_to="销售代表A"
        )
        
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 80.0
            
            response = await lead_service.update_lead(
                str(sample_lead_in_db.id), update_data, db_session
            )
        
        assert response is not None
        assert response.name == "李四"
        assert response.company == "更新后的公司"
        assert response.budget == 200000.0
        assert response.status == LeadStatus.QUALIFIED
        assert response.assigned_to == "销售代表A"
        assert response.assigned_at is not None
        assert response.updated_at > sample_lead_in_db.updated_at
    
    async def test_update_lead_not_found(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试更新不存在的线索"""
        update_data = LeadUpdate(name="新名称")
        response = await lead_service.update_lead("non-existent-id", update_data, db_session)
        assert response is None
    
    async def test_delete_lead(
        self,
        lead_service: LeadService,
        db_session: AsyncSession,
        sample_lead_in_db: Lead
    ):
        """测试删除线索"""
        lead_id = str(sample_lead_in_db.id)
        
        # 删除线索
        result = await lead_service.delete_lead(lead_id, db_session)
        assert result is True
        
        # 验证线索已被删除
        response = await lead_service.get_lead(lead_id, db_session)
        assert response is None
    
    async def test_delete_lead_not_found(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试删除不存在的线索"""
        result = await lead_service.delete_lead("non-existent-id", db_session)
        assert result is False
    
    async def test_list_leads_basic(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试基本线索列表查询"""
        # 创建多个线索
        leads_data = [
            {
                "name": f"用户{i+1}",
                "company": f"公司{i+1}",
                "industry": "technology",
                "source": LeadSource.WEBSITE,
                "status": LeadStatus.NEW if i % 2 == 0 else LeadStatus.QUALIFIED,
                "budget": 50000 * (i + 1)
            }
            for i in range(5)
        ]
        
        for lead_data in leads_data:
            lead = Lead(**lead_data)
            db_session.add(lead)
        
        await db_session.commit()
        
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.0
            
            response = await lead_service.list_leads(db_session, page=1, size=10)
        
        assert isinstance(response, LeadListResponse)
        assert len(response.leads) == 5
        assert response.total == 5
        assert response.page == 1
        assert response.size == 10
        assert response.pages == 1
    
    async def test_list_leads_with_filters(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试带过滤条件的线索列表查询"""
        # 创建不同状态的线索
        leads_data = [
            {
                "name": "用户1",
                "company": "公司1",
                "industry": "technology",
                "source": LeadSource.WEBSITE,
                "status": LeadStatus.NEW,
                "assigned_to": "销售A"
            },
            {
                "name": "用户2",
                "company": "公司2",
                "industry": "finance",
                "source": LeadSource.EMAIL_CAMPAIGN,
                "status": LeadStatus.QUALIFIED,
                "assigned_to": "销售B"
            },
            {
                "name": "用户3",
                "company": "公司3",
                "industry": "technology",
                "source": LeadSource.WEBSITE,
                "status": LeadStatus.CONVERTED,
                "assigned_to": "销售A"
            }
        ]
        
        for lead_data in leads_data:
            lead = Lead(**lead_data)
            db_session.add(lead)
        
        await db_session.commit()
        
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.0
            
            # 按状态过滤
            response = await lead_service.list_leads(
                db_session, status=LeadStatus.NEW
            )
            assert len(response.leads) == 1
            assert response.leads[0].status == LeadStatus.NEW
            
            # 按来源过滤
            response = await lead_service.list_leads(
                db_session, source=LeadSource.WEBSITE
            )
            assert len(response.leads) == 2
            
            # 按分配人过滤
            response = await lead_service.list_leads(
                db_session, assigned_to="销售A"
            )
            assert len(response.leads) == 2
            
            # 按行业过滤
            response = await lead_service.list_leads(
                db_session, industry="technology"
            )
            assert len(response.leads) == 2
    
    async def test_list_leads_with_search(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试带搜索条件的线索列表查询"""
        # 创建线索
        leads_data = [
            {
                "name": "张三",
                "company": "阿里巴巴",
                "requirements": "需要CRM系统",
                "source": LeadSource.WEBSITE
            },
            {
                "name": "李四",
                "company": "腾讯科技",
                "requirements": "需要ERP系统",
                "source": LeadSource.WEBSITE
            },
            {
                "name": "王五",
                "company": "百度公司",
                "requirements": "需要OA系统",
                "source": LeadSource.WEBSITE
            }
        ]
        
        for lead_data in leads_data:
            lead = Lead(**lead_data)
            db_session.add(lead)
        
        await db_session.commit()
        
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.0
            
            # 按姓名搜索
            response = await lead_service.list_leads(db_session, search="张三")
            assert len(response.leads) == 1
            assert response.leads[0].name == "张三"
            
            # 按公司搜索
            response = await lead_service.list_leads(db_session, search="腾讯")
            assert len(response.leads) == 1
            assert response.leads[0].company == "腾讯科技"
            
            # 按需求搜索
            response = await lead_service.list_leads(db_session, search="CRM")
            assert len(response.leads) == 1
            assert "CRM" in response.leads[0].requirements
    
    async def test_list_leads_pagination(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试线索列表分页"""
        # 创建10个线索
        for i in range(10):
            lead = Lead(
                name=f"用户{i+1}",
                company=f"公司{i+1}",
                source=LeadSource.WEBSITE
            )
            db_session.add(lead)
        
        await db_session.commit()
        
        with patch.object(lead_service.scoring_service, 'calculate_lead_score') as mock_score:
            mock_score.return_value = AsyncMock()
            mock_score.return_value.total_score = 75.0
            
            # 第一页
            response = await lead_service.list_leads(db_session, page=1, size=3)
            assert len(response.leads) == 3
            assert response.total == 10
            assert response.page == 1
            assert response.size == 3
            assert response.pages == 4
            
            # 第二页
            response = await lead_service.list_leads(db_session, page=2, size=3)
            assert len(response.leads) == 3
            assert response.page == 2
            
            # 最后一页
            response = await lead_service.list_leads(db_session, page=4, size=3)
            assert len(response.leads) == 1
            assert response.page == 4
    
    async def test_assign_leads(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试批量分配线索"""
        # 创建线索
        leads = []
        for i in range(3):
            lead = Lead(
                name=f"用户{i+1}",
                company=f"公司{i+1}",
                source=LeadSource.WEBSITE
            )
            db_session.add(lead)
            leads.append(lead)
        
        await db_session.commit()
        
        # 批量分配
        assignment = LeadAssignmentRequest(
            lead_ids=[str(lead.id) for lead in leads],
            assigned_to="销售代表A",
            reason="按地区分配"
        )
        
        response = await lead_service.assign_leads(assignment, db_session)
        
        assert isinstance(response, LeadAssignmentResponse)
        assert response.success_count == 3
        assert response.failed_count == 0
        assert len(response.failed_leads) == 0
        assert "成功分配 3 个线索" in response.message
        
        # 验证分配结果
        for lead in leads:
            await db_session.refresh(lead)
            assert lead.assigned_to == "销售代表A"
            assert lead.assigned_at is not None
    
    async def test_assign_leads_partial_failure(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试部分失败的线索分配"""
        # 创建一个线索
        lead = Lead(
            name="用户1",
            company="公司1",
            source=LeadSource.WEBSITE
        )
        db_session.add(lead)
        await db_session.commit()
        
        # 尝试分配（包含不存在的线索ID）
        assignment = LeadAssignmentRequest(
            lead_ids=[str(lead.id), "non-existent-id"],
            assigned_to="销售代表A"
        )
        
        response = await lead_service.assign_leads(assignment, db_session)
        
        assert response.success_count == 1
        assert response.failed_count == 1
        assert len(response.failed_leads) == 1
        assert "non-existent-id" in response.failed_leads
        assert "失败 1 个" in response.message
    
    async def test_add_interaction(
        self,
        lead_service: LeadService,
        db_session: AsyncSession,
        sample_lead_in_db: Lead
    ):
        """测试添加线索互动记录"""
        interaction_data = InteractionCreate(
            interaction_type="phone_call",
            channel="phone",
            direction="outbound",
            subject="初次接触",
            content="介绍公司产品和服务",
            outcome="positive",
            next_action="发送产品资料",
            participant="销售代表"
        )
        
        response = await lead_service.add_interaction(
            str(sample_lead_in_db.id), interaction_data, db_session
        )
        
        assert response is not None
        assert isinstance(response, InteractionResponse)
        assert response.lead_id == str(sample_lead_in_db.id)
        assert response.interaction_type == "phone_call"
        assert response.channel == "phone"
        assert response.direction == "outbound"
        assert response.subject == "初次接触"
        assert response.content == "介绍公司产品和服务"
        assert response.outcome == "positive"
        assert response.next_action == "发送产品资料"
        assert response.participant == "销售代表"
        assert response.id is not None
        assert response.created_at is not None
        assert response.interaction_at is not None
    
    async def test_add_interaction_lead_not_found(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试为不存在的线索添加互动记录"""
        interaction_data = InteractionCreate(
            interaction_type="email",
            channel="email",
            direction="inbound",
            subject="咨询产品",
            content="客户询问产品功能"
        )
        
        response = await lead_service.add_interaction(
            "non-existent-id", interaction_data, db_session
        )
        
        assert response is None
    
    async def test_get_lead_statistics(
        self,
        lead_service: LeadService,
        db_session: AsyncSession
    ):
        """测试获取线索统计信息"""
        # 创建不同状态和来源的线索
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        leads_data = [
            {
                "name": "用户1",
                "company": "公司1",
                "source": LeadSource.WEBSITE,
                "status": LeadStatus.NEW,
                "assigned_to": "销售A",
                "created_at": now  # 今天
            },
            {
                "name": "用户2",
                "company": "公司2",
                "source": LeadSource.EMAIL_CAMPAIGN,
                "status": LeadStatus.QUALIFIED,
                "assigned_to": "销售B",
                "created_at": now  # 今天
            },
            {
                "name": "用户3",
                "company": "公司3",
                "source": LeadSource.WEBSITE,
                "status": LeadStatus.CONVERTED,
                "assigned_to": "销售A",
                "created_at": now - timedelta(days=2)  # 前天
            }
        ]
        
        for lead_data in leads_data:
            lead = Lead(**lead_data)
            db_session.add(lead)
        
        # 添加评分记录
        await db_session.commit()
        
        # 为每个线索添加评分
        from sqlalchemy import select
        stmt = select(Lead)
        result = await db_session.execute(stmt)
        leads = result.scalars().all()
        
        for i, lead in enumerate(leads):
            score = LeadScore(
                lead_id=lead.id,
                total_score=70.0 + i * 10,
                confidence=0.8,
                score_factors=[],
                algorithm_version="v1.0"
            )
            db_session.add(score)
        
        await db_session.commit()
        
        # 获取统计信息
        stats = await lead_service.get_lead_statistics(db_session)
        
        assert isinstance(stats, LeadStatistics)
        assert stats.total_leads == 3
        assert stats.by_status[LeadStatus.NEW.value] == 1
        assert stats.by_status[LeadStatus.QUALIFIED.value] == 1
        assert stats.by_status[LeadStatus.CONVERTED.value] == 1
        assert stats.by_source[LeadSource.WEBSITE.value] == 2
        assert stats.by_source[LeadSource.EMAIL_CAMPAIGN.value] == 1
        assert stats.by_assigned["销售A"] == 2
        assert stats.by_assigned["销售B"] == 1
        assert stats.average_score > 0
        assert stats.conversion_rate > 0  # 有1个转化的线索
        assert stats.created_today == 2  # 今天创建的线索
        assert stats.created_this_week >= 2
        assert stats.created_this_month >= 2