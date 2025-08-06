#!/usr/bin/env python3
"""
修复emoji编码问题的脚本
"""

import os
import re

def fix_emoji_in_file(file_path):
    """修复文件中的emoji字符"""
    
    # emoji到文本的映射
    emoji_map = {
        '🚀': '[启动]',
        '📦': '[组件]',
        '📝': '[文本]',
        '🔍': '[搜索]',
        '📊': '[统计]',
        '🤖': '[AI]',
        '⚡': '[性能]',
        '🌐': '[网络]',
        '🧹': '[清理]',
        '🎯': '[目标]',
        '💡': '[提示]',
        '🔧': '[配置]',
        '🎪': '[场景]',
        '📈': '[分析]',
        '🚨': '[注意]',
        '🎉': '[完成]',
        '📞': '[支持]',
        '✅': '[成功]',
        '❌': '[失败]',
        '⭐': '[评分]',
        '🔄': '[处理]',
        '💭': '[生成]',
        '📚': '[来源]',
        '🏆': '[推荐]',
        '💾': '[内存]',
        '🔗': '[接口]',
        '🐍': '[Python]',
        '📖': '[文档]',
        '💼': '[业务]',
        '🎓': '[教育]'
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换emoji
        for emoji, replacement in emoji_map.items():
            content = content.replace(emoji, replacement)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 修复完成: {file_path}")
        return True
        
    except Exception as e:
        print(f"✗ 修复失败: {file_path} - {e}")
        return False

def main():
    """主函数"""
    files_to_fix = [
        'examples/rag_service_examples.py',
        'examples/rag_simple_demo.py',
        'examples/run_rag_examples.py'
    ]
    
    print("开始修复emoji编码问题...")
    
    success_count = 0
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            if fix_emoji_in_file(file_path):
                success_count += 1
        else:
            print(f"✗ 文件不存在: {file_path}")
    
    print(f"\n修复完成: {success_count}/{len(files_to_fix)} 个文件")

if __name__ == "__main__":
    main()