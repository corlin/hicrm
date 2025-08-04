"""
线索评分服务测试
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.lead_scoring_service import LeadScoringService
from src.models.lead import Lead, LeadScore, ScoreFactor, LeadStatus, LeadSource
from src.schemas.lead import LeadScoreDetail, ScoreFactorDetail, ScoreFactorConfig
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
def scoring_service():
    """创建评分服务实例"""
    return LeadScoringService()


@pytest.fixture
def sample_lead():
    """示例线索"""
    return Lead(
        name="张三",
        company="测试科技有限公司",
        title="技术总监",
        industry="technology",
        contact={
            "email": "zhangsan@test.com",
            "phone": "13800138000",
            "wechat": "zhangsan_wx"
        },
        company_info={
            "size": "medium",
            "revenue": 50000000,
            "employees": 200,
            "website": "https://test.com"
        },
        requirements="需要CRM系统来管理客户关系",
        budget=100000.0,
        timeline="3个月",
        source=LeadSource.WEBSITE,
        status=LeadStatus.NEW,
        tags=["高优先级", "技术决策者"],
        notes="通过官网表单提交的线索"
    )


@pytest.fixture
async def sample_score_factors(db_session: AsyncSession):
    """创建示例评分因子"""
    factors_data = [
        {
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
                    "startup": 20,
                    "unknown": 10
                }
            },
            "is_active": "true"
        },
        {
            "name": "budget_range",
            "category": "financial",
            "description": "预算范围评分",
            "weight": 0.30,
            "max_score": 100.0,
            "min_score": 0.0,
            "calculation_rules": {
                "type": "threshold",
                "thresholds": [
                    {"min": 1000000, "score": 100},
                    {"min": 500000, "score": 80},
                    {"min": 100000, "score": 60},
                    {"min": 50000, "score": 40},
                    {"min": 10000, "score": 20},
                    {"min": 0, "score": 10}
                ]
            },
            "is_active": "true"
        },
        {
            "name": "industry_match",
            "category": "business",
            "description": "行业匹配度评分",
            "weight": 0.20,
            "max_score": 100.0,
            "min_score": 0.0,
            "calculation_rules": {
                "type": "categorical",
                "mappings": {
                    "manufacturing": 90,
                    "technology": 85,
                    "finance": 80,
                    "healthcare": 75,
                    "retail": 70,
                    "education": 65,
                    "government": 60,
                    "other": 30,
                    "unknown": 10
                }
            },
            "is_active": "true"
        },
        {
            "name": "contact_quality",
            "category": "contact",
            "description": "联系信息质量评分",
            "weight": 0.25,
            "max_score": 100.0,
            "min_score": 0.0,
            "calculation_rules": {
                "type": "composite",
                "components": {
                    "has_email": 30,
                    "has_phone": 25,
                    "has_title": 20,
                    "has_linkedin": 15,
                    "has_address": 10
                }
            },
            "is_active": "true"
        }
    ]
    
    factors = []
    for factor_data in factors_data:
        factor = ScoreFactor(**factor_data)
        db_session.add(factor)
        factors.append(factor)
    
    await db_session.commit()
    return factors


class TestLeadScoringService:
    """线索评分服务测试类"""
    
    async def test_calculate_lead_score_basic(
        self, 
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_lead: Lead,
        sample_score_factors
    ):
        """测试基本线索评分计算"""
        # 保存线索到数据库
        db_session.add(sample_lead)
        await db_session.commit()
        await db_session.refresh(sample_lead)
        
        # 计算评分
        score_detail = await scoring_service.calculate_lead_score(sample_lead, db_session)
        
        # 验证评分结果
        assert isinstance(score_detail, LeadScoreDetail)
        assert 0 <= score_detail.total_score <= 100
        assert 0 <= score_detail.confidence <= 1
        assert len(score_detail.factors) == 4  # 4个评分因子
        assert score_detail.algorithm_version == "v1.0"
        assert score_detail.calculated_at is not None
        
        # 验证各个因子的评分
        factor_names = [f.name for f in score_detail.factors]
        assert "company_size" in factor_names
        assert "budget_range" in factor_names
        assert "industry_match" in factor_names
        assert "contact_quality" in factor_names
    
    async def test_calculate_categorical_score(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试分类型评分计算"""
        # 创建不同公司规模的线索
        test_cases = [
            ("enterprise", 100),
            ("large", 80),
            ("medium", 60),
            ("small", 40),
            ("startup", 20),
            ("unknown", 10)
        ]
        
        for company_size, expected_score in test_cases:
            lead = Lead(
                name="测试用户",
                company="测试公司",
                industry="technology",
                company_info={"size": company_size},
                source=LeadSource.WEBSITE
            )
            db_session.add(lead)
            await db_session.commit()
            await db_session.refresh(lead)
            
            score_detail = await scoring_service.calculate_lead_score(lead, db_session)
            
            # 找到公司规模因子的评分
            company_size_factor = next(
                f for f in score_detail.factors if f.name == "company_size"
            )
            assert company_size_factor.value == expected_score
    
    async def test_calculate_threshold_score(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试阈值型评分计算"""
        # 创建不同预算的线索
        test_cases = [
            (1500000, 100),  # >= 1000000
            (800000, 80),    # >= 500000
            (150000, 60),    # >= 100000
            (75000, 40),     # >= 50000
            (25000, 20),     # >= 10000
            (5000, 10)       # >= 0
        ]
        
        for budget, expected_score in test_cases:
            lead = Lead(
                name="测试用户",
                company="测试公司",
                industry="technology",
                budget=budget,
                source=LeadSource.WEBSITE
            )
            db_session.add(lead)
            await db_session.commit()
            await db_session.refresh(lead)
            
            score_detail = await scoring_service.calculate_lead_score(lead, db_session)
            
            # 找到预算因子的评分
            budget_factor = next(
                f for f in score_detail.factors if f.name == "budget_range"
            )
            assert budget_factor.value == expected_score
    
    async def test_calculate_composite_score(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试复合型评分计算"""
        # 创建具有完整联系信息的线索
        lead = Lead(
            name="测试用户",
            company="测试公司",
            title="技术总监",
            industry="technology",
            contact={
                "email": "test@example.com",
                "phone": "13800138000",
                "linkedin": "linkedin.com/in/test",
                "address": "北京市朝阳区"
            },
            source=LeadSource.WEBSITE
        )
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        score_detail = await scoring_service.calculate_lead_score(lead, db_session)
        
        # 找到联系信息质量因子的评分
        contact_factor = next(
            f for f in score_detail.factors if f.name == "contact_quality"
        )
        
        # 应该包含: email(30) + phone(25) + title(20) + linkedin(15) + address(10) = 100
        assert contact_factor.value == 100
        assert "有邮箱" in contact_factor.reason
        assert "有电话" in contact_factor.reason
        assert "有职位" in contact_factor.reason
        assert "有LinkedIn" in contact_factor.reason
        assert "有地址" in contact_factor.reason
    
    async def test_calculate_confidence(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试置信度计算"""
        # 创建信息完整的线索
        complete_lead = Lead(
            name="完整信息用户",
            company="完整信息公司",
            title="技术总监",
            industry="technology",
            contact={
                "email": "complete@example.com",
                "phone": "13800138000"
            },
            company_info={"size": "medium"},
            budget=100000.0,
            timeline="3个月",
            source=LeadSource.WEBSITE
        )
        db_session.add(complete_lead)
        await db_session.commit()
        await db_session.refresh(complete_lead)
        
        complete_score = await scoring_service.calculate_lead_score(complete_lead, db_session)
        
        # 创建信息不完整的线索
        incomplete_lead = Lead(
            name="不完整信息用户",
            company="不完整信息公司",
            source=LeadSource.WEBSITE
        )
        db_session.add(incomplete_lead)
        await db_session.commit()
        await db_session.refresh(incomplete_lead)
        
        incomplete_score = await scoring_service.calculate_lead_score(incomplete_lead, db_session)
        
        # 完整信息的线索应该有更高的置信度
        assert complete_score.confidence > incomplete_score.confidence
    
    async def test_score_caching(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_lead: Lead,
        sample_score_factors
    ):
        """测试评分缓存机制"""
        # 保存线索到数据库
        db_session.add(sample_lead)
        await db_session.commit()
        await db_session.refresh(sample_lead)
        
        # 第一次计算评分
        score1 = await scoring_service.calculate_lead_score(sample_lead, db_session)
        
        # 第二次计算评分（应该使用缓存）
        score2 = await scoring_service.calculate_lead_score(sample_lead, db_session)
        
        # 评分应该相同（使用了缓存）
        assert score1.total_score == score2.total_score
        assert score1.calculated_at == score2.calculated_at
        
        # 强制重新计算
        score3 = await scoring_service.calculate_lead_score(
            sample_lead, db_session, force_recalculate=True
        )
        
        # 新的评分时间应该更新
        assert score3.calculated_at >= score1.calculated_at
    
    async def test_batch_calculate_scores(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试批量评分计算"""
        # 创建多个线索
        leads = []
        for i in range(3):
            lead = Lead(
                name=f"用户{i+1}",
                company=f"公司{i+1}",
                industry="technology",
                budget=50000 * (i + 1),
                source=LeadSource.WEBSITE
            )
            db_session.add(lead)
            leads.append(lead)
        
        await db_session.commit()
        
        # 批量计算评分
        lead_ids = [str(lead.id) for lead in leads]
        results = await scoring_service.batch_calculate_scores(lead_ids, db_session)
        
        # 验证结果
        assert len(results) == 3
        for lead_id in lead_ids:
            assert lead_id in results
            assert isinstance(results[lead_id], LeadScoreDetail)
    
    async def test_get_score_factor_configs(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试获取评分因子配置"""
        configs = await scoring_service.get_score_factor_configs(db_session)
        
        assert len(configs) == 4
        for config in configs:
            assert isinstance(config, ScoreFactorConfig)
            assert config.name in ["company_size", "budget_range", "industry_match", "contact_quality"]
            assert 0 <= config.weight <= 1
            assert config.is_active is True
    
    async def test_update_score_factor(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试更新评分因子配置"""
        # 获取第一个因子
        factor = sample_score_factors[0]
        factor_id = str(factor.id)
        
        # 创建新的配置
        new_config = ScoreFactorConfig(
            name="updated_company_size",
            category="company",
            description="更新后的公司规模评分",
            weight=0.35,
            max_score=120.0,
            min_score=5.0,
            calculation_rules={
                "type": "categorical",
                "mappings": {"large": 100, "medium": 50}
            },
            is_active=False
        )
        
        # 更新配置
        await scoring_service.update_score_factor(factor_id, new_config, db_session)
        
        # 验证更新
        await db_session.refresh(factor)
        assert factor.name == "updated_company_size"
        assert factor.weight == 0.35
        assert factor.max_score == 120.0
        assert factor.min_score == 5.0
        assert factor.is_active == "false"
    
    async def test_default_factors_initialization(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession
    ):
        """测试默认评分因子初始化"""
        # 确保数据库中没有评分因子
        from sqlalchemy import select, func
        count_stmt = select(func.count(ScoreFactor.id))
        result = await db_session.execute(count_stmt)
        initial_count = result.scalar()
        
        # 创建线索并计算评分（应该触发默认因子初始化）
        lead = Lead(
            name="测试用户",
            company="测试公司",
            industry="technology",
            source=LeadSource.WEBSITE
        )
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 计算评分
        await scoring_service.calculate_lead_score(lead, db_session)
        
        # 验证默认因子已创建
        result = await db_session.execute(count_stmt)
        final_count = result.scalar()
        assert final_count > initial_count
    
    async def test_error_handling(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_score_factors
    ):
        """测试错误处理"""
        # 创建有问题的线索（缺少必要字段）
        lead = Lead(
            name="",  # 空名称
            company="",  # 空公司
            source=LeadSource.WEBSITE
        )
        db_session.add(lead)
        await db_session.commit()
        await db_session.refresh(lead)
        
        # 计算评分应该不会抛出异常
        score_detail = await scoring_service.calculate_lead_score(lead, db_session)
        
        # 应该返回有效的评分结果，即使数据不完整
        assert isinstance(score_detail, LeadScoreDetail)
        assert 0 <= score_detail.total_score <= 100
        assert 0 <= score_detail.confidence <= 1
    
    async def test_score_persistence(
        self,
        scoring_service: LeadScoringService,
        db_session: AsyncSession,
        sample_lead: Lead,
        sample_score_factors
    ):
        """测试评分持久化"""
        # 保存线索到数据库
        db_session.add(sample_lead)
        await db_session.commit()
        await db_session.refresh(sample_lead)
        
        # 计算评分
        score_detail = await scoring_service.calculate_lead_score(sample_lead, db_session)
        
        # 验证评分已保存到数据库
        from sqlalchemy import select
        stmt = select(LeadScore).where(LeadScore.lead_id == sample_lead.id)
        result = await db_session.execute(stmt)
        saved_score = result.scalar_one_or_none()
        
        assert saved_score is not None
        assert saved_score.total_score == score_detail.total_score
        assert saved_score.confidence == score_detail.confidence
        assert saved_score.algorithm_version == score_detail.algorithm_version
        assert len(saved_score.score_factors) == len(score_detail.factors)