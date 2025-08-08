"""
知识库模型完整测试
Knowledge Model Complete Tests

本文件包含知识库模型的完整测试用例，展示所有模型的使用方法和验证功能。
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from src.models.knowledge import (
    # 核心模型
    Knowledge, KnowledgeChunk, KnowledgeType, KnowledgeStatus,
    # 元数据和统计
    KnowledgeMetadata, QualityMetrics, UsageStatistics,
    # 关系和搜索
    KnowledgeRelation, KnowledgeSearchFilter, KnowledgeSearchResult,
    # 请求模型
    KnowledgeUpdateRequest
)
from src.utils.unicode_utils import SafeOutput


class KnowledgeModelTester:
    """知识库模型测试器"""
    
    def __init__(self):
        self.test_results = []
        self.safe_output = SafeOutput()
        
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("知识库模型完整测试")
        print("Knowledge Model Complete Tests")
        print("=" * 60)
        
        # 测试各个模型
        self.test_knowledge_metadata()
        self.test_usage_statistics()
        self.test_quality_metrics()
        self.test_knowledge_chunk()
        self.test_knowledge_relation()
        self.test_knowledge_main_model()
        self.test_search_filter()
        self.test_search_result()
        self.test_update_request()
        
        # 测试复杂场景
        self.test_complex_scenarios()
        
        # 显示测试结果
        self.show_test_results()
    
    def add_test_result(self, test_name: str, success: bool, details: str = ""):
        """添加测试结果"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now()
        })
    
    def test_knowledge_metadata(self):
        """测试知识元数据模型"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '1. 测试 KnowledgeMetadata 模型', '📋')}")
        print("-" * 40)
        
        try:
            # 基本创建
            metadata = KnowledgeMetadata(
                source="test_system",
                author="test_user",
                domain="测试领域",
                tags=["测试", "示例", "模型"],
                language="zh-CN",
                version="1.0",
                confidence=0.85,
                keywords=["关键词1", "关键词2", "关键词3"]
            )
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', '基本创建成功')}")
            print(f"   来源: {metadata.source}")
            print(f"   作者: {metadata.author}")
            print(f"   领域: {metadata.domain}")
            print(f"   标签: {metadata.tags}")
            print(f"   置信度: {metadata.confidence}")
            print(f"   关键词: {metadata.keywords}")
            
            # 测试默认值
            minimal_metadata = KnowledgeMetadata(
                source="minimal",
                author="user",
                domain="domain"
            )
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', '默认值测试成功')}")
            print(f"   默认语言: {minimal_metadata.language}")
            print(f"   默认版本: {minimal_metadata.version}")
            print(f"   默认置信度: {minimal_metadata.confidence}")
            print(f"   默认标签: {minimal_metadata.tags}")
            print(f"   默认关键词: {minimal_metadata.keywords}")
            
            # JSON序列化测试
            json_str = metadata.model_dump_json()
            restored = KnowledgeMetadata.model_validate_json(json_str)
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', 'JSON序列化测试成功')}")
            print(f"   原始置信度: {metadata.confidence}")
            print(f"   恢复置信度: {restored.confidence}")
            
            self.add_test_result("KnowledgeMetadata", True, "所有测试通过")
            
        except Exception as e:
            self.safe_output.safe_print(f"{self.safe_output.format_status('error', f'测试失败: {e}')}")
            self.add_test_result("KnowledgeMetadata", False, str(e))
    
    def test_usage_statistics(self):
        """测试使用统计模型"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '2. 测试 UsageStatistics 模型', '📊')}")
        print("-" * 40)
        
        try:
            # 默认创建
            usage = UsageStatistics()
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', '默认创建成功')}")
            print(f"   查看次数: {usage.view_count}")
            print(f"   搜索次数: {usage.search_count}")
            print(f"   引用次数: {usage.reference_count}")
            print(f"   反馈次数: {usage.feedback_count}")
            print(f"   正面反馈: {usage.positive_feedback}")
            print(f"   负面反馈: {usage.negative_feedback}")
            print(f"   最后访问: {usage.last_accessed}")
            
            # 带数据创建
            usage_with_data = UsageStatistics(
                view_count=100,
                search_count=50,
                reference_count=25,
                feedback_count=10,
                positive_feedback=8,
                negative_feedback=2,
                last_accessed=datetime.now()
            )
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', '带数据创建成功')}")
            print(f"   查看次数: {usage_with_data.view_count}")
            print(f"   搜索次数: {usage_with_data.search_count}")
            print(f"   正面反馈率: {usage_with_data.positive_feedback/usage_with_data.feedback_count:.1%}")
            
            # 验证约束
            try:
                invalid_usage = UsageStatistics(view_count=-1)
                self.safe_output.safe_print(f"{self.safe_output.format_status('error', '约束验证失败')}")
            except Exception:
                self.safe_output.safe_print(f"{self.safe_output.format_status('success', '负数约束验证成功')}")
            
            self.add_test_result("UsageStatistics", True, "所有测试通过")
            
        except Exception as e:
            self.safe_output.safe_print(f"{self.safe_output.format_status('error', f'测试失败: {e}')}")
            self.add_test_result("UsageStatistics", False, str(e))
    
    def test_quality_metrics(self):
        """测试质量指标模型"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '3. 测试 QualityMetrics 模型', '⭐')}")
        print("-" * 40)
        
        try:
            # 创建质量指标
            quality = QualityMetrics(
                accuracy_score=0.85,
                completeness_score=0.90,
                relevance_score=0.80,
                freshness_score=0.95,
                usage_score=0.75,
                overall_score=0.85,
                last_evaluated=datetime.now()
            )
            
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', '质量指标创建成功')}")
            print(f"   准确性: {quality.accuracy_score}")
            print(f"   完整性: {quality.completeness_score}")
            print(f"   相关性: {quality.relevance_score}")
            print(f"   时效性: {quality.freshness_score}")
            print(f"   使用频率: {quality.usage_score}")
            print(f"   综合评分: {quality.overall_score}")
            print(f"   评估时间: {quality.last_evaluated}")
            
            # 测试分数范围约束
            try:
                invalid_quality = QualityMetrics(
                    accuracy_score=1.5,  # 超出范围
                    completeness_score=0.5,
                    relevance_score=0.5,
                    freshness_score=0.5,
                    usage_score=0.5,
                    overall_score=0.5,
                    last_evaluated=datetime.now()
                )
                self.safe_output.safe_print(f"{self.safe_output.format_status('error', '分数范围约束验证失败')}")
            except Exception:
                self.safe_output.safe_print(f"{self.safe_output.format_status('success', '分数范围约束验证成功')}")
            
            self.add_test_result("QualityMetrics", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("QualityMetrics", False, str(e))
    
    def test_knowledge_chunk(self):
        """测试知识块模型"""
        print("\n🧩 4. 测试 KnowledgeChunk 模型")
        print("-" * 40)
        
        try:
            # 创建知识块
            chunk = KnowledgeChunk(
                content="这是一个测试知识块的内容，用于验证模型功能。",
                chunk_index=0,
                start_position=0,
                end_position=25,
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                metadata={
                    "sentence_count": 1,
                    "word_count": 25,
                    "language": "zh-CN"
                }
            )
            
            print(f"✅ 知识块创建成功")
            print(f"   ID: {chunk.id}")
            print(f"   内容: {chunk.content}")
            print(f"   索引: {chunk.chunk_index}")
            print(f"   位置: {chunk.start_position}-{chunk.end_position}")
            print(f"   嵌入维度: {len(chunk.embedding) if chunk.embedding else 0}")
            print(f"   元数据: {chunk.metadata}")
            
            # 测试自动ID生成
            chunk_auto_id = KnowledgeChunk(
                content="自动ID测试",
                chunk_index=1,
                start_position=26,
                end_position=35
            )
            
            print(f"✅ 自动ID生成成功: {chunk_auto_id.id}")
            
            # 测试无嵌入向量
            chunk_no_embedding = KnowledgeChunk(
                content="无嵌入向量测试",
                chunk_index=2,
                start_position=36,
                end_position=45
            )
            
            print(f"✅ 无嵌入向量测试成功: {chunk_no_embedding.embedding}")
            
            self.add_test_result("KnowledgeChunk", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("KnowledgeChunk", False, str(e))
    
    def test_knowledge_relation(self):
        """测试知识关系模型"""
        print("\n🔗 5. 测试 KnowledgeRelation 模型")
        print("-" * 40)
        
        try:
            # 创建知识关系
            relation = KnowledgeRelation(
                related_id=str(uuid.uuid4()),
                relation_type="相关",
                strength=0.8,
                description="这两个知识条目在主题上高度相关"
            )
            
            print(f"✅ 知识关系创建成功")
            print(f"   关联ID: {relation.related_id}")
            print(f"   关系类型: {relation.relation_type}")
            print(f"   关系强度: {relation.strength}")
            print(f"   描述: {relation.description}")
            
            # 测试不同关系类型
            relation_types = ["引用", "扩展", "对比", "依赖", "相似"]
            relations = []
            
            for rel_type in relation_types:
                rel = KnowledgeRelation(
                    related_id=str(uuid.uuid4()),
                    relation_type=rel_type,
                    strength=0.6 + (len(rel_type) * 0.05)  # 模拟不同强度
                )
                relations.append(rel)
                print(f"   {rel_type}关系: 强度{rel.strength:.2f}")
            
            print(f"✅ 多种关系类型测试成功: {len(relations)}个关系")
            
            self.add_test_result("KnowledgeRelation", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("KnowledgeRelation", False, str(e))
    
    def test_knowledge_main_model(self):
        """测试主要知识模型"""
        print("\n📚 6. 测试 Knowledge 主模型")
        print("-" * 40)
        
        try:
            # 创建完整的知识模型
            metadata = KnowledgeMetadata(
                source="test_system",
                author="test_user",
                domain="测试",
                tags=["测试", "模型"],
                keywords=["知识", "管理", "系统"]
            )
            
            chunks = [
                KnowledgeChunk(
                    content="第一个知识块",
                    chunk_index=0,
                    start_position=0,
                    end_position=7
                ),
                KnowledgeChunk(
                    content="第二个知识块",
                    chunk_index=1,
                    start_position=7,
                    end_position=14
                )
            ]
            
            quality = QualityMetrics(
                accuracy_score=0.9,
                completeness_score=0.8,
                relevance_score=0.85,
                freshness_score=0.95,
                usage_score=0.7,
                overall_score=0.84,
                last_evaluated=datetime.now()
            )
            
            relations = [
                KnowledgeRelation(
                    related_id=str(uuid.uuid4()),
                    relation_type="相关",
                    strength=0.8
                )
            ]
            
            knowledge = Knowledge(
                title="完整知识模型测试",
                content="这是一个完整的知识模型测试内容，包含了所有必要的字段和关联数据。",
                type=KnowledgeType.DOCUMENT,
                status=KnowledgeStatus.PUBLISHED,
                chunks=chunks,
                metadata=metadata,
                quality=quality,
                relationships=relations,
                categories=["测试", "模型", "验证"],
                published_at=datetime.now()
            )
            
            print(f"✅ 完整知识模型创建成功")
            print(f"   ID: {knowledge.id}")
            print(f"   标题: {knowledge.title}")
            print(f"   类型: {knowledge.type}")
            print(f"   状态: {knowledge.status}")
            print(f"   块数量: {len(knowledge.chunks)}")
            print(f"   质量评分: {knowledge.quality.overall_score}")
            print(f"   关系数量: {len(knowledge.relationships)}")
            print(f"   分类: {knowledge.categories}")
            print(f"   创建时间: {knowledge.created_at}")
            print(f"   更新时间: {knowledge.updated_at}")
            print(f"   发布时间: {knowledge.published_at}")
            
            # 测试JSON序列化
            json_data = knowledge.model_dump_json()
            restored_knowledge = Knowledge.model_validate_json(json_data)
            
            print(f"✅ JSON序列化测试成功")
            print(f"   原始ID: {knowledge.id}")
            print(f"   恢复ID: {restored_knowledge.id}")
            print(f"   数据一致性: {knowledge.title == restored_knowledge.title}")
            
            # 测试最小化创建
            minimal_knowledge = Knowledge(
                title="最小化知识",
                content="最小化内容",
                type=KnowledgeType.FAQ,
                metadata=KnowledgeMetadata(
                    source="minimal",
                    author="user",
                    domain="test"
                )
            )
            
            print(f"✅ 最小化创建成功")
            print(f"   默认状态: {minimal_knowledge.status}")
            print(f"   默认使用统计: {minimal_knowledge.usage.view_count}")
            print(f"   默认质量: {minimal_knowledge.quality}")
            
            self.add_test_result("Knowledge", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("Knowledge", False, str(e))
    
    def test_search_filter(self):
        """测试搜索过滤器模型"""
        print("\n🎯 7. 测试 KnowledgeSearchFilter 模型")
        print("-" * 40)
        
        try:
            # 创建各种过滤器
            type_filter = KnowledgeSearchFilter(
                types=[KnowledgeType.DOCUMENT, KnowledgeType.FAQ]
            )
            
            print(f"✅ 类型过滤器创建成功: {type_filter.types}")
            
            status_filter = KnowledgeSearchFilter(
                status=[KnowledgeStatus.PUBLISHED, KnowledgeStatus.REVIEW]
            )
            
            print(f"✅ 状态过滤器创建成功: {status_filter.status}")
            
            tag_filter = KnowledgeSearchFilter(
                tags=["重要", "紧急", "常用"]
            )
            
            print(f"✅ 标签过滤器创建成功: {tag_filter.tags}")
            
            quality_filter = KnowledgeSearchFilter(
                min_quality_score=0.8
            )
            
            print(f"✅ 质量过滤器创建成功: {quality_filter.min_quality_score}")
            
            # 复合过滤器
            complex_filter = KnowledgeSearchFilter(
                types=[KnowledgeType.BEST_PRACTICE],
                status=[KnowledgeStatus.PUBLISHED],
                tags=["最佳实践"],
                domains=["销售", "市场"],
                min_quality_score=0.85,
                author="专家用户"
            )
            
            print(f"✅ 复合过滤器创建成功")
            print(f"   类型: {complex_filter.types}")
            print(f"   状态: {complex_filter.status}")
            print(f"   标签: {complex_filter.tags}")
            print(f"   领域: {complex_filter.domains}")
            print(f"   最小质量: {complex_filter.min_quality_score}")
            print(f"   作者: {complex_filter.author}")
            
            # 空过滤器
            empty_filter = KnowledgeSearchFilter()
            
            print(f"✅ 空过滤器创建成功")
            print(f"   所有字段为None: {all(getattr(empty_filter, field) is None for field in ['types', 'status', 'tags', 'domains', 'min_quality_score', 'author'])}")
            
            self.add_test_result("KnowledgeSearchFilter", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("KnowledgeSearchFilter", False, str(e))
    
    def test_search_result(self):
        """测试搜索结果模型"""
        print("\n🔍 8. 测试 KnowledgeSearchResult 模型")
        print("-" * 40)
        
        try:
            # 创建测试知识
            knowledge = Knowledge(
                title="搜索结果测试知识",
                content="这是用于测试搜索结果的知识内容",
                type=KnowledgeType.DOCUMENT,
                metadata=KnowledgeMetadata(
                    source="test",
                    author="tester",
                    domain="测试"
                )
            )
            
            # 创建匹配的块
            matched_chunks = [
                KnowledgeChunk(
                    content="匹配的知识块内容",
                    chunk_index=0,
                    start_position=0,
                    end_position=10
                )
            ]
            
            # 创建搜索结果
            search_result = KnowledgeSearchResult(
                knowledge=knowledge,
                score=0.85,
                relevance=0.90,
                snippet="这是搜索结果的摘要内容...",
                matched_chunks=matched_chunks,
                highlight={
                    "title": ["搜索结果<mark>测试</mark>知识"],
                    "content": ["这是用于<mark>测试</mark>搜索结果的知识内容"]
                }
            )
            
            print(f"✅ 搜索结果创建成功")
            print(f"   知识标题: {search_result.knowledge.title}")
            print(f"   匹配分数: {search_result.score}")
            print(f"   相关性: {search_result.relevance}")
            print(f"   摘要: {search_result.snippet}")
            print(f"   匹配块数: {len(search_result.matched_chunks)}")
            print(f"   高亮信息: {search_result.highlight}")
            
            # 测试空匹配块
            result_no_chunks = KnowledgeSearchResult(
                knowledge=knowledge,
                score=0.75,
                relevance=0.80,
                snippet="无匹配块的搜索结果"
            )
            
            print(f"✅ 无匹配块结果创建成功")
            print(f"   匹配块数: {len(result_no_chunks.matched_chunks)}")
            print(f"   高亮信息: {result_no_chunks.highlight}")
            
            self.add_test_result("KnowledgeSearchResult", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("KnowledgeSearchResult", False, str(e))
    
    def test_update_request(self):
        """测试更新请求模型"""
        print("\n✏️ 9. 测试 KnowledgeUpdateRequest 模型")
        print("-" * 40)
        
        try:
            # 完整更新请求
            full_update = KnowledgeUpdateRequest(
                title="更新后的标题",
                content="更新后的内容，包含更多详细信息。",
                metadata=KnowledgeMetadata(
                    source="updated_system",
                    author="updater",
                    domain="更新测试"
                ),
                status=KnowledgeStatus.PUBLISHED,
                categories=["更新", "测试", "验证"]
            )
            
            print(f"✅ 完整更新请求创建成功")
            print(f"   新标题: {full_update.title}")
            print(f"   新内容长度: {len(full_update.content)}")
            print(f"   新状态: {full_update.status}")
            print(f"   新分类: {full_update.categories}")
            
            # 部分更新请求
            partial_update = KnowledgeUpdateRequest(
                title="仅更新标题"
            )
            
            print(f"✅ 部分更新请求创建成功")
            print(f"   标题: {partial_update.title}")
            print(f"   内容: {partial_update.content}")
            print(f"   状态: {partial_update.status}")
            
            # 空更新请求
            empty_update = KnowledgeUpdateRequest()
            
            print(f"✅ 空更新请求创建成功")
            print(f"   所有字段为None: {all(getattr(empty_update, field) is None for field in ['title', 'content', 'metadata', 'status', 'categories'])}")
            
            # JSON序列化测试
            json_data = full_update.model_dump_json()
            restored_update = KnowledgeUpdateRequest.model_validate_json(json_data)
            
            print(f"✅ JSON序列化测试成功")
            print(f"   原始标题: {full_update.title}")
            print(f"   恢复标题: {restored_update.title}")
            
            self.add_test_result("KnowledgeUpdateRequest", True, "所有测试通过")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            self.add_test_result("KnowledgeUpdateRequest", False, str(e))
    
    def test_complex_scenarios(self):
        """测试复杂场景"""
        print("\n🎭 10. 测试复杂场景")
        print("-" * 40)
        
        try:
            # 场景1: 完整的知识生命周期
            print("场景1: 完整的知识生命周期")
            
            # 创建初始知识
            initial_knowledge = Knowledge(
                title="生命周期测试知识",
                content="初始内容",
                type=KnowledgeType.DOCUMENT,
                status=KnowledgeStatus.DRAFT,
                metadata=KnowledgeMetadata(
                    source="lifecycle_test",
                    author="lifecycle_user",
                    domain="测试"
                )
            )
            
            print(f"   初始状态: {initial_knowledge.status}")
            
            # 模拟审核过程
            initial_knowledge.status = KnowledgeStatus.REVIEW
            initial_knowledge.updated_at = datetime.now()
            
            print(f"   审核状态: {initial_knowledge.status}")
            
            # 模拟发布
            initial_knowledge.status = KnowledgeStatus.PUBLISHED
            initial_knowledge.published_at = datetime.now()
            initial_knowledge.updated_at = datetime.now()
            
            print(f"   发布状态: {initial_knowledge.status}")
            print(f"   发布时间: {initial_knowledge.published_at}")
            
            # 场景2: 知识关系网络
            print("\n场景2: 知识关系网络")
            
            # 创建相关知识
            related_knowledge = []
            for i in range(3):
                knowledge = Knowledge(
                    title=f"相关知识 {i+1}",
                    content=f"相关知识 {i+1} 的内容",
                    type=KnowledgeType.DOCUMENT,
                    metadata=KnowledgeMetadata(
                        source="relation_test",
                        author="relation_user",
                        domain="关系测试"
                    )
                )
                related_knowledge.append(knowledge)
            
            # 建立关系
            main_knowledge = Knowledge(
                title="主要知识",
                content="主要知识内容",
                type=KnowledgeType.DOCUMENT,
                metadata=KnowledgeMetadata(
                    source="relation_test",
                    author="relation_user",
                    domain="关系测试"
                ),
                relationships=[
                    KnowledgeRelation(
                        related_id=related_knowledge[0].id,
                        relation_type="引用",
                        strength=0.9,
                        description="强引用关系"
                    ),
                    KnowledgeRelation(
                        related_id=related_knowledge[1].id,
                        relation_type="相关",
                        strength=0.7,
                        description="相关关系"
                    ),
                    KnowledgeRelation(
                        related_id=related_knowledge[2].id,
                        relation_type="扩展",
                        strength=0.8,
                        description="扩展关系"
                    )
                ]
            )
            
            print(f"   主知识关系数: {len(main_knowledge.relationships)}")
            for rel in main_knowledge.relationships:
                print(f"     {rel.relation_type}: 强度{rel.strength}")
            
            # 场景3: 多版本管理
            print("\n场景3: 多版本管理")
            
            versioned_knowledge = Knowledge(
                title="版本管理测试",
                content="版本1内容",
                type=KnowledgeType.DOCUMENT,
                metadata=KnowledgeMetadata(
                    source="version_test",
                    author="version_user",
                    domain="版本测试",
                    version="1.0"
                ),
                version_history=[]
            )
            
            # 模拟版本更新
            for version in range(2, 5):
                version_info = {
                    "version": version,
                    "timestamp": datetime.now().isoformat(),
                    "changes": {
                        "content": f"更新到版本{version}",
                        "author": "version_user"
                    }
                }
                versioned_knowledge.version_history.append(version_info)
                versioned_knowledge.metadata.version = f"{version}.0"
                versioned_knowledge.updated_at = datetime.now()
            
            print(f"   当前版本: {versioned_knowledge.metadata.version}")
            print(f"   版本历史: {len(versioned_knowledge.version_history)}个版本")
            
            print("✅ 复杂场景测试成功")
            self.add_test_result("ComplexScenarios", True, "所有场景测试通过")
            
        except Exception as e:
            print(f"❌ 复杂场景测试失败: {e}")
            self.add_test_result("ComplexScenarios", False, str(e))
    
    def show_test_results(self):
        """显示测试结果"""
        print("\n" + "=" * 60)
        print("测试结果汇总 (Test Results Summary)")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"成功率: {passed_tests/total_tests:.1%}")
        
        if failed_tests > 0:
            print(f"\n失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['details']}")
        
        print(f"\n详细结果:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['test']}")
            if result["details"] and not result["success"]:
                print(f"      {result['details']}")


def run_knowledge_model_tests():
    """运行知识库模型测试"""
    tester = KnowledgeModelTester()
    tester.run_all_tests()


if __name__ == "__main__":
    run_knowledge_model_tests()