#!/usr/bin/env python3
"""
修复编码问题
"""

import os

def fix_file(filepath):
    """修复单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换emoji
        replacements = [
            ('🚀', '[启动]'),
            ('📦', '[组件]'),
            ('📝', '[文本]'),
            ('🔍', '[搜索]'),
            ('📊', '[统计]'),
            ('🤖', '[AI]'),
            ('⚡', '[性能]'),
            ('🌐', '[网络]'),
            ('🧹', '[清理]'),
            ('🎯', '[目标]'),
            ('💡', '[提示]'),
            ('🔧', '[配置]'),
            ('🎪', '[场景]'),
            ('📈', '[分析]'),
            ('🚨', '[注意]'),
            ('🎉', '[完成]'),
            ('📞', '[支持]'),
            ('✅', '[成功]'),
            ('❌', '[失败]'),
            ('⭐', '[评分]'),
            ('🔄', '[处理]'),
            ('💭', '[生成]'),
            ('📚', '[来源]'),
            ('🏆', '[推荐]'),
            ('💾', '[内存]'),
            ('🔗', '[接口]'),
            ('🐍', '[Python]'),
            ('📖', '[文档]'),
            ('💼', '[业务]'),
            ('🎓', '[教育]')
        ]
        
        for emoji, replacement in replacements:
            content = content.replace(emoji, replacement)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Fixed: {filepath}")
        return True
        
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

# 修复文件
files = [
    'examples/rag_service_examples.py',
    'examples/rag_simple_demo.py', 
    'examples/run_rag_examples.py'
]

for file in files:
    if os.path.exists(file):
        fix_file(file)
    else:
        print(f"File not found: {file}")

print("Done!")