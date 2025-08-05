"""
运行对话状态管理示例程序

这个脚本用于运行和验证对话状态管理系统的各种示例程序。
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from examples.conversation_state_examples import ConversationStateExamples
from examples.sales_conversation_demo import SalesConversationDemo


async def run_basic_examples():
    """运行基础功能示例"""
    print("🔧 运行基础功能示例...")
    examples = ConversationStateExamples()
    await examples.run_all_examples()


async def run_sales_demo():
    """运行销售对话演示"""
    print("\n💼 运行销售对话演示...")
    demo = SalesConversationDemo()
    await demo.run_demo()


async def main():
    """主函数"""
    print("🚀 对话状态管理系统验证程序")
    print("="*80)
    
    try:
        # 运行基础功能示例
        await run_basic_examples()
        
        # 等待用户确认
        print("\n" + "="*80)
        input("按回车键继续运行销售对话演示...")
        
        # 运行销售对话演示
        await run_sales_demo()
        
        print("\n" + "="*80)
        print("🎉 所有示例程序运行完成！")
        print("✅ 对话状态管理系统验证成功")
        print("="*80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断程序执行")
    except Exception as e:
        print(f"\n❌ 程序执行出错: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())