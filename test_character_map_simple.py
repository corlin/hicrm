#!/usr/bin/env python3
"""
Simple test script for character mapping functionality.
"""

import sys
sys.path.append('.')

from src.utils.unicode_utils.character_map import CharacterMap

def test_character_mapping():
    """Test the character mapping functionality."""
    print("Testing Character Mapping System...")
    
    char_map = CharacterMap()
    
    # Test Unicode supported
    print("\n1. Testing with Unicode support:")
    test_chars = ['✅', '❌', '→', '█', '─']
    for char in test_chars:
        result = char_map.get_symbol(char, unicode_supported=True)
        print(f"  {char} -> {result}")
    
    # Test Unicode not supported
    print("\n2. Testing without Unicode support:")
    for char in test_chars:
        result = char_map.get_symbol(char, unicode_supported=False)
        print(f"  {char} -> {result}")
    
    # Test text replacement
    print("\n3. Testing text replacement:")
    test_text = "Status: ✅ Success → Complete ❌ Failed"
    print(f"  Original: {test_text}")
    
    result_unicode = char_map.replace_unicode_in_text(test_text, unicode_supported=True)
    print(f"  Unicode:  {result_unicode}")
    
    result_ascii = char_map.replace_unicode_in_text(test_text, unicode_supported=False)
    print(f"  ASCII:    {result_ascii}")
    
    # Test categories
    print("\n4. Testing categories:")
    categories = char_map.get_available_categories()
    print(f"  Available categories: {categories}")
    
    for category in categories:
        symbols = char_map.get_symbols_in_category(category)
        print(f"  {category}: {len(symbols)} symbols")
        # Show first few symbols
        items = list(symbols.items())[:3]
        for unicode_char, ascii_fallback in items:
            print(f"    {unicode_char} -> {ascii_fallback}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    test_character_mapping()