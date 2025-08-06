#!/usr/bin/env python3
"""
RAG示例运行器

统一运行所有RAG服务示例程序，提供交互式选择和批量运行功能。
"""

import asyncio
import sys
import os
import subprocess
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RAGExampleRunner:
    """RAG示例运行器"""
    
    def __init__(self):
        self.examples = {
            '1': {
                'name': 'RAG服务完整演示',
                'file': 'rag_service_examples.py',
                'description': '展示RAG服务的所有功能，包括10个详细示例',
                'args': []
            },
            '2': {
                'name': 'RAG简化演示',
                'file': 'rag_simple_demo.py', 
                'description': '快速验证RAG核心功能，无外部依赖',
                'args': []
            },
            '3': {
                'name': 'RAG交互式问答',
                'file': 'rag_simple_demo.py',
                'description': '交互式问答演示，可以输入问题测试',
                'args': ['interactive']
            },
            '4': {
                'name': 'RAG性能测试',
                'file': 'rag_simple_demo.py',
                'description': '测试不同配置下的性能表现',
                'args': ['performance']
            },
            '5': {
                'name': 'RAG基础组件测试',
                'file': 'rag_simple_demo.py',
                'description': '测试RAG系统的基础组件',
                'args': ['basic']
            }
        }
        
        self.specific_examples = {
            '6': {
                'name': 'RAG服务初始化',
                'file': 'rag_service_examples.py',
                'description': '演示RAG服务的初始化和配置',
                'args': ['1']
            },
            '7': {
                'name': '中文文本处理',
                'file': 'rag_service_examples.py',
                'description': '演示中文文本分割和处理',
                'args': ['2']
            },
            '8': {
                'name': '检索模式对比',
                'file': 'rag_service_examples.py',
                'description': '对比不同检索模式的效果',
                'args': ['4']
            },
            '9': {
                'name': '端到端问答',
                'file': 'rag_service_examples.py',
                'description': '完整的RAG问答流程演示',
                'args': ['7']
            },
            '10': {
                'name': 'API接口演示',
                'file': 'rag_service_examples.py',
                'description': '展示RAG API接口的使用方法',
                'args': ['9']
            }
        }
    
    def show_menu(self):
        """显示示例菜单"""
        print("\n" + "="*60)
        print("🤖 RAG服务示例运行器")
        print("="*60)
        
        print("\n📋 主要示例:")
        for key, example in self.examples.items():
            print(f"{key}. {example['name']}")
            print(f"   {example['description']}")
        
        print(f"\n🔧 特定功能示例:")
        for key, example in self.specific_examples.items():
            print(f"{key}. {example['name']}")
            print(f"   {example['description']}")
        
        print(f"\n🚀 批量运行:")
        print("a. 运行所有主要示例")
        print("b. 运行所有特定示例")
        print("c. 运行全部示例")
        
        print(f"\n其他选项:")
        print("h. 显示帮助信息")
        print("q. 退出")
        print("="*60)
    
    async def run_example(self, key: str):
        """运行指定示例"""
        all_examples = {**self.examples, **self.specific_examples}
        
        if key not in all_examples:
            print(f"❌ 示例 '{key}' 不存在")
            return False
        
        example = all_examples[key]
        
        print(f"\n🚀 运行示例: {example['name']}")
        print(f"📝 描述: {example['description']}")
        print("-" * 50)
        
        try:
            # 构建命令
            cmd = ['uv', 'run', 'python', f"examples/{example['file']}"]
            cmd.extend(example['args'])
            
            print(f"执行命令: {' '.join(cmd)}")
            print()
            
            # 运行示例
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(stdout.decode('utf-8', errors='ignore'))
                print(f"✅ 示例 '{example['name']}' 运行成功")
                return True
            else:
                print(f"❌ 示例运行失败:")
                print(stderr.decode('utf-8', errors='ignore'))
                return False
                
        except Exception as e:
            print(f"❌ 运行示例时出错: {e}")
            return False
    
    async def run_batch(self, batch_type: str):
        """批量运行示例"""
        if batch_type == 'a':
            examples_to_run = self.examples
            batch_name = "主要示例"
        elif batch_type == 'b':
            examples_to_run = self.specific_examples
            batch_name = "特定功能示例"
        elif batch_type == 'c':
            examples_to_run = {**self.examples, **self.specific_examples}
            batch_name = "全部示例"
        else:
            print(f"❌ 未知的批量类型: {batch_type}")
            return
        
        print(f"\n🚀 批量运行{batch_name}")
        print("="*50)
        
        success_count = 0
        total_count = len(examples_to_run)
        
        for key in examples_to_run.keys():
            print(f"\n[{success_count + 1}/{total_count}] 运行示例 {key}")
            
            success = await self.run_example(key)
            if success:
                success_count += 1
            
            # 添加间隔
            if key != list(examples_to_run.keys())[-1]:
                print("\n" + "-"*30 + " 下一个示例 " + "-"*30)
                await asyncio.sleep(1)
        
        print(f"\n📊 批量运行结果:")
        print(f"  成功: {success_count}/{total_count}")
        print(f"  失败: {total_count - success_count}/{total_count}")
        
        if success_count == total_count:
            print("🎉 所有示例运行成功！")
        else:
            print("⚠️ 部分示例运行失败，请检查错误信息")
    
    def show_help(self):
        """显示帮助信息"""
        print("\n" + "="*60)
        print("📖 RAG示例运行器帮助")
        print("="*60)
        
        print("\n🎯 功能说明:")
        print("本工具用于统一运行RAG服务的各种示例程序，包括：")
        print("• 完整功能演示")
        print("• 简化验证程序")
        print("• 交互式问答")
        print("• 性能测试")
        print("• 特定功能演示")
        
        print(f"\n🚀 使用方法:")
        print("1. 选择要运行的示例编号")
        print("2. 或选择批量运行选项")
        print("3. 查看运行结果和输出")
        
        print(f"\n📋 示例分类:")
        print("• 主要示例 (1-5): 核心功能演示")
        print("• 特定示例 (6-10): 针对性功能测试")
        print("• 批量运行 (a-c): 自动运行多个示例")
        
        print(f"\n💡 提示:")
        print("• 首次运行可能需要下载模型")
        print("• 某些示例需要向量数据库支持")
        print("• 可以随时按 Ctrl+C 中断运行")
        
        print(f"\n🔧 环境要求:")
        print("• Python 3.11+")
        print("• uv 包管理器")
        print("• 项目依赖已安装")
        
        print("="*60)
    
    async def interactive_mode(self):
        """交互模式"""
        print("🎯 欢迎使用RAG示例运行器！")
        print("输入 'h' 查看帮助，输入 'q' 退出")
        
        while True:
            try:
                self.show_menu()
                choice = input("\n请选择示例编号或选项: ").strip().lower()
                
                if choice == 'q':
                    print("👋 再见！")
                    break
                elif choice == 'h':
                    self.show_help()
                elif choice in ['a', 'b', 'c']:
                    await self.run_batch(choice)
                elif choice in {**self.examples, **self.specific_examples}:
                    await self.run_example(choice)
                else:
                    print(f"❌ 无效选择: '{choice}'")
                    print("请输入有效的示例编号或选项")
                
                if choice != 'h':
                    input("\n按回车键继续...")
                    
            except KeyboardInterrupt:
                print("\n👋 用户中断，退出程序")
                break
            except Exception as e:
                print(f"❌ 程序错误: {e}")
                input("按回车键继续...")
    
    async def run_single(self, example_key: str):
        """运行单个示例"""
        print(f"🚀 运行单个示例: {example_key}")
        success = await self.run_example(example_key)
        
        if success:
            print(f"\n✅ 示例运行完成")
        else:
            print(f"\n❌ 示例运行失败")
            sys.exit(1)


async def main():
    """主函数"""
    runner = RAGExampleRunner()
    
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg == 'help' or arg == '-h' or arg == '--help':
            runner.show_help()
        elif arg == 'list':
            runner.show_menu()
        elif arg in ['a', 'b', 'c']:
            await runner.run_batch(arg)
        elif arg in {**runner.examples, **runner.specific_examples}:
            await runner.run_single(arg)
        else:
            print(f"❌ 未知参数: {arg}")
            print("使用 'help' 查看帮助信息")
            sys.exit(1)
    else:
        # 交互模式
        await runner.interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)