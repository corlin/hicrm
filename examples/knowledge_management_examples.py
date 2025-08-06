"""
知识库管理系统完整示例
Knowledge Management System Complete Examples

本示例展示了知识库管理系统的完整功能，包括：
1. 知识创建和管理
2. 文档解析和分块
3. 质量评估
4. 搜索和过滤
5. 使用统计
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 导入知识库相关模块
from src.models.knowledge import (
    Knowledge, KnowledgeType, KnowledgeStatus, KnowledgeMetadata,
    KnowledgeSearchFilter, KnowledgeUpdateRequest, QualityMetrics,
    UsageStatistics, KnowledgeChunk
)
from src.services.knowledge_service import (
    KnowledgeService, DocumentParser, QualityAssessment
)


class KnowledgeManagementDemo:
    """知识库管理演示类"""
    
    def __init__(self):
        self.knowledge_service = KnowledgeService()
        self.parser = DocumentParser()
        self.quality_assessor = QualityAssessment()
        
    async def run_complete_demo(self):
        """运行完整演示"""
        print("=" * 60)
        print("知识库管理系统完整演示")
        print("Knowledge Management System Complete Demo")
        print("=" * 60)
        
        # 1. 文档解析演示
        await self.demo_document_parsing()
        
        # 2. 知识创建演示
        knowledge_ids = await self.demo_knowledge_creation()
        
        # 3. 知识更新演示
        await self.demo_knowledge_update(knowledge_ids[0])
        
        # 4. 质量评估演示
        await self.demo_quality_assessment()
        
        # 5. 知识搜索演示
        await self.demo_knowledge_search()
        
        # 6. 使用统计演示
        await self.demo_usage_statistics(knowledge_ids)
        
        # 7. 批量操作演示
        await self.demo_batch_operations()
        
        # 8. 高级过滤演示
        await self.demo_advanced_filtering()
        
        print("\n" + "=" * 60)
        print("演示完成！Demo Complete!")
        print("=" * 60)
    
    async def demo_document_parsing(self):
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
            print(f"  内容: {chunk.content[:50]}...")
            print(f"  位置: {chunk.start_position}-{chunk.end_position}")
            print(f"  元数据: {chunk.metadata}")
        
        # 关键词提取
        keywords = self.parser.extract_keywords(sample_content, max_keywords=8)
        print(f"\n提取的关键词: {keywords}")
    
    async def demo_knowledge_creation(self) -> List[str]:
        """知识创建演示"""
        print("\n🔨 2. 知识创建演示 (Knowledge Creation Demo)")
        print("-" * 40)
        
        knowledge_ids = []
        
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
            
            metadata = KnowledgeMetadata(
                source="demo_system",
                author="demo_user",
                domain=data["domain"],
                tags=data["tags"]
            )
            
            knowledge = await self.knowledge_service.create_knowledge(
                title=data["title"],
                content=data["content"],
                knowledge_type=data["type"],
                metadata=metadata
            )
            
            knowledge_ids.append(knowledge.id)
            
            print(f"  ID: {knowledge.id}")
            print(f"  类型: {knowledge.type}")
            print(f"  状态: {knowledge.status}")
            print(f"  块数量: {len(knowledge.chunks)}")
            print(f"  关键词: {knowledge.metadata.keywords[:5]}")
            
            if knowledge.quality:
                print(f"  质量评分: {knowledge.quality.overall_score:.2f}")
        
        return knowledge_ids
    
    async def demo_knowledge_update(self, knowledge_id: str):
        """知识更新演示"""
        print("\n✏️ 3. 知识更新演示 (Knowledge Update Demo)")
        print("-" * 40)
        
        print(f"更新知识条目: {knowledge_id}")
        
        # 获取原始知识
        original = self.knowledge_service.get_knowledge(knowledge_id)
        if original:
            print(f"原始标题: {original.title}")
            print(f"原始状态: {original.status}")
            print(f"版本历史: {len(original.version_history)} 个版本")
        
        # 创建更新请求
        update_request = KnowledgeUpdateRequest(
            title="CRM系统实施指南 (更新版)",
            content=original.content + "\n\n补充内容：实施过程中要特别注意变更管理和风险控制。",
            status=KnowledgeStatus.PUBLISHED
        )
        
        # 执行更新
        updated = await self.knowledge_service.update_knowledge(knowledge_id, update_request)
        
        print(f"\n更新后:")
        print(f"  新标题: {updated.title}")
        print(f"  新状态: {updated.status}")
        print(f"  版本历史: {len(updated.version_history)} 个版本")
        print(f"  最后更新: {updated.updated_at}")
        
        # 显示版本历史
        if updated.version_history:
            latest_version = updated.version_history[-1]
            print(f"  最新变更: {latest_version}")
    
    async def demo_quality_assessment(self):
        """质量评估演示"""
        print("\n⭐ 4. 质量评估演示 (Quality Assessment Demo)")
        print("-" * 40)
        
        # 获取所有知识进行质量评估
        all_knowledge = self.knowledge_service.list_knowledge()
        
        print(f"对 {len(all_knowledge)} 个知识条目进行质量评估:")
        
        for knowledge in all_knowledge:
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
        
        # 批量质量评估
        print("\n执行批量质量评估...")
        batch_results = await self.knowledge_service.batch_quality_assessment()
        
        avg_quality = sum(q.overall_score for q in batch_results.values()) / len(batch_results)
        print(f"平均质量评分: {avg_quality:.2f}")
    
    async def demo_knowledge_search(self):
        """知识搜索演示"""
        print("\n🔍 5. 知识搜索演示 (Knowledge Search Demo)")
        print("-" * 40)
        
        search_queries = [
            "CRM系统实施",
            "客户数据管理",
            "销售流程",
            "数据安全"
        ]
        
        for query in search_queries:
            print(f"\n搜索查询: '{query}'")
            
            results = await self.knowledge_service.search_knowledge(
                query=query,
                limit=3
            )
            
            print(f"找到 {len(results)} 个结果:")
            
            for i, result in enumerate(results):
                print(f"\n  结果 {i+1}:")
                print(f"    标题: {result.knowledge.title}")
                print(f"    类型: {result.knowledge.type}")
                print(f"    匹配分数: {result.score:.2f}")
                print(f"    相关性: {result.relevance:.2f}")
                print(f"    摘要: {result.snippet[:100]}...")
                
                if result.matched_chunks:
                    print(f"    匹配块数: {len(result.matched_chunks)}")
    
    async def demo_usage_statistics(self, knowledge_ids: List[str]):
        """使用统计演示"""
        print("\n📊 6. 使用统计演示 (Usage Statistics Demo)")
        print("-" * 40)
        
        # 模拟一些使用活动
        for knowledge_id in knowledge_ids:
            # 模拟查看
            knowledge = self.knowledge_service.get_knowledge(knowledge_id)
            
            # 模拟引用
            self.knowledge_service.update_usage_statistics(knowledge_id, "reference")
            self.knowledge_service.update_usage_statistics(knowledge_id, "reference")
            
            # 模拟反馈
            self.knowledge_service.update_usage_statistics(knowledge_id, "feedback", True)
            self.knowledge_service.update_usage_statistics(knowledge_id, "feedback", False)
        
        # 显示统计信息
        print("\n使用统计:")
        for knowledge_id in knowledge_ids:
            knowledge = self.knowledge_service.get_knowledge(knowledge_id)
            if knowledge:
                usage = knowledge.usage
                print(f"\n📋 {knowledge.title}")
                print(f"  查看次数: {usage.view_count}")
                print(f"  搜索命中: {usage.search_count}")
                print(f"  被引用: {usage.reference_count}")
                print(f"  反馈总数: {usage.feedback_count}")
                print(f"  正面反馈: {usage.positive_feedback}")
                print(f"  负面反馈: {usage.negative_feedback}")
                print(f"  最后访问: {usage.last_accessed}")
        
        # 获取整体统计
        stats = self.knowledge_service.get_knowledge_statistics()
        print(f"\n📈 整体统计:")
        print(f"  总知识数: {stats['total_knowledge']}")
        print(f"  按类型分布: {stats['by_type']}")
        print(f"  按状态分布: {stats['by_status']}")
        print(f"  平均质量: {stats['average_quality']:.2f}")
        print(f"  总块数: {stats['total_chunks']}")
    
    async def demo_batch_operations(self):
        """批量操作演示"""
        print("\n🔄 7. 批量操作演示 (Batch Operations Demo)")
        print("-" * 40)
        
        # 批量创建知识
        batch_data = [
            {
                "title": f"技术文档 {i}",
                "content": f"这是第 {i} 个技术文档的内容。包含了相关的技术说明和操作指南。",
                "type": KnowledgeType.DOCUMENT,
                "domain": "技术文档"
            }
            for i in range(1, 4)
        ]
        
        print("批量创建知识条目...")
        batch_ids = []
        
        for data in batch_data:
            metadata = KnowledgeMetadata(
                source="batch_import",
                author="system",
                domain=data["domain"],
                tags=["技术", "文档", "批量导入"]
            )
            
            knowledge = await self.knowledge_service.create_knowledge(
                title=data["title"],
                content=data["content"],
                knowledge_type=data["type"],
                metadata=metadata
            )
            
            batch_ids.append(knowledge.id)
            print(f"  创建: {knowledge.title} (ID: {knowledge.id})")
        
        # 批量质量评估
        print("\n执行批量质量评估...")
        quality_results = await self.knowledge_service.batch_quality_assessment()
        
        for knowledge_id, quality in quality_results.items():
            if knowledge_id in batch_ids:
                knowledge = self.knowledge_service.get_knowledge(knowledge_id)
                print(f"  {knowledge.title}: 质量评分 {quality.overall_score:.2f}")
        
        # 批量删除
        print("\n批量删除演示知识...")
        for knowledge_id in batch_ids:
            success = await self.knowledge_service.delete_knowledge(knowledge_id)
            print(f"  删除 {knowledge_id}: {'成功' if success else '失败'}")
    
    async def demo_advanced_filtering(self):
        """高级过滤演示"""
        print("\n🎯 8. 高级过滤演示 (Advanced Filtering Demo)")
        print("-" * 40)
        
        # 按类型过滤
        print("按知识类型过滤:")
        type_filter = KnowledgeSearchFilter(types=[KnowledgeType.FAQ, KnowledgeType.BEST_PRACTICE])
        filtered_by_type = self.knowledge_service.list_knowledge(filter_params=type_filter)
        
        for knowledge in filtered_by_type:
            print(f"  {knowledge.type}: {knowledge.title}")
        
        # 按状态过滤
        print("\n按状态过滤 (已发布):")
        status_filter = KnowledgeSearchFilter(status=[KnowledgeStatus.PUBLISHED])
        filtered_by_status = self.knowledge_service.list_knowledge(filter_params=status_filter)
        
        for knowledge in filtered_by_status:
            print(f"  {knowledge.status}: {knowledge.title}")
        
        # 按标签过滤
        print("\n按标签过滤 (包含'CRM'):")
        tag_filter = KnowledgeSearchFilter(tags=["CRM"])
        filtered_by_tags = self.knowledge_service.list_knowledge(filter_params=tag_filter)
        
        for knowledge in filtered_by_tags:
            print(f"  标签{knowledge.metadata.tags}: {knowledge.title}")
        
        # 按质量分数过滤
        print("\n按质量分数过滤 (>0.7):")
        quality_filter = KnowledgeSearchFilter(min_quality_score=0.7)
        filtered_by_quality = self.knowledge_service.list_knowledge(filter_params=quality_filter)
        
        for knowledge in filtered_by_quality:
            quality_score = knowledge.quality.overall_score if knowledge.quality else 0
            print(f"  质量{quality_score:.2f}: {knowledge.title}")
        
        # 复合过滤
        print("\n复合过滤 (FAQ类型 + CRM标签):")
        complex_filter = KnowledgeSearchFilter(
            types=[KnowledgeType.FAQ],
            tags=["CRM"]
        )
        filtered_complex = self.knowledge_service.list_knowledge(filter_params=complex_filter)
        
        for knowledge in filtered_complex:
            print(f"  {knowledge.type} + {knowledge.metadata.tags}: {knowledge.title}")


async def run_knowledge_examples():
    """运行知识库管理示例"""
    demo = KnowledgeManagementDemo()
    await demo.run_complete_demo()


def run_sync_examples():
    """同步运行示例"""
    print("启动知识库管理系统演示...")
    asyncio.run(run_knowledge_examples())


if __name__ == "__main__":
    run_sync_examples()