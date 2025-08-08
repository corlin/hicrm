# 多模态数据分析测试

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import json

from src.models.multimodal import (
    DataModalityType, VoiceAnalysisResult, BehaviorData, MultimodalDataPoint,
    CustomerValueIndicator, HighValueCustomerProfile, DataFusionResult,
    MultimodalAnalysisRequest, MultimodalAnalysisResult
)
from src.services.speech_recognition_service import SpeechRecognitionService
from src.services.behavior_analysis_service import BehaviorAnalysisService
from src.services.high_value_customer_service import HighValueCustomerService
from src.services.multimodal_fusion_service import MultimodalFusionService


class TestSpeechRecognitionService:
    """语音识别服务测试"""
    
    @pytest.fixture
    def speech_service(self):
        return SpeechRecognitionService()
    
    @pytest.fixture
    def sample_audio_data(self):
        # 模拟音频数据
        return b"fake_audio_data_for_testing" * 100
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, speech_service, sample_audio_data):
        """测试语音转文本成功"""
        result = await speech_service.transcribe_audio(
            sample_audio_data, 
            format='wav', 
            language='zh-CN'
        )
        
        assert isinstance(result, VoiceAnalysisResult)
        assert result.transcript != ""
        assert 0.0 <= result.confidence <= 1.0
        assert result.sentiment in ['positive', 'negative', 'neutral']
        assert result.speaking_rate > 0
        assert isinstance(result.keywords, list)
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_invalid_format(self, speech_service, sample_audio_data):
        """测试不支持的音频格式"""
        with pytest.raises(ValueError, match="不支持的音频格式"):
            await speech_service.transcribe_audio(
                sample_audio_data, 
                format='xyz'
            )
    
    @pytest.mark.asyncio
    async def test_transcribe_audio_file_too_large(self, speech_service):
        """测试音频文件过大"""
        large_audio_data = b"x" * (51 * 1024 * 1024)  # 51MB
        
        with pytest.raises(ValueError, match="音频文件过大"):
            await speech_service.transcribe_audio(large_audio_data)
    
    @pytest.mark.asyncio
    async def test_batch_transcribe(self, speech_service):
        """测试批量语音识别"""
        audio_files = [
            {'data': b"audio1" * 100, 'format': 'wav'},
            {'data': b"audio2" * 200, 'format': 'mp3'},
            {'data': b"audio3" * 150, 'format': 'flac'}
        ]
        
        results = await speech_service.batch_transcribe(audio_files)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, VoiceAnalysisResult)
    
    @pytest.mark.asyncio
    async def test_validate_audio_quality(self, speech_service, sample_audio_data):
        """测试音频质量验证"""
        quality_result = await speech_service.validate_audio_quality(sample_audio_data)
        
        assert 'quality_score' in quality_result
        assert 'is_valid' in quality_result
        assert 'issues' in quality_result
        assert 'recommendations' in quality_result
        assert 0.0 <= quality_result['quality_score'] <= 1.0
        assert isinstance(quality_result['is_valid'], bool)
    
    @pytest.mark.asyncio
    async def test_get_supported_languages(self, speech_service):
        """测试获取支持的语言列表"""
        languages = await speech_service.get_supported_languages()
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert 'zh-CN' in languages
        assert 'en-US' in languages


class TestBehaviorAnalysisService:
    """客户行为分析服务测试"""
    
    @pytest.fixture
    def behavior_service(self):
        return BehaviorAnalysisService()
    
    @pytest.fixture
    def sample_behavior_data(self):
        return [
            BehaviorData(
                customer_id="test_customer_1",
                session_id="session_1",
                page_views=[
                    {"url": "/products", "timestamp": datetime.now(), "duration": 120},
                    {"url": "/pricing", "timestamp": datetime.now(), "duration": 180}
                ],
                click_events=[
                    {"element": "demo_button", "timestamp": datetime.now()},
                    {"element": "pricing_link", "timestamp": datetime.now()}
                ],
                time_spent={"/products": 120.0, "/pricing": 180.0},
                interaction_patterns={"scroll_depth": 0.8, "click_through_rate": 0.7},
                engagement_score=0.75,
                conversion_indicators=["demo_request"],
                timestamp=datetime.now()
            ),
            BehaviorData(
                customer_id="test_customer_1",
                session_id="session_2",
                page_views=[
                    {"url": "/features", "timestamp": datetime.now(), "duration": 200}
                ],
                click_events=[
                    {"element": "feature_link", "timestamp": datetime.now()}
                ],
                time_spent={"/features": 200.0},
                interaction_patterns={"scroll_depth": 0.9, "click_through_rate": 0.8},
                engagement_score=0.85,
                conversion_indicators=["contact_form"],
                timestamp=datetime.now()
            )
        ]
    
    @pytest.mark.asyncio
    async def test_analyze_customer_behavior_success(self, behavior_service, sample_behavior_data):
        """测试客户行为分析成功"""
        result = await behavior_service.analyze_customer_behavior(
            "test_customer_1",
            sample_behavior_data
        )
        
        assert result['customer_id'] == "test_customer_1"
        assert 'engagement_metrics' in result
        assert 'access_patterns' in result
        assert 'conversion_metrics' in result
        assert 'behavior_profile' in result
        assert 'anomalies' in result
        assert 'recommendations' in result
        
        # 验证参与度指标
        engagement_metrics = result['engagement_metrics']
        assert 'average_engagement_score' in engagement_metrics
        assert 'total_page_views' in engagement_metrics
        assert 'total_clicks' in engagement_metrics
        
        # 验证行为画像
        behavior_profile = result['behavior_profile']
        assert 'overall_score' in behavior_profile
        assert 'customer_type' in behavior_profile
        assert 'engagement_level' in behavior_profile
    
    @pytest.mark.asyncio
    async def test_analyze_customer_behavior_empty_data(self, behavior_service):
        """测试空数据的行为分析"""
        result = await behavior_service.analyze_customer_behavior(
            "test_customer_empty",
            []
        )
        
        assert result['customer_id'] == "test_customer_empty"
        assert result['data_points_count'] == 0
        assert result['behavior_profile']['overall_score'] == 0.0
        assert result['behavior_profile']['customer_type'] == 'unknown'
    
    @pytest.mark.asyncio
    async def test_analyze_customer_behavior_with_time_window(self, behavior_service, sample_behavior_data):
        """测试带时间窗口的行为分析"""
        time_window = timedelta(days=7)
        
        result = await behavior_service.analyze_customer_behavior(
            "test_customer_1",
            sample_behavior_data,
            time_window
        )
        
        assert result['customer_id'] == "test_customer_1"
        assert result['data_points_count'] <= len(sample_behavior_data)


class TestHighValueCustomerService:
    """高价值客户识别服务测试"""
    
    @pytest.fixture
    def high_value_service(self):
        return HighValueCustomerService()
    
    @pytest.fixture
    def sample_customer_data(self):
        return [
            {
                'id': 'customer_1',
                'name': 'ABC公司',
                'size': 'large',
                'industry': 'technology',
                'status': 'qualified',
                'location': {'city': '北京'},
                'founded_year': 2010
            },
            {
                'id': 'customer_2',
                'name': 'XYZ公司',
                'size': 'small',
                'industry': 'retail',
                'status': 'prospect',
                'location': {'city': '上海'},
                'founded_year': 2020
            }
        ]
    
    @pytest.fixture
    def sample_behavior_data_for_hv(self):
        return [
            BehaviorData(
                customer_id="customer_1",
                session_id="session_1",
                page_views=[{"url": "/products", "duration": 300}] * 5,
                click_events=[{"element": "demo_button"}] * 3,
                time_spent={"/products": 300.0, "/pricing": 200.0},
                interaction_patterns={"scroll_depth": 0.9},
                engagement_score=0.9,
                conversion_indicators=["demo_request", "contact_form"],
                timestamp=datetime.now()
            )
        ]
    
    @pytest.fixture
    def sample_voice_data_for_hv(self):
        return [
            VoiceAnalysisResult(
                transcript="我们对你们的产品很感兴趣",
                confidence=0.95,
                sentiment="positive",
                emotion="interested",
                speaking_rate=120.0,
                pause_frequency=0.1,
                voice_quality={"clarity": 0.9, "volume": 0.8},
                keywords=["产品", "感兴趣"],
                intent="product_inquiry"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_identify_high_value_customers_success(
        self, 
        high_value_service, 
        sample_customer_data, 
        sample_behavior_data_for_hv, 
        sample_voice_data_for_hv
    ):
        """测试高价值客户识别成功"""
        profiles = await high_value_service.identify_high_value_customers(
            sample_customer_data,
            sample_behavior_data_for_hv,
            sample_voice_data_for_hv
        )
        
        assert isinstance(profiles, list)
        assert len(profiles) > 0
        
        profile = profiles[0]
        assert isinstance(profile, HighValueCustomerProfile)
        assert profile.customer_id in ['customer_1', 'customer_2']
        assert 0.0 <= profile.overall_score <= 1.0
        assert len(profile.value_indicators) > 0
        assert isinstance(profile.behavioral_patterns, dict)
        assert isinstance(profile.recommended_actions, list)
    
    @pytest.mark.asyncio
    async def test_identify_high_value_customers_empty_data(self, high_value_service):
        """测试空数据的高价值客户识别"""
        profiles = await high_value_service.identify_high_value_customers(
            [], [], []
        )
        
        assert isinstance(profiles, list)
        assert len(profiles) == 0
    
    @pytest.mark.asyncio
    async def test_identify_high_value_customers_with_time_window(
        self, 
        high_value_service, 
        sample_customer_data, 
        sample_behavior_data_for_hv, 
        sample_voice_data_for_hv
    ):
        """测试带时间窗口的高价值客户识别"""
        time_window = timedelta(days=7)
        
        profiles = await high_value_service.identify_high_value_customers(
            sample_customer_data,
            sample_behavior_data_for_hv,
            sample_voice_data_for_hv,
            time_window
        )
        
        assert isinstance(profiles, list)


class TestMultimodalFusionService:
    """多模态数据融合服务测试"""
    
    @pytest.fixture
    def fusion_service(self):
        return MultimodalFusionService()
    
    @pytest.fixture
    def sample_analysis_request(self):
        return MultimodalAnalysisRequest(
            customer_id="test_customer_fusion",
            analysis_type="high_value_identification",
            modalities=[
                DataModalityType.TEXT,
                DataModalityType.VOICE,
                DataModalityType.BEHAVIOR
            ],
            time_range={
                'start': datetime.now() - timedelta(days=7),
                'end': datetime.now()
            },
            parameters={}
        )
    
    @pytest.mark.asyncio
    async def test_process_multimodal_analysis_success(self, fusion_service, sample_analysis_request):
        """测试多模态分析处理成功"""
        result = await fusion_service.process_multimodal_analysis(sample_analysis_request)
        
        assert isinstance(result, MultimodalAnalysisResult)
        assert result.customer_id == "test_customer_fusion"
        assert result.analysis_type == "high_value_identification"
        assert 'results' in result.results or result.results is not None
        assert isinstance(result.recommendations, list)
        assert 0.0 <= result.confidence <= 1.0
        assert result.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_process_multimodal_analysis_different_types(self, fusion_service):
        """测试不同类型的多模态分析"""
        analysis_types = [
            'high_value_identification',
            'behavior_pattern_analysis',
            'sentiment_analysis',
            'engagement_analysis'
        ]
        
        for analysis_type in analysis_types:
            request = MultimodalAnalysisRequest(
                customer_id="test_customer",
                analysis_type=analysis_type,
                modalities=[DataModalityType.BEHAVIOR],
                time_range={
                    'start': datetime.now() - timedelta(days=1),
                    'end': datetime.now()
                }
            )
            
            result = await fusion_service.process_multimodal_analysis(request)
            assert result.analysis_type == analysis_type
            assert isinstance(result.results, dict)
    
    @pytest.mark.asyncio
    async def test_create_analysis_pipeline(self, fusion_service):
        """测试创建分析管道"""
        customer_id = "pipeline_test_customer"
        modalities = [DataModalityType.TEXT, DataModalityType.BEHAVIOR]
        analysis_types = ['high_value_identification', 'sentiment_analysis']
        
        results = await fusion_service.create_analysis_pipeline(
            customer_id, modalities, analysis_types
        )
        
        assert isinstance(results, list)
        assert len(results) <= len(analysis_types)  # 可能有失败的分析
        
        for result in results:
            assert isinstance(result, MultimodalAnalysisResult)
            assert result.customer_id == customer_id
    
    @pytest.mark.asyncio
    async def test_batch_process_customers(self, fusion_service):
        """测试批量处理客户"""
        customer_ids = ["batch_customer_1", "batch_customer_2", "batch_customer_3"]
        
        results = await fusion_service.batch_process_customers(customer_ids)
        
        assert isinstance(results, dict)
        assert len(results) <= len(customer_ids)  # 可能有失败的处理
        
        for customer_id, result in results.items():
            assert customer_id in customer_ids
            assert isinstance(result, MultimodalAnalysisResult)
            assert result.customer_id == customer_id


class TestMultimodalDataIntegration:
    """多模态数据集成测试"""
    
    @pytest.fixture
    def all_services(self):
        return {
            'speech': SpeechRecognitionService(),
            'behavior': BehaviorAnalysisService(),
            'high_value': HighValueCustomerService(),
            'fusion': MultimodalFusionService()
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_multimodal_analysis(self, all_services):
        """测试端到端多模态分析"""
        # 准备测试数据
        customer_id = "e2e_test_customer"
        
        # 创建分析请求
        request = MultimodalAnalysisRequest(
            customer_id=customer_id,
            analysis_type="high_value_identification",
            modalities=[
                DataModalityType.TEXT,
                DataModalityType.VOICE,
                DataModalityType.BEHAVIOR,
                DataModalityType.INTERACTION
            ],
            time_range={
                'start': datetime.now() - timedelta(days=30),
                'end': datetime.now()
            },
            parameters={'detailed_analysis': True}
        )
        
        # 执行分析
        fusion_service = all_services['fusion']
        result = await fusion_service.process_multimodal_analysis(request)
        
        # 验证结果
        assert isinstance(result, MultimodalAnalysisResult)
        assert result.customer_id == customer_id
        assert result.analysis_type == "high_value_identification"
        assert len(result.recommendations) > 0
        assert result.confidence > 0.0
        
        # 验证分析结果包含预期字段
        analysis_results = result.results
        assert 'value_score' in analysis_results
        assert 'value_level' in analysis_results
        assert 'confidence' in analysis_results
    
    @pytest.mark.asyncio
    async def test_multimodal_data_consistency(self, all_services):
        """测试多模态数据一致性"""
        fusion_service = all_services['fusion']
        
        # 测试相同客户的多次分析结果一致性
        customer_id = "consistency_test_customer"
        
        request = MultimodalAnalysisRequest(
            customer_id=customer_id,
            analysis_type="high_value_identification",
            modalities=[DataModalityType.BEHAVIOR, DataModalityType.TEXT],
            time_range={
                'start': datetime.now() - timedelta(days=7),
                'end': datetime.now()
            }
        )
        
        # 执行多次分析
        results = []
        for _ in range(3):
            result = await fusion_service.process_multimodal_analysis(request)
            results.append(result)
        
        # 验证结果一致性
        assert len(results) == 3
        
        # 检查价值评分的一致性(允许小幅波动)
        value_scores = [
            r.results.get('value_score', 0) for r in results
        ]
        
        if len(value_scores) > 1:
            score_std = np.std(value_scores)
            assert score_std < 0.1, f"价值评分波动过大: {value_scores}"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, all_services):
        """测试错误处理和恢复"""
        fusion_service = all_services['fusion']
        
        # 测试无效的分析类型
        invalid_request = MultimodalAnalysisRequest(
            customer_id="error_test_customer",
            analysis_type="invalid_analysis_type",
            modalities=[DataModalityType.TEXT],
            time_range={
                'start': datetime.now() - timedelta(days=1),
                'end': datetime.now()
            }
        )
        
        result = await fusion_service.process_multimodal_analysis(invalid_request)
        
        # 应该返回结果，但包含错误信息
        assert isinstance(result, MultimodalAnalysisResult)
        assert 'error' in result.results or result.confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, all_services):
        """测试性能基准"""
        fusion_service = all_services['fusion']
        
        # 测试单个客户分析的性能
        start_time = datetime.now()
        
        request = MultimodalAnalysisRequest(
            customer_id="performance_test_customer",
            analysis_type="high_value_identification",
            modalities=[
                DataModalityType.TEXT,
                DataModalityType.VOICE,
                DataModalityType.BEHAVIOR
            ],
            time_range={
                'start': datetime.now() - timedelta(days=30),
                'end': datetime.now()
            }
        )
        
        result = await fusion_service.process_multimodal_analysis(request)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 验证性能要求
        assert processing_time < 10.0, f"处理时间过长: {processing_time}秒"
        assert result.processing_time < 10.0, f"报告的处理时间过长: {result.processing_time}秒"
    
    @pytest.mark.asyncio
    async def test_scalability_with_multiple_customers(self, all_services):
        """测试多客户扩展性"""
        fusion_service = all_services['fusion']
        
        # 测试批量处理性能
        customer_ids = [f"scale_test_customer_{i}" for i in range(5)]
        
        start_time = datetime.now()
        results = await fusion_service.batch_process_customers(
            customer_ids, 
            "high_value_identification"
        )
        end_time = datetime.now()
        
        batch_processing_time = (end_time - start_time).total_seconds()
        
        # 验证批量处理结果
        assert isinstance(results, dict)
        assert len(results) <= len(customer_ids)
        
        # 验证批量处理性能
        assert batch_processing_time < 30.0, f"批量处理时间过长: {batch_processing_time}秒"
        
        # 验证平均处理时间
        if results:
            avg_processing_time = batch_processing_time / len(results)
            assert avg_processing_time < 10.0, f"平均处理时间过长: {avg_processing_time}秒"


# 性能测试标记
@pytest.mark.performance
class TestMultimodalPerformance:
    """多模态分析性能测试"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_processing(self):
        """测试大数据集处理性能"""
        fusion_service = MultimodalFusionService()
        
        # 创建大量模拟数据
        large_behavior_data = []
        for i in range(100):
            large_behavior_data.append(BehaviorData(
                customer_id="large_dataset_customer",
                session_id=f"session_{i}",
                page_views=[{"url": f"/page_{j}", "duration": 60} for j in range(10)],
                click_events=[{"element": f"element_{j}"} for j in range(5)],
                time_spent={f"/page_{j}": 60.0 for j in range(10)},
                interaction_patterns={"scroll_depth": 0.8},
                engagement_score=0.7 + (i % 3) * 0.1,
                conversion_indicators=["action_1", "action_2"],
                timestamp=datetime.now() - timedelta(hours=i)
            ))
        
        # 测试处理性能
        start_time = datetime.now()
        
        behavior_service = BehaviorAnalysisService()
        result = await behavior_service.analyze_customer_behavior(
            "large_dataset_customer",
            large_behavior_data
        )
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 验证结果和性能
        assert result['data_points_count'] == 100
        assert processing_time < 5.0, f"大数据集处理时间过长: {processing_time}秒"
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis_performance(self):
        """测试并发分析性能"""
        fusion_service = MultimodalFusionService()
        
        # 创建多个并发分析任务
        tasks = []
        customer_count = 10
        
        for i in range(customer_count):
            request = MultimodalAnalysisRequest(
                customer_id=f"concurrent_customer_{i}",
                analysis_type="high_value_identification",
                modalities=[DataModalityType.BEHAVIOR, DataModalityType.TEXT],
                time_range={
                    'start': datetime.now() - timedelta(days=7),
                    'end': datetime.now()
                }
            )
            tasks.append(fusion_service.process_multimodal_analysis(request))
        
        # 执行并发分析
        start_time = datetime.now()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = datetime.now()
        
        concurrent_processing_time = (end_time - start_time).total_seconds()
        
        # 验证并发处理结果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == customer_count
        
        # 验证并发处理性能
        assert concurrent_processing_time < 15.0, f"并发处理时间过长: {concurrent_processing_time}秒"
        
        # 验证平均处理时间
        avg_time = concurrent_processing_time / customer_count
        assert avg_time < 5.0, f"平均并发处理时间过长: {avg_time}秒"