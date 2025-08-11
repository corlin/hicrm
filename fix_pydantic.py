#!/usr/bin/env python3
"""
修复Pydantic deprecation warnings
"""

import re

def fix_pydantic_dict_calls():
    """修复.dict()调用为.model_dump()"""
    
    file_path = "src/agents/orchestrator.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换 workflow_state.dict() 为 workflow_state.model_dump()
    content = re.sub(r'workflow_state\.dict\(\)', 'workflow_state.model_dump()', content)
    
    # 替换 final_state.dict() 为 final_state.model_dump()
    content = re.sub(r'final_state\.dict\(\)', 'final_state.model_dump()', content)
    
    # 替换 initial_state.dict() 为 initial_state.model_dump()
    content = re.sub(r'initial_state\.dict\(\)', 'initial_state.model_dump()', content)
    
    # 替换 response.dict() 为 response.model_dump()
    content = re.sub(r'response\.dict\(\)', 'response.model_dump()', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Fixed Pydantic deprecation warnings")

if __name__ == "__main__":
    fix_pydantic_dict_calls()