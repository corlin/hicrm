"""
销售机会模式测试
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from src.schemas.opportunity import (
    OpportunityStageCreate, OpportunityStageUpdate, OpportunityStageResponse,
    OpportunityCreate, OpportunityUpdate, OpportunityResponse,
    ActivityCreate, ActivityUpdate, ActivityResponse,
    StageTransitionRequest, StageTransitionResponse,
    ProductInfo, CompetitorInfo, StakeholderInfo, RiskInfo, NextAction,
    OpportunityStatistics, FunnelAnalysis, FunnelAnalysisResponse
)
from src.models.opportunity import OpportunityStatus, OpportunityPriority, StageType


class TestOpportunityStageSchemas:
    """销售机会阶段模式测试"""
    
    def test_opportunity_stage_create_valid(self):
        """测试有效的阶段创建模式"""
        stage_data = {
            "name": "需求分析",
            "description": "分析客户需求阶段",
            "stage_type": StageType.NEEDS_ANALYSIS,
            "order": 1,
            "probability": 0.3,
            "requirements": ["需求调研", "方案设计"],
            "entry_criteria": ["客户确认需求"],
            "exit_criteria": ["需求文档完成"],
            "duration_days": 7,
            "is_active": True,
            "custom_fields": {"color": "blue"}
        }
        
        stage = OpportunityStageCreate(**stage_data)
        
        assert stage.name == "需求分析"
        assert stage.stage_type == StageType.NEEDS_ANALYSIS
        assert stage.order == 1
        assert stage.probability == 0.3
        assert len(stage.requirements) == 2
        assert len(stage.entry_criteria) == 1
        assert len(stage.exit_criteria) == 1
        assert stage.duration_days == 7
        assert stage.is_active is True
        assert stage.custom_fields["color"] == "blue"
    
    def test_opportunity_stage_create_invalid_probability(self):
        """测试无效概率的阶段创建"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityStageCreate(
                name="测试阶段",
                stage_type=StageType.QUALIFICATION,
                order=1,
                probability=1.5  # 无效概率
            )
        
        assert "probability" in str(exc_info.value)
    
    def test_opportunity_stage_create_invalid_order(self):
        """测试无效顺序的阶段创建"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityStageCreate(
                name="测试阶段",
                stage_type=StageType.QUALIFICATION,
                order=0,  # 无效顺序
                probability=0.5
            )
        
        assert "order" in str(exc_info.value)
    
    def test_opportunity_stage_update_partial(self):
        """测试部分更新阶段模式"""
        update_data = {
            "name": "更新后的阶段名称",
            "probability": 0.8
        }
        
        stage_update = OpportunityStageUpdate(**update_data)
        
        assert stage_update.name == "更新后的阶段名称"
        assert stage_update.probability == 0.8
        assert stage_update.stage_type is None  # 未设置的字段应为None
        assert stage_update.order is None
    
    def test_opportunity_stage_response(self):
        """测试阶段响应模式"""
        stage_data = {
            "id": "stage-123",
            "name": "商务谈判",
            "description": "与客户进行商务谈判",
            "stage_type": StageType.NEGOTIATION,
            "order": 3,
            "probability": 0.7,
            "requirements": ["价格谈判", "合同条款"],
            "entry_criteria": ["方案确认"],
            "exit_criteria": ["合同签署"],
            "duration_days": 14,
            "is_active": True,
            "custom_fields": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        stage_response = OpportunityStageResponse(**stage_data)
        
        assert stage_response.id == "stage-123"
        assert stage_response.name == "商务谈判"
        assert stage_response.stage_type == StageType.NEGOTIATION
        assert stage_response.created_at is not None
        assert stage_response.updated_at is not None


class TestOpportunitySchemas:
    """销售机会模式测试"""
    
    def test_product_info_valid(self):
        """测试有效的产品信息模式"""
        product_data = {
            "id": "prod-001",
            "name": "CRM标准版",
            "version": "v2.0",
            "quantity": 2,
            "unit_price": 50000.0,
            "total_price": 100000.0,
            "description": "客户关系管理系统标准版"
        }
        
        product = ProductInfo(**product_data)
        
        assert product.id == "prod-001"
        assert product.name == "CRM标准版"
        assert product.quantity == 2
        assert product.unit_price == 50000.0
        assert product.total_price == 100000.0
    
    def test_competitor_info_valid(self):
        """测试有效的竞争对手信息模式"""
        competitor_data = {
            "name": "竞争对手A",
            "strengths": ["价格优势", "本地化服务"],
            "weaknesses": ["功能单一", "技术落后"],
            "market_position": "挑战者",
            "pricing": 80000.0,
            "notes": "主要竞争对手"
        }
        
        competitor = CompetitorInfo(**competitor_data)
        
        assert competitor.name == "竞争对手A"
        assert len(competitor.strengths) == 2
        assert len(competitor.weaknesses) == 2
        assert competitor.market_position == "挑战者"
        assert competitor.pricing == 80000.0
    
    def test_stakeholder_info_valid(self):
        """测试有效的利益相关者信息模式"""
        stakeholder_data = {
            "name": "张总",
            "title": "CTO",
            "role": "技术决策者",
            "influence_level": "high",
            "decision_power": "strong",
            "contact": {"phone": "13800138000", "email": "zhang@company.com"},
            "notes": "关键决策人"
        }
        
        stakeholder = StakeholderInfo(**stakeholder_data)
        
        assert stakeholder.name == "张总"
        assert stakeholder.title == "CTO"
        assert stakeholder.role == "技术决策者"
        assert stakeholder.influence_level == "high"
        assert stakeholder.contact["phone"] == "13800138000"
    
    def test_risk_info_valid(self):
        """测试有效的风险信息模式"""
        risk_data = {
            "type": "技术风险",
            "description": "技术方案可能不满足客户需求",
            "probability": 0.3,
            "impact": "high",
            "mitigation_plan": "提前进行技术验证",
            "owner": "技术经理"
        }
        
        risk = RiskInfo(**risk_data)
        
        assert risk.type == "技术风险"
        assert risk.description == "技术方案可能不满足客户需求"
        assert risk.probability == 0.3
        assert risk.impact == "high"
        assert risk.mitigation_plan == "提前进行技术验证"
        assert risk.owner == "技术经理"
    
    def test_risk_info_invalid_probability(self):
        """测试无效概率的风险信息"""
        with pytest.raises(ValidationError) as exc_info:
            RiskInfo(
                type="技术风险",
                description="风险描述",
                probability=1.5,  # 无效概率
                impact="high"
            )
        
        assert "probability" in str(exc_info.value)
    
    def test_next_action_valid(self):
        """测试有效的后续行动模式"""
        action_data = {
            "action": "准备技术方案",
            "assignee": "张工程师",
            "due_date": datetime.utcnow() + timedelta(days=7),
            "priority": "high",
            "status": "pending"
        }
        
        action = NextAction(**action_data)
        
        assert action.action == "准备技术方案"
        assert action.assignee == "张工程师"
        assert action.priority == "high"
        assert action.status == "pending"
        assert action.due_date is not None
    
    def test_opportunity_create_valid(self):
        """测试有效的机会创建模式"""
        opportunity_data = {
            "name": "ABC公司CRM项目",
            "description": "为ABC公司实施CRM系统",
            "customer_id": "customer-123",
            "value": 500000.0,
            "probability": 0.6,
            "stage_id": "stage-001",
            "expected_close_date": datetime.utcnow() + timedelta(days=90),
            "status": OpportunityStatus.OPEN,
            "priority": OpportunityPriority.HIGH,
            "products": [
                {
                    "id": "prod-001",
                    "name": "CRM标准版",
                    "quantity": 1,
                    "unit_price": 500000.0,
                    "total_price": 500000.0
                }
            ],
            "competitors": [
                {
                    "name": "竞争对手A",
                    "strengths": ["价格优势"],
                    "weaknesses": ["功能不足"],
                    "pricing": 400000.0
                }
            ],
            "stakeholders": [
                {
                    "name": "李总",
                    "title": "CEO",
                    "role": "最终决策者",
                    "influence_level": "high",
                    "decision_power": "strong"
                }
            ],
            "risks": [
                {
                    "type": "预算风险",
                    "description": "客户预算可能不足",
                    "probability": 0.2,
                    "impact": "high"
                }
            ],
            "assigned_to": "销售经理",
            "team_members": ["销售经理", "技术顾问"],
            "tags": ["大客户", "重点项目"],
            "category": "新客户",
            "custom_fields": {"source": "展会"}
        }
        
        opportunity = OpportunityCreate(**opportunity_data)
        
        assert opportunity.name == "ABC公司CRM项目"
        assert opportunity.customer_id == "customer-123"
        assert opportunity.value == 500000.0
        assert opportunity.probability == 0.6
        assert opportunity.status == OpportunityStatus.OPEN
        assert opportunity.priority == OpportunityPriority.HIGH
        assert len(opportunity.products) == 1
        assert len(opportunity.competitors) == 1
        assert len(opportunity.stakeholders) == 1
        assert len(opportunity.risks) == 1
        assert len(opportunity.team_members) == 2
        assert len(opportunity.tags) == 2
    
    def test_opportunity_create_invalid_value(self):
        """测试无效价值的机会创建"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(
                name="测试机会",
                customer_id="customer-123",
                value=-1000.0,  # 无效价值
                stage_id="stage-001"
            )
        
        assert "value" in str(exc_info.value)
    
    def test_opportunity_create_invalid_probability(self):
        """测试无效概率的机会创建"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(
                name="测试机会",
                customer_id="customer-123",
                value=100000.0,
                stage_id="stage-001",
                probability=1.5  # 无效概率
            )
        
        assert "probability" in str(exc_info.value)
    
    def test_opportunity_create_invalid_expected_close_date(self):
        """测试无效预期关闭日期的机会创建"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(
                name="测试机会",
                customer_id="customer-123",
                value=100000.0,
                stage_id="stage-001",
                expected_close_date=datetime.utcnow() - timedelta(days=1)  # 过去的日期
            )
        
        assert "预期关闭日期不能早于当前时间" in str(exc_info.value)
    
    def test_opportunity_update_partial(self):
        """测试部分更新机会模式"""
        update_data = {
            "name": "更新后的机会名称",
            "value": 600000.0,
            "probability": 0.8
        }
        
        opportunity_update = OpportunityUpdate(**update_data)
        
        assert opportunity_update.name == "更新后的机会名称"
        assert opportunity_update.value == 600000.0
        assert opportunity_update.probability == 0.8
        assert opportunity_update.customer_id is None  # 未设置的字段应为None
        assert opportunity_update.stage_id is None
    
    def test_opportunity_response(self):
        """测试机会响应模式"""
        stage_data = {
            "id": "stage-001",
            "name": "需求分析",
            "description": "分析客户需求",
            "stage_type": StageType.NEEDS_ANALYSIS,
            "order": 1,
            "probability": 0.3,
            "requirements": [],
            "entry_criteria": [],
            "exit_criteria": [],
            "is_active": True,
            "custom_fields": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        opportunity_data = {
            "id": "opp-123",
            "name": "ABC公司CRM项目",
            "description": "为ABC公司实施CRM系统",
            "customer_id": "customer-123",
            "value": 500000.0,
            "probability": 0.6,
            "stage_id": "stage-001",
            "expected_close_date": datetime.utcnow() + timedelta(days=90),
            "status": OpportunityStatus.OPEN,
            "priority": OpportunityPriority.HIGH,
            "products": [],
            "solution_details": {},
            "competitors": [],
            "competitive_advantages": [],
            "stakeholders": [],
            "decision_makers": [],
            "risks": [],
            "challenges": [],
            "team_members": [],
            "tags": [],
            "custom_fields": {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "stage": OpportunityStageResponse(**stage_data),
            "activities": [],
            "stage_history": []
        }
        
        opportunity_response = OpportunityResponse(**opportunity_data)
        
        assert opportunity_response.id == "opp-123"
        assert opportunity_response.name == "ABC公司CRM项目"
        assert opportunity_response.value == 500000.0
        assert opportunity_response.stage.name == "需求分析"
        assert opportunity_response.created_at is not None
        assert opportunity_response.updated_at is not None


class TestActivitySchemas:
    """活动模式测试"""
    
    def test_activity_create_valid(self):
        """测试有效的活动创建模式"""
        activity_data = {
            "activity_type": "meeting",
            "title": "需求调研会议",
            "description": "与客户讨论具体需求",
            "scheduled_at": datetime.utcnow() + timedelta(days=1),
            "duration_minutes": 120,
            "participants": ["客户代表", "销售经理", "技术顾问"],
            "organizer": "销售经理",
            "outcome": "pending",
            "next_actions": [
                {
                    "action": "准备技术方案",
                    "assignee": "技术顾问",
                    "priority": "high",
                    "status": "pending"
                }
            ],
            "status": "planned",
            "custom_fields": {"location": "客户办公室"}
        }
        
        activity = ActivityCreate(**activity_data)
        
        assert activity.activity_type == "meeting"
        assert activity.title == "需求调研会议"
        assert activity.duration_minutes == 120
        assert len(activity.participants) == 3
        assert activity.organizer == "销售经理"
        assert len(activity.next_actions) == 1
        assert activity.status == "planned"
        assert activity.custom_fields["location"] == "客户办公室"
    
    def test_activity_create_invalid_duration(self):
        """测试无效持续时间的活动创建"""
        with pytest.raises(ValidationError) as exc_info:
            ActivityCreate(
                activity_type="meeting",
                title="测试会议",
                duration_minutes=0  # 无效持续时间
            )
        
        assert "duration_minutes" in str(exc_info.value)
    
    def test_activity_update_partial(self):
        """测试部分更新活动模式"""
        update_data = {
            "title": "更新后的会议标题",
            "outcome": "completed",
            "completed_at": datetime.utcnow()
        }
        
        activity_update = ActivityUpdate(**update_data)
        
        assert activity_update.title == "更新后的会议标题"
        assert activity_update.outcome == "completed"
        assert activity_update.completed_at is not None
        assert activity_update.activity_type is None  # 未设置的字段应为None
    
    def test_activity_response(self):
        """测试活动响应模式"""
        activity_data = {
            "id": "activity-123",
            "opportunity_id": "opp-123",
            "activity_type": "call",
            "title": "客户电话沟通",
            "description": "讨论项目进展",
            "scheduled_at": datetime.utcnow(),
            "duration_minutes": 30,
            "participants": ["客户", "销售经理"],
            "organizer": "销售经理",
            "outcome": "positive",
            "next_actions": [],
            "status": "completed",
            "custom_fields": {},
            "completed_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        activity_response = ActivityResponse(**activity_data)
        
        assert activity_response.id == "activity-123"
        assert activity_response.opportunity_id == "opp-123"
        assert activity_response.activity_type == "call"
        assert activity_response.title == "客户电话沟通"
        assert activity_response.status == "completed"
        assert activity_response.completed_at is not None
        assert activity_response.created_at is not None


class TestStageTransitionSchemas:
    """阶段转换模式测试"""
    
    def test_stage_transition_request_valid(self):
        """测试有效的阶段转换请求模式"""
        request_data = {
            "opportunity_id": "opp-123",
            "to_stage_id": "stage-002",
            "reason": "客户确认需求",
            "notes": "客户对方案很满意",
            "validate_criteria": True
        }
        
        request = StageTransitionRequest(**request_data)
        
        assert request.opportunity_id == "opp-123"
        assert request.to_stage_id == "stage-002"
        assert request.reason == "客户确认需求"
        assert request.notes == "客户对方案很满意"
        assert request.validate_criteria is True
    
    def test_stage_transition_response_success(self):
        """测试成功的阶段转换响应模式"""
        response_data = {
            "success": True,
            "message": "阶段转换成功",
            "opportunity": None,  # 在实际使用中会包含完整的机会信息
            "validation_errors": []
        }
        
        response = StageTransitionResponse(**response_data)
        
        assert response.success is True
        assert response.message == "阶段转换成功"
        assert response.opportunity is None
        assert len(response.validation_errors) == 0
    
    def test_stage_transition_response_failure(self):
        """测试失败的阶段转换响应模式"""
        response_data = {
            "success": False,
            "message": "阶段转换失败",
            "opportunity": None,
            "validation_errors": ["未满足退出标准", "缺少必要文档"]
        }
        
        response = StageTransitionResponse(**response_data)
        
        assert response.success is False
        assert response.message == "阶段转换失败"
        assert len(response.validation_errors) == 2
        assert "未满足退出标准" in response.validation_errors


class TestStatisticsSchemas:
    """统计模式测试"""
    
    def test_opportunity_statistics_valid(self):
        """测试有效的机会统计模式"""
        stats_data = {
            "total_opportunities": 100,
            "total_value": 10000000.0,
            "weighted_value": 6000000.0,
            "by_status": {"open": 80, "won": 15, "lost": 5},
            "by_stage": {"qualification": 30, "needs_analysis": 25, "proposal": 20, "negotiation": 15, "closed": 10},
            "by_priority": {"high": 20, "medium": 50, "low": 30},
            "by_assigned": {"销售经理A": 40, "销售经理B": 35, "销售经理C": 25},
            "average_value": 100000.0,
            "win_rate": 0.75,
            "average_sales_cycle": 90.5,
            "created_this_month": 15,
            "expected_close_this_month": 8
        }
        
        stats = OpportunityStatistics(**stats_data)
        
        assert stats.total_opportunities == 100
        assert stats.total_value == 10000000.0
        assert stats.weighted_value == 6000000.0
        assert stats.by_status["open"] == 80
        assert stats.by_stage["qualification"] == 30
        assert stats.win_rate == 0.75
        assert stats.average_sales_cycle == 90.5
    
    def test_funnel_analysis_valid(self):
        """测试有效的漏斗分析模式"""
        funnel_data = {
            "stage_id": "stage-001",
            "stage_name": "资格认证",
            "opportunity_count": 50,
            "total_value": 5000000.0,
            "weighted_value": 1500000.0,
            "conversion_rate": 0.8,
            "average_duration": 15.5
        }
        
        funnel = FunnelAnalysis(**funnel_data)
        
        assert funnel.stage_id == "stage-001"
        assert funnel.stage_name == "资格认证"
        assert funnel.opportunity_count == 50
        assert funnel.total_value == 5000000.0
        assert funnel.conversion_rate == 0.8
        assert funnel.average_duration == 15.5
    
    def test_funnel_analysis_response_valid(self):
        """测试有效的漏斗分析响应模式"""
        funnel_stages = [
            {
                "stage_id": "stage-001",
                "stage_name": "资格认证",
                "opportunity_count": 50,
                "total_value": 5000000.0,
                "weighted_value": 1500000.0,
                "conversion_rate": 0.8,
                "average_duration": 15.5
            },
            {
                "stage_id": "stage-002",
                "stage_name": "需求分析",
                "opportunity_count": 40,
                "total_value": 4000000.0,
                "weighted_value": 1600000.0,
                "conversion_rate": 0.75,
                "average_duration": 20.0
            }
        ]
        
        response_data = {
            "funnel_stages": funnel_stages,
            "overall_conversion_rate": 0.6,
            "total_pipeline_value": 9000000.0,
            "weighted_pipeline_value": 3100000.0,
            "analysis_date": datetime.utcnow()
        }
        
        response = FunnelAnalysisResponse(**response_data)
        
        assert len(response.funnel_stages) == 2
        assert response.overall_conversion_rate == 0.6
        assert response.total_pipeline_value == 9000000.0
        assert response.weighted_pipeline_value == 3100000.0
        assert response.analysis_date is not None
    
    def test_opportunity_list_response_valid(self):
        """测试有效的机会列表响应模式"""
        list_data = {
            "opportunities": [],  # 在实际使用中会包含机会列表
            "total": 100,
            "page": 1,
            "size": 20,
            "pages": 5
        }
        
        list_response = OpportunityListResponse(**list_data)
        
        assert len(list_response.opportunities) == 0
        assert list_response.total == 100
        assert list_response.page == 1
        assert list_response.size == 20
        assert list_response.pages == 5


class TestValidationEdgeCases:
    """验证边界情况测试"""
    
    def test_empty_string_validation(self):
        """测试空字符串验证"""
        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(
                name="",  # 空字符串
                customer_id="customer-123",
                value=100000.0,
                stage_id="stage-001"
            )
        
        assert "name" in str(exc_info.value)
    
    def test_long_string_validation(self):
        """测试超长字符串验证"""
        long_name = "x" * 201  # 超过200字符限制
        
        with pytest.raises(ValidationError) as exc_info:
            OpportunityCreate(
                name=long_name,
                customer_id="customer-123",
                value=100000.0,
                stage_id="stage-001"
            )
        
        assert "name" in str(exc_info.value)
    
    def test_zero_value_validation(self):
        """测试零值验证"""
        opportunity = OpportunityCreate(
            name="零价值机会",
            customer_id="customer-123",
            value=0.0,  # 零值应该是有效的
            stage_id="stage-001"
        )
        
        assert opportunity.value == 0.0
    
    def test_boundary_probability_validation(self):
        """测试概率边界值验证"""
        # 测试0.0概率
        opportunity1 = OpportunityCreate(
            name="零概率机会",
            customer_id="customer-123",
            value=100000.0,
            stage_id="stage-001",
            probability=0.0
        )
        assert opportunity1.probability == 0.0
        
        # 测试1.0概率
        opportunity2 = OpportunityCreate(
            name="确定机会",
            customer_id="customer-123",
            value=100000.0,
            stage_id="stage-001",
            probability=1.0
        )
        assert opportunity2.probability == 1.0
    
    def test_custom_fields_validation(self):
        """测试自定义字段验证"""
        custom_fields = {
            "source": "展会",
            "priority_score": 85,
            "tags": ["重点客户", "大项目"],
            "metadata": {
                "created_by": "系统",
                "import_date": "2024-01-01"
            }
        }
        
        opportunity = OpportunityCreate(
            name="自定义字段测试",
            customer_id="customer-123",
            value=100000.0,
            stage_id="stage-001",
            custom_fields=custom_fields
        )
        
        assert opportunity.custom_fields["source"] == "展会"
        assert opportunity.custom_fields["priority_score"] == 85
        assert len(opportunity.custom_fields["tags"]) == 2
        assert opportunity.custom_fields["metadata"]["created_by"] == "系统"