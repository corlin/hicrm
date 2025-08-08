#!/usr/bin/env python3
"""
多模态数据分析快速开始示例

这是一个简化的示例，展示如何快速使用多模态分析功能。

运行方式:
    python examples/quick_start_multimodal.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.multimodal_fusion_service import MultimodalFusionService
from src.models.multimodal import MultimodalAnalysisRequest, DataModalityType

async def quick_analysis_example():
    """快速分析示例"""
    print("🚀 多模态数据分析快速开始")
    print("=" * 50)
    
    # 1. 初始化服务
    fusion_service = MultimodalFusionService()
    print("✅ 服务初始化完成")
    
    # 2. 创建分析请求
    request = MultimodalAnalysisRequest(
        customer_id="quick_demo_customer",
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
    
    # 3. 执行分析
    print("🔄 执行多模态分析...")
    result = await fusion_service.process_multimodal_analysis(request)
    
    # 4. 显示结果
    print("📊 分析结果:")
    print(f"   客户ID: {result.customer_id}")
    print(f"   分析类型: {result.analysis_type}")
    print(f"   置信度: {result.confidence:.2f}")
    print(f"   处理时间: {result.processing_time:.3f} 秒")
    
    if result.results:
        print("   详细结果:")
        for key, value in result.results.items():
            if isinstance(value, (int, float)):
                print(f"     {key}: {value:.2f}")
            elif isinstance(value, str):
                print(f"     {key}: {value}")
    
    if result.recommendations:
        print("   💡 推荐建议:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"     {i}. {rec}")
    
    print("\n🎉 分析完成！")

if __name__ == "__main__":
    asyncio.run(quick_analysis_example())