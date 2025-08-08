# 客户行为数据分析服务

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
import json
from collections import defaultdict

from ..models.multimodal import (
    BehaviorData, CustomerValueIndicator, DataModalityType,
    MultimodalDataPoint
)
from ..core.config import settings

logger = logging.getLogger(__name__)

class BehaviorAnalysisService:
    """客户行为分析服务"""
    
    def __init__(self):
        self.settings = settings
        self.behavior_patterns = {}
        self.value_thresholds = {
            'high_engagement': 0.8,
            'medium_engagement': 0.5,
            'low_engagement': 0.2
        }
    
    async def analyze_customer_behavior(
        self, 
        customer_id: str,
        behavior_data: List[BehaviorData],
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        分析客户行为数据
        
        Args:
            customer_id: 客户ID
            behavior_data: 行为数据列表
            time_window: 分析时间窗口
            
        Returns:
            Dict: 行为分析结果
        """
        try:
            if not behavior_data:
                return self._create_empty_analysis(customer_id)
            
            # 过滤时间窗口内的数据
            if time_window:
                cutoff_time = datetime.now() - time_window
                behavior_data = [
                    data for data in behavior_data 
                    if data.timestamp >= cutoff_time
                ]
            
            # 计算基础指标
            engagement_metrics = await self._calculate_engagement_metrics(behavior_data)
            
            # 分析访问模式
            access_patterns = await self._analyze_access_patterns(behavior_data)
            
            # 计算转化指标
            conversion_metrics = await self._calculate_conversion_metrics(behavior_data)
            
            # 识别行为异常
            anomalies = await self._detect_behavior_anomalies(behavior_data)
            
            # 生成行为画像
            behavior_profile = await self._generate_behavior_profile(
                engagement_metrics, access_patterns, conversion_metrics
            )
            
            return {
                'customer_id': customer_id,
                'analysis_timestamp': datetime.now(),
                'data_points_count': len(behavior_data),
                'engagement_metrics': engagement_metrics,
                'access_patterns': access_patterns,
                'conversion_metrics': conversion_metrics,
                'behavior_profile': behavior_profile,
                'anomalies': anomalies,
                'recommendations': await self._generate_recommendations(behavior_profile)
            }
            
        except Exception as e:
            logger.error(f"客户行为分析失败: {str(e)}")
            raise
    
    async def _calculate_engagement_metrics(
        self, 
        behavior_data: List[BehaviorData]
    ) -> Dict[str, float]:
        """计算参与度指标"""
        if not behavior_data:
            return {}
        
        # 计算平均参与度
        avg_engagement = np.mean([data.engagement_score for data in behavior_data])
        
        # 计算总页面浏览量
        total_page_views = sum(len(data.page_views) for data in behavior_data)
        
        # 计算总点击次数
        total_clicks = sum(len(data.click_events) for data in behavior_data)
        
        # 计算平均会话时长
        total_time = sum(
            sum(data.time_spent.values()) for data in behavior_data
        )
        avg_session_duration = total_time / len(behavior_data) if behavior_data else 0
        
        # 计算跳出率(单页面会话比例)
        single_page_sessions = sum(
            1 for data in behavior_data if len(data.page_views) == 1
        )
        bounce_rate = single_page_sessions / len(behavior_data) if behavior_data else 0
        
        return {
            'average_engagement_score': avg_engagement,
            'total_page_views': total_page_views,
            'total_clicks': total_clicks,
            'average_session_duration': avg_session_duration,
            'bounce_rate': bounce_rate,
            'sessions_count': len(behavior_data)
        }
    
    async def _analyze_access_patterns(
        self, 
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """分析访问模式"""
        # 统计访问时间分布
        hour_distribution = defaultdict(int)
        day_distribution = defaultdict(int)
        
        # 统计页面访问频率
        page_frequency = defaultdict(int)
        
        # 统计访问路径
        access_paths = []
        
        for data in behavior_data:
            # 时间分布
            timestamp = data.timestamp
            hour_distribution[timestamp.hour] += 1
            day_distribution[timestamp.weekday()] += 1
            
            # 页面频率
            for page_view in data.page_views:
                page_url = page_view.get('url', 'unknown')
                page_frequency[page_url] += 1
            
            # 访问路径
            if data.page_views:
                path = [pv.get('url', 'unknown') for pv in data.page_views]
                access_paths.append(path)
        
        # 找出最常访问的时间段
        peak_hour = max(hour_distribution.items(), key=lambda x: x[1])[0] if hour_distribution else 0
        peak_day = max(day_distribution.items(), key=lambda x: x[1])[0] if day_distribution else 0
        
        # 找出最热门页面
        top_pages = sorted(page_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'peak_access_hour': peak_hour,
            'peak_access_day': peak_day,
            'hour_distribution': dict(hour_distribution),
            'day_distribution': dict(day_distribution),
            'top_pages': top_pages,
            'unique_pages_visited': len(page_frequency),
            'common_access_paths': self._find_common_paths(access_paths)
        }
    
    def _find_common_paths(self, paths: List[List[str]]) -> List[Dict[str, Any]]:
        """找出常见的访问路径"""
        path_frequency = defaultdict(int)
        
        for path in paths:
            if len(path) >= 2:
                # 统计2-3页面的访问序列
                for i in range(len(path) - 1):
                    sequence = tuple(path[i:i+2])
                    path_frequency[sequence] += 1
        
        # 返回最常见的路径
        common_paths = sorted(path_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {
                'path': list(path),
                'frequency': freq,
                'percentage': freq / len(paths) if paths else 0
            }
            for path, freq in common_paths
        ]
    
    async def _calculate_conversion_metrics(
        self, 
        behavior_data: List[BehaviorData]
    ) -> Dict[str, Any]:
        """计算转化指标"""
        conversion_events = []
        funnel_stages = defaultdict(int)
        
        for data in behavior_data:
            # 收集转化指标
            conversion_events.extend(data.conversion_indicators)
            
            # 分析漏斗阶段
            for indicator in data.conversion_indicators:
                if 'contact_form' in indicator:
                    funnel_stages['contact_form'] += 1
                elif 'demo_request' in indicator:
                    funnel_stages['demo_request'] += 1
                elif 'pricing_page' in indicator:
                    funnel_stages['pricing_interest'] += 1
                elif 'download' in indicator:
                    funnel_stages['resource_download'] += 1
        
        # 计算转化率
        total_sessions = len(behavior_data)
        conversion_rate = len(set(conversion_events)) / total_sessions if total_sessions > 0 else 0
        
        return {
            'conversion_rate': conversion_rate,
            'total_conversion_events': len(conversion_events),
            'unique_conversion_events': len(set(conversion_events)),
            'funnel_stages': dict(funnel_stages),
            'conversion_velocity': self._calculate_conversion_velocity(behavior_data)
        }
    
    def _calculate_conversion_velocity(self, behavior_data: List[BehaviorData]) -> float:
        """计算转化速度"""
        if len(behavior_data) < 2:
            return 0.0
        
        # 计算从首次访问到转化的平均时间
        first_visit = min(data.timestamp for data in behavior_data)
        conversion_times = []
        
        for data in behavior_data:
            if data.conversion_indicators:
                time_to_conversion = (data.timestamp - first_visit).total_seconds() / 3600  # 小时
                conversion_times.append(time_to_conversion)
        
        return np.mean(conversion_times) if conversion_times else 0.0
    
    async def _detect_behavior_anomalies(
        self, 
        behavior_data: List[BehaviorData]
    ) -> List[Dict[str, Any]]:
        """检测行为异常"""
        anomalies = []
        
        if not behavior_data:
            return anomalies
        
        # 计算基准指标
        engagement_scores = [data.engagement_score for data in behavior_data]
        avg_engagement = np.mean(engagement_scores)
        std_engagement = np.std(engagement_scores)
        
        session_durations = [
            sum(data.time_spent.values()) for data in behavior_data
        ]
        avg_duration = np.mean(session_durations)
        std_duration = np.std(session_durations)
        
        # 检测异常
        for i, data in enumerate(behavior_data):
            session_duration = sum(data.time_spent.values())
            
            # 参与度异常
            if abs(data.engagement_score - avg_engagement) > 2 * std_engagement:
                anomalies.append({
                    'type': 'engagement_anomaly',
                    'session_id': data.session_id,
                    'value': data.engagement_score,
                    'expected_range': [avg_engagement - std_engagement, avg_engagement + std_engagement],
                    'severity': 'high' if abs(data.engagement_score - avg_engagement) > 3 * std_engagement else 'medium'
                })
            
            # 会话时长异常
            if abs(session_duration - avg_duration) > 2 * std_duration:
                anomalies.append({
                    'type': 'duration_anomaly',
                    'session_id': data.session_id,
                    'value': session_duration,
                    'expected_range': [avg_duration - std_duration, avg_duration + std_duration],
                    'severity': 'high' if abs(session_duration - avg_duration) > 3 * std_duration else 'medium'
                })
            
            # 异常访问模式
            if len(data.page_views) > 50:  # 单次会话页面浏览过多
                anomalies.append({
                    'type': 'excessive_browsing',
                    'session_id': data.session_id,
                    'value': len(data.page_views),
                    'severity': 'medium'
                })
        
        return anomalies
    
    async def _generate_behavior_profile(
        self,
        engagement_metrics: Dict[str, float],
        access_patterns: Dict[str, Any],
        conversion_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成行为画像"""
        # 计算综合评分
        engagement_score = engagement_metrics.get('average_engagement_score', 0)
        conversion_rate = conversion_metrics.get('conversion_rate', 0)
        session_quality = 1 - engagement_metrics.get('bounce_rate', 1)
        
        overall_score = (engagement_score * 0.4 + conversion_rate * 0.4 + session_quality * 0.2)
        
        # 确定客户类型
        if overall_score >= self.value_thresholds['high_engagement']:
            customer_type = 'high_value'
            engagement_level = 'high'
        elif overall_score >= self.value_thresholds['medium_engagement']:
            customer_type = 'medium_value'
            engagement_level = 'medium'
        else:
            customer_type = 'low_value'
            engagement_level = 'low'
        
        # 分析兴趣点
        interests = self._identify_interests(access_patterns)
        
        # 预测购买意向
        purchase_intent = self._predict_purchase_intent(
            engagement_metrics, conversion_metrics
        )
        
        return {
            'overall_score': overall_score,
            'customer_type': customer_type,
            'engagement_level': engagement_level,
            'interests': interests,
            'purchase_intent': purchase_intent,
            'preferred_access_time': {
                'hour': access_patterns.get('peak_access_hour', 9),
                'day': access_patterns.get('peak_access_day', 1)
            },
            'behavior_consistency': self._calculate_consistency_score(access_patterns),
            'digital_maturity': self._assess_digital_maturity(engagement_metrics)
        }
    
    def _identify_interests(self, access_patterns: Dict[str, Any]) -> List[str]:
        """识别客户兴趣点"""
        interests = []
        top_pages = access_patterns.get('top_pages', [])
        
        for page, frequency in top_pages:
            if 'product' in page.lower():
                interests.append('product_information')
            elif 'pricing' in page.lower():
                interests.append('pricing')
            elif 'demo' in page.lower():
                interests.append('product_demo')
            elif 'case' in page.lower() or 'success' in page.lower():
                interests.append('success_stories')
            elif 'support' in page.lower():
                interests.append('technical_support')
        
        return list(set(interests))
    
    def _predict_purchase_intent(
        self,
        engagement_metrics: Dict[str, float],
        conversion_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """预测购买意向"""
        # 基于多个因素计算购买意向
        factors = {
            'engagement_score': engagement_metrics.get('average_engagement_score', 0) * 0.3,
            'conversion_rate': conversion_metrics.get('conversion_rate', 0) * 0.4,
            'session_depth': min(1.0, engagement_metrics.get('total_page_views', 0) / 10) * 0.2,
            'conversion_velocity': min(1.0, 1 / max(1, conversion_metrics.get('conversion_velocity', 24))) * 0.1
        }
        
        intent_score = sum(factors.values())
        
        if intent_score >= 0.8:
            intent_level = 'very_high'
        elif intent_score >= 0.6:
            intent_level = 'high'
        elif intent_score >= 0.4:
            intent_level = 'medium'
        elif intent_score >= 0.2:
            intent_level = 'low'
        else:
            intent_level = 'very_low'
        
        return {
            'score': intent_score,
            'level': intent_level,
            'factors': factors,
            'confidence': min(1.0, intent_score + 0.1)
        }
    
    def _calculate_consistency_score(self, access_patterns: Dict[str, Any]) -> float:
        """计算行为一致性评分"""
        # 基于访问时间分布的一致性
        hour_dist = access_patterns.get('hour_distribution', {})
        day_dist = access_patterns.get('day_distribution', {})
        
        if not hour_dist or not day_dist:
            return 0.0
        
        # 计算时间分布的集中度
        hour_entropy = self._calculate_entropy(list(hour_dist.values()))
        day_entropy = self._calculate_entropy(list(day_dist.values()))
        
        # 一致性评分(熵越低，一致性越高)
        max_hour_entropy = np.log2(24)  # 24小时的最大熵
        max_day_entropy = np.log2(7)    # 7天的最大熵
        
        hour_consistency = 1 - (hour_entropy / max_hour_entropy)
        day_consistency = 1 - (day_entropy / max_day_entropy)
        
        return (hour_consistency + day_consistency) / 2
    
    def _calculate_entropy(self, values: List[int]) -> float:
        """计算熵值"""
        if not values or sum(values) == 0:
            return 0.0
        
        total = sum(values)
        probabilities = [v / total for v in values if v > 0]
        
        return -sum(p * np.log2(p) for p in probabilities)
    
    def _assess_digital_maturity(self, engagement_metrics: Dict[str, float]) -> str:
        """评估数字化成熟度"""
        avg_session_duration = engagement_metrics.get('average_session_duration', 0)
        bounce_rate = engagement_metrics.get('bounce_rate', 1)
        total_clicks = engagement_metrics.get('total_clicks', 0)
        
        # 综合评估数字化使用能力
        if avg_session_duration > 300 and bounce_rate < 0.3 and total_clicks > 20:
            return 'advanced'
        elif avg_session_duration > 120 and bounce_rate < 0.6 and total_clicks > 10:
            return 'intermediate'
        else:
            return 'beginner'
    
    async def _generate_recommendations(
        self, 
        behavior_profile: Dict[str, Any]
    ) -> List[str]:
        """生成行为分析建议"""
        recommendations = []
        
        customer_type = behavior_profile.get('customer_type', 'low_value')
        engagement_level = behavior_profile.get('engagement_level', 'low')
        purchase_intent = behavior_profile.get('purchase_intent', {})
        
        # 基于客户类型的建议
        if customer_type == 'high_value':
            recommendations.extend([
                "优先分配高级销售代表跟进",
                "提供个性化产品演示",
                "安排高管会面机会"
            ])
        elif customer_type == 'medium_value':
            recommendations.extend([
                "发送详细产品资料",
                "邀请参加产品网络研讨会",
                "提供案例研究和成功故事"
            ])
        else:
            recommendations.extend([
                "发送基础产品介绍",
                "提供免费试用机会",
                "通过邮件营销培养兴趣"
            ])
        
        # 基于购买意向的建议
        intent_level = purchase_intent.get('level', 'low')
        if intent_level in ['very_high', 'high']:
            recommendations.append("立即安排销售电话")
            recommendations.append("准备详细报价方案")
        elif intent_level == 'medium':
            recommendations.append("发送产品对比资料")
            recommendations.append("邀请参加产品演示")
        
        # 基于兴趣点的建议
        interests = behavior_profile.get('interests', [])
        if 'pricing' in interests:
            recommendations.append("提供详细价格信息和ROI分析")
        if 'product_demo' in interests:
            recommendations.append("安排个性化产品演示")
        if 'technical_support' in interests:
            recommendations.append("安排技术专家咨询")
        
        return list(set(recommendations))  # 去重
    
    def _create_empty_analysis(self, customer_id: str) -> Dict[str, Any]:
        """创建空的分析结果"""
        return {
            'customer_id': customer_id,
            'analysis_timestamp': datetime.now(),
            'data_points_count': 0,
            'engagement_metrics': {},
            'access_patterns': {},
            'conversion_metrics': {},
            'behavior_profile': {
                'overall_score': 0.0,
                'customer_type': 'unknown',
                'engagement_level': 'none'
            },
            'anomalies': [],
            'recommendations': ["收集更多客户行为数据"]
        }