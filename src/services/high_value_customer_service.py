# 高价值客户自动识别算法服务

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from ..models.multimodal import (
    HighValueCustomerProfile, CustomerValueIndicator, DataModalityType,
    MultimodalDataPoint, BehaviorData, VoiceAnalysisResult
)
from ..models.customer import Customer
from ..models.lead import Lead
from ..core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ValueScoringWeights:
    """价值评分权重配置"""
    behavioral_weight: float = 0.35
    transactional_weight: float = 0.25
    engagement_weight: float = 0.20
    demographic_weight: float = 0.15
    voice_sentiment_weight: float = 0.05

class HighValueCustomerService:
    """高价值客户识别服务"""
    
    def __init__(self):
        self.settings = settings
        self.scoring_weights = ValueScoringWeights()
        self.value_thresholds = {
            'very_high': 0.85,
            'high': 0.70,
            'medium': 0.50,
            'low': 0.30
        }
        self.model_cache = {}
        
    async def identify_high_value_customers(
        self,
        customer_data: List[Dict[str, Any]],
        behavior_data: List[BehaviorData],
        voice_data: List[VoiceAnalysisResult],
        time_window: Optional[timedelta] = None
    ) -> List[HighValueCustomerProfile]:
        """
        识别高价值客户
        
        Args:
            customer_data: 客户基础数据
            behavior_data: 行为数据
            voice_data: 语音分析数据
            time_window: 分析时间窗口
            
        Returns:
            List[HighValueCustomerProfile]: 高价值客户画像列表
        """
        try:
            high_value_customers = []
            
            # 按客户ID分组数据
            customer_groups = self._group_data_by_customer(
                customer_data, behavior_data, voice_data
            )
            
            for customer_id, grouped_data in customer_groups.items():
                try:
                    # 计算客户价值评分
                    value_profile = await self._calculate_customer_value(
                        customer_id, grouped_data, time_window
                    )
                    
                    # 判断是否为高价值客户
                    if value_profile.overall_score >= self.value_thresholds['medium']:
                        high_value_customers.append(value_profile)
                        
                except Exception as e:
                    logger.error(f"计算客户 {customer_id} 价值评分失败: {str(e)}")
                    continue
            
            # 按评分排序
            high_value_customers.sort(key=lambda x: x.overall_score, reverse=True)
            
            logger.info(f"识别出 {len(high_value_customers)} 个高价值客户")
            return high_value_customers
            
        except Exception as e:
            logger.error(f"高价值客户识别失败: {str(e)}")
            raise
    
    def _group_data_by_customer(
        self,
        customer_data: List[Dict[str, Any]],
        behavior_data: List[BehaviorData],
        voice_data: List[VoiceAnalysisResult]
    ) -> Dict[str, Dict[str, Any]]:
        """按客户ID分组数据"""
        groups = {}
        
        # 分组客户基础数据
        for customer in customer_data:
            customer_id = customer.get('id')
            if customer_id:
                groups[customer_id] = {
                    'customer_info': customer,
                    'behavior_data': [],
                    'voice_data': []
                }
        
        # 分组行为数据
        for behavior in behavior_data:
            customer_id = behavior.customer_id
            if customer_id in groups:
                groups[customer_id]['behavior_data'].append(behavior)
        
        # 分组语音数据(假设voice_data中包含customer_id)
        for voice in voice_data:
            # 这里需要根据实际数据结构调整
            customer_id = getattr(voice, 'customer_id', None)
            if customer_id and customer_id in groups:
                groups[customer_id]['voice_data'].append(voice)
        
        return groups
    
    async def _calculate_customer_value(
        self,
        customer_id: str,
        grouped_data: Dict[str, Any],
        time_window: Optional[timedelta]
    ) -> HighValueCustomerProfile:
        """计算客户价值评分"""
        
        customer_info = grouped_data['customer_info']
        behavior_data = grouped_data['behavior_data']
        voice_data = grouped_data['voice_data']
        
        # 计算各维度指标
        behavioral_indicators = await self._calculate_behavioral_indicators(
            behavior_data, time_window
        )
        
        transactional_indicators = await self._calculate_transactional_indicators(
            customer_info
        )
        
        engagement_indicators = await self._calculate_engagement_indicators(
            behavior_data, voice_data
        )
        
        demographic_indicators = await self._calculate_demographic_indicators(
            customer_info
        )
        
        voice_sentiment_indicators = await self._calculate_voice_sentiment_indicators(
            voice_data
        )
        
        # 合并所有指标
        all_indicators = (
            behavioral_indicators + 
            transactional_indicators + 
            engagement_indicators + 
            demographic_indicators + 
            voice_sentiment_indicators
        )
        
        # 计算综合评分
        overall_score = self._calculate_weighted_score(all_indicators)
        
        # 生成行为模式分析
        behavioral_patterns = await self._analyze_behavioral_patterns(behavior_data)
        
        # 生成沟通偏好分析
        communication_preferences = await self._analyze_communication_preferences(
            voice_data, behavior_data
        )
        
        # 预测客户价值
        predicted_value = await self._predict_customer_value(
            all_indicators, behavioral_patterns
        )
        
        # 识别风险因素
        risk_factors = await self._identify_risk_factors(
            all_indicators, behavioral_patterns
        )
        
        # 识别机会点
        opportunities = await self._identify_opportunities(
            all_indicators, behavioral_patterns
        )
        
        # 生成推荐行动
        recommended_actions = await self._generate_recommended_actions(
            overall_score, all_indicators, risk_factors, opportunities
        )
        
        return HighValueCustomerProfile(
            customer_id=customer_id,
            overall_score=overall_score,
            value_indicators=all_indicators,
            behavioral_patterns=behavioral_patterns,
            communication_preferences=communication_preferences,
            engagement_history=self._extract_engagement_history(behavior_data),
            predicted_value=predicted_value,
            risk_factors=risk_factors,
            opportunities=opportunities,
            recommended_actions=recommended_actions,
            last_updated=datetime.now()
        )
    
    async def _calculate_behavioral_indicators(
        self,
        behavior_data: List[BehaviorData],
        time_window: Optional[timedelta]
    ) -> List[CustomerValueIndicator]:
        """计算行为指标"""
        indicators = []
        
        if not behavior_data:
            return indicators
        
        # 过滤时间窗口
        if time_window:
            cutoff_time = datetime.now() - time_window
            behavior_data = [
                data for data in behavior_data 
                if data.timestamp >= cutoff_time
            ]
        
        if not behavior_data:
            return indicators
        
        # 访问频率指标
        visit_frequency = len(behavior_data) / max(1, time_window.days if time_window else 30)
        indicators.append(CustomerValueIndicator(
            indicator_name="visit_frequency",
            value=min(1.0, visit_frequency / 5),  # 标准化到0-1
            weight=0.3,
            confidence=0.9,
            source_modality=DataModalityType.BEHAVIOR,
            calculation_method="visits_per_day_normalized"
        ))
        
        # 平均参与度
        avg_engagement = np.mean([data.engagement_score for data in behavior_data])
        indicators.append(CustomerValueIndicator(
            indicator_name="average_engagement",
            value=avg_engagement,
            weight=0.4,
            confidence=0.95,
            source_modality=DataModalityType.BEHAVIOR,
            calculation_method="mean_engagement_score"
        ))
        
        # 会话深度(平均页面浏览数)
        avg_page_views = np.mean([len(data.page_views) for data in behavior_data])
        session_depth_score = min(1.0, avg_page_views / 20)  # 标准化
        indicators.append(CustomerValueIndicator(
            indicator_name="session_depth",
            value=session_depth_score,
            weight=0.2,
            confidence=0.85,
            source_modality=DataModalityType.BEHAVIOR,
            calculation_method="average_page_views_normalized"
        ))
        
        # 转化指标数量
        total_conversions = sum(len(data.conversion_indicators) for data in behavior_data)
        conversion_score = min(1.0, total_conversions / 10)  # 标准化
        indicators.append(CustomerValueIndicator(
            indicator_name="conversion_activity",
            value=conversion_score,
            weight=0.1,
            confidence=0.8,
            source_modality=DataModalityType.BEHAVIOR,
            calculation_method="total_conversions_normalized"
        ))
        
        return indicators
    
    async def _calculate_transactional_indicators(
        self,
        customer_info: Dict[str, Any]
    ) -> List[CustomerValueIndicator]:
        """计算交易指标"""
        indicators = []
        
        # 公司规模指标
        company_size = customer_info.get('size', 'small')
        size_scores = {
            'startup': 0.2,
            'small': 0.4,
            'medium': 0.6,
            'large': 0.8,
            'enterprise': 1.0
        }
        size_score = size_scores.get(company_size, 0.4)
        
        indicators.append(CustomerValueIndicator(
            indicator_name="company_size",
            value=size_score,
            weight=0.4,
            confidence=0.95,
            source_modality=DataModalityType.TEXT,
            calculation_method="categorical_mapping"
        ))
        
        # 行业价值指标
        industry = customer_info.get('industry', 'unknown')
        high_value_industries = [
            'finance', 'technology', 'healthcare', 'manufacturing', 'retail'
        ]
        industry_score = 0.8 if industry.lower() in high_value_industries else 0.4
        
        indicators.append(CustomerValueIndicator(
            indicator_name="industry_value",
            value=industry_score,
            weight=0.3,
            confidence=0.8,
            source_modality=DataModalityType.TEXT,
            calculation_method="industry_classification"
        ))
        
        # 客户状态指标
        status = customer_info.get('status', 'prospect')
        status_scores = {
            'prospect': 0.3,
            'qualified': 0.6,
            'customer': 0.9,
            'inactive': 0.1
        }
        status_score = status_scores.get(status, 0.3)
        
        indicators.append(CustomerValueIndicator(
            indicator_name="customer_status",
            value=status_score,
            weight=0.3,
            confidence=0.9,
            source_modality=DataModalityType.TEXT,
            calculation_method="status_mapping"
        ))
        
        return indicators
    
    async def _calculate_engagement_indicators(
        self,
        behavior_data: List[BehaviorData],
        voice_data: List[VoiceAnalysisResult]
    ) -> List[CustomerValueIndicator]:
        """计算参与度指标"""
        indicators = []
        
        # 数字化参与度
        if behavior_data:
            digital_engagement = np.mean([data.engagement_score for data in behavior_data])
            indicators.append(CustomerValueIndicator(
                indicator_name="digital_engagement",
                value=digital_engagement,
                weight=0.6,
                confidence=0.9,
                source_modality=DataModalityType.BEHAVIOR,
                calculation_method="mean_digital_engagement"
            ))
        
        # 语音参与度
        if voice_data:
            # 基于语音分析的参与度
            voice_engagement_factors = []
            for voice in voice_data:
                # 综合考虑置信度、情感和意图
                engagement_factor = (
                    voice.confidence * 0.4 +
                    (1.0 if voice.sentiment == 'positive' else 0.5 if voice.sentiment == 'neutral' else 0.2) * 0.3 +
                    (1.0 if voice.intent else 0.5) * 0.3
                )
                voice_engagement_factors.append(engagement_factor)
            
            voice_engagement = np.mean(voice_engagement_factors)
            indicators.append(CustomerValueIndicator(
                indicator_name="voice_engagement",
                value=voice_engagement,
                weight=0.4,
                confidence=0.8,
                source_modality=DataModalityType.VOICE,
                calculation_method="composite_voice_engagement"
            ))
        
        return indicators
    
    async def _calculate_demographic_indicators(
        self,
        customer_info: Dict[str, Any]
    ) -> List[CustomerValueIndicator]:
        """计算人口统计学指标"""
        indicators = []
        
        # 地理位置价值(假设有地理信息)
        location = customer_info.get('location', {})
        city = location.get('city', '')
        
        # 一线城市给予更高评分
        tier1_cities = ['北京', '上海', '广州', '深圳']
        tier2_cities = ['杭州', '南京', '成都', '武汉', '西安', '苏州']
        
        if city in tier1_cities:
            location_score = 1.0
        elif city in tier2_cities:
            location_score = 0.8
        else:
            location_score = 0.6
        
        indicators.append(CustomerValueIndicator(
            indicator_name="location_value",
            value=location_score,
            weight=0.5,
            confidence=0.7,
            source_modality=DataModalityType.TEXT,
            calculation_method="city_tier_classification"
        ))
        
        # 公司成立时间(稳定性指标)
        founded_year = customer_info.get('founded_year')
        if founded_year:
            company_age = datetime.now().year - founded_year
            # 3-20年的公司给予较高评分
            if 3 <= company_age <= 20:
                stability_score = 0.9
            elif company_age > 20:
                stability_score = 0.8
            else:
                stability_score = 0.6
        else:
            stability_score = 0.5
        
        indicators.append(CustomerValueIndicator(
            indicator_name="company_stability",
            value=stability_score,
            weight=0.5,
            confidence=0.6,
            source_modality=DataModalityType.TEXT,
            calculation_method="company_age_assessment"
        ))
        
        return indicators
    
    async def _calculate_voice_sentiment_indicators(
        self,
        voice_data: List[VoiceAnalysisResult]
    ) -> List[CustomerValueIndicator]:
        """计算语音情感指标"""
        indicators = []
        
        if not voice_data:
            return indicators
        
        # 整体情感倾向
        positive_count = sum(1 for voice in voice_data if voice.sentiment == 'positive')
        sentiment_ratio = positive_count / len(voice_data)
        
        indicators.append(CustomerValueIndicator(
            indicator_name="sentiment_positivity",
            value=sentiment_ratio,
            weight=0.4,
            confidence=0.8,
            source_modality=DataModalityType.VOICE,
            calculation_method="positive_sentiment_ratio"
        ))
        
        # 语音质量和清晰度
        avg_confidence = np.mean([voice.confidence for voice in voice_data])
        indicators.append(CustomerValueIndicator(
            indicator_name="voice_clarity",
            value=avg_confidence,
            weight=0.3,
            confidence=0.9,
            source_modality=DataModalityType.VOICE,
            calculation_method="average_transcription_confidence"
        ))
        
        # 意图明确性
        intent_clarity = sum(1 for voice in voice_data if voice.intent) / len(voice_data)
        indicators.append(CustomerValueIndicator(
            indicator_name="intent_clarity",
            value=intent_clarity,
            weight=0.3,
            confidence=0.7,
            source_modality=DataModalityType.VOICE,
            calculation_method="intent_detection_ratio"
        ))
        
        return indicators
    
    def _calculate_weighted_score(
        self,
        indicators: List[CustomerValueIndicator]
    ) -> float:
        """计算加权综合评分"""
        if not indicators:
            return 0.0
        
        # 按模态分组
        modality_groups = {}
        for indicator in indicators:
            modality = indicator.source_modality
            if modality not in modality_groups:
                modality_groups[modality] = []
            modality_groups[modality].append(indicator)
        
        # 计算各模态的加权评分
        modality_scores = {}
        for modality, group_indicators in modality_groups.items():
            total_weighted_value = sum(
                indicator.value * indicator.weight * indicator.confidence
                for indicator in group_indicators
            )
            total_weight = sum(
                indicator.weight * indicator.confidence
                for indicator in group_indicators
            )
            modality_scores[modality] = total_weighted_value / max(total_weight, 0.001)
        
        # 应用模态权重
        final_score = 0.0
        weights = self.scoring_weights
        
        final_score += modality_scores.get(DataModalityType.BEHAVIOR, 0) * weights.behavioral_weight
        final_score += modality_scores.get(DataModalityType.TEXT, 0) * weights.transactional_weight
        final_score += modality_scores.get(DataModalityType.INTERACTION, 0) * weights.engagement_weight
        final_score += modality_scores.get(DataModalityType.VOICE, 0) * weights.voice_sentiment_weight
        
        # 如果没有某些模态的数据，按比例调整权重
        available_weight = 0
        if DataModalityType.BEHAVIOR in modality_scores:
            available_weight += weights.behavioral_weight
        if DataModalityType.TEXT in modality_scores:
            available_weight += weights.transactional_weight + weights.demographic_weight
        if DataModalityType.INTERACTION in modality_scores:
            available_weight += weights.engagement_weight
        if DataModalityType.VOICE in modality_scores:
            available_weight += weights.voice_sentiment_weight
        
        if available_weight > 0:
            final_score = final_score / available_weight
        
        return min(1.0, max(0.0, final_score))
    
    async def _analyze_behavioral_patterns(
        self,
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """分析行为模式"""
        if not behavior_data:
            return {}
        
        # 访问时间模式
        access_hours = [data.timestamp.hour for data in behavior_data]
        peak_hour = max(set(access_hours), key=access_hours.count) if access_hours else 9
        
        # 访问频率模式
        dates = [data.timestamp.date() for data in behavior_data]
        unique_dates = len(set(dates))
        avg_daily_visits = len(behavior_data) / max(unique_dates, 1)
        
        # 页面偏好模式
        all_pages = []
        for data in behavior_data:
            all_pages.extend([pv.get('url', '') for pv in data.page_views])
        
        page_frequency = {}
        for page in all_pages:
            page_frequency[page] = page_frequency.get(page, 0) + 1
        
        top_pages = sorted(page_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'peak_access_hour': peak_hour,
            'average_daily_visits': avg_daily_visits,
            'total_unique_days': unique_dates,
            'top_visited_pages': top_pages,
            'session_consistency': self._calculate_session_consistency(behavior_data),
            'engagement_trend': self._calculate_engagement_trend(behavior_data)
        }
    
    def _calculate_session_consistency(self, behavior_data: List[BehaviorData]) -> float:
        """计算会话一致性"""
        if len(behavior_data) < 2:
            return 0.0
        
        engagement_scores = [data.engagement_score for data in behavior_data]
        std_dev = np.std(engagement_scores)
        mean_score = np.mean(engagement_scores)
        
        # 一致性 = 1 - (标准差 / 均值)，标准化到0-1
        consistency = max(0.0, 1.0 - (std_dev / max(mean_score, 0.1)))
        return consistency
    
    def _calculate_engagement_trend(self, behavior_data: List[BehaviorData]) -> str:
        """计算参与度趋势"""
        if len(behavior_data) < 3:
            return "insufficient_data"
        
        # 按时间排序
        sorted_data = sorted(behavior_data, key=lambda x: x.timestamp)
        
        # 计算前半部分和后半部分的平均参与度
        mid_point = len(sorted_data) // 2
        early_engagement = np.mean([data.engagement_score for data in sorted_data[:mid_point]])
        recent_engagement = np.mean([data.engagement_score for data in sorted_data[mid_point:]])
        
        diff = recent_engagement - early_engagement
        
        if diff > 0.1:
            return "increasing"
        elif diff < -0.1:
            return "decreasing"
        else:
            return "stable"
    
    async def _analyze_communication_preferences(
        self,
        voice_data: List[VoiceAnalysisResult],
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """分析沟通偏好"""
        preferences = {
            'preferred_channels': [],
            'communication_style': 'unknown',
            'response_time_preference': 'unknown',
            'content_preferences': []
        }
        
        # 基于语音数据分析沟通风格
        if voice_data:
            avg_speaking_rate = np.mean([voice.speaking_rate for voice in voice_data])
            avg_pause_frequency = np.mean([voice.pause_frequency for voice in voice_data])
            
            if avg_speaking_rate > 150 and avg_pause_frequency < 0.1:
                preferences['communication_style'] = 'direct_fast'
            elif avg_speaking_rate < 100 and avg_pause_frequency > 0.2:
                preferences['communication_style'] = 'thoughtful_slow'
            else:
                preferences['communication_style'] = 'balanced'
            
            preferences['preferred_channels'].append('voice_call')
        
        # 基于行为数据分析偏好
        if behavior_data:
            preferences['preferred_channels'].append('digital_interaction')
            
            # 分析内容偏好
            all_pages = []
            for data in behavior_data:
                all_pages.extend([pv.get('url', '') for pv in data.page_views])
            
            if any('demo' in page.lower() for page in all_pages):
                preferences['content_preferences'].append('product_demos')
            if any('case' in page.lower() for page in all_pages):
                preferences['content_preferences'].append('case_studies')
            if any('pricing' in page.lower() for page in all_pages):
                preferences['content_preferences'].append('pricing_information')
        
        return preferences
    
    async def _predict_customer_value(
        self,
        indicators: List[CustomerValueIndicator],
        behavioral_patterns: Dict[str, Any]
    ) -> float:
        """预测客户价值"""
        # 基于当前指标和行为模式预测未来价值
        current_score = self._calculate_weighted_score(indicators)
        
        # 趋势调整
        engagement_trend = behavioral_patterns.get('engagement_trend', 'stable')
        trend_multiplier = {
            'increasing': 1.2,
            'stable': 1.0,
            'decreasing': 0.8,
            'insufficient_data': 1.0
        }.get(engagement_trend, 1.0)
        
        # 一致性调整
        consistency = behavioral_patterns.get('session_consistency', 0.5)
        consistency_multiplier = 0.8 + (consistency * 0.4)  # 0.8-1.2范围
        
        predicted_value = current_score * trend_multiplier * consistency_multiplier
        return min(1.0, max(0.0, predicted_value))
    
    async def _identify_risk_factors(
        self,
        indicators: List[CustomerValueIndicator],
        behavioral_patterns: Dict[str, Any]
    ) -> List[str]:
        """识别风险因素"""
        risks = []
        
        # 参与度下降风险
        if behavioral_patterns.get('engagement_trend') == 'decreasing':
            risks.append("参与度呈下降趋势")
        
        # 低一致性风险
        consistency = behavioral_patterns.get('session_consistency', 0.5)
        if consistency < 0.3:
            risks.append("行为模式不一致，可能兴趣不稳定")
        
        # 低语音情感风险
        voice_indicators = [i for i in indicators if i.source_modality == DataModalityType.VOICE]
        if voice_indicators:
            sentiment_score = next((i.value for i in voice_indicators if i.indicator_name == 'sentiment_positivity'), 0.5)
            if sentiment_score < 0.4:
                risks.append("语音交流中负面情绪较多")
        
        # 访问频率过低风险
        avg_daily_visits = behavioral_patterns.get('average_daily_visits', 0)
        if avg_daily_visits < 0.5:
            risks.append("访问频率较低，可能兴趣不足")
        
        return risks
    
    async def _identify_opportunities(
        self,
        indicators: List[CustomerValueIndicator],
        behavioral_patterns: Dict[str, Any]
    ) -> List[str]:
        """识别机会点"""
        opportunities = []
        
        # 高参与度机会
        engagement_indicators = [
            i for i in indicators 
            if 'engagement' in i.indicator_name and i.value > 0.7
        ]
        if engagement_indicators:
            opportunities.append("客户参与度高，适合深度沟通")
        
        # 上升趋势机会
        if behavioral_patterns.get('engagement_trend') == 'increasing':
            opportunities.append("参与度上升趋势，时机良好")
        
        # 高价值行业机会
        industry_indicators = [
            i for i in indicators 
            if i.indicator_name == 'industry_value' and i.value > 0.7
        ]
        if industry_indicators:
            opportunities.append("所属高价值行业，潜在价值大")
        
        # 大公司机会
        size_indicators = [
            i for i in indicators 
            if i.indicator_name == 'company_size' and i.value > 0.7
        ]
        if size_indicators:
            opportunities.append("公司规模较大，决策能力强")
        
        # 积极语音情感机会
        voice_indicators = [i for i in indicators if i.source_modality == DataModalityType.VOICE]
        if voice_indicators:
            sentiment_score = next((i.value for i in voice_indicators if i.indicator_name == 'sentiment_positivity'), 0.5)
            if sentiment_score > 0.7:
                opportunities.append("语音交流积极正面，关系良好")
        
        return opportunities
    
    async def _generate_recommended_actions(
        self,
        overall_score: float,
        indicators: List[CustomerValueIndicator],
        risk_factors: List[str],
        opportunities: List[str]
    ) -> List[str]:
        """生成推荐行动"""
        actions = []
        
        # 基于综合评分的基础行动
        if overall_score >= self.value_thresholds['very_high']:
            actions.extend([
                "立即分配顶级销售代表",
                "安排高管层面会议",
                "提供定制化解决方案",
                "优先处理所有需求"
            ])
        elif overall_score >= self.value_thresholds['high']:
            actions.extend([
                "分配经验丰富的销售代表",
                "安排产品演示",
                "提供详细ROI分析",
                "建立定期沟通机制"
            ])
        elif overall_score >= self.value_thresholds['medium']:
            actions.extend([
                "安排专业销售跟进",
                "发送相关案例研究",
                "邀请参加网络研讨会"
            ])
        else:
            actions.extend([
                "通过邮件营销培养",
                "提供基础产品信息",
                "监控行为变化"
            ])
        
        # 基于风险因素的行动
        if "参与度呈下降趋势" in risk_factors:
            actions.append("主动联系了解原因，重新激发兴趣")
        
        if "语音交流中负面情绪较多" in risk_factors:
            actions.append("安排客户成功经理进行关怀")
        
        # 基于机会点的行动
        if "参与度上升趋势，时机良好" in opportunities:
            actions.append("抓住时机，加快推进节奏")
        
        if "语音交流积极正面，关系良好" in opportunities:
            actions.append("利用良好关系，推荐更多产品")
        
        return list(set(actions))  # 去重
    
    def _extract_engagement_history(
        self,
        behavior_data: List[BehaviorData]
    ) -> List[Dict[str, Any]]:
        """提取参与历史"""
        history = []
        
        for data in behavior_data:
            history.append({
                'timestamp': data.timestamp,
                'session_id': data.session_id,
                'engagement_score': data.engagement_score,
                'page_views_count': len(data.page_views),
                'clicks_count': len(data.click_events),
                'time_spent_total': sum(data.time_spent.values()),
                'conversion_indicators': data.conversion_indicators
            })
        
        # 按时间排序
        history.sort(key=lambda x: x['timestamp'])
        
        return history
    
    async def get_value_distribution(
        self,
        customer_profiles: List[HighValueCustomerProfile]
    ) -> Dict[str, Any]:
        """获取价值分布统计"""
        if not customer_profiles:
            return {}
        
        scores = [profile.overall_score for profile in customer_profiles]
        
        # 按价值等级分类
        value_distribution = {
            'very_high': sum(1 for score in scores if score >= self.value_thresholds['very_high']),
            'high': sum(1 for score in scores if self.value_thresholds['high'] <= score < self.value_thresholds['very_high']),
            'medium': sum(1 for score in scores if self.value_thresholds['medium'] <= score < self.value_thresholds['high']),
            'low': sum(1 for score in scores if score < self.value_thresholds['medium'])
        }
        
        return {
            'total_customers': len(customer_profiles),
            'value_distribution': value_distribution,
            'average_score': np.mean(scores),
            'median_score': np.median(scores),
            'score_std': np.std(scores),
            'top_10_percent_threshold': np.percentile(scores, 90)
        }