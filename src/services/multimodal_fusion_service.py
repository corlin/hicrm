# 多模态数据融合和分析管道服务

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
from datetime import datetime, timedelta
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from ..models.multimodal import (
    MultimodalDataPoint, DataFusionResult, MultimodalAnalysisRequest,
    MultimodalAnalysisResult, DataModalityType, BehaviorData, VoiceAnalysisResult,
    HighValueCustomerProfile
)
from .speech_recognition_service import SpeechRecognitionService
from .behavior_analysis_service import BehaviorAnalysisService
from .high_value_customer_service import HighValueCustomerService
from ..core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class FusionConfig:
    """融合配置"""
    text_weight: float = 0.3
    voice_weight: float = 0.25
    behavior_weight: float = 0.35
    interaction_weight: float = 0.1
    confidence_threshold: float = 0.6
    max_processing_time: int = 300  # 秒

class MultimodalFusionService:
    """多模态数据融合服务"""
    
    def __init__(self):
        self.settings = settings
        self.fusion_config = FusionConfig()
        self.speech_service = SpeechRecognitionService()
        self.behavior_service = BehaviorAnalysisService()
        self.high_value_service = HighValueCustomerService()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.processing_cache = {}
        
    async def process_multimodal_analysis(
        self,
        request: MultimodalAnalysisRequest
    ) -> MultimodalAnalysisResult:
        """
        处理多模态分析请求
        
        Args:
            request: 多模态分析请求
            
        Returns:
            MultimodalAnalysisResult: 分析结果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"开始处理客户 {request.customer_id} 的多模态分析")
            
            # 收集多模态数据
            multimodal_data = await self._collect_multimodal_data(
                request.customer_id,
                request.modalities,
                request.time_range
            )
            
            # 数据预处理
            processed_data = await self._preprocess_data(multimodal_data)
            
            # 特征提取
            features = await self._extract_features(processed_data)
            
            # 数据融合
            fusion_result = await self._fuse_multimodal_data(
                request.customer_id,
                features,
                processed_data
            )
            
            # 执行分析
            analysis_results = await self._perform_analysis(
                request.analysis_type,
                fusion_result,
                request.parameters
            )
            
            # 生成高价值客户画像(如果需要)
            high_value_profile = None
            if request.analysis_type == 'high_value_identification':
                high_value_profile = await self._generate_high_value_profile(
                    request.customer_id,
                    processed_data,
                    fusion_result
                )
            
            # 生成推荐建议
            recommendations = await self._generate_recommendations(
                analysis_results,
                fusion_result,
                high_value_profile
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 如果分析结果包含错误，设置置信度为0
            confidence = 0.0 if 'error' in analysis_results else fusion_result.fusion_quality
            
            return MultimodalAnalysisResult(
                request_id=f"req_{request.customer_id}_{int(start_time.timestamp())}",
                customer_id=request.customer_id,
                analysis_type=request.analysis_type,
                results=analysis_results,
                high_value_profile=high_value_profile,
                recommendations=recommendations,
                confidence=confidence,
                processing_time=processing_time,
                created_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"多模态分析处理失败: {str(e)}")
            raise
    
    async def _collect_multimodal_data(
        self,
        customer_id: str,
        modalities: List[DataModalityType],
        time_range: Dict[str, datetime]
    ) -> Dict[DataModalityType, List[Any]]:
        """收集多模态数据"""
        data_collection = {}
        
        # 并行收集各种模态的数据
        collection_tasks = []
        
        if DataModalityType.TEXT in modalities:
            collection_tasks.append(
                self._collect_text_data(customer_id, time_range)
            )
        
        if DataModalityType.VOICE in modalities:
            collection_tasks.append(
                self._collect_voice_data(customer_id, time_range)
            )
        
        if DataModalityType.BEHAVIOR in modalities:
            collection_tasks.append(
                self._collect_behavior_data(customer_id, time_range)
            )
        
        if DataModalityType.INTERACTION in modalities:
            collection_tasks.append(
                self._collect_interaction_data(customer_id, time_range)
            )
        
        # 等待所有数据收集完成
        results = await asyncio.gather(*collection_tasks, return_exceptions=True)
        
        # 整理结果
        modality_list = [m for m in modalities]
        for i, result in enumerate(results):
            if not isinstance(result, Exception) and i < len(modality_list):
                data_collection[modality_list[i]] = result
            elif isinstance(result, Exception):
                logger.warning(f"收集 {modality_list[i] if i < len(modality_list) else 'unknown'} 数据失败: {str(result)}")
                if i < len(modality_list):
                    data_collection[modality_list[i]] = []
        
        return data_collection
    
    async def _collect_text_data(
        self,
        customer_id: str,
        time_range: Dict[str, datetime]
    ) -> List[Dict[str, Any]]:
        """收集文本数据"""
        # 模拟收集客户的文本交互数据
        # 在实际实现中，这里会从数据库或其他数据源获取
        text_data = [
            {
                'id': f'text_{customer_id}_1',
                'content': '我们公司正在寻找一个CRM系统，希望能够提高销售效率',
                'timestamp': datetime.now() - timedelta(days=2),
                'source': 'email',
                'sentiment': 'positive'
            },
            {
                'id': f'text_{customer_id}_2',
                'content': '请问你们的产品支持多少用户同时使用？',
                'timestamp': datetime.now() - timedelta(days=1),
                'source': 'chat',
                'sentiment': 'neutral'
            }
        ]
        
        # 过滤时间范围
        start_time = time_range.get('start', datetime.now() - timedelta(days=30))
        end_time = time_range.get('end', datetime.now())
        
        filtered_data = [
            data for data in text_data
            if start_time <= data['timestamp'] <= end_time
        ]
        
        return filtered_data
    
    async def _collect_voice_data(
        self,
        customer_id: str,
        time_range: Dict[str, datetime]
    ) -> List[VoiceAnalysisResult]:
        """收集语音数据"""
        # 模拟语音数据收集
        # 在实际实现中，这里会从语音存储系统获取音频文件并进行分析
        
        # 创建模拟的语音分析结果
        voice_data = [
            VoiceAnalysisResult(
                transcript="你好，我想了解一下你们的CRM产品",
                confidence=0.92,
                sentiment="positive",
                emotion="interested",
                speaking_rate=120.5,
                pause_frequency=0.15,
                voice_quality={
                    "clarity": 0.88,
                    "volume": 0.75,
                    "pitch_stability": 0.82
                },
                keywords=["CRM", "产品", "了解"],
                intent="product_inquiry"
            ),
            VoiceAnalysisResult(
                transcript="我们公司有200多名员工，需要一个能够管理客户关系的系统",
                confidence=0.89,
                sentiment="neutral",
                emotion="business_focused",
                speaking_rate=110.2,
                pause_frequency=0.18,
                voice_quality={
                    "clarity": 0.85,
                    "volume": 0.78,
                    "pitch_stability": 0.80
                },
                keywords=["公司", "员工", "管理", "客户关系", "系统"],
                intent="requirement_specification"
            )
        ]
        
        return voice_data
    
    async def _collect_behavior_data(
        self,
        customer_id: str,
        time_range: Dict[str, datetime]
    ) -> List[BehaviorData]:
        """收集行为数据"""
        # 模拟行为数据收集
        behavior_data = [
            BehaviorData(
                customer_id=customer_id,
                session_id=f"session_{customer_id}_1",
                page_views=[
                    {"url": "/products", "timestamp": datetime.now() - timedelta(hours=2), "duration": 120},
                    {"url": "/pricing", "timestamp": datetime.now() - timedelta(hours=2, minutes=-5), "duration": 180},
                    {"url": "/demo", "timestamp": datetime.now() - timedelta(hours=2, minutes=-10), "duration": 300}
                ],
                click_events=[
                    {"element": "demo_button", "timestamp": datetime.now() - timedelta(hours=2, minutes=-10)},
                    {"element": "pricing_link", "timestamp": datetime.now() - timedelta(hours=2, minutes=-5)},
                    {"element": "contact_form", "timestamp": datetime.now() - timedelta(hours=2, minutes=-2)}
                ],
                time_spent={
                    "/products": 120.0,
                    "/pricing": 180.0,
                    "/demo": 300.0
                },
                interaction_patterns={
                    "scroll_depth": 0.85,
                    "click_through_rate": 0.75,
                    "form_completion": True
                },
                engagement_score=0.82,
                conversion_indicators=["demo_request", "contact_form_filled"],
                timestamp=datetime.now() - timedelta(hours=2)
            ),
            BehaviorData(
                customer_id=customer_id,
                session_id=f"session_{customer_id}_2",
                page_views=[
                    {"url": "/case-studies", "timestamp": datetime.now() - timedelta(hours=24), "duration": 240},
                    {"url": "/features", "timestamp": datetime.now() - timedelta(hours=24, minutes=-8), "duration": 200}
                ],
                click_events=[
                    {"element": "case_study_download", "timestamp": datetime.now() - timedelta(hours=24, minutes=-5)},
                    {"element": "feature_comparison", "timestamp": datetime.now() - timedelta(hours=24, minutes=-3)}
                ],
                time_spent={
                    "/case-studies": 240.0,
                    "/features": 200.0
                },
                interaction_patterns={
                    "scroll_depth": 0.92,
                    "click_through_rate": 0.68,
                    "form_completion": False
                },
                engagement_score=0.75,
                conversion_indicators=["resource_download"],
                timestamp=datetime.now() - timedelta(hours=24)
            )
        ]
        
        # 过滤时间范围
        start_time = time_range.get('start', datetime.now() - timedelta(days=30))
        end_time = time_range.get('end', datetime.now())
        
        filtered_data = [
            data for data in behavior_data
            if start_time <= data.timestamp <= end_time
        ]
        
        return filtered_data
    
    async def _collect_interaction_data(
        self,
        customer_id: str,
        time_range: Dict[str, datetime]
    ) -> List[Dict[str, Any]]:
        """收集交互数据"""
        # 模拟交互数据收集
        interaction_data = [
            {
                'id': f'interaction_{customer_id}_1',
                'type': 'email',
                'direction': 'inbound',
                'content': '询问产品功能详情',
                'timestamp': datetime.now() - timedelta(days=1),
                'response_time': 3600,  # 1小时响应
                'satisfaction_score': 0.8
            },
            {
                'id': f'interaction_{customer_id}_2',
                'type': 'phone_call',
                'direction': 'outbound',
                'content': '产品演示预约',
                'timestamp': datetime.now() - timedelta(hours=6),
                'response_time': 0,
                'satisfaction_score': 0.9
            }
        ]
        
        # 过滤时间范围
        start_time = time_range.get('start', datetime.now() - timedelta(days=30))
        end_time = time_range.get('end', datetime.now())
        
        filtered_data = [
            data for data in interaction_data
            if start_time <= data['timestamp'] <= end_time
        ]
        
        return filtered_data
    
    async def _preprocess_data(
        self,
        multimodal_data: Dict[DataModalityType, List[Any]]
    ) -> Dict[DataModalityType, List[MultimodalDataPoint]]:
        """数据预处理"""
        processed_data = {}
        
        for modality, data_list in multimodal_data.items():
            processed_points = []
            
            for i, data in enumerate(data_list):
                try:
                    # 根据模态类型进行不同的预处理
                    if modality == DataModalityType.TEXT:
                        processed_point = await self._preprocess_text_data(data, i)
                    elif modality == DataModalityType.VOICE:
                        processed_point = await self._preprocess_voice_data(data, i)
                    elif modality == DataModalityType.BEHAVIOR:
                        processed_point = await self._preprocess_behavior_data(data, i)
                    elif modality == DataModalityType.INTERACTION:
                        processed_point = await self._preprocess_interaction_data(data, i)
                    else:
                        continue
                    
                    processed_points.append(processed_point)
                    
                except Exception as e:
                    logger.warning(f"预处理 {modality} 数据失败: {str(e)}")
                    continue
            
            processed_data[modality] = processed_points
        
        return processed_data
    
    async def _preprocess_text_data(
        self,
        data: Dict[str, Any],
        index: int
    ) -> MultimodalDataPoint:
        """预处理文本数据"""
        # 提取文本特征
        content = data.get('content', '')
        features = await self._extract_text_features(content)
        
        return MultimodalDataPoint(
            id=f"text_{index}_{data.get('id', '')}",
            customer_id=data.get('customer_id', ''),
            modality=DataModalityType.TEXT,
            raw_data=data,
            processed_data={
                'content_length': len(content),
                'word_count': len(content.split()),
                'sentiment': data.get('sentiment', 'neutral'),
                'source': data.get('source', 'unknown')
            },
            features=features,
            metadata={
                'timestamp': data.get('timestamp', datetime.now()),
                'source': data.get('source', 'unknown')
            },
            quality_score=self._calculate_text_quality(content),
            timestamp=data.get('timestamp', datetime.now())
        )
    
    async def _preprocess_voice_data(
        self,
        data: VoiceAnalysisResult,
        index: int
    ) -> MultimodalDataPoint:
        """预处理语音数据"""
        # 提取语音特征
        features = await self._extract_voice_features(data)
        
        return MultimodalDataPoint(
            id=f"voice_{index}",
            customer_id="",  # 需要从上下文获取
            modality=DataModalityType.VOICE,
            raw_data=data.dict(),
            processed_data={
                'transcript_length': len(data.transcript),
                'confidence': data.confidence,
                'sentiment': data.sentiment,
                'emotion': data.emotion,
                'speaking_rate': data.speaking_rate,
                'keywords_count': len(data.keywords)
            },
            features=features,
            metadata={
                'has_intent': data.intent is not None,
                'voice_quality_avg': np.mean(list(data.voice_quality.values())) if data.voice_quality else 0
            },
            quality_score=data.confidence,
            timestamp=datetime.now()  # 实际应该从语音文件获取
        )
    
    async def _preprocess_behavior_data(
        self,
        data: BehaviorData,
        index: int
    ) -> MultimodalDataPoint:
        """预处理行为数据"""
        # 提取行为特征
        features = await self._extract_behavior_features(data)
        
        return MultimodalDataPoint(
            id=f"behavior_{index}_{data.session_id}",
            customer_id=data.customer_id,
            modality=DataModalityType.BEHAVIOR,
            raw_data=data.dict(),
            processed_data={
                'page_views_count': len(data.page_views),
                'clicks_count': len(data.click_events),
                'total_time_spent': sum(data.time_spent.values()),
                'engagement_score': data.engagement_score,
                'conversion_count': len(data.conversion_indicators)
            },
            features=features,
            metadata={
                'session_id': data.session_id,
                'has_conversions': len(data.conversion_indicators) > 0
            },
            quality_score=data.engagement_score,
            timestamp=data.timestamp
        )
    
    async def _preprocess_interaction_data(
        self,
        data: Dict[str, Any],
        index: int
    ) -> MultimodalDataPoint:
        """预处理交互数据"""
        # 提取交互特征
        features = await self._extract_interaction_features(data)
        
        return MultimodalDataPoint(
            id=f"interaction_{index}_{data.get('id', '')}",
            customer_id=data.get('customer_id', ''),
            modality=DataModalityType.INTERACTION,
            raw_data=data,
            processed_data={
                'interaction_type': data.get('type', 'unknown'),
                'direction': data.get('direction', 'unknown'),
                'response_time': data.get('response_time', 0),
                'satisfaction_score': data.get('satisfaction_score', 0.5)
            },
            features=features,
            metadata={
                'timestamp': data.get('timestamp', datetime.now()),
                'type': data.get('type', 'unknown')
            },
            quality_score=data.get('satisfaction_score', 0.5),
            timestamp=data.get('timestamp', datetime.now())
        )
    
    async def _extract_features(
        self,
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]]
    ) -> Dict[DataModalityType, np.ndarray]:
        """提取特征向量"""
        features = {}
        
        for modality, data_points in processed_data.items():
            if not data_points:
                features[modality] = np.array([])
                continue
            
            # 合并所有数据点的特征
            all_features = []
            for point in data_points:
                if point.features:
                    all_features.append(point.features)
            
            if all_features:
                # 计算平均特征向量
                features[modality] = np.mean(all_features, axis=0)
            else:
                features[modality] = np.array([])
        
        return features
    
    async def _extract_text_features(self, content: str) -> List[float]:
        """提取文本特征"""
        # 简单的文本特征提取
        features = [
            len(content),  # 文本长度
            len(content.split()),  # 词数
            content.count('?'),  # 问号数量
            content.count('!'),  # 感叹号数量
            len([w for w in content.split() if len(w) > 6]),  # 长词数量
        ]
        
        # 标准化特征
        max_values = [1000, 200, 10, 10, 50]  # 预设的最大值用于标准化
        normalized_features = [
            min(1.0, f / max_val) for f, max_val in zip(features, max_values)
        ]
        
        return normalized_features
    
    async def _extract_voice_features(self, data: VoiceAnalysisResult) -> List[float]:
        """提取语音特征"""
        features = [
            data.confidence,
            data.speaking_rate / 200.0,  # 标准化语速
            data.pause_frequency,
            1.0 if data.sentiment == 'positive' else 0.5 if data.sentiment == 'neutral' else 0.0,
            len(data.keywords) / 10.0,  # 标准化关键词数量
            np.mean(list(data.voice_quality.values())) if data.voice_quality else 0.5,
            1.0 if data.intent else 0.0
        ]
        
        return features
    
    async def _extract_behavior_features(self, data: BehaviorData) -> List[float]:
        """提取行为特征"""
        features = [
            data.engagement_score,
            len(data.page_views) / 20.0,  # 标准化页面浏览数
            len(data.click_events) / 50.0,  # 标准化点击数
            sum(data.time_spent.values()) / 3600.0,  # 标准化总时间(小时)
            len(data.conversion_indicators) / 5.0,  # 标准化转化指标数
            data.interaction_patterns.get('scroll_depth', 0.5),
            data.interaction_patterns.get('click_through_rate', 0.5)
        ]
        
        return features
    
    async def _extract_interaction_features(self, data: Dict[str, Any]) -> List[float]:
        """提取交互特征"""
        features = [
            data.get('satisfaction_score', 0.5),
            1.0 if data.get('direction') == 'inbound' else 0.0,
            min(1.0, data.get('response_time', 3600) / 3600.0),  # 标准化响应时间
            1.0 if data.get('type') == 'phone_call' else 0.5 if data.get('type') == 'email' else 0.0
        ]
        
        return features
    
    def _calculate_text_quality(self, content: str) -> float:
        """计算文本质量评分"""
        if not content:
            return 0.0
        
        # 基于长度、完整性等因素计算质量
        length_score = min(1.0, len(content) / 100)  # 长度评分
        completeness_score = 1.0 if content.endswith(('.', '!', '?')) else 0.8
        
        return (length_score + completeness_score) / 2
    
    async def _fuse_multimodal_data(
        self,
        customer_id: str,
        features: Dict[DataModalityType, np.ndarray],
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]]
    ) -> DataFusionResult:
        """融合多模态数据"""
        
        # 计算各模态的置信度
        confidence_scores = {}
        for modality, data_points in processed_data.items():
            if data_points:
                avg_quality = np.mean([point.quality_score for point in data_points])
                confidence_scores[modality] = avg_quality
            else:
                confidence_scores[modality] = 0.0
        
        # 融合特征向量
        fused_features = await self._fuse_features(features, confidence_scores)
        
        # 计算融合质量
        fusion_quality = self._calculate_fusion_quality(confidence_scores, features)
        
        # 生成洞察
        insights = await self._generate_insights(processed_data, fused_features)
        
        # 异常检测
        anomalies = await self._detect_anomalies(processed_data, fused_features)
        
        return DataFusionResult(
            customer_id=customer_id,
            fusion_timestamp=datetime.now(),
            input_modalities=list(features.keys()),
            fused_features=fused_features.tolist(),
            confidence_scores=confidence_scores,
            fusion_quality=fusion_quality,
            insights=insights,
            anomalies=anomalies
        )
    
    async def _fuse_features(
        self,
        features: Dict[DataModalityType, np.ndarray],
        confidence_scores: Dict[DataModalityType, float]
    ) -> np.ndarray:
        """融合特征向量"""
        
        # 收集有效特征
        valid_features = []
        weights = []
        
        config = self.fusion_config
        modality_weights = {
            DataModalityType.TEXT: config.text_weight,
            DataModalityType.VOICE: config.voice_weight,
            DataModalityType.BEHAVIOR: config.behavior_weight,
            DataModalityType.INTERACTION: config.interaction_weight
        }
        
        for modality, feature_vector in features.items():
            if len(feature_vector) > 0:
                # 标准化特征向量长度
                if len(feature_vector) < 10:
                    # 填充到10维
                    padded_features = np.pad(feature_vector, (0, 10 - len(feature_vector)), 'constant')
                else:
                    # 截取前10维
                    padded_features = feature_vector[:10]
                
                valid_features.append(padded_features)
                
                # 计算权重(模态权重 * 置信度)
                modality_weight = modality_weights.get(modality, 0.1)
                confidence = confidence_scores.get(modality, 0.5)
                final_weight = modality_weight * confidence
                weights.append(final_weight)
        
        if not valid_features:
            return np.zeros(10)  # 返回零向量
        
        # 加权平均融合
        weights = np.array(weights)
        weights = weights / np.sum(weights)  # 归一化权重
        
        fused_vector = np.zeros(10)
        for i, (features_vec, weight) in enumerate(zip(valid_features, weights)):
            fused_vector += features_vec * weight
        
        return fused_vector
    
    def _calculate_fusion_quality(
        self,
        confidence_scores: Dict[DataModalityType, float],
        features: Dict[DataModalityType, np.ndarray]
    ) -> float:
        """计算融合质量"""
        
        # 基于多个因素计算融合质量
        
        # 1. 模态完整性(有多少种模态的数据)
        available_modalities = len([f for f in features.values() if len(f) > 0])
        completeness_score = available_modalities / 4.0  # 假设最多4种模态
        
        # 2. 平均置信度
        valid_confidences = [conf for conf in confidence_scores.values() if conf > 0]
        avg_confidence = np.mean(valid_confidences) if valid_confidences else 0.0
        
        # 3. 数据一致性(简化计算)
        consistency_score = 0.8  # 简化为固定值，实际应该计算模态间的一致性
        
        # 综合评分
        fusion_quality = (
            completeness_score * 0.4 +
            avg_confidence * 0.4 +
            consistency_score * 0.2
        )
        
        return min(1.0, max(0.0, fusion_quality))
    
    async def _generate_insights(
        self,
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]],
        fused_features: np.ndarray
    ) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 基于各模态数据生成洞察
        
        # 文本洞察
        if DataModalityType.TEXT in processed_data:
            text_points = processed_data[DataModalityType.TEXT]
            if text_points:
                avg_sentiment = np.mean([
                    1.0 if point.processed_data.get('sentiment') == 'positive' 
                    else 0.5 if point.processed_data.get('sentiment') == 'neutral' 
                    else 0.0
                    for point in text_points
                ])
                if avg_sentiment > 0.7:
                    insights.append("客户在文本交流中表现出积极态度")
                elif avg_sentiment < 0.3:
                    insights.append("客户在文本交流中存在负面情绪")
        
        # 语音洞察
        if DataModalityType.VOICE in processed_data:
            voice_points = processed_data[DataModalityType.VOICE]
            if voice_points:
                avg_confidence = np.mean([point.quality_score for point in voice_points])
                if avg_confidence > 0.8:
                    insights.append("客户语音交流清晰，沟通效果良好")
                
                # 检查是否有明确意图
                has_intent = any(
                    point.processed_data.get('has_intent', False) 
                    for point in voice_points
                )
                if has_intent:
                    insights.append("客户在语音交流中表达了明确的业务意图")
        
        # 行为洞察
        if DataModalityType.BEHAVIOR in processed_data:
            behavior_points = processed_data[DataModalityType.BEHAVIOR]
            if behavior_points:
                avg_engagement = np.mean([
                    point.processed_data.get('engagement_score', 0.5) 
                    for point in behavior_points
                ])
                if avg_engagement > 0.8:
                    insights.append("客户数字化参与度很高，表现出强烈兴趣")
                
                # 检查转化行为
                has_conversions = any(
                    point.processed_data.get('conversion_count', 0) > 0 
                    for point in behavior_points
                )
                if has_conversions:
                    insights.append("客户已产生转化行为，购买意向明确")
        
        # 基于融合特征的洞察
        if len(fused_features) > 0:
            overall_score = np.mean(fused_features)
            if overall_score > 0.7:
                insights.append("综合分析显示客户为高价值潜在客户")
            elif overall_score > 0.5:
                insights.append("客户表现出中等程度的购买意向")
        
        return insights
    
    async def _detect_anomalies(
        self,
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]],
        fused_features: np.ndarray
    ) -> List[str]:
        """检测异常"""
        anomalies = []
        
        # 检测各模态的异常
        
        # 行为异常检测
        if DataModalityType.BEHAVIOR in processed_data:
            behavior_points = processed_data[DataModalityType.BEHAVIOR]
            if behavior_points:
                engagement_scores = [
                    point.processed_data.get('engagement_score', 0.5) 
                    for point in behavior_points
                ]
                
                # 检测参与度异常波动
                if len(engagement_scores) > 1:
                    std_dev = np.std(engagement_scores)
                    if std_dev > 0.3:
                        anomalies.append("客户参与度波动异常，行为模式不稳定")
                
                # 检测异常高的页面浏览量
                page_views = [
                    point.processed_data.get('page_views_count', 0) 
                    for point in behavior_points
                ]
                max_page_views = max(page_views) if page_views else 0
                if max_page_views > 50:
                    anomalies.append("检测到异常高的页面浏览量，可能为机器人行为")
        
        # 语音异常检测
        if DataModalityType.VOICE in processed_data:
            voice_points = processed_data[DataModalityType.VOICE]
            if voice_points:
                confidences = [point.quality_score for point in voice_points]
                avg_confidence = np.mean(confidences)
                
                if avg_confidence < 0.5:
                    anomalies.append("语音识别置信度较低，可能存在音频质量问题")
        
        # 基于融合特征的异常检测
        if len(fused_features) > 0:
            # 检测特征向量中的异常值
            feature_std = np.std(fused_features)
            feature_mean = np.mean(fused_features)
            
            outliers = np.abs(fused_features - feature_mean) > 2 * feature_std
            if np.any(outliers):
                anomalies.append("检测到融合特征中存在异常值")
        
        return anomalies
    
    async def _perform_analysis(
        self,
        analysis_type: str,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行具体分析"""
        
        if analysis_type == 'high_value_identification':
            return await self._perform_high_value_analysis(fusion_result, parameters)
        elif analysis_type == 'behavior_pattern_analysis':
            return await self._perform_behavior_analysis(fusion_result, parameters)
        elif analysis_type == 'sentiment_analysis':
            return await self._perform_sentiment_analysis(fusion_result, parameters)
        elif analysis_type == 'engagement_analysis':
            return await self._perform_engagement_analysis(fusion_result, parameters)
        else:
            return {'error': f'不支持的分析类型: {analysis_type}'}
    
    async def _perform_high_value_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行高价值客户分析"""
        
        # 基于融合特征计算价值评分
        fused_features = np.array(fusion_result.fused_features)
        
        if len(fused_features) == 0:
            return {'value_score': 0.0, 'value_level': 'unknown'}
        
        # 计算综合价值评分
        value_score = np.mean(fused_features)
        
        # 应用置信度权重
        weighted_score = value_score * fusion_result.fusion_quality
        
        # 确定价值等级
        if weighted_score >= 0.8:
            value_level = 'very_high'
        elif weighted_score >= 0.6:
            value_level = 'high'
        elif weighted_score >= 0.4:
            value_level = 'medium'
        else:
            value_level = 'low'
        
        return {
            'value_score': weighted_score,
            'value_level': value_level,
            'confidence': fusion_result.fusion_quality,
            'contributing_factors': self._identify_value_factors(fusion_result)
        }
    
    async def _perform_behavior_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行行为模式分析"""
        
        return {
            'behavior_consistency': 0.75,  # 简化实现
            'engagement_trend': 'increasing',
            'interaction_frequency': 'high',
            'conversion_likelihood': 0.68
        }
    
    async def _perform_sentiment_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行情感分析"""
        
        return {
            'overall_sentiment': 'positive',
            'sentiment_score': 0.72,
            'emotion_distribution': {
                'positive': 0.6,
                'neutral': 0.3,
                'negative': 0.1
            },
            'sentiment_trend': 'stable'
        }
    
    async def _perform_engagement_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行参与度分析"""
        
        return {
            'engagement_score': 0.78,
            'engagement_level': 'high',
            'peak_engagement_time': '14:00-16:00',
            'engagement_channels': ['website', 'voice_call', 'email']
        }
    
    def _identify_value_factors(self, fusion_result: DataFusionResult) -> List[str]:
        """识别价值贡献因素"""
        factors = []
        
        confidence_scores = fusion_result.confidence_scores
        
        if confidence_scores.get(DataModalityType.BEHAVIOR, 0) > 0.7:
            factors.append("高数字化参与度")
        
        if confidence_scores.get(DataModalityType.VOICE, 0) > 0.7:
            factors.append("积极的语音交流")
        
        if confidence_scores.get(DataModalityType.TEXT, 0) > 0.7:
            factors.append("正面的文本沟通")
        
        if len(fusion_result.input_modalities) >= 3:
            factors.append("多渠道活跃用户")
        
        return factors
    
    async def _generate_high_value_profile(
        self,
        customer_id: str,
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]],
        fusion_result: DataFusionResult
    ) -> Optional[HighValueCustomerProfile]:
        """生成高价值客户画像"""
        
        try:
            # 准备数据用于高价值客户服务
            customer_data = [{'id': customer_id, 'size': 'medium', 'industry': 'technology', 'status': 'qualified'}]
            
            behavior_data = []
            if DataModalityType.BEHAVIOR in processed_data:
                for point in processed_data[DataModalityType.BEHAVIOR]:
                    # 从MultimodalDataPoint重构BehaviorData
                    behavior_data.append(BehaviorData(
                        customer_id=customer_id,
                        session_id=point.metadata.get('session_id', 'unknown'),
                        page_views=point.raw_data.get('page_views', []),
                        click_events=point.raw_data.get('click_events', []),
                        time_spent=point.raw_data.get('time_spent', {}),
                        interaction_patterns=point.raw_data.get('interaction_patterns', {}),
                        engagement_score=point.processed_data.get('engagement_score', 0.5),
                        conversion_indicators=point.raw_data.get('conversion_indicators', []),
                        timestamp=point.timestamp
                    ))
            
            voice_data = []
            if DataModalityType.VOICE in processed_data:
                for point in processed_data[DataModalityType.VOICE]:
                    # 从MultimodalDataPoint重构VoiceAnalysisResult
                    raw_data = point.raw_data
                    voice_data.append(VoiceAnalysisResult(
                        transcript=raw_data.get('transcript', ''),
                        confidence=raw_data.get('confidence', 0.5),
                        sentiment=raw_data.get('sentiment', 'neutral'),
                        emotion=raw_data.get('emotion', 'neutral'),
                        speaking_rate=raw_data.get('speaking_rate', 120.0),
                        pause_frequency=raw_data.get('pause_frequency', 0.1),
                        voice_quality=raw_data.get('voice_quality', {}),
                        keywords=raw_data.get('keywords', []),
                        intent=raw_data.get('intent')
                    ))
            
            # 调用高价值客户服务
            profiles = await self.high_value_service.identify_high_value_customers(
                customer_data, behavior_data, voice_data
            )
            
            return profiles[0] if profiles else None
            
        except Exception as e:
            logger.error(f"生成高价值客户画像失败: {str(e)}")
            return None
    
    async def _generate_recommendations(
        self,
        analysis_results: Dict[str, Any],
        fusion_result: DataFusionResult,
        high_value_profile: Optional[HighValueCustomerProfile]
    ) -> List[str]:
        """生成推荐建议"""
        recommendations = []
        
        # 基于分析结果生成建议
        if 'value_level' in analysis_results:
            value_level = analysis_results['value_level']
            
            if value_level == 'very_high':
                recommendations.extend([
                    "立即分配顶级销售代表跟进",
                    "安排高管层面会议",
                    "提供定制化解决方案演示"
                ])
            elif value_level == 'high':
                recommendations.extend([
                    "分配经验丰富的销售代表",
                    "安排详细产品演示",
                    "提供ROI分析报告"
                ])
            elif value_level == 'medium':
                recommendations.extend([
                    "发送产品资料和案例研究",
                    "邀请参加网络研讨会",
                    "定期跟进了解需求"
                ])
        
        # 基于洞察生成建议
        for insight in fusion_result.insights:
            if "积极态度" in insight:
                recommendations.append("利用客户积极态度，加快推进节奏")
            elif "高价值潜在客户" in insight:
                recommendations.append("优先资源配置，重点关注")
            elif "购买意向明确" in insight:
                recommendations.append("准备详细报价方案")
        
        # 基于异常生成建议
        for anomaly in fusion_result.anomalies:
            if "音频质量问题" in anomaly:
                recommendations.append("改善通话环境，确保沟通质量")
            elif "行为模式不稳定" in anomaly:
                recommendations.append("深入了解客户需求变化原因")
        
        # 基于高价值画像生成建议
        if high_value_profile:
            recommendations.extend(high_value_profile.recommended_actions)
        
        return list(set(recommendations))  # 去重
    
    async def create_analysis_pipeline(
        self,
        customer_id: str,
        modalities: List[DataModalityType],
        analysis_types: List[str]
    ) -> List[MultimodalAnalysisResult]:
        """创建分析管道"""
        
        results = []
        
        for analysis_type in analysis_types:
            request = MultimodalAnalysisRequest(
                customer_id=customer_id,
                analysis_type=analysis_type,
                modalities=modalities,
                time_range={
                    'start': datetime.now() - timedelta(days=30),
                    'end': datetime.now()
                }
            )
            
            try:
                result = await self.process_multimodal_analysis(request)
                results.append(result)
            except Exception as e:
                logger.error(f"分析管道处理失败 {analysis_type}: {str(e)}")
                continue
        
        return results
    
    async def batch_process_customers(
        self,
        customer_ids: List[str],
        analysis_type: str = 'high_value_identification'
    ) -> Dict[str, MultimodalAnalysisResult]:
        """批量处理客户"""
        
        results = {}
        
        # 并行处理多个客户
        tasks = []
        for customer_id in customer_ids:
            request = MultimodalAnalysisRequest(
                customer_id=customer_id,
                analysis_type=analysis_type,
                modalities=[
                    DataModalityType.TEXT,
                    DataModalityType.VOICE,
                    DataModalityType.BEHAVIOR,
                    DataModalityType.INTERACTION
                ],
                time_range={
                    'start': datetime.now() - timedelta(days=30),
                    'end': datetime.now()
                }
            )
            tasks.append(self.process_multimodal_analysis(request))
        
        # 等待所有任务完成
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        for i, result in enumerate(task_results):
            customer_id = customer_ids[i]
            if isinstance(result, Exception):
                logger.error(f"客户 {customer_id} 处理失败: {str(result)}")
            else:
                results[customer_id] = result
        
        return results
        anomalies = []
        
        # 检测各种异常模式
        
        # 1. 参与度异常
        if DataModalityType.BEHAVIOR in processed_data:
            behavior_points = processed_data[DataModalityType.BEHAVIOR]
            if behavior_points:
                engagement_scores = [
                    point.processed_data.get('engagement_score', 0.5) 
                    for point in behavior_points
                ]
                if len(engagement_scores) > 1:
                    std_engagement = np.std(engagement_scores)
                    if std_engagement > 0.3:
                        anomalies.append("客户参与度波动较大，行为不一致")
        
        # 2. 情感不一致
        text_sentiment = None
        voice_sentiment = None
        
        if DataModalityType.TEXT in processed_data:
            text_points = processed_data[DataModalityType.TEXT]
            if text_points:
                text_sentiment = np.mean([
                    1.0 if point.processed_data.get('sentiment') == 'positive' 
                    else 0.5 if point.processed_data.get('sentiment') == 'neutral' 
                    else 0.0
                    for point in text_points
                ])
        
        if DataModalityType.VOICE in processed_data:
            voice_points = processed_data[DataModalityType.VOICE]
            if voice_points:
                voice_sentiment = np.mean([
                    1.0 if point.raw_data.get('sentiment') == 'positive' 
                    else 0.5 if point.raw_data.get('sentiment') == 'neutral' 
                    else 0.0
                    for point in voice_points
                ])
        
        if text_sentiment is not None and voice_sentiment is not None:
            if abs(text_sentiment - voice_sentiment) > 0.4:
                anomalies.append("文本和语音情感表达不一致")
        
        # 3. 时间异常
        all_timestamps = []
        for modality_points in processed_data.values():
            for point in modality_points:
                all_timestamps.append(point.timestamp)
        
        if len(all_timestamps) > 1:
            # 检查是否有异常的时间间隔
            sorted_timestamps = sorted(all_timestamps)
            intervals = [
                (sorted_timestamps[i+1] - sorted_timestamps[i]).total_seconds() / 3600
                for i in range(len(sorted_timestamps) - 1)
            ]
            
            if any(interval > 168 for interval in intervals):  # 超过一周
                anomalies.append("客户交互存在异常长的时间间隔")
        
        return anomalies
    

    
    async def _perform_high_value_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行高价值客户分析"""
        
        # 基于融合特征计算价值评分
        fused_features = np.array(fusion_result.fused_features)
        value_score = np.mean(fused_features) if len(fused_features) > 0 else 0.0
        
        # 调整评分基于置信度
        avg_confidence = np.mean(list(fusion_result.confidence_scores.values()))
        adjusted_score = value_score * avg_confidence
        
        # 确定价值等级
        if adjusted_score >= 0.8:
            value_tier = 'very_high'
        elif adjusted_score >= 0.6:
            value_tier = 'high'
        elif adjusted_score >= 0.4:
            value_tier = 'medium'
        else:
            value_tier = 'low'
        
        return {
            'value_score': adjusted_score,
            'value_level': value_tier,
            'confidence': avg_confidence,
            'contributing_factors': fusion_result.insights,
            'risk_indicators': fusion_result.anomalies,
            'data_completeness': len(fusion_result.input_modalities) / 4.0
        }
    
    async def _perform_engagement_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行参与度分析"""
        
        # 基于融合结果分析参与度
        engagement_indicators = []
        
        # 从洞察中提取参与度信息
        for insight in fusion_result.insights:
            if '参与度' in insight or '兴趣' in insight:
                engagement_indicators.append(insight)
        
        # 计算综合参与度评分
        fused_features = np.array(fusion_result.fused_features)
        engagement_score = np.mean(fused_features) if len(fused_features) > 0 else 0.0
        
        return {
            'engagement_score': engagement_score,
            'engagement_indicators': engagement_indicators,
            'trend': 'stable',  # 简化处理
            'recommendations': [
                '继续保持当前参与度' if engagement_score > 0.7 else '需要提升客户参与度'
            ]
        }
    
    async def _perform_sentiment_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行情感分析"""
        
        # 从洞察中提取情感信息
        sentiment_indicators = []
        overall_sentiment = 'neutral'
        
        for insight in fusion_result.insights:
            if '积极' in insight or '正面' in insight:
                sentiment_indicators.append(insight)
                overall_sentiment = 'positive'
            elif '负面' in insight or '消极' in insight:
                sentiment_indicators.append(insight)
                overall_sentiment = 'negative'
        
        return {
            'overall_sentiment': overall_sentiment,
            'sentiment_indicators': sentiment_indicators,
            'sentiment_consistency': len(fusion_result.anomalies) == 0,
            'confidence': fusion_result.fusion_quality
        }
    
    async def _perform_behavior_pattern_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行行为模式分析"""
        
        return {
            'pattern_type': 'engaged_explorer',  # 简化处理
            'consistency_score': 1.0 - len(fusion_result.anomalies) * 0.2,
            'behavioral_insights': fusion_result.insights,
            'anomalies': fusion_result.anomalies
        }
    
    async def _perform_general_analysis(
        self,
        fusion_result: DataFusionResult,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行通用分析"""
        
        return {
            'fusion_quality': fusion_result.fusion_quality,
            'data_completeness': len(fusion_result.input_modalities) / 4.0,
            'insights': fusion_result.insights,
            'anomalies': fusion_result.anomalies,
            'confidence_scores': fusion_result.confidence_scores
        }
    
    async def _generate_high_value_profile(
        self,
        customer_id: str,
        processed_data: Dict[DataModalityType, List[MultimodalDataPoint]],
        fusion_result: DataFusionResult
    ) -> Optional[HighValueCustomerProfile]:
        """生成高价值客户画像"""
        
        try:
            # 准备数据用于高价值客户服务
            customer_data = [{'id': customer_id}]  # 简化的客户数据
            
            behavior_data = []
            if DataModalityType.BEHAVIOR in processed_data:
                # 从处理后的数据重构BehaviorData对象
                for point in processed_data[DataModalityType.BEHAVIOR]:
                    raw_data = point.raw_data
                    behavior_data.append(BehaviorData(**raw_data))
            
            voice_data = []
            if DataModalityType.VOICE in processed_data:
                # 从处理后的数据重构VoiceAnalysisResult对象
                for point in processed_data[DataModalityType.VOICE]:
                    raw_data = point.raw_data
                    voice_data.append(VoiceAnalysisResult(**raw_data))
            
            # 调用高价值客户识别服务
            profiles = await self.high_value_service.identify_high_value_customers(
                customer_data, behavior_data, voice_data
            )
            
            return profiles[0] if profiles else None
            
        except Exception as e:
            logger.error(f"生成高价值客户画像失败: {str(e)}")
            return None
    
    async def _generate_recommendations(
        self,
        analysis_results: Dict[str, Any],
        fusion_result: DataFusionResult,
        high_value_profile: Optional[HighValueCustomerProfile]
    ) -> List[str]:
        """生成推荐建议"""
        
        recommendations = []
        
        # 基于分析结果生成建议
        if 'value_level' in analysis_results:
            value_level = analysis_results['value_level']
            if value_level == 'very_high':
                recommendations.extend([
                    "立即安排高级销售代表跟进",
                    "提供VIP客户服务",
                    "安排高管层面会议"
                ])
            elif value_level == 'high':
                recommendations.extend([
                    "安排专业销售代表跟进",
                    "提供详细产品演示",
                    "发送个性化方案"
                ])
            elif value_level == 'medium':
                recommendations.extend([
                    "定期跟进维护关系",
                    "发送相关案例研究",
                    "邀请参加活动"
                ])
        
        # 基于洞察生成建议
        for insight in fusion_result.insights:
            if "高价值" in insight:
                recommendations.append("重点关注，优先分配资源")
            elif "积极态度" in insight:
                recommendations.append("趁热打铁，加快推进节奏")
            elif "购买意向明确" in insight:
                recommendations.append("准备详细报价和合同")
        
        # 基于异常生成建议
        for anomaly in fusion_result.anomalies:
            if "不一致" in anomaly:
                recommendations.append("深入了解客户真实需求和顾虑")
            elif "时间间隔" in anomaly:
                recommendations.append("主动联系，重新激发兴趣")
        
        # 基于高价值画像生成建议
        if high_value_profile:
            recommendations.extend(high_value_profile.recommended_actions)
        
        # 去重并返回
        return list(set(recommendations))
    
    async def batch_process_customers(
        self,
        customer_ids: List[str],
        analysis_type: str = 'high_value_identification',
        time_window: Optional[timedelta] = None
    ) -> List[MultimodalAnalysisResult]:
        """批量处理客户分析"""
        
        results = []
        
        # 并行处理多个客户
        tasks = []
        for customer_id in customer_ids:
            request = MultimodalAnalysisRequest(
                customer_id=customer_id,
                analysis_type=analysis_type,
                modalities=[
                    DataModalityType.TEXT,
                    DataModalityType.VOICE,
                    DataModalityType.BEHAVIOR,
                    DataModalityType.INTERACTION
                ],
                time_range={
                    'start': datetime.now() - (time_window or timedelta(days=30)),
                    'end': datetime.now()
                }
            )
            tasks.append(self.process_multimodal_analysis(request))
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果为字典格式
        result_dict = {}
        for i, result in enumerate(results):
            customer_id = customer_ids[i]
            if not isinstance(result, Exception):
                result_dict[customer_id] = result
            else:
                logger.error(f"客户 {customer_id} 处理失败: {str(result)}")
        
        logger.info(f"批量处理完成，成功处理 {len(result_dict)}/{len(customer_ids)} 个客户")
        
        return result_dict