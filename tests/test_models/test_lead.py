"""
线索模型测试
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.lead import Lead, LeadScore, ScoreFactor, LeadInteraction, LeadStatus, LeadSource
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
def sample_lead_data():
    """示例线索数据"""
    return {
        "name": "张三",
        "company": "测试科技有限公司",
        "title": "技术总监",
        "industry": "technology",
        "contact": {
            "email": "zhangsan@test.com",
            "phone": "13800138000",
            "wechat": "zhangsan_wx"
        },
        "company_info": {
            "size": "medium",
            "revenue": 50000000,
            "employees": 200,
            "website": "https://test.com"
        },
        "requirements": "需要CRM系统来管理客户关系",
        "budget": 100000.0,
        "timeline": "3个月",
        "source": LeadSource.WEBSITE,
        "status": LeadStatus.NEW,
        "tags": ["高优先级", "技术决策者"],
        "notes": "通过官网表单提交的线索",
        "custom_fields": {"industry_segment": "SaaS"}
    }


@pytest.fixture
def sample_score_factor_data():
    """示例评分因子数据"""
    return {
        "name": "company_size",
        "category": "company",
        "description": "公司规模评分",
        "weight": 0.25,
        "max_score": 100.0,
        "min_score": 0.0,
        "calculation_rules": {
            "type": "categorical",
            "mappings": {
                "enterprise": 100,
                "large": 80,
                "medium": 60,
                "small": 40,
                "startup": 20
            }
        },
        "is_active": "true"
    }


class TestLeadModel:
    """线索模型测试类"""
    
    async def test_create_lead(self, db_session: AsyncSession, sample_lead_data):
        """测试创建线索"""
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        assert lead.id is not None
        assert lead.name == "张三"
        assert lead.company == "测试科技有限公司"
        assert lead.status == LeadStatus.NEW
        assert lead.source == LeadSource.WEBSITE
        assert lead.budget == 100000.0
        assert lead.created_at is not None
        assert lead.updated_at is not None
    
    async def test_lead_relationships(self, db_session: AsyncSession, sample_lead_data):
        """测试线索关系"""
        # 创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建评分记录
        score = LeadScore(
            lead_id=lead.id,
            total_score=75.5,
            confidence=0.85,
            score_factors=[
                {
                    "name": "company_size",
                    "category": "company",
                    "weight": 0.25,
                    "value": 60.0,
                    "score": 15.0,
                    "reason": "中型公司"
                }
            ],
            algorithm_version="v1.0"
        )
        db_session.add(score)
        
        # 创建互动记录
        interaction = LeadInteraction(
            lead_id=lead.id,
            interaction_type="phone_call",
            channel="phone",
            direction="outbound",
            subject="初次接触",
            content="介绍公司产品和服务",
            outcome="positive",
            participant="销售代表"
        )
        db_session.add(interaction)
        
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(lead)
        assert len(lead.lead_scores) == 1
        assert len(lead.interactions) == 1
        assert lead.lead_scores[0].total_score == 75.5
        assert lead.interactions[0].interaction_type == "phone_call"
    
    async def test_lead_status_enum(self, db_session: AsyncSession, sample_lead_data):
        """测试线索状态枚举"""
        lead = Lead(**sample_lead_data)
        
        # 测试所有状态
        for status in LeadStatus:
            lead.status = status
            db_session.add(lead)
            await db_session.commit()
            await db_session.refresh(lead)
            assert lead.status == status
    
    async def test_lead_source_enum(self, db_session: AsyncSession, sample_lead_data):
        """测试线索来源枚举"""
        # 测试所有来源
        for source in LeadSource:
            lead_data = sample_lead_data.copy()
            lead_data["source"] = source
            lead = Lead(**lead_data)
            db_session.add(lead)
            await db_session.commit()
            await db_session.refresh(lead)
            assert lead.source == source
    
    async def test_lead_json_fields(self, db_session: AsyncSession, sample_lead_data):
        """测试JSON字段"""
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 验证contact JSON字段
        assert lead.contact["email"] == "zhangsan@test.com"
        assert lead.contact["phone"] == "13800138000"
        
        # 验证company_info JSON字段
        assert lead.company_info["size"] == "medium"
        assert lead.company_info["revenue"] == 50000000
        
        # 验证tags JSON字段
        assert "高优先级" in lead.tags
        assert "技术决策者" in lead.tags
        
        # 验证custom_fields JSON字段
        assert lead.custom_fields["industry_segment"] == "SaaS"


class TestLeadScoreModel:
    """线索评分模型测试类"""
    
    async def test_create_lead_score(self, db_session: AsyncSession, sample_lead_data):
        """测试创建线索评分"""
        # 先创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建评分
        score_factors = [
            {
                "name": "company_size",
                "category": "company",
                "weight": 0.25,
                "value": 60.0,
                "score": 15.0,
                "reason": "中型公司"
            },
            {
                "name": "budget_range",
                "category": "financial",
                "weight": 0.30,
                "value": 80.0,
                "score": 24.0,
                "reason": "预算充足"
            }
        ]
        
        score = LeadScore(
            lead_id=lead.id,
            total_score=78.5,
            confidence=0.92,
            score_factors=score_factors,
            algorithm_version="v1.0"
        )
        
        db_session.add(score)
        await db_session.commit()
        await db_session.refresh(score)
        
        assert score.id is not None
        assert score.lead_id == lead.id
        assert score.total_score == 78.5
        assert score.confidence == 0.92
        assert len(score.score_factors) == 2
        assert score.algorithm_version == "v1.0"
        assert score.calculated_at is not None
    
    async def test_lead_score_relationship(self, db_session: AsyncSession, sample_lead_data):
        """测试线索评分关系"""
        # 创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建多个评分记录（模拟历史评分）
        scores = []
        for i in range(3):
            score = LeadScore(
                lead_id=lead.id,
                total_score=70.0 + i * 5,
                confidence=0.8 + i * 0.05,
                score_factors=[],
                algorithm_version="v1.0"
            )
            scores.append(score)
            db_session.add(score)
        
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(lead)
        assert len(lead.lead_scores) == 3
        
        # 验证反向关系
        for score in scores:
            await db_session.refresh(score)
            assert score.lead.id == lead.id


class TestScoreFactorModel:
    """评分因子模型测试类"""
    
    async def test_create_score_factor(self, db_session: AsyncSession, sample_score_factor_data):
        """测试创建评分因子"""
        factor = ScoreFactor(**sample_score_factor_data)
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        
        assert factor.id is not None
        assert factor.name == "company_size"
        assert factor.category == "company"
        assert factor.weight == 0.25
        assert factor.max_score == 100.0
        assert factor.min_score == 0.0
        assert factor.is_active == "true"
        assert factor.created_at is not None
        assert factor.updated_at is not None
    
    async def test_score_factor_calculation_rules(self, db_session: AsyncSession, sample_score_factor_data):
        """测试评分因子计算规则"""
        factor = ScoreFactor(**sample_score_factor_data)
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        
        # 验证计算规则JSON字段
        rules = factor.calculation_rules
        assert rules["type"] == "categorical"
        assert "mappings" in rules
        assert rules["mappings"]["enterprise"] == 100
        assert rules["mappings"]["medium"] == 60
    
    async def test_score_factor_active_status(self, db_session: AsyncSession, sample_score_factor_data):
        """测试评分因子激活状态"""
        # 测试激活状态
        factor_data = sample_score_factor_data.copy()
        factor_data["is_active"] = "true"
        factor = ScoreFactor(**factor_data)
        db_session.add(factor)
        await db_session.commit()
        await db_session.refresh(factor)
        assert factor.is_active == "true"
        
        # 测试非激活状态
        factor_data["is_active"] = "false"
        factor_data["name"] = "inactive_factor"
        inactive_factor = ScoreFactor(**factor_data)
        db_session.add(inactive_factor)
        await db_session.commit()
        await db_session.refresh(inactive_factor)
        assert inactive_factor.is_active == "false"


class TestLeadInteractionModel:
    """线索互动模型测试类"""
    
    async def test_create_lead_interaction(self, db_session: AsyncSession, sample_lead_data):
        """测试创建线索互动"""
        # 先创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建互动记录
        interaction = LeadInteraction(
            lead_id=lead.id,
            interaction_type="email",
            channel="email",
            direction="inbound",
            subject="产品咨询",
            content="客户询问产品功能和价格",
            outcome="需要跟进",
            next_action="发送产品介绍资料",
            participant="张三"
        )
        
        db_session.add(interaction)
        await db_session.commit()
        await db_session.refresh(interaction)
        
        assert interaction.id is not None
        assert interaction.lead_id == lead.id
        assert interaction.interaction_type == "email"
        assert interaction.channel == "email"
        assert interaction.direction == "inbound"
        assert interaction.subject == "产品咨询"
        assert interaction.content == "客户询问产品功能和价格"
        assert interaction.outcome == "需要跟进"
        assert interaction.next_action == "发送产品介绍资料"
        assert interaction.participant == "张三"
        assert interaction.interaction_at is not None
        assert interaction.created_at is not None
    
    async def test_lead_interaction_relationship(self, db_session: AsyncSession, sample_lead_data):
        """测试线索互动关系"""
        # 创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建多个互动记录
        interactions = []
        interaction_types = ["email", "phone_call", "meeting"]
        
        for i, interaction_type in enumerate(interaction_types):
            interaction = LeadInteraction(
                lead_id=lead.id,
                interaction_type=interaction_type,
                channel=interaction_type,
                direction="outbound" if i % 2 == 0 else "inbound",
                subject=f"互动 {i+1}",
                content=f"互动内容 {i+1}",
                participant="销售代表"
            )
            interactions.append(interaction)
            db_session.add(interaction)
        
        await db_session.commit()
        
        # 验证关系
        await db_session.refresh(lead)
        assert len(lead.interactions) == 3
        
        # 验证反向关系
        for interaction in interactions:
            await db_session.refresh(interaction)
            assert interaction.lead.id == lead.id
    
    async def test_interaction_timestamps(self, db_session: AsyncSession, sample_lead_data):
        """测试互动时间戳"""
        # 创建线索
        lead = Lead(**sample_lead_data)
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 创建带自定义时间的互动
        custom_time = datetime(2024, 1, 15, 10, 30, 0)
        interaction = LeadInteraction(
            lead_id=lead.id,
            interaction_type="phone_call",
            channel="phone",
            direction="outbound",
            subject="预约演示",
            content="与客户预约产品演示时间",
            interaction_at=custom_time,
            participant="销售代表"
        )
        
        db_session.add(interaction)
        await db_session.commit()
        await db_session.refresh(interaction)
        
        assert interaction.interaction_at == custom_time
        assert interaction.created_at is not None
        assert interaction.created_at != custom_time  # created_at应该是当前时间