"""
Unit tests for the character mapping system.
"""

import pytest
from src.utils.unicode_utils.character_map import CharacterMap


class TestCharacterMap:
    """Test cases for the CharacterMap class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.char_map = CharacterMap()
    
    def test_get_symbol_unicode_supported(self):
        """Test get_symbol returns Unicode when supported."""
        result = self.char_map.get_symbol('✅', unicode_supported=True)
        assert result == '✅'
        
        result = self.char_map.get_symbol('→', unicode_supported=True)
        assert result == '→'
    
    def test_get_symbol_unicode_not_supported(self):
        """Test get_symbol returns ASCII fallback when Unicode not supported."""
        result = self.char_map.get_symbol('✅', unicode_supported=False)
        assert result == '[OK]'
        
        result = self.char_map.get_symbol('❌', unicode_supported=False)
        assert result == '[ERROR]'
        
        result = self.char_map.get_symbol('→', unicode_supported=False)
        assert result == '->'
    
    def test_get_symbol_with_category_hint(self):
        """Test get_symbol with category hint."""
        result = self.char_map.get_symbol('✅', category='status', unicode_supported=False)
        assert result == '[OK]'
        
        result = self.char_map.get_symbol('→', category='progress', unicode_supported=False)
        assert result == '->'
    
    def test_get_symbol_unknown_character(self):
        """Test get_symbol with unknown Unicode character."""
        result = self.char_map.get_symbol('🦄', unicode_supported=False)
        # Should return hex code placeholder
        assert result == '[1F984]'
    
    def test_replace_unicode_in_text_supported(self):
        """Test replace_unicode_in_text when Unicode is supported."""
        text = "Status: ✅ Success → Complete"
        result = self.char_map.replace_unicode_in_text(text, unicode_supported=True)
        assert result == text  # Should be unchanged
    
    def test_replace_unicode_in_text_not_supported(self):
        """Test replace_unicode_in_text when Unicode is not supported."""
        text = "Status: ✅ Success → Complete"
        result = self.char_map.replace_unicode_in_text(text, unicode_supported=False)
        assert result == "Status: [OK] Success -> Complete"
    
    def test_replace_unicode_complex_text(self):
        """Test replace_unicode_in_text with complex text."""
        text = "Progress: █████░░░░░ 50% ✅ Done ❌ Failed"
        result = self.char_map.replace_unicode_in_text(text, unicode_supported=False)
        expected = "Progress: #####..... 50% [OK] Done [ERROR] Failed"
        assert result == expected
    
    def test_get_available_categories(self):
        """Test get_available_categories returns correct categories."""
        categories = self.char_map.get_available_categories()
        assert 'status' in categories
        assert 'progress' in categories
        assert 'decoration' in categories
        assert len(categories) == 3
    
    def test_get_symbols_in_category_status(self):
        """Test get_symbols_in_category for status symbols."""
        symbols = self.char_map.get_symbols_in_category('status')
        assert '✅' in symbols
        assert symbols['✅'] == '[OK]'
        assert '❌' in symbols
        assert symbols['❌'] == '[ERROR]'
    
    def test_get_symbols_in_category_progress(self):
        """Test get_symbols_in_category for progress symbols."""
        symbols = self.char_map.get_symbols_in_category('progress')
        assert '→' in symbols
        assert symbols['→'] == '->'
        assert '█' in symbols
        assert symbols['█'] == '#'
    
    def test_get_symbols_in_category_decoration(self):
        """Test get_symbols_in_category for decoration symbols."""
        symbols = self.char_map.get_symbols_in_category('decoration')
        assert '─' in symbols
        assert symbols['─'] == '-'
        assert '★' in symbols
        assert symbols['★'] == '*'
    
    def test_get_symbols_in_category_invalid(self):
        """Test get_symbols_in_category with invalid category."""
        with pytest.raises(ValueError, match="Invalid category: invalid"):
            self.char_map.get_symbols_in_category('invalid')
    
    def test_add_custom_mapping(self):
        """Test adding custom Unicode to ASCII mapping."""
        self.char_map.add_custom_mapping('🎉', '[PARTY]', 'status')
        
        result = self.char_map.get_symbol('🎉', unicode_supported=False)
        assert result == '[PARTY]'
        
        # Verify it's in the status category
        status_symbols = self.char_map.get_symbols_in_category('status')
        assert '🎉' in status_symbols
        assert status_symbols['🎉'] == '[PARTY]'
    
    def test_add_custom_mapping_invalid_category(self):
        """Test adding custom mapping with invalid category."""
        with pytest.raises(ValueError, match="Invalid category: invalid"):
            self.char_map.add_custom_mapping('🎉', '[PARTY]', 'invalid')
    
    def test_category_map_isolation(self):
        """Test that category maps are properly isolated."""
        # Get a copy of status symbols
        status_symbols = self.char_map.get_symbols_in_category('status')
        original_count = len(status_symbols)
        
        # Modify the returned dictionary
        status_symbols['🔥'] = '[FIRE]'
        
        # Verify the original mapping wasn't affected
        new_status_symbols = self.char_map.get_symbols_in_category('status')
        assert len(new_status_symbols) == original_count
        assert '🔥' not in new_status_symbols
    
    def test_comprehensive_symbol_coverage(self):
        """Test that all major symbol types are covered."""
        # Test status symbols
        status_tests = [
            ('✅', '[OK]'),
            ('❌', '[ERROR]'),
            ('⚠', '[WARNING]'),
            ('ℹ', '[INFO]'),
        ]
        
        for unicode_char, expected in status_tests:
            result = self.char_map.get_symbol(unicode_char, unicode_supported=False)
            assert result == expected, f"Failed for {unicode_char}"
        
        # Test progress symbols
        progress_tests = [
            ('█', '#'),
            ('→', '->'),
            ('•', '*'),
            ('●', '*'),
        ]
        
        for unicode_char, expected in progress_tests:
            result = self.char_map.get_symbol(unicode_char, unicode_supported=False)
            assert result == expected, f"Failed for {unicode_char}"
        
        # Test decoration symbols
        decoration_tests = [
            ('─', '-'),
            ('│', '|'),
            ('┌', '+'),
            ('★', '*'),
        ]
        
        for unicode_char, expected in decoration_tests:
            result = self.char_map.get_symbol(unicode_char, unicode_supported=False)
            assert result == expected, f"Failed for {unicode_char}"