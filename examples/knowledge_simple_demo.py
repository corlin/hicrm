"""
知识库管理系统简化演示
Knowledge Management System Simple Demo

这个演示不依赖向量服务和嵌入服务，专注于展示知识模型的功能。
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 导入知识库相关模块
from src.models.knowledge import (
    Knowledge, KnowledgeType, KnowledgeStatus, KnowledgeMetadata,
    KnowledgeSearchFilter, KnowledgeUpdateRequest, QualityMetrics,
    UsageStatistics, KnowledgeChunk, KnowledgeRelation
)
from src.services.knowledge_service import DocumentParser, QualityAssessment


class SimpleKnowledgeDemo:
    """简化的知识库演示类"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.quality_assessor = QualityAssessment()
        self.knowledge_store: Dict[str, Knowledge] = {}
        
    def run_demo(self):
        """运行演示"""
        print("=" * 60)
        print("知识库管理系统简化演示")
        print("Knowledge Management System Simple Demo")
        print("=" * 60)
        
        # 1. 文档解析演示
        self.demo_document_parsing()
        
        # 2. 知识模型演示
        knowledge_list = self.demo_knowledge_models()
        
        # 3. 质量评估演示
        self.demo_quality_assessment(knowledge_list)
        
        # 4. 搜索过滤演示
        self.demo_search_filtering(knowledge_list)
        
        # 5. 使用统计演示
        self.demo_usage_statistics(knowledge_list)
        
        print("\n" + "=" * 60)
        print("演示完成！Demo Complete!")
        print("=" * 60)
    
    def demo_document_parsing(self):
        """文档解析演示"""
        print("\n📄 1. 文档解析演示 (Document Parsing Demo)")
        print("-" * 40)
        
        # 示例文档内容
        sample_content = """
        客户关系管理系统（CRM）是企业管理客户信息和客户关系的重要工具。
        通过CRM系统，企业可以更好地了解客户需求，提高客户满意度。
        现代CRM系统通常包括销售管理、市场营销、客户服务等功能模块。
        人工智能技术的应用使得CRM系统能够提供更智能的客户分析和预测。
        企业应该根据自身业务特点选择合适的CRM解决方案。
        """
        
        print(f"原始文档内容：\n{sample_content.strip()}")
        
        # 文档分块
        chunks = self.parser.parse_text(sample_content, chunk_size=100, overlap=20)
        print(f"\n分块结果：共 {len(chunks)} 个块")
        
        for i, chunk in enumerate(chunks):
            print(f"\n块 {i+1}:")
            print(f"  ID: {chunk.id}")
            print(f"  内容: {chunk.content[:50]}...")
            print(f"  位置: {chunk.start_position}-{chunk.end_position}")
            print(f"  元数据: {chunk.metadata}")
        
        # 关键词提取
        keywords = self.parser.extract_keywords(sample_content, max_keywords=8)
        print(f"\n提取的关键词: {keywords}")
    
    def demo_knowledge_models(self) -> List[Knowledge]:
        """知识模型演示"""
        print("\n🔨 2. 知识模型演示 (Knowledge Models Demo)")
        print("-" * 40)
        
        knowledge_list = []
        
        # 创建不同类型的知识条目
        knowledge_data = [
            {
                "title": "CRM系统实施指南",
                "content": """
                CRM系统实施是一个复杂的过程，需要考虑多个方面。
                首先，企业需要明确CRM系统的目标和需求。
                其次，选择合适的CRM软件和供应商。
                然后，制定详细的实施计划和时间表。
                最后，进行系统测试和用户培训。
                成功的CRM实施需要管理层的支持和员工的配合。
                """,
                "type": KnowledgeType.BEST_PRACTICE,
                "domain": "CRM实施",
                "tags": ["CRM", "实施", "最佳实践"]
            },
            {
                "title": "客户数据管理常见问题",
                "content": """
                Q: 如何确保客户数据的准确性？
                A: 建立数据验证规则，定期清理重复数据，培训员工正确录入。
                
                Q: 客户数据安全如何保障？
                A: 实施访问控制，数据加密，定期备份，遵循数据保护法规。
                
                Q: 如何处理客户数据更新？
                A: 建立数据更新流程，设置自动同步机制，维护数据变更日志。
                """,
                "type": KnowledgeType.FAQ,
                "domain": "数据管理",
                "tags": ["FAQ", "数据管理", "客户数据"]
            },
            {
                "title": "销售流程标准模板",
                "content": """
                标准销售流程包括以下步骤：
                1. 潜在客户识别和资格认定
                2. 需求分析和解决方案设计
                3. 商务谈判和合同签署
                4. 项目实施和交付
                5. 售后服务和客户维护
                
                每个步骤都有相应的检查点和交付物。
                销售团队应严格按照流程执行，确保销售质量。
                """,
                "type": KnowledgeType.TEMPLATE,
                "domain": "销售管理",
                "tags": ["销售流程", "模板", "标准化"]
            }
        ]
        
        for i, data in enumerate(knowledge_data):
            print(f"\n创建知识条目 {i+1}: {data['title']}")
            
            # 创建元数据
            metadata = KnowledgeMetadata(
                source="demo_system",
                author="demo_user",
                domain=data["domain"],
                tags=data["tags"]
            )
            
            # 解析文档并创建块
            chunks = self.parser.parse_text(data["content"])
            
            # 创建知识关系（示例）
            relationships = []
            if i > 0:  # 为非第一个知识创建关系
                relationships.append(
                    KnowledgeRelation(
                        related_id=knowledge_list[0].id,
                        relation_type="相关",
                        strength=0.7,
                        description=f"与{knowledge_list[0].title}相关"
                    )
                )
            
            # 创建知识实体
            knowledge = Knowledge(
                title=data["title"],
                content=data["content"],
                type=data["type"],
                status=KnowledgeStatus.PUBLISHED,
                chunks=chunks,
                metadata=metadata,
                relationships=relationships,
                categories=data["tags"],
                published_at=datetime.now()
            )
            
            # 评估质量
            quality = self.quality_assessor.assess_quality(knowledge)
            knowledge.quality = quality
            
            # 存储知识
            self.knowledge_store[knowledge.id] = knowledge
            knowledge_list.append(knowledge)
            
            print(f"  ID: {knowledge.id}")
            print(f"  类型: {knowledge.type}")
            print(f"  状态: {knowledge.status}")
            print(f"  块数量: {len(knowledge.chunks)}")
            print(f"  关键词: {knowledge.metadata.keywords[:5]}")
            print(f"  关系数量: {len(knowledge.relationships)}")
            
            if knowledge.quality:
                print(f"  质量评分: {knowledge.quality.overall_score:.2f}")
        
        return knowledge_list
    
    def demo_quality_assessment(self, knowledge_list: List[Knowledge]):
        """质量评估演示"""
        print("\n⭐ 3. 质量评估演示 (Quality Assessment Demo)")
        print("-" * 40)
        
        print(f"对 {len(knowledge_list)} 个知识条目进行质量评估:")
        
        total_quality = 0
        for knowledge in knowledge_list:
            if knowledge.quality:
                quality = knowledge.quality
                print(f"\n📋 {knowledge.title}")
                print(f"  综合评分: {quality.overall_score:.2f}")
                print(f"  准确性: {quality.accuracy_score:.2f}")
                print(f"  完整性: {quality.completeness_score:.2f}")
                print(f"  相关性: {quality.relevance_score:.2f}")
                print(f"  时效性: {quality.freshness_score:.2f}")
                print(f"  使用频率: {quality.usage_score:.2f}")
                print(f"  评估时间: {quality.last_evaluated}")
                
                total_quality += quality.overall_score
        
        avg_quality = total_quality / len(knowledge_list) if knowledge_list else 0
        print(f"\n平均质量评分: {avg_quality:.2f}")
    
    def demo_search_filtering(self, knowledge_list: List[Knowledge]):
        """搜索过滤演示"""
        print("\n🎯 4. 搜索过滤演示 (Search Filtering Demo)")
        print("-" * 40)
        
        # 按类型过滤
        print("按知识类型过滤:")
        faq_knowledge = [k for k in knowledge_list if k.type == KnowledgeType.FAQ]
        best_practice_knowledge = [k for k in knowledge_list if k.type == KnowledgeType.BEST_PRACTICE]
        
        print(f"  FAQ类型: {len(faq_knowledge)} 个")
        for k in faq_knowledge:
            print(f"    - {k.title}")
        
        print(f"  最佳实践类型: {len(best_practice_knowledge)} 个")
        for k in best_practice_knowledge:
            print(f"    - {k.title}")
        
        # 按标签过滤
        print("\n按标签过滤 (包含'CRM'):")
        crm_knowledge = [k for k in knowledge_list if 'CRM' in k.metadata.tags]
        
        for k in crm_knowledge:
            print(f"  - {k.title} (标签: {k.metadata.tags})")
        
        # 按质量分数过滤
        print("\n按质量分数过滤 (>0.7):")
        high_quality_knowledge = [k for k in knowledge_list if k.quality and k.quality.overall_score > 0.7]
        
        for k in high_quality_knowledge:
            quality_score = k.quality.overall_score if k.quality else 0
            print(f"  - {k.title} (质量: {quality_score:.2f})")
        
        # 演示搜索过滤器模型
        print("\n搜索过滤器模型演示:")
        
        # 创建复合过滤器
        complex_filter = KnowledgeSearchFilter(
            types=[KnowledgeType.FAQ, KnowledgeType.BEST_PRACTICE],
            status=[KnowledgeStatus.PUBLISHED],
            tags=["CRM"],
            min_quality_score=0.7
        )
        
        print(f"  过滤器类型: {complex_filter.types}")
        print(f"  过滤器状态: {complex_filter.status}")
        print(f"  过滤器标签: {complex_filter.tags}")
        print(f"  最小质量分数: {complex_filter.min_quality_score}")
        
        # 应用过滤器
        filtered_knowledge = []
        for k in knowledge_list:
            # 检查类型
            if complex_filter.types and k.type not in complex_filter.types:
                continue
            # 检查状态
            if complex_filter.status and k.status not in complex_filter.status:
                continue
            # 检查标签
            if complex_filter.tags and not any(tag in k.metadata.tags for tag in complex_filter.tags):
                continue
            # 检查质量
            if complex_filter.min_quality_score and k.quality and k.quality.overall_score < complex_filter.min_quality_score:
                continue
            
            filtered_knowledge.append(k)
        
        print(f"  过滤结果: {len(filtered_knowledge)} 个知识条目")
        for k in filtered_knowledge:
            print(f"    - {k.title}")
    
    def demo_usage_statistics(self, knowledge_list: List[Knowledge]):
        """使用统计演示"""
        print("\n📊 5. 使用统计演示 (Usage Statistics Demo)")
        print("-" * 40)
        
        # 模拟一些使用活动
        for i, knowledge in enumerate(knowledge_list):
            # 模拟不同的使用模式
            knowledge.usage.view_count = (i + 1) * 10
            knowledge.usage.search_count = (i + 1) * 5
            knowledge.usage.reference_count = (i + 1) * 2
            knowledge.usage.feedback_count = (i + 1) * 1
            knowledge.usage.positive_feedback = knowledge.usage.feedback_count - 1 if knowledge.usage.feedback_count > 1 else knowledge.usage.feedback_count
            knowledge.usage.negative_feedback = 1 if knowledge.usage.feedback_count > 1 else 0
            knowledge.usage.last_accessed = datetime.now() - timedelta(days=i)
        
        # 显示统计信息
        print("使用统计:")
        for knowledge in knowledge_list:
            usage = knowledge.usage
            print(f"\n📋 {knowledge.title}")
            print(f"  查看次数: {usage.view_count}")
            print(f"  搜索命中: {usage.search_count}")
            print(f"  被引用: {usage.reference_count}")
            print(f"  反馈总数: {usage.feedback_count}")
            print(f"  正面反馈: {usage.positive_feedback}")
            print(f"  负面反馈: {usage.negative_feedback}")
            print(f"  最后访问: {usage.last_accessed}")
            
            if usage.feedback_count > 0:
                positive_rate = usage.positive_feedback / usage.feedback_count
                print(f"  正面反馈率: {positive_rate:.1%}")
        
        # 整体统计
        total_views = sum(k.usage.view_count for k in knowledge_list)
        total_searches = sum(k.usage.search_count for k in knowledge_list)
        total_references = sum(k.usage.reference_count for k in knowledge_list)
        
        print(f"\n📈 整体统计:")
        print(f"  总知识数: {len(knowledge_list)}")
        print(f"  总查看次数: {total_views}")
        print(f"  总搜索次数: {total_searches}")
        print(f"  总引用次数: {total_references}")
        
        # 按类型统计
        type_stats = {}
        for k in knowledge_list:
            if k.type not in type_stats:
                type_stats[k.type] = 0
            type_stats[k.type] += 1
        
        print(f"  按类型分布: {dict(type_stats)}")
        
        # 按状态统计
        status_stats = {}
        for k in knowledge_list:
            if k.status not in status_stats:
                status_stats[k.status] = 0
            status_stats[k.status] += 1
        
        print(f"  按状态分布: {dict(status_stats)}")
        
        # 平均质量
        quality_scores = [k.quality.overall_score for k in knowledge_list if k.quality]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        print(f"  平均质量: {avg_quality:.2f}")
        
        # 总块数
        total_chunks = sum(len(k.chunks) for k in knowledge_list)
        print(f"  总块数: {total_chunks}")


def run_simple_demo():
    """运行简化演示"""
    demo = SimpleKnowledgeDemo()
    demo.run_demo()


if __name__ == "__main__":
    run_simple_demo()