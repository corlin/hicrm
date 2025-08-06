"""
Unicode utilities package for handling cross-platform Unicode output.

This package provides utilities for safe Unicode character output with automatic
fallback to ASCII alternatives when Unicode is not supported by the console.

Main components:
- SafeOutput: Main utility class for Unicode-safe printing
- ConsoleHandler: Console encoding detection and setup
- CharacterMap: Unicode to ASCII character mappings

Usage:
    from src.utils.unicode_utils import SafeOutput
    
    output = SafeOutput()
    output.safe_print("Status: ✅ Success")
"""

# Import main components when they're implemented
# These imports will be uncommented as we implement each component

# from .safe_output import SafeOutput
# from .console_handler import ConsoleHandler  
# from .character_map import CharacterMap

# Public API exports
__all__ = [
    # 'SafeOutput',
    # 'ConsoleHandler', 
    # 'CharacterMap',
]

# Version information
__version__ = "1.0.0"