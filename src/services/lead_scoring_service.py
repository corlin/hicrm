"""
线索评分服务
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload

from src.models.lead import Lead, LeadScore, ScoreFactor
from src.schemas.lead import LeadScoreDetail, ScoreFactorDetail, ScoreFactorConfig
from src.core.database import get_db

logger = logging.getLogger(__name__)


class LeadScoringService:
    """线索评分服务"""
    
    def __init__(self):
        self.algorithm_version = "v1.0"
        self.default_factors = self._get_default_score_factors()
    
    def _get_default_score_factors(self) -> List[Dict[str, Any]]:
        """获取默认评分因子配置"""
        return [
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
                }
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
                }
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
                }
            },
            {
                "name": "urgency_level",
                "category": "timing",
                "description": "紧急程度评分",
                "weight": 0.15,
                "max_score": 100.0,
                "min_score": 0.0,
                "calculation_rules": {
                    "type": "timeline",
                    "mappings": {
                        "immediate": 100,
                        "1_month": 80,
                        "3_months": 60,
                        "6_months": 40,
                        "1_year": 20,
                        "unknown": 10
                    }
                }
            },
            {
                "name": "contact_quality",
                "category": "contact",
                "description": "联系信息质量评分",
                "weight": 0.10,
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
                }
            }
        ]
    
    async def calculate_lead_score(
        self, 
        lead: Lead, 
        db: AsyncSession,
        force_recalculate: bool = False
    ) -> LeadScoreDetail:
        """计算线索评分"""
        try:
            # 检查是否需要重新计算
            if not force_recalculate:
                existing_score = await self._get_latest_score(lead.id, db)
                if existing_score and self._is_score_fresh(existing_score):
                    return self._convert_to_score_detail(existing_score)
            
            # 获取评分因子配置
            score_factors = await self._get_active_score_factors(db)
            if not score_factors:
                # 使用默认配置
                await self._initialize_default_factors(db)
                score_factors = await self._get_active_score_factors(db)
            
            # 计算各个因子的分数
            factor_scores = []
            total_weighted_score = 0.0
            total_weight = 0.0
            
            for factor in score_factors:
                factor_score = await self._calculate_factor_score(lead, factor)
                factor_scores.append(factor_score)
                total_weighted_score += factor_score.score
                total_weight += factor_score.weight
            
            # 计算总分和置信度
            final_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
            confidence = self._calculate_confidence(factor_scores, lead)
            
            # 创建评分详情
            score_detail = LeadScoreDetail(
                total_score=round(final_score, 2),
                confidence=round(confidence, 3),
                factors=factor_scores,
                algorithm_version=self.algorithm_version,
                calculated_at=datetime.utcnow()
            )
            
            # 保存评分结果
            await self._save_lead_score(lead.id, score_detail, db)
            
            logger.info(f"计算线索评分完成: lead_id={lead.id}, score={final_score}")
            return score_detail
            
        except Exception as e:
            logger.error(f"计算线索评分失败: lead_id={lead.id}, error={str(e)}")
            raise
    
    async def _calculate_factor_score(
        self, 
        lead: Lead, 
        factor: ScoreFactor
    ) -> ScoreFactorDetail:
        """计算单个因子的分数"""
        try:
            rules = factor.calculation_rules
            rule_type = rules.get("type", "categorical")
            
            if rule_type == "categorical":
                score, reason = self._calculate_categorical_score(lead, factor, rules)
            elif rule_type == "threshold":
                score, reason = self._calculate_threshold_score(lead, factor, rules)
            elif rule_type == "timeline":
                score, reason = self._calculate_timeline_score(lead, factor, rules)
            elif rule_type == "composite":
                score, reason = self._calculate_composite_score(lead, factor, rules)
            else:
                score, reason = 0.0, f"未知的计算规则类型: {rule_type}"
            
            # 应用权重
            weighted_score = score * factor.weight
            
            return ScoreFactorDetail(
                name=factor.name,
                category=factor.category,
                weight=factor.weight,
                value=score,
                score=weighted_score,
                reason=reason
            )
            
        except Exception as e:
            logger.error(f"计算因子分数失败: factor={factor.name}, error={str(e)}")
            return ScoreFactorDetail(
                name=factor.name,
                category=factor.category,
                weight=factor.weight,
                value=0.0,
                score=0.0,
                reason=f"计算错误: {str(e)}"
            )
    
    def _calculate_categorical_score(
        self, 
        lead: Lead, 
        factor: ScoreFactor, 
        rules: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算分类型评分"""
        mappings = rules.get("mappings", {})
        
        if factor.name == "company_size":
            company_info = lead.company_info or {}
            size = company_info.get("size", "unknown").lower()
            score = mappings.get(size, mappings.get("unknown", 0))
            reason = f"公司规模: {size}"
            
        elif factor.name == "industry_match":
            industry = (lead.industry or "unknown").lower()
            score = mappings.get(industry, mappings.get("unknown", 0))
            reason = f"行业: {industry}"
            
        else:
            score = mappings.get("unknown", 0)
            reason = f"未知的分类因子: {factor.name}"
        
        return float(score), reason
    
    def _calculate_threshold_score(
        self, 
        lead: Lead, 
        factor: ScoreFactor, 
        rules: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算阈值型评分"""
        thresholds = rules.get("thresholds", [])
        
        if factor.name == "budget_range":
            budget = lead.budget or 0
            for threshold in thresholds:
                if budget >= threshold["min"]:
                    score = threshold["score"]
                    reason = f"预算: {budget:,.0f}元"
                    return float(score), reason
            
            score = 0
            reason = f"预算: {budget:,.0f}元 (低于最低阈值)"
        else:
            score = 0
            reason = f"未知的阈值因子: {factor.name}"
        
        return float(score), reason
    
    def _calculate_timeline_score(
        self, 
        lead: Lead, 
        factor: ScoreFactor, 
        rules: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算时间线评分"""
        mappings = rules.get("mappings", {})
        timeline = (lead.timeline or "unknown").lower()
        
        # 标准化时间线描述
        timeline_mapping = {
            "立即": "immediate",
            "马上": "immediate", 
            "urgent": "immediate",
            "1个月": "1_month",
            "一个月": "1_month",
            "3个月": "3_months",
            "三个月": "3_months",
            "6个月": "6_months",
            "六个月": "6_months",
            "1年": "1_year",
            "一年": "1_year"
        }
        
        normalized_timeline = timeline_mapping.get(timeline, timeline)
        score = mappings.get(normalized_timeline, mappings.get("unknown", 0))
        reason = f"时间线: {lead.timeline or '未知'}"
        
        return float(score), reason
    
    def _calculate_composite_score(
        self, 
        lead: Lead, 
        factor: ScoreFactor, 
        rules: Dict[str, Any]
    ) -> Tuple[float, str]:
        """计算复合型评分"""
        components = rules.get("components", {})
        
        if factor.name == "contact_quality":
            contact = lead.contact or {}
            total_score = 0
            reasons = []
            
            if contact.get("email"):
                total_score += components.get("has_email", 0)
                reasons.append("有邮箱")
            
            if contact.get("phone"):
                total_score += components.get("has_phone", 0)
                reasons.append("有电话")
            
            if lead.title:
                total_score += components.get("has_title", 0)
                reasons.append("有职位")
            
            if contact.get("linkedin"):
                total_score += components.get("has_linkedin", 0)
                reasons.append("有LinkedIn")
            
            if contact.get("address"):
                total_score += components.get("has_address", 0)
                reasons.append("有地址")
            
            reason = f"联系信息完整度: {', '.join(reasons) if reasons else '信息不完整'}"
            return float(total_score), reason
        
        return 0.0, f"未知的复合因子: {factor.name}"
    
    def _calculate_confidence(
        self, 
        factor_scores: List[ScoreFactorDetail], 
        lead: Lead
    ) -> float:
        """计算置信度"""
        # 基础置信度
        base_confidence = 0.5
        
        # 根据数据完整性调整置信度
        completeness_bonus = 0.0
        
        # 检查关键字段完整性
        if lead.company and len(lead.company.strip()) > 0:
            completeness_bonus += 0.1
        
        if lead.industry:
            completeness_bonus += 0.1
        
        if lead.budget and lead.budget > 0:
            completeness_bonus += 0.15
        
        if lead.timeline:
            completeness_bonus += 0.1
        
        contact = lead.contact or {}
        if contact.get("email") or contact.get("phone"):
            completeness_bonus += 0.1
        
        # 根据评分因子的一致性调整置信度
        if factor_scores:
            scores = [f.value for f in factor_scores]
            score_variance = self._calculate_variance(scores)
            # 分数越一致，置信度越高
            consistency_bonus = max(0, 0.05 - score_variance / 1000)
        else:
            consistency_bonus = 0
        
        final_confidence = min(1.0, base_confidence + completeness_bonus + consistency_bonus)
        return final_confidence
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """计算方差"""
        if not scores:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / len(scores)
        return variance
    
    async def _get_latest_score(
        self, 
        lead_id: str, 
        db: AsyncSession
    ) -> Optional[LeadScore]:
        """获取最新的评分记录"""
        try:
            stmt = select(LeadScore).where(
                LeadScore.lead_id == lead_id
            ).order_by(LeadScore.calculated_at.desc()).limit(1)
            
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"获取最新评分失败: lead_id={lead_id}, error={str(e)}")
            return None
    
    def _is_score_fresh(self, score: LeadScore, hours: int = 24) -> bool:
        """检查评分是否新鲜"""
        if not score.calculated_at:
            return False
        
        age = datetime.utcnow() - score.calculated_at
        return age < timedelta(hours=hours)
    
    async def _get_active_score_factors(self, db: AsyncSession) -> List[ScoreFactor]:
        """获取活跃的评分因子"""
        try:
            stmt = select(ScoreFactor).where(
                ScoreFactor.is_active == "true"
            ).order_by(ScoreFactor.category, ScoreFactor.name)
            
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"获取评分因子失败: error={str(e)}")
            return []
    
    async def _initialize_default_factors(self, db: AsyncSession) -> None:
        """初始化默认评分因子"""
        try:
            for factor_config in self.default_factors:
                factor = ScoreFactor(
                    name=factor_config["name"],
                    category=factor_config["category"],
                    description=factor_config["description"],
                    weight=factor_config["weight"],
                    max_score=factor_config["max_score"],
                    min_score=factor_config["min_score"],
                    calculation_rules=factor_config["calculation_rules"],
                    is_active="true"
                )
                db.add(factor)
            
            await db.commit()
            logger.info("默认评分因子初始化完成")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"初始化默认评分因子失败: error={str(e)}")
            raise
    
    async def _save_lead_score(
        self, 
        lead_id: str, 
        score_detail: LeadScoreDetail, 
        db: AsyncSession
    ) -> None:
        """保存线索评分"""
        try:
            # 转换因子详情为JSON格式
            factors_json = [
                {
                    "name": f.name,
                    "category": f.category,
                    "weight": f.weight,
                    "value": f.value,
                    "score": f.score,
                    "reason": f.reason
                }
                for f in score_detail.factors
            ]
            
            lead_score = LeadScore(
                lead_id=lead_id,
                total_score=score_detail.total_score,
                confidence=score_detail.confidence,
                score_factors=factors_json,
                algorithm_version=score_detail.algorithm_version,
                calculated_at=score_detail.calculated_at
            )
            
            db.add(lead_score)
            await db.commit()
            
        except Exception as e:
            await db.rollback()
            logger.error(f"保存线索评分失败: lead_id={lead_id}, error={str(e)}")
            raise
    
    def _convert_to_score_detail(self, lead_score: LeadScore) -> LeadScoreDetail:
        """转换数据库记录为评分详情"""
        factors = []
        for factor_data in lead_score.score_factors or []:
            factors.append(ScoreFactorDetail(
                name=factor_data["name"],
                category=factor_data["category"],
                weight=factor_data["weight"],
                value=factor_data["value"],
                score=factor_data["score"],
                reason=factor_data["reason"]
            ))
        
        return LeadScoreDetail(
            total_score=lead_score.total_score,
            confidence=lead_score.confidence,
            factors=factors,
            algorithm_version=lead_score.algorithm_version,
            calculated_at=lead_score.calculated_at
        )
    
    async def batch_calculate_scores(
        self, 
        lead_ids: List[str], 
        db: AsyncSession,
        force_recalculate: bool = False
    ) -> Dict[str, LeadScoreDetail]:
        """批量计算线索评分"""
        results = {}
        
        # 获取线索数据
        stmt = select(Lead).where(Lead.id.in_(lead_ids))
        result = await db.execute(stmt)
        leads = result.scalars().all()
        
        # 并发计算评分
        tasks = []
        for lead in leads:
            task = self.calculate_lead_score(lead, db, force_recalculate)
            tasks.append((str(lead.id), task))
        
        # 等待所有任务完成
        for lead_id, task in tasks:
            try:
                score_detail = await task
                results[lead_id] = score_detail
            except Exception as e:
                logger.error(f"批量计算评分失败: lead_id={lead_id}, error={str(e)}")
                # 继续处理其他线索
                continue
        
        return results
    
    async def get_score_factor_configs(self, db: AsyncSession) -> List[ScoreFactorConfig]:
        """获取评分因子配置"""
        factors = await self._get_active_score_factors(db)
        configs = []
        
        for factor in factors:
            config = ScoreFactorConfig(
                name=factor.name,
                category=factor.category,
                description=factor.description,
                weight=factor.weight,
                max_score=factor.max_score,
                min_score=factor.min_score,
                calculation_rules=factor.calculation_rules,
                is_active=factor.is_active == "true"
            )
            configs.append(config)
        
        return configs
    
    async def update_score_factor(
        self, 
        factor_id: str, 
        config: ScoreFactorConfig, 
        db: AsyncSession
    ) -> None:
        """更新评分因子配置"""
        try:
            stmt = select(ScoreFactor).where(ScoreFactor.id == factor_id)
            result = await db.execute(stmt)
            factor = result.scalar_one_or_none()
            
            if not factor:
                raise ValueError(f"评分因子不存在: {factor_id}")
            
            # 更新配置
            factor.name = config.name
            factor.category = config.category
            factor.description = config.description
            factor.weight = config.weight
            factor.max_score = config.max_score
            factor.min_score = config.min_score
            factor.calculation_rules = config.calculation_rules
            factor.is_active = "true" if config.is_active else "false"
            factor.updated_at = datetime.utcnow()
            
            await db.commit()
            logger.info(f"评分因子配置更新成功: factor_id={factor_id}")
            
        except Exception as e:
            await db.rollback()
            logger.error(f"更新评分因子配置失败: factor_id={factor_id}, error={str(e)}")
            raise