#!/usr/bin/env python3
"""
测试导入
"""

import sys
sys.path.append('.')

try:
    from src.agents.orchestrator import AgentOrchestrator
    print('✓ AgentOrchestrator import successful')
except Exception as e:
    print(f'✗ AgentOrchestrator import failed: {e}')

try:
    from src.agents.base import AgentMessage, AgentResponse
    print('✓ Base classes import successful')
except Exception as e:
    print(f'✗ Base classes import failed: {e}')

try:
    import pytest
    print('✓ pytest import successful')
except Exception as e:
    print(f'✗ pytest import failed: {e}')

print("All import tests completed.")