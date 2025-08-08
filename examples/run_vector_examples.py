#!/usr/bin/env python3
"""
向量数据库和嵌入服务示例运行器

这个脚本提供了一个统一的入口来运行所有向量数据库和嵌入服务相关的示例。
支持交互式选择和批量运行。
"""

import asyncio
import sys
import os
import logging
from typing import Dict, List, Callable

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.unicode_utils import SafeOutput

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorExamplesRunner:
    """向量示例运行器"""
    
    def __init__(self):
        self.safe_output = SafeOutput()
        self.examples = {
            "1": {
                "name": "向量数据库服务示例",
                "description": "Qdrant向量数据库的基本操作和高级功能",
                "module": "vector_database_examples",
                "sub_examples": {
                    "1": "基本设置和初始化",
                    "2": "添加文档到向量数据库", 
                    "3": "基本向量搜索",
                    "4": "带过滤条件的搜索",
                    "5": "直接使用向量搜索",
                    "6": "相似度计算",
                    "7": "文档管理操作",
                    "8": "集合管理",
                    "9": "性能测试"
                }
            },
            "2": {
                "name": "BGE-M3嵌入服务示例",
                "description": "BGE-M3多语言嵌入模型的使用方法",
                "module": "embedding_service_examples",
                "sub_examples": {
                    "1": "基本初始化和模型信息",
                    "2": "单个文本编码",
                    "3": "批量文本编码",
                    "4": "相似度计算",
                    "5": "一对多相似度计算",
                    "6": "重排序功能",
                    "7": "缓存性能测试",
                    "8": "归一化对比",
                    "9": "多语言性能对比"
                }
            },
            "3": {
                "name": "混合搜索服务示例",
                "description": "结合向量搜索和BM25搜索的混合检索",
                "module": "hybrid_search_examples",
                "sub_examples": {
                    "1": "服务初始化",
                    "2": "添加文档到混合搜索系统",
                    "3": "仅向量搜索模式",
                    "4": "仅BM25搜索模式",
                    "5": "混合搜索模式",
                    "6": "自定义搜索权重",
                    "7": "带过滤条件的搜索",
                    "8": "语义搜索功能",
                    "9": "不同搜索模式性能对比",
                    "10": "搜索统计信息"
                }
            },
            "4": {
                "name": "中文语义搜索示例",
                "description": "专门针对中文文本的语义搜索功能",
                "module": "chinese_search_examples",
                "sub_examples": {
                    "1": "中文搜索服务初始化",
                    "2": "添加中文文档",
                    "3": "中文文本处理功能",
                    "4": "中文语义搜索",
                    "5": "同义词扩展搜索对比",
                    "6": "自定义权重搜索",
                    "7": "查询意图分析",
                    "8": "相似文档查找",
                    "9": "搜索建议生成",
                    "10": "中文搜索性能分析"
                }
            }
        }
    
    def display_main_menu(self):
        """显示主菜单"""
        self.safe_output.safe_print("\n" + "="*80)
        self.safe_output.safe_print(self.safe_output.format_status("info", "向量数据库和嵌入服务示例运行器", "🚀"))
        self.safe_output.safe_print("="*80)
        self.safe_output.safe_print("请选择要运行的示例类别:")
        self.safe_output.safe_print()
        
        for key, example in self.examples.items():
            self.safe_output.safe_print(f"{key}. {example['name']}")
            self.safe_output.safe_print(f"   {example['description']}")
            self.safe_output.safe_print()
        
        self.safe_output.safe_print("0. 运行所有示例")
        self.safe_output.safe_print("q. 退出")
        print("-"*80)
    
    def display_sub_menu(self, category_key: str):
        """显示子菜单"""
        category = self.examples[category_key]
        category_name = category["name"]
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', f'{category_name} - 子示例', '📋')}")
        print("="*60)
        
        for key, description in category['sub_examples'].items():
            print(f"{key}. {description}")
        
        print()
        print("0. 运行所有子示例")
        print("b. 返回主菜单")
        print("q. 退出")
        print("-"*60)
    
    async def run_example(self, module_name: str, sub_example: str = None):
        """运行指定示例"""
        try:
            self.safe_output.safe_print(f"\n{self.safe_output.format_status('processing', f'正在运行 {module_name} 示例...', '🔄')}")
            
            if module_name == "vector_database_examples":
                from examples.vector_database_examples import run_all_examples, run_specific_example
                if sub_example:
                    await run_specific_example(int(sub_example))
                else:
                    await run_all_examples()
                    
            elif module_name == "embedding_service_examples":
                from examples.embedding_service_examples import run_all_examples, run_specific_example
                if sub_example:
                    await run_specific_example(int(sub_example))
                else:
                    await run_all_examples()
                    
            elif module_name == "hybrid_search_examples":
                from examples.hybrid_search_examples import run_all_examples, run_specific_example
                if sub_example:
                    await run_specific_example(int(sub_example))
                else:
                    await run_all_examples()
                    
            elif module_name == "chinese_search_examples":
                from examples.chinese_search_examples import run_all_examples, run_specific_example
                if sub_example:
                    await run_specific_example(int(sub_example))
                else:
                    await run_all_examples()
            
            self.safe_output.safe_print(f"\n{self.safe_output.format_status('success', f'{module_name} 示例运行完成!')}")
            
        except Exception as e:
            self.safe_output.safe_print(f"\n{self.safe_output.format_status('error', f'运行示例时出错: {e}')}")
            logger.error(f"运行示例失败: {e}")
    
    async def run_all_examples(self):
        """运行所有示例"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '开始运行所有向量数据库和嵌入服务示例...', '🚀')}")
        self.safe_output.safe_print("="*80)
        
        for key, example in self.examples.items():
            print(f"\n📂 正在运行: {example['name']}")
            print("-"*60)
            
            try:
                await self.run_example(example['module'])
                example_name = example["name"]
                self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'{example_name} 完成')}")
            except Exception as e:
                example_name = example["name"]
                self.safe_output.safe_print(f"{self.safe_output.format_status('error', f'{example_name} 失败: {e}')}")
                logger.error(f"示例 {example['name']} 运行失败: {e}")
                
                # 询问是否继续
                continue_choice = input("\n是否继续运行其他示例? (y/n): ").lower()
                if continue_choice != 'y':
                    break
        
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('success', '所有示例运行完成!', '🎉')}")
    
    async def interactive_mode(self):
        """交互式模式"""
        while True:
            self.display_main_menu()
            choice = input("请选择 (0-4, q): ").strip().lower()
            
            if choice == 'q':
                self.safe_output.safe_print(self.safe_output.format_status("info", "再见!", "👋"))
                break
            elif choice == '0':
                await self.run_all_examples()
                input("\n按回车键继续...")
            elif choice in self.examples:
                await self.handle_category_choice(choice)
            else:
                self.safe_output.safe_print(self.safe_output.format_status("error", "无效选择，请重试"))
    
    async def handle_category_choice(self, category_key: str):
        """处理类别选择"""
        category = self.examples[category_key]
        
        while True:
            self.display_sub_menu(category_key)
            sub_choice = input("请选择子示例: ").strip().lower()
            
            if sub_choice == 'q':
                return
            elif sub_choice == 'b':
                break
            elif sub_choice == '0':
                await self.run_example(category['module'])
                input("\n按回车键继续...")
            elif sub_choice in category['sub_examples']:
                await self.run_example(category['module'], sub_choice)
                input("\n按回车键继续...")
            else:
                self.safe_output.safe_print(self.safe_output.format_status("error", "无效选择，请重试"))
    
    def display_help(self):
        """显示帮助信息"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '向量数据库和嵌入服务示例帮助', '📖')}")
        self.safe_output.safe_print("="*60)
        self.safe_output.safe_print("使用方法:")
        print("  python run_vector_examples.py              # 交互式模式")
        print("  python run_vector_examples.py --all        # 运行所有示例")
        print("  python run_vector_examples.py --category 1 # 运行指定类别")
        print("  python run_vector_examples.py --help       # 显示帮助")
        print()
        print("示例类别:")
        for key, example in self.examples.items():
            print(f"  {key}: {example['name']}")
        print()
        print("环境要求:")
        print("  - Qdrant 向量数据库 (localhost:6334)")
        print("  - Elasticsearch (localhost:9200)")
        print("  - Python 3.11+ 和相关依赖")
        print()
        print("配置文件:")
        print("  - .env 文件中配置服务连接信息")
        print("  - 详见 examples/README_VECTOR_EXAMPLES.md")
    
    async def run_category(self, category_key: str):
        """运行指定类别的所有示例"""
        if category_key not in self.examples:
            self.safe_output.safe_print(f"{self.safe_output.format_status('error', f'无效的类别: {category_key}')}")
            return
        
        category = self.examples[category_key]
        category_name = category["name"]
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', f'运行类别: {category_name}', '🚀')}")
        self.safe_output.safe_print("="*60)
        
        await self.run_example(category['module'])
    
    def check_environment(self):
        """检查运行环境"""
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '检查运行环境...', '🔍')}")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 11):
            python_version_str = f"{python_version.major}.{python_version.minor}"
            self.safe_output.safe_print(f"{self.safe_output.format_status('warning', f'Python版本过低: {python_version_str}')}")
            print("   建议使用Python 3.11+")
        else:
            python_version_str = f"{python_version.major}.{python_version.minor}"
            self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'Python版本: {python_version_str}')}")
        
        # 检查必要的模块
        required_modules = [
            'asyncio', 'numpy', 'logging', 'time'
        ]
        
        missing_modules = []
        for module in required_modules:
            try:
                __import__(module)
                self.safe_output.safe_print(f"{self.safe_output.format_status('success', f'{module} 模块可用')}")
            except ImportError:
                missing_modules.append(module)
                self.safe_output.safe_print(f"{self.safe_output.format_status('error', f'{module} 模块缺失')}")
        
        if missing_modules:
            missing_modules_str = ', '.join(missing_modules)
            self.safe_output.safe_print(f"\n{self.safe_output.format_status('warning', f'缺失模块: {missing_modules_str}')}")
            print("请运行: uv sync")
        
        # 检查服务连接 (简单检查)
        self.safe_output.safe_print(f"\n{self.safe_output.format_status('info', '服务连接检查:', '📡')}")
        self.safe_output.safe_print("   请确保以下服务正在运行:")
        self.safe_output.safe_print("   - Qdrant: localhost:6334")
        print("   - Elasticsearch: localhost:9200")
        print("   详细连接测试将在示例运行时进行")


async def main():
    """主函数"""
    runner = VectorExamplesRunner()
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h']:
            runner.display_help()
            return
        elif arg == '--all':
            await runner.run_all_examples()
            return
        elif arg == '--category' and len(sys.argv) > 2:
            category = sys.argv[2]
            await runner.run_category(category)
            return
        elif arg == '--check':
            runner.check_environment()
            return
        else:
            runner.safe_output.safe_print(f"{runner.safe_output.format_status('error', f'未知参数: {arg}')}")
            runner.display_help()
            return
    
    # 默认交互式模式
    runner.safe_output.safe_print(runner.safe_output.format_status("info", "启动交互式模式...", "🎯"))
    runner.check_environment()
    await runner.interactive_mode()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_output = SafeOutput()
        safe_output.safe_print(f"\n\n{safe_output.format_status('info', '用户中断，程序退出', '👋')}")
    except Exception as e:
        safe_output = SafeOutput()
        safe_output.safe_print(f"\n{safe_output.format_status('error', f'程序运行出错: {e}')}")
        logger.error(f"程序异常: {e}")
        sys.exit(1)
