"""
线索模式测试
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.schemas.lead import (
    ContactInfo, CompanyInfo, ScoreFactorDetail, LeadScoreDetail,
    InteractionBase, InteractionCreate, InteractionResponse,
    LeadBase, LeadCreate, LeadUpdate, LeadResponse, LeadListResponse,
    ScoreFactorConfig, ScoreFactorResponse, LeadScoreRequest, LeadScoreResponse,
    LeadAssignmentRequest, LeadAssignmentResponse, LeadStatistics
)
from src.models.lead import LeadStatus, LeadSource


class TestContactInfo:
    """联系信息模式测试"""
    
    def test_contact_info_valid(self):
        """测试有效的联系信息"""
        contact = ContactInfo(
            phone="13800138000",
            email="test@example.com",
            wechat="test_wx",
            address="北京市朝阳区",
            linkedin="linkedin.com/in/test"
        )
        
        assert contact.phone == "13800138000"
        assert contact.email == "test@example.com"
        assert contact.wechat == "test_wx"
        assert contact.address == "北京市朝阳区"
        assert contact.linkedin == "linkedin.com/in/test"
    
    def test_contact_info_optional_fields(self):
        """测试可选字段"""
        contact = ContactInfo()
        
        assert contact.phone is None
        assert contact.email is None
        assert contact.wechat is None
        assert contact.address is None
        assert contact.linkedin is None
    
    def test_contact_info_partial(self):
        """测试部分字段"""
        contact = ContactInfo(
            email="test@example.com",
            phone="13800138000"
        )
        
        assert contact.email == "test@example.com"
        assert contact.phone == "13800138000"
        assert contact.wechat is None


class TestCompanyInfo:
    """公司信息模式测试"""
    
    def test_company_info_valid(self):
        """测试有效的公司信息"""
        company = CompanyInfo(
            size="medium",
            revenue=50000000.0,
            employees=200,
            website="https://example.com",
            location="北京",
            founded_year=2010
        )
        
        assert company.size == "medium"
        assert company.revenue == 50000000.0
        assert company.employees == 200
        assert company.website == "https://example.com"
        assert company.location == "北京"
        assert company.founded_year == 2010
    
    def test_company_info_optional_fields(self):
        """测试可选字段"""
        company = CompanyInfo()
        
        assert company.size is None
        assert company.revenue is None
        assert company.employees is None
        assert company.website is None
        assert company.location is None
        assert company.founded_year is None


class TestScoreFactorDetail:
    """评分因子详情模式测试"""
    
    def test_score_factor_detail_valid(self):
        """测试有效的评分因子详情"""
        factor = ScoreFactorDetail(
            name="company_size",
            category="company",
            weight=0.25,
            value=60.0,
            score=15.0,
            reason="中型公司"
        )
        
        assert factor.name == "company_size"
        assert factor.category == "company"
        assert factor.weight == 0.25
        assert factor.value == 60.0
        assert factor.score == 15.0
        assert factor.reason == "中型公司"
    
    def test_score_factor_detail_validation(self):
        """测试评分因子详情验证"""
        # 权重超出范围
        with pytest.raises(ValidationError):
            ScoreFactorDetail(
                name="test",
                category="test",
                weight=1.5,  # 超出范围
                value=50.0,
                score=10.0,
                reason="测试"
            )
        
        # 因子值超出范围
        with pytest.raises(ValidationError):
            ScoreFactorDetail(
                name="test",
                category="test",
                weight=0.5,
                value=150.0,  # 超出范围
                score=10.0,
                reason="测试"
            )


class TestLeadScoreDetail:
    """线索评分详情模式测试"""
    
    def test_lead_score_detail_valid(self):
        """测试有效的线索评分详情"""
        factors = [
            ScoreFactorDetail(
                name="company_size",
                category="company",
                weight=0.25,
                value=60.0,
                score=15.0,
                reason="中型公司"
            ),
            ScoreFactorDetail(
                name="budget_range",
                category="financial",
                weight=0.30,
                value=80.0,
                score=24.0,
                reason="预算充足"
            )
        ]
        
        score_detail = LeadScoreDetail(
            total_score=78.5,
            confidence=0.92,
            factors=factors,
            algorithm_version="v1.0",
            calculated_at=datetime.utcnow()
        )
        
        assert score_detail.total_score == 78.5
        assert score_detail.confidence == 0.92
        assert len(score_detail.factors) == 2
        assert score_detail.algorithm_version == "v1.0"
        assert score_detail.calculated_at is not None
    
    def test_lead_score_detail_validation(self):
        """测试线索评分详情验证"""
        # 总分超出范围
        with pytest.raises(ValidationError):
            LeadScoreDetail(
                total_score=150.0,  # 超出范围
                confidence=0.8,
                factors=[],
                algorithm_version="v1.0",
                calculated_at=datetime.utcnow()
            )
        
        # 置信度超出范围
        with pytest.raises(ValidationError):
            LeadScoreDetail(
                total_score=75.0,
                confidence=1.5,  # 超出范围
                factors=[],
                algorithm_version="v1.0",
                calculated_at=datetime.utcnow()
            )


class TestLeadCreate:
    """线索创建模式测试"""
    
    def test_lead_create_valid(self):
        """测试有效的线索创建"""
        lead = LeadCreate(
            name="张三",
            company="测试公司",
            title="技术总监",
            industry="technology",
            contact=ContactInfo(
                email="zhangsan@test.com",
                phone="13800138000"
            ),
            company_info=CompanyInfo(
                size="medium",
                revenue=50000000
            ),
            requirements="需要CRM系统",
            budget=100000.0,
            timeline="3个月",
            source=LeadSource.WEBSITE,
            status=LeadStatus.NEW,
            tags=["高优先级"],
            notes="测试线索",
            custom_fields={"segment": "enterprise"}
        )
        
        assert lead.name == "张三"
        assert lead.company == "测试公司"
        assert lead.title == "技术总监"
        assert lead.industry == "technology"
        assert lead.contact.email == "zhangsan@test.com"
        assert lead.company_info.size == "medium"
        assert lead.requirements == "需要CRM系统"
        assert lead.budget == 100000.0
        assert lead.timeline == "3个月"
        assert lead.source == LeadSource.WEBSITE
        assert lead.status == LeadStatus.NEW
        assert lead.tags == ["高优先级"]
        assert lead.notes == "测试线索"
        assert lead.custom_fields == {"segment": "enterprise"}
    
    def test_lead_create_required_fields(self):
        """测试必填字段"""
        # 缺少必填字段
        with pytest.raises(ValidationError):
            LeadCreate(
                # name缺失
                company="测试公司",
                source=LeadSource.WEBSITE
            )
        
        with pytest.raises(ValidationError):
            LeadCreate(
                name="张三",
                # company缺失
                source=LeadSource.WEBSITE
            )
        
        with pytest.raises(ValidationError):
            LeadCreate(
                name="张三",
                company="测试公司"
                # source缺失
            )
    
    def test_lead_create_budget_validation(self):
        """测试预算验证"""
        # 负数预算
        with pytest.raises(ValidationError):
            LeadCreate(
                name="张三",
                company="测试公司",
                source=LeadSource.WEBSITE,
                budget=-1000.0  # 负数
            )
    
    def test_lead_create_default_values(self):
        """测试默认值"""
        lead = LeadCreate(
            name="张三",
            company="测试公司",
            source=LeadSource.WEBSITE
        )
        
        assert lead.status == LeadStatus.NEW  # 默认状态
        assert lead.tags == []  # 默认空列表
        assert lead.custom_fields == {}  # 默认空字典


class TestLeadUpdate:
    """线索更新模式测试"""
    
    def test_lead_update_partial(self):
        """测试部分更新"""
        update = LeadUpdate(
            name="新名称",
            budget=200000.0,
            status=LeadStatus.QUALIFIED
        )
        
        assert update.name == "新名称"
        assert update.budget == 200000.0
        assert update.status == LeadStatus.QUALIFIED
        assert update.company is None  # 未更新的字段
        assert update.industry is None
    
    def test_lead_update_all_optional(self):
        """测试所有字段都是可选的"""
        update = LeadUpdate()
        
        assert update.name is None
        assert update.company is None
        assert update.budget is None
        assert update.status is None


class TestInteractionCreate:
    """互动创建模式测试"""
    
    def test_interaction_create_valid(self):
        """测试有效的互动创建"""
        interaction = InteractionCreate(
            interaction_type="phone_call",
            channel="phone",
            direction="outbound",
            subject="初次接触",
            content="介绍产品功能",
            outcome="positive",
            next_action="发送资料",
            participant="销售代表",
            interaction_at=datetime.utcnow()
        )
        
        assert interaction.interaction_type == "phone_call"
        assert interaction.channel == "phone"
        assert interaction.direction == "outbound"
        assert interaction.subject == "初次接触"
        assert interaction.content == "介绍产品功能"
        assert interaction.outcome == "positive"
        assert interaction.next_action == "发送资料"
        assert interaction.participant == "销售代表"
        assert interaction.interaction_at is not None
    
    def test_interaction_create_required_fields(self):
        """测试必填字段"""
        # 缺少必填字段
        with pytest.raises(ValidationError):
            InteractionCreate()  # interaction_type缺失
    
    def test_interaction_create_optional_fields(self):
        """测试可选字段"""
        interaction = InteractionCreate(
            interaction_type="email"
        )
        
        assert interaction.interaction_type == "email"
        assert interaction.channel is None
        assert interaction.direction is None
        assert interaction.subject is None
        assert interaction.content is None
        assert interaction.outcome is None
        assert interaction.next_action is None
        assert interaction.participant is None
        assert interaction.interaction_at is None


class TestLeadAssignmentRequest:
    """线索分配请求模式测试"""
    
    def test_lead_assignment_request_valid(self):
        """测试有效的线索分配请求"""
        request = LeadAssignmentRequest(
            lead_ids=["id1", "id2", "id3"],
            assigned_to="销售代表A",
            reason="按地区分配"
        )
        
        assert request.lead_ids == ["id1", "id2", "id3"]
        assert request.assigned_to == "销售代表A"
        assert request.reason == "按地区分配"
    
    def test_lead_assignment_request_required_fields(self):
        """测试必填字段"""
        # 缺少必填字段
        with pytest.raises(ValidationError):
            LeadAssignmentRequest(
                # lead_ids缺失
                assigned_to="销售代表A"
            )
        
        with pytest.raises(ValidationError):
            LeadAssignmentRequest(
                lead_ids=["id1", "id2"],
                # assigned_to缺失
            )
    
    def test_lead_assignment_request_optional_reason(self):
        """测试可选的原因字段"""
        request = LeadAssignmentRequest(
            lead_ids=["id1", "id2"],
            assigned_to="销售代表A"
        )
        
        assert request.reason is None


class TestLeadAssignmentResponse:
    """线索分配响应模式测试"""
    
    def test_lead_assignment_response_valid(self):
        """测试有效的线索分配响应"""
        response = LeadAssignmentResponse(
            success_count=3,
            failed_count=1,
            failed_leads=["failed_id"],
            message="成功分配3个线索，失败1个"
        )
        
        assert response.success_count == 3
        assert response.failed_count == 1
        assert response.failed_leads == ["failed_id"]
        assert response.message == "成功分配3个线索，失败1个"
    
    def test_lead_assignment_response_no_failures(self):
        """测试无失败的分配响应"""
        response = LeadAssignmentResponse(
            success_count=5,
            failed_count=0,
            failed_leads=[],
            message="成功分配5个线索"
        )
        
        assert response.success_count == 5
        assert response.failed_count == 0
        assert response.failed_leads == []


class TestLeadStatistics:
    """线索统计模式测试"""
    
    def test_lead_statistics_valid(self):
        """测试有效的线索统计"""
        stats = LeadStatistics(
            total_leads=100,
            by_status={"new": 30, "qualified": 40, "converted": 20, "lost": 10},
            by_source={"website": 50, "email": 30, "referral": 20},
            by_assigned={"销售A": 40, "销售B": 35, "未分配": 25},
            average_score=75.5,
            conversion_rate=20.0,
            created_today=5,
            created_this_week=25,
            created_this_month=80
        )
        
        assert stats.total_leads == 100
        assert stats.by_status["new"] == 30
        assert stats.by_source["website"] == 50
        assert stats.by_assigned["销售A"] == 40
        assert stats.average_score == 75.5
        assert stats.conversion_rate == 20.0
        assert stats.created_today == 5
        assert stats.created_this_week == 25
        assert stats.created_this_month == 80


class TestScoreFactorConfig:
    """评分因子配置模式测试"""
    
    def test_score_factor_config_valid(self):
        """测试有效的评分因子配置"""
        config = ScoreFactorConfig(
            name="company_size",
            category="company",
            description="公司规模评分",
            weight=0.25,
            max_score=100.0,
            min_score=0.0,
            calculation_rules={
                "type": "categorical",
                "mappings": {"large": 100, "medium": 60, "small": 30}
            },
            is_active=True
        )
        
        assert config.name == "company_size"
        assert config.category == "company"
        assert config.description == "公司规模评分"
        assert config.weight == 0.25
        assert config.max_score == 100.0
        assert config.min_score == 0.0
        assert config.calculation_rules["type"] == "categorical"
        assert config.is_active is True
    
    def test_score_factor_config_validation(self):
        """测试评分因子配置验证"""
        # 权重超出范围
        with pytest.raises(ValidationError):
            ScoreFactorConfig(
                name="test",
                category="test",
                weight=1.5,  # 超出范围
                calculation_rules={}
            )
        
        # 最大分值小于等于最小分值
        with pytest.raises(ValidationError):
            ScoreFactorConfig(
                name="test",
                category="test",
                weight=0.5,
                max_score=50.0,
                min_score=60.0,  # 大于最大分值
                calculation_rules={}
            )
    
    def test_score_factor_config_defaults(self):
        """测试默认值"""
        config = ScoreFactorConfig(
            name="test",
            category="test",
            weight=0.5,
            calculation_rules={}
        )
        
        assert config.max_score == 100.0  # 默认值
        assert config.min_score == 0.0    # 默认值
        assert config.is_active is True   # 默认值