"""
知识库管理服务测试
Knowledge Management Service Tests
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.models.knowledge import (
    Knowledge, KnowledgeType, KnowledgeStatus, KnowledgeMetadata,
    KnowledgeSearchFilter, KnowledgeUpdateRequest, QualityMetrics
)
from src.services.knowledge_service import (
    KnowledgeService, DocumentParser, QualityAssessment
)


class TestDocumentParser:
    """文档解析器测试"""
    
    def test_parse_text_basic(self):
        """测试基本文本解析"""
        parser = DocumentParser()
        content = "这是第一句话。这是第二句话。这是第三句话。"
        
        chunks = parser.parse_text(content, chunk_size=20)
        
        assert len(chunks) > 0
        assert all(chunk.content for chunk in chunks)
        assert all(chunk.chunk_index >= 0 for chunk in chunks)
    
    def test_parse_text_with_overlap(self):
        """测试带重叠的文本解析"""
        parser = DocumentParser()
        content = "这是一个很长的句子用来测试重叠功能。" * 10
        
        chunks = parser.parse_text(content, chunk_size=50, overlap=10)
        
        assert len(chunks) > 1
        # 检查重叠
        for i in range(len(chunks) - 1):
            current_end = chunks[i].content[-10:]
            next_start = chunks[i + 1].content[:10]
            # 应该有部分重叠
            assert len(set(current_end) & set(next_start)) > 0
    
    def test_extract_keywords(self):
        """测试关键词提取"""
        parser = DocumentParser()
        content = "客户关系管理系统是企业管理客户信息的重要工具。客户满意度和客户服务质量直接影响企业发展。"
        
        keywords = parser.extract_keywords(content, max_keywords=5)
        
        assert len(keywords) <= 5
        assert "客户" in keywords  # 高频词应该被提取
        assert all(len(word) >= 2 for word in keywords)  # 过滤单字
    
    def test_split_sentences(self):
        """测试分句功能"""
        parser = DocumentParser()
        text = "第一句话。第二句话！第三句话？第四句话；"
        
        sentences = parser._split_sentences(text)
        
        assert len(sentences) == 4
        assert all(sentence.endswith('。') for sentence in sentences)


class TestQualityAssessment:
    """质量评估测试"""
    
    def test_assess_quality_basic(self):
        """测试基本质量评估"""
        assessor = QualityAssessment()
        
        # 创建测试知识
        metadata = KnowledgeMetadata(
            source="test",
            author="test_author",
            domain="test_domain",
            tags=["tag1", "tag2"],
            keywords=["keyword1", "keyword2"]
        )
        
        knowledge = Knowledge(
            title="测试知识",
            content="这是一个测试知识条目，包含足够的内容来进行质量评估。" * 10,
            type=KnowledgeType.DOCUMENT,
            metadata=metadata
        )
        
        quality = assessor.assess_quality(knowledge)
        
        assert isinstance(quality, QualityMetrics)
        assert 0 <= quality.overall_score <= 1
        assert 0 <= quality.accuracy_score <= 1
        assert 0 <= quality.completeness_score <= 1
        assert 0 <= quality.relevance_score <= 1
        assert 0 <= quality.freshness_score <= 1
        assert 0 <= quality.usage_score <= 1
    
    def test_assess_completeness(self):
        """测试完整性评估"""
        assessor = QualityAssessment()
        
        # 完整的知识
        complete_metadata = KnowledgeMetadata(
            source="test",
            author="test_author",
            domain="test_domain",
            tags=["tag1", "tag2"],
            keywords=["keyword1", "keyword2"]
        )
        
        complete_knowledge = Knowledge(
            title="完整知识",
            content="这是一个完整的知识条目。" * 50,
            type=KnowledgeType.DOCUMENT,
            metadata=complete_metadata
        )
        
        # 不完整的知识
        incomplete_metadata = KnowledgeMetadata(
            source="test",
            author="test_author",
            domain=""
        )
        
        incomplete_knowledge = Knowledge(
            title="不完整知识",
            content="短内容",
            type=KnowledgeType.DOCUMENT,
            metadata=incomplete_metadata
        )
        
        complete_score = assessor._assess_completeness(complete_knowledge)
        incomplete_score = assessor._assess_completeness(incomplete_knowledge)
        
        assert complete_score > incomplete_score
    
    def test_assess_freshness(self):
        """测试时效性评估"""
        assessor = QualityAssessment()
        
        # 新知识
        fresh_knowledge = Knowledge(
            title="新知识",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=KnowledgeMetadata(source="test", author="test", domain="test"),
            updated_at=datetime.now()
        )
        
        # 旧知识
        old_knowledge = Knowledge(
            title="旧知识",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=KnowledgeMetadata(source="test", author="test", domain="test"),
            updated_at=datetime.now() - timedelta(days=400)
        )
        
        fresh_score = assessor._assess_freshness(fresh_knowledge)
        old_score = assessor._assess_freshness(old_knowledge)
        
        assert fresh_score > old_score


@pytest.mark.asyncio
class TestKnowledgeService:
    """知识库服务测试"""
    
    @pytest.fixture
    def mock_services(self):
        """模拟依赖服务"""
        with patch('src.services.knowledge_service.VectorService') as mock_vector, \
             patch('src.services.knowledge_service.EmbeddingService') as mock_embedding:
            
            mock_vector_instance = Mock()
            mock_vector_instance.search = AsyncMock(return_value=[])
            mock_vector_instance.add_vector = AsyncMock()
            mock_vector.return_value = mock_vector_instance
            
            mock_embedding_instance = Mock()
            mock_embedding_instance.get_embedding = AsyncMock(return_value=[0.1] * 1024)
            mock_embedding.return_value = mock_embedding_instance
            
            yield mock_vector_instance, mock_embedding_instance
    
    @pytest.fixture
    def knowledge_service(self, mock_services):
        """知识库服务实例"""
        return KnowledgeService()
    
    @pytest.fixture
    def sample_metadata(self):
        """示例元数据"""
        return KnowledgeMetadata(
            source="test_source",
            author="test_author",
            domain="test_domain",
            tags=["tag1", "tag2"]
        )
    
    async def test_create_knowledge(self, knowledge_service, sample_metadata):
        """测试创建知识"""
        title = "测试知识"
        content = "这是一个测试知识条目的内容。包含多个句子用于测试分块功能。"
        knowledge_type = KnowledgeType.DOCUMENT
        
        knowledge = await knowledge_service.create_knowledge(
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            metadata=sample_metadata
        )
        
        assert knowledge.title == title
        assert knowledge.content == content
        assert knowledge.type == knowledge_type
        assert knowledge.status == KnowledgeStatus.DRAFT
        assert len(knowledge.chunks) > 0
        assert knowledge.quality is not None
        assert knowledge.id in knowledge_service.knowledge_store
    
    async def test_update_knowledge(self, knowledge_service, sample_metadata):
        """测试更新知识"""
        # 先创建知识
        knowledge = await knowledge_service.create_knowledge(
            title="原标题",
            content="原内容",
            knowledge_type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata
        )
        
        # 更新知识
        update_request = KnowledgeUpdateRequest(
            title="新标题",
            content="新内容，更长的内容用于测试更新功能。",
            status=KnowledgeStatus.PUBLISHED
        )
        
        updated_knowledge = await knowledge_service.update_knowledge(
            knowledge.id,
            update_request
        )
        
        assert updated_knowledge.title == "新标题"
        assert updated_knowledge.content == "新内容，更长的内容用于测试更新功能。"
        assert updated_knowledge.status == KnowledgeStatus.PUBLISHED
        assert len(updated_knowledge.version_history) == 1
    
    async def test_delete_knowledge(self, knowledge_service, sample_metadata):
        """测试删除知识"""
        # 先创建知识
        knowledge = await knowledge_service.create_knowledge(
            title="待删除知识",
            content="内容",
            knowledge_type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata
        )
        
        knowledge_id = knowledge.id
        assert knowledge_id in knowledge_service.knowledge_store
        
        # 删除知识
        result = await knowledge_service.delete_knowledge(knowledge_id)
        
        assert result is True
        assert knowledge_id not in knowledge_service.knowledge_store
    
    def test_get_knowledge(self, knowledge_service, sample_metadata):
        """测试获取知识"""
        # 手动添加知识到存储
        knowledge = Knowledge(
            title="测试知识",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata
        )
        knowledge_service.knowledge_store[knowledge.id] = knowledge
        
        # 获取知识
        retrieved = knowledge_service.get_knowledge(knowledge.id)
        
        assert retrieved is not None
        assert retrieved.id == knowledge.id
        assert retrieved.usage.view_count == 1  # 访问计数应该增加
    
    def test_list_knowledge(self, knowledge_service, sample_metadata):
        """测试列出知识"""
        # 添加多个知识条目
        for i in range(5):
            knowledge = Knowledge(
                title=f"知识{i}",
                content=f"内容{i}",
                type=KnowledgeType.DOCUMENT,
                metadata=sample_metadata
            )
            knowledge_service.knowledge_store[knowledge.id] = knowledge
        
        # 列出所有知识
        knowledge_list = knowledge_service.list_knowledge()
        assert len(knowledge_list) == 5
        
        # 测试分页
        paginated = knowledge_service.list_knowledge(limit=2, offset=1)
        assert len(paginated) == 2
    
    def test_list_knowledge_with_filter(self, knowledge_service, sample_metadata):
        """测试带过滤器的知识列表"""
        # 添加不同类型的知识
        doc_knowledge = Knowledge(
            title="文档知识",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata,
            status=KnowledgeStatus.PUBLISHED
        )
        
        faq_knowledge = Knowledge(
            title="FAQ知识",
            content="内容",
            type=KnowledgeType.FAQ,
            metadata=sample_metadata,
            status=KnowledgeStatus.DRAFT
        )
        
        knowledge_service.knowledge_store[doc_knowledge.id] = doc_knowledge
        knowledge_service.knowledge_store[faq_knowledge.id] = faq_knowledge
        
        # 按类型过滤
        filter_params = KnowledgeSearchFilter(types=[KnowledgeType.DOCUMENT])
        filtered = knowledge_service.list_knowledge(filter_params=filter_params)
        
        assert len(filtered) == 1
        assert filtered[0].type == KnowledgeType.DOCUMENT
    
    async def test_search_knowledge(self, knowledge_service, sample_metadata, mock_services):
        """测试知识搜索"""
        mock_vector, mock_embedding = mock_services
        
        # 模拟向量搜索结果
        knowledge = Knowledge(
            title="搜索测试知识",
            content="这是用于搜索测试的知识内容",
            type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata
        )
        knowledge_service.knowledge_store[knowledge.id] = knowledge
        
        mock_vector.search.return_value = [
            {
                "knowledge_id": knowledge.id,
                "chunk_id": "test_chunk_id",
                "score": 0.8
            }
        ]
        
        # 执行搜索
        results = await knowledge_service.search_knowledge("搜索测试")
        
        assert len(results) > 0
        assert results[0].knowledge.id == knowledge.id
        assert 0 <= results[0].score <= 1
        assert 0 <= results[0].relevance <= 1
    
    def test_update_usage_statistics(self, knowledge_service, sample_metadata):
        """测试更新使用统计"""
        knowledge = Knowledge(
            title="统计测试知识",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata
        )
        knowledge_service.knowledge_store[knowledge.id] = knowledge
        
        # 更新引用统计
        knowledge_service.update_usage_statistics(knowledge.id, "reference")
        assert knowledge.usage.reference_count == 1
        
        # 更新反馈统计
        knowledge_service.update_usage_statistics(knowledge.id, "feedback", True)
        assert knowledge.usage.feedback_count == 1
        assert knowledge.usage.positive_feedback == 1
        
        knowledge_service.update_usage_statistics(knowledge.id, "feedback", False)
        assert knowledge.usage.feedback_count == 2
        assert knowledge.usage.negative_feedback == 1
    
    async def test_batch_quality_assessment(self, knowledge_service, sample_metadata):
        """测试批量质量评估"""
        # 添加多个知识条目
        for i in range(3):
            knowledge = Knowledge(
                title=f"质量测试知识{i}",
                content=f"内容{i}" * 20,
                type=KnowledgeType.DOCUMENT,
                metadata=sample_metadata
            )
            knowledge_service.knowledge_store[knowledge.id] = knowledge
        
        # 执行批量评估
        results = await knowledge_service.batch_quality_assessment()
        
        assert len(results) == 3
        for quality in results.values():
            assert isinstance(quality, QualityMetrics)
            assert 0 <= quality.overall_score <= 1
    
    def test_get_knowledge_statistics(self, knowledge_service, sample_metadata):
        """测试获取知识库统计"""
        # 添加不同类型和状态的知识
        doc_knowledge = Knowledge(
            title="文档",
            content="内容",
            type=KnowledgeType.DOCUMENT,
            metadata=sample_metadata,
            status=KnowledgeStatus.PUBLISHED
        )
        
        faq_knowledge = Knowledge(
            title="FAQ",
            content="内容",
            type=KnowledgeType.FAQ,
            metadata=sample_metadata,
            status=KnowledgeStatus.DRAFT
        )
        
        knowledge_service.knowledge_store[doc_knowledge.id] = doc_knowledge
        knowledge_service.knowledge_store[faq_knowledge.id] = faq_knowledge
        
        # 获取统计信息
        stats = knowledge_service.get_knowledge_statistics()
        
        assert stats["total_knowledge"] == 2
        assert stats["by_type"][KnowledgeType.DOCUMENT] == 1
        assert stats["by_type"][KnowledgeType.FAQ] == 1
        assert stats["by_status"][KnowledgeStatus.PUBLISHED] == 1
        assert stats["by_status"][KnowledgeStatus.DRAFT] == 1
        assert "average_quality" in stats
        assert "total_chunks" in stats


if __name__ == "__main__":
    pytest.main([__file__])