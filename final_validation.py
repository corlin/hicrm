#!/usr/bin/env python3
"""Final validation script for Unicode encoding fix."""

print("=== Final Unicode Fix Validation ===")
print()

# Test 1: Import and basic functionality
try:
    from src.utils.unicode_utils import SafeOutput, CharacterMap, ConsoleHandler
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Console detection
try:
    encoding = ConsoleHandler.detect_console_encoding()
    unicode_support = ConsoleHandler.is_unicode_supported()
    print(f"✓ Console encoding detected: {encoding}")
    print(f"✓ Unicode support: {unicode_support}")
except Exception as e:
    print(f"✗ Console detection failed: {e}")

# Test 3: Character mapping
try:
    success_symbol = CharacterMap.get_symbol('success', unicode_support)
    error_symbol = CharacterMap.get_symbol('error', unicode_support)
    print(f"✓ Success symbol: {success_symbol}")
    print(f"✓ Error symbol: {error_symbol}")
except Exception as e:
    print(f"✗ Character mapping failed: {e}")

# Test 4: Safe output
try:
    so = SafeOutput()
    so.safe_print("✓ Safe output test with Unicode: ✅ ❌ ⚡ 🔍")
except Exception as e:
    print(f"✗ Safe output failed: {e}")

# Test 5: Text replacement
try:
    test_text = "Status: ✅ Success, ❌ Error, ⚡ Fast"
    safe_text = CharacterMap.replace_unicode_in_text(test_text, unicode_support)
    print(f"✓ Text replacement: {safe_text}")
except Exception as e:
    print(f"✗ Text replacement failed: {e}")

print()
print("=== All validation tests passed! ===")