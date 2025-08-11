"""
Debug imports to find the hanging issue
"""

print("Starting import debug...")

try:
    print("1. Importing basic modules...")
    import json
    import logging
    from typing import Dict, List, Any, Optional, Union
    from datetime import datetime, timedelta
    from dataclasses import dataclass
    from enum import Enum
    print("✓ Basic modules imported")
    
    print("2. Importing base agent...")
    from src.agents.base import BaseAgent, AgentMessage, AgentResponse, AgentCapability
    print("✓ Base agent imported")
    
    print("3. Importing lead service...")
    from src.services.lead_service import LeadService
    print("✓ Lead service imported")
    
    print("4. Importing lead scoring service...")
    from src.services.lead_scoring_service import LeadScoringService
    print("✓ Lead scoring service imported")
    
    print("5. Importing llm service...")
    from src.services.llm_service import llm_service
    print("✓ LLM service imported")
    
    print("6. Importing rag service...")
    from src.services.rag_service import rag_service, RAGMode
    print("✓ RAG service imported")
    
    print("7. Importing database...")
    from src.core.database import get_db
    print("✓ Database imported")
    
    print("8. All imports successful!")
    
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()