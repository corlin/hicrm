#!/usr/bin/env python3
"""
嵌入服务使用示例

本文件展示如何使用BGE-M3嵌入服务进行文本向量化、相似度计算、
重排序等功能。包括中英文文本处理、批量操作、缓存机制等演示。
"""

import asyncio
import sys
import os
import logging
import time
from typing import List, Dict, Any, Tuple
import numpy as np

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.embedding_service import embedding_service

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EmbeddingServiceExamples:
    """嵌入服务使用示例类"""
    
    def __init__(self):
        self.sample_texts = {
            "chinese": [
                "人工智能是计算机科学的一个重要分支",
                "机器学习算法可以从数据中自动学习模式",
                "深度学习使用多层神经网络进行特征提取",
                "自然语言处理技术帮助计算机理解人类语言",
                "计算机视觉让机器能够识别和理解图像内容"
            ],
            "english": [
                "Artificial intelligence is a branch of computer science",
                "Machine learning algorithms can automatically learn patterns from data",
                "Deep learning uses multi-layer neural networks for feature extraction",
                "Natural language processing helps computers understand human language",
                "Computer vision enables machines to recognize and understand image content"
            ],
            "mixed": [
                "AI人工智能 technology is rapidly advancing",
                "机器学习 machine learning 在各个领域都有应用",
                "Deep learning深度学习 has revolutionized computer vision",
                "NLP自然语言处理 enables better human-computer interaction"
            ]
        }
    
    async def example_01_basic_initialization(self):
        """示例1: 基本初始化和模型信息"""
        print("\n" + "="*60)
        print("示例1: 基本初始化和模型信息")
        print("="*60)
        
        try:
            # 初始化嵌入服务
            logger.info("初始化BGE-M3嵌入服务...")
            await embedding_service.initialize()
            
            # 获取模型信息
            model_info = await embedding_service.get_model_info()
            print("模型信息:")
            for key, value in model_info.items():
                print(f"  {key}: {value}")
            
            # 初始化重排序模型
            logger.info("初始化重排序模型...")
            await embedding_service.initialize_reranker()
            
            # 再次获取模型信息
            model_info = await embedding_service.get_model_info()
            print("\n更新后的模型信息:")
            for key, value in model_info.items():
                print(f"  {key}: {value}")
                
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    async def example_02_single_text_encoding(self):
        """示例2: 单个文本编码"""
        print("\n" + "="*60)
        print("示例2: 单个文本编码")
        print("="*60)
        
        try:
            test_texts = [
                "这是一个中文测试句子。",
                "This is an English test sentence.",
                "这是一个混合语言的句子 with English words."
            ]
            
            for text in test_texts:
                print(f"\n文本: '{text}'")
                
                # 编码文本
                start_time = time.time()
                embedding = await embedding_service.encode(text)
                encode_time = time.time() - start_time
                
                print(f"编码耗时: {encode_time*1000:.2f} 毫秒")
                print(f"向量维度: {len(embedding)}")
                print(f"向量类型: {type(embedding)}")
                print(f"向量前5个值: {embedding[:5]}")
                print(f"向量范数: {np.linalg.norm(embedding):.4f}")
                
        except Exception as e:
            logger.error(f"单文本编码失败: {e}")
            raise
    
    async def example_03_batch_encoding(self):
        """示例3: 批量文本编码"""
        print("\n" + "="*60)
        print("示例3: 批量文本编码")
        print("="*60)
        
        try:
            # 测试不同语言的批量编码
            for lang, texts in self.sample_texts.items():
                print(f"\n{lang.upper()} 文本批量编码:")
                print(f"文本数量: {len(texts)}")
                
                # 批量编码
                start_time = time.time()
                embeddings = await embedding_service.encode(texts)
                encode_time = time.time() - start_time
                
                print(f"批量编码耗时: {encode_time:.3f} 秒")
                print(f"平均每个文本: {encode_time/len(texts)*1000:.2f} 毫秒")
                print(f"返回向量数量: {len(embeddings)}")
                print(f"每个向量维度: {len(embeddings[0])}")
                
                # 显示部分结果
                for i, (text, embedding) in enumerate(zip(texts[:2], embeddings[:2])):
                    print(f"  文本{i+1}: {text[:30]}...")
                    print(f"  向量前3个值: {embedding[:3]}")
                
        except Exception as e:
            logger.error(f"批量编码失败: {e}")
            raise
    
    async def example_04_similarity_calculation(self):
        """示例4: 相似度计算"""
        print("\n" + "="*60)
        print("示例4: 相似度计算")
        print("="*60)
        
        try:
            # 测试文本对的相似度
            text_pairs = [
                # 高相似度对
                ("人工智能技术", "AI技术发展"),
                ("机器学习算法", "机器学习方法"),
                ("深度学习网络", "神经网络模型"),
                
                # 中等相似度对
                ("人工智能", "计算机科学"),
                ("机器学习", "数据分析"),
                
                # 低相似度对
                ("人工智能", "苹果水果"),
                ("机器学习", "天气预报"),
                
                # 跨语言相似度
                ("人工智能", "artificial intelligence"),
                ("机器学习", "machine learning"),
                ("深度学习", "deep learning")
            ]
            
            print("文本对相似度计算:")
            print("-" * 80)
            print(f"{'文本1':<25} {'文本2':<25} {'相似度':<10} {'类型'}")
            print("-" * 80)
            
            for text1, text2 in text_pairs:
                similarity = await embedding_service.compute_similarity(text1, text2)
                
                # 判断相似度类型
                if similarity > 0.8:
                    sim_type = "高相似"
                elif similarity > 0.6:
                    sim_type = "中等相似"
                elif similarity > 0.4:
                    sim_type = "低相似"
                else:
                    sim_type = "不相似"
                
                print(f"{text1:<25} {text2:<25} {similarity:<10.4f} {sim_type}")
                
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            raise
    
    async def example_05_multi_similarity_calculation(self):
        """示例5: 一对多相似度计算"""
        print("\n" + "="*60)
        print("示例5: 一对多相似度计算")
        print("="*60)
        
        try:
            # 查询文本
            queries = [
                "人工智能技术应用",
                "machine learning applications",
                "深度学习算法优化"
            ]
            
            # 候选文档
            documents = self.sample_texts["chinese"] + self.sample_texts["english"]
            
            for query in queries:
                print(f"\n查询: '{query}'")
                print("-" * 60)
                
                # 计算与所有文档的相似度
                similarities = await embedding_service.compute_similarities(query, documents)
                
                # 排序并显示结果
                doc_sim_pairs = list(zip(documents, similarities))
                doc_sim_pairs.sort(key=lambda x: x[1], reverse=True)
                
                print("最相关的文档 (按相似度排序):")
                for i, (doc, sim) in enumerate(doc_sim_pairs[:5], 1):
                    print(f"  {i}. 相似度: {sim:.4f}")
                    print(f"     文档: {doc}")
                    print()
                
        except Exception as e:
            logger.error(f"多相似度计算失败: {e}")
            raise
    
    async def example_06_reranking(self):
        """示例6: 重排序功能"""
        print("\n" + "="*60)
        print("示例6: 重排序功能")
        print("="*60)
        
        try:
            # 查询和候选文档
            query = "人工智能在医疗领域的应用"
            documents = [
                "人工智能技术在医疗诊断中发挥重要作用",
                "机器学习算法可以分析医疗影像数据",
                "深度学习帮助医生进行疾病预测",
                "自然语言处理用于分析医疗记录",
                "计算机视觉技术用于医疗图像识别",
                "区块链技术在金融领域的应用",  # 不相关文档
                "量子计算的基本原理和发展前景"    # 不相关文档
            ]
            
            print(f"查询: '{query}'")
            print(f"候选文档数量: {len(documents)}")
            
            # 执行重排序
            print("\n执行重排序...")
            rerank_results = await embedding_service.rerank(query, documents, top_k=5)
            
            print("重排序结果 (按相关性排序):")
            print("-" * 60)
            for i, (doc_idx, score) in enumerate(rerank_results, 1):
                print(f"{i}. 分数: {score:.4f}")
                print(f"   文档: {documents[doc_idx]}")
                print()
            
            # 比较重排序前后的顺序
            print("原始顺序 vs 重排序后:")
            print("-" * 60)
            for i, (doc_idx, score) in enumerate(rerank_results):
                print(f"原始位置 {doc_idx+1} -> 重排序位置 {i+1} (分数: {score:.4f})")
                
        except Exception as e:
            logger.error(f"重排序失败: {e}")
            # 重排序可能因为模型问题失败，这是正常的
            print("注意: 重排序功能可能需要特定的模型配置")
    
    async def example_07_caching_performance(self):
        """示例7: 缓存性能测试"""
        print("\n" + "="*60)
        print("示例7: 缓存性能测试")
        print("="*60)
        
        try:
            test_text = "这是一个用于测试缓存性能的文本示例"
            
            # 清空缓存
            embedding_service.clear_cache()
            print("已清空缓存")
            
            # 第一次编码 (无缓存)
            print(f"\n第一次编码 (无缓存): '{test_text}'")
            start_time = time.time()
            embedding1 = await embedding_service.encode(test_text)
            first_time = time.time() - start_time
            print(f"耗时: {first_time*1000:.2f} 毫秒")
            
            # 第二次编码 (使用缓存)
            print(f"\n第二次编码 (使用缓存): '{test_text}'")
            start_time = time.time()
            embedding2 = await embedding_service.encode(test_text)
            second_time = time.time() - start_time
            print(f"耗时: {second_time*1000:.2f} 毫秒")
            
            # 验证结果一致性
            are_equal = np.allclose(embedding1, embedding2)
            print(f"\n结果一致性: {are_equal}")
            print(f"性能提升: {(first_time/second_time):.1f}x")
            
            # 缓存信息
            model_info = await embedding_service.get_model_info()
            print(f"当前缓存大小: {model_info.get('cache_size', 0)}")
            
            # 批量测试缓存效果
            print("\n批量缓存测试:")
            test_texts = [f"测试文本 {i}" for i in range(10)]
            
            # 第一次批量编码
            start_time = time.time()
            await embedding_service.encode(test_texts)
            first_batch_time = time.time() - start_time
            
            # 第二次批量编码 (全部使用缓存)
            start_time = time.time()
            await embedding_service.encode(test_texts)
            second_batch_time = time.time() - start_time
            
            print(f"第一次批量编码: {first_batch_time*1000:.2f} 毫秒")
            print(f"第二次批量编码: {second_batch_time*1000:.2f} 毫秒")
            print(f"批量性能提升: {(first_batch_time/second_batch_time):.1f}x")
            
        except Exception as e:
            logger.error(f"缓存性能测试失败: {e}")
            raise
    
    async def example_08_normalization_comparison(self):
        """示例8: 归一化对比"""
        print("\n" + "="*60)
        print("示例8: 归一化对比")
        print("="*60)
        
        try:
            test_text = "人工智能技术的发展前景"
            
            # 归一化编码
            print("归一化编码:")
            normalized_embedding = await embedding_service.encode(test_text, normalize=True)
            norm_magnitude = np.linalg.norm(normalized_embedding)
            print(f"  向量范数: {norm_magnitude:.6f}")
            print(f"  前5个值: {normalized_embedding[:5]}")
            
            # 非归一化编码
            print("\n非归一化编码:")
            unnormalized_embedding = await embedding_service.encode(test_text, normalize=False)
            unnorm_magnitude = np.linalg.norm(unnormalized_embedding)
            print(f"  向量范数: {unnorm_magnitude:.6f}")
            print(f"  前5个值: {unnormalized_embedding[:5]}")
            
            # 相似度计算对比
            text1 = "人工智能"
            text2 = "机器智能"
            
            print(f"\n相似度计算对比:")
            print(f"文本1: '{text1}'")
            print(f"文本2: '{text2}'")
            
            # 归一化相似度
            norm_similarity = await embedding_service.compute_similarity(
                text1, text2, normalize=True
            )
            print(f"归一化相似度: {norm_similarity:.4f}")
            
            # 非归一化相似度
            unnorm_similarity = await embedding_service.compute_similarity(
                text1, text2, normalize=False
            )
            print(f"非归一化相似度: {unnorm_similarity:.4f}")
            
        except Exception as e:
            logger.error(f"归一化对比失败: {e}")
            raise
    
    async def example_09_multilingual_performance(self):
        """示例9: 多语言性能对比"""
        print("\n" + "="*60)
        print("示例9: 多语言性能对比")
        print("="*60)
        
        try:
            # 不同语言的相同概念
            concepts = {
                "人工智能": {
                    "zh": "人工智能是计算机科学的重要分支",
                    "en": "Artificial intelligence is an important branch of computer science",
                    "mixed": "人工智能 artificial intelligence 是重要的技术领域"
                },
                "机器学习": {
                    "zh": "机器学习算法可以从数据中学习",
                    "en": "Machine learning algorithms can learn from data",
                    "mixed": "机器学习 machine learning 算法很强大"
                }
            }
            
            print("跨语言语义相似度测试:")
            print("-" * 70)
            print(f"{'概念':<10} {'语言对':<15} {'相似度':<10} {'评价'}")
            print("-" * 70)
            
            for concept, texts in concepts.items():
                # 中英文对比
                zh_en_sim = await embedding_service.compute_similarity(
                    texts["zh"], texts["en"]
                )
                
                # 中文与混合语言对比
                zh_mixed_sim = await embedding_service.compute_similarity(
                    texts["zh"], texts["mixed"]
                )
                
                # 英文与混合语言对比
                en_mixed_sim = await embedding_service.compute_similarity(
                    texts["en"], texts["mixed"]
                )
                
                # 评价相似度
                def evaluate_similarity(sim):
                    if sim > 0.8:
                        return "优秀"
                    elif sim > 0.6:
                        return "良好"
                    elif sim > 0.4:
                        return "一般"
                    else:
                        return "较差"
                
                print(f"{concept:<10} {'中-英':<15} {zh_en_sim:<10.4f} {evaluate_similarity(zh_en_sim)}")
                print(f"{'':<10} {'中-混合':<15} {zh_mixed_sim:<10.4f} {evaluate_similarity(zh_mixed_sim)}")
                print(f"{'':<10} {'英-混合':<15} {en_mixed_sim:<10.4f} {evaluate_similarity(en_mixed_sim)}")
                print()
            
            # 性能对比
            print("不同语言编码性能对比:")
            print("-" * 50)
            
            for lang, texts in self.sample_texts.items():
                if lang == "mixed":
                    continue
                    
                start_time = time.time()
                await embedding_service.encode(texts)
                encode_time = time.time() - start_time
                
                avg_time = encode_time / len(texts) * 1000
                print(f"{lang.upper():<10} 平均编码时间: {avg_time:.2f} 毫秒/文本")
                
        except Exception as e:
            logger.error(f"多语言性能对比失败: {e}")
            raise
    
    async def example_10_cleanup(self):
        """示例10: 清理资源"""
        print("\n" + "="*60)
        print("示例10: 清理资源")
        print("="*60)
        
        try:
            # 获取清理前的状态
            model_info = await embedding_service.get_model_info()
            print(f"清理前缓存大小: {model_info.get('cache_size', 0)}")
            
            # 清理缓存
            print("清理嵌入服务缓存...")
            embedding_service.clear_cache()
            
            # 获取清理后的状态
            model_info = await embedding_service.get_model_info()
            print(f"清理后缓存大小: {model_info.get('cache_size', 0)}")
            
            # 关闭服务
            print("关闭嵌入服务...")
            await embedding_service.close()
            
            print("资源清理完成!")
            
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
            raise


async def run_all_examples():
    """运行所有示例"""
    examples = EmbeddingServiceExamples()
    
    try:
        await examples.example_01_basic_initialization()
        await examples.example_02_single_text_encoding()
        await examples.example_03_batch_encoding()
        await examples.example_04_similarity_calculation()
        await examples.example_05_multi_similarity_calculation()
        await examples.example_06_reranking()
        await examples.example_07_caching_performance()
        await examples.example_08_normalization_comparison()
        await examples.example_09_multilingual_performance()
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        raise
    finally:
        await examples.example_10_cleanup()


async def run_specific_example(example_num: int):
    """运行特定示例"""
    examples = EmbeddingServiceExamples()
    
    # 基本初始化总是需要的
    await examples.example_01_basic_initialization()
    
    try:
        if example_num == 2:
            await examples.example_02_single_text_encoding()
        elif example_num == 3:
            await examples.example_03_batch_encoding()
        elif example_num == 4:
            await examples.example_04_similarity_calculation()
        elif example_num == 5:
            await examples.example_05_multi_similarity_calculation()
        elif example_num == 6:
            await examples.example_06_reranking()
        elif example_num == 7:
            await examples.example_07_caching_performance()
        elif example_num == 8:
            await examples.example_08_normalization_comparison()
        elif example_num == 9:
            await examples.example_09_multilingual_performance()
        else:
            print(f"示例 {example_num} 不存在")
            return
            
    finally:
        await examples.example_10_cleanup()


if __name__ == "__main__":
    print("BGE-M3嵌入服务使用示例")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1])
            print(f"运行示例 {example_num}")
            asyncio.run(run_specific_example(example_num))
        except ValueError:
            print("请提供有效的示例编号 (1-9)")
    else:
        print("运行所有示例...")
        asyncio.run(run_all_examples())