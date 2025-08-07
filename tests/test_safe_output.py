"""
Unit tests for the SafeOutput class and related functionality.

Tests cover Unicode-safe printing, status formatting, progress indicators,
section headers, and error handling scenarios.
"""

import pytest
import sys
import io
from unittest.mock import Mock, patch, MagicMock
from src.utils.unicode_utils.safe_output import SafeOutput
from src.utils.unicode_utils.character_map import CharacterMap
from src.utils.unicode_utils.console_handler import ConsoleHandler


class TestSafeOutput:
    """Test cases for the SafeOutput class."""
    
    def test_init_with_unicode_enabled(self):
        """Test SafeOutput initialization with Unicode explicitly enabled."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        assert output.unicode_supported is True
    
    def test_init_with_unicode_disabled(self):
        """Test SafeOutput initialization with Unicode explicitly disabled."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        assert output.unicode_supported is False
    
    @patch('src.utils.unicode_utils.safe_output.ConsoleHandler.is_unicode_supported')
    def test_init_with_auto_detection(self, mock_is_unicode_supported):
        """Test SafeOutput initialization with automatic Unicode detection."""
        mock_is_unicode_supported.return_value = True
        
        output = SafeOutput(enable_unicode=None, auto_setup=False)
        mock_is_unicode_supported.assert_called_once()
    
    @patch('src.utils.unicode_utils.safe_output.ConsoleHandler.setup_unicode_console')
    def test_init_with_auto_setup(self, mock_setup_unicode_console):
        """Test SafeOutput initialization with automatic console setup."""
        mock_setup_unicode_console.return_value = True
        
        output = SafeOutput(auto_setup=True)
        mock_setup_unicode_console.assert_called_once()
    
    def test_safe_print_basic(self):
        """Test basic safe_print functionality."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        
        # Capture output
        captured_output = io.StringIO()
        output.safe_print("Hello", "World", file=captured_output)
        
        result = captured_output.getvalue()
        assert "Hello World" in result
    
    def test_safe_print_with_unicode_supported(self):
        """Test safe_print with Unicode characters when Unicode is supported."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        captured_output = io.StringIO()
        output.safe_print("Test ✅ Unicode", file=captured_output)
        
        result = captured_output.getvalue()
        assert "✅" in result
    
    def test_safe_print_with_unicode_not_supported(self):
        """Test safe_print with Unicode characters when Unicode is not supported."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        
        captured_output = io.StringIO()
        output.safe_print("Test ✅ Unicode", file=captured_output)
        
        result = captured_output.getvalue()
        assert "[OK]" in result
        assert "✅" not in result
    
    @patch('builtins.print')
    def test_safe_print_unicode_encode_error_handling(self, mock_print):
        """Test safe_print handling of UnicodeEncodeError."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        # Mock print to raise UnicodeEncodeError on first call
        mock_print.side_effect = [UnicodeEncodeError('utf-8', '✅', 0, 1, 'test error'), None]
        
        # This should not raise an exception
        output.safe_print("Test ✅ Unicode")
        
        # Should have been called twice (original attempt + fallback)
        assert mock_print.call_count == 2
    
    @patch('sys.stderr')
    @patch('builtins.print')
    def test_safe_print_general_exception_handling(self, mock_print, mock_stderr):
        """Test safe_print handling of general exceptions."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        # Mock print to raise a general exception
        mock_print.side_effect = Exception("General error")
        
        # This should not raise an exception
        output.safe_print("Test message")
        
        # Should have been called at least once (original attempt)
        mock_print.assert_called()
    
    def test_safe_print_custom_parameters(self):
        """Test safe_print with custom separator, end, and flush parameters."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        
        captured_output = io.StringIO()
        output.safe_print("A", "B", "C", sep="-", end="!\n", file=captured_output, flush=True)
        
        result = captured_output.getvalue()
        assert result == "A-B-C!\n"


class TestStatusFormatting:
    """Test cases for status message formatting."""
    
    def test_format_status_success(self):
        """Test formatting success status messages."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("success", "Operation completed")
        assert "✅" in result
        assert "Operation completed" in result
    
    def test_format_status_error(self):
        """Test formatting error status messages."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("error", "Something failed")
        assert "❌" in result
        assert "Something failed" in result
    
    def test_format_status_warning(self):
        """Test formatting warning status messages."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("warning", "Be careful")
        assert "⚠️" in result
        assert "Be careful" in result
    
    def test_format_status_info(self):
        """Test formatting info status messages."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("info", "Just so you know")
        assert "ℹ️" in result
        assert "Just so you know" in result
    
    def test_format_status_processing(self):
        """Test formatting processing status messages."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("processing", "Working on it")
        assert "⏳" in result
        assert "Working on it" in result
    
    def test_format_status_unknown_defaults_to_bullet(self):
        """Test that unknown status types default to bullet symbol."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("unknown", "Mystery message")
        assert "•" in result
        assert "Mystery message" in result
    
    def test_format_status_with_custom_symbol(self):
        """Test formatting status with custom symbol override."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_status("success", "Custom symbol", status_symbol="🎉")
        assert "🎉" in result
        assert "Custom symbol" in result
    
    def test_format_status_ascii_fallback(self):
        """Test status formatting with ASCII fallback."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_status("success", "ASCII mode")
        assert "[OK]" in result
        assert "ASCII mode" in result
        assert "✅" not in result
    
    def test_format_status_case_insensitive(self):
        """Test that status formatting is case insensitive."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        result_lower = output.format_status("success", "test")
        result_upper = output.format_status("SUCCESS", "test")
        result_mixed = output.format_status("Success", "test")
        
        # All should use the same symbol
        assert "✅" in result_lower
        assert "✅" in result_upper
        assert "✅" in result_mixed


class TestProgressFormatting:
    """Test cases for progress indicator formatting."""
    
    def test_format_progress_basic(self):
        """Test basic progress formatting."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(50, 100)
        
        assert "[" in result and "]" in result  # Progress bar brackets
        assert "50.0%" in result
    
    def test_format_progress_with_prefix(self):
        """Test progress formatting with prefix."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(25, 100, prefix="Loading")
        
        assert "Loading" in result
        assert "25.0%" in result
    
    def test_format_progress_zero_total(self):
        """Test progress formatting with zero total."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(10, 0)
        
        assert "0.0%" in result  # Should handle division by zero
    
    def test_format_progress_over_100_percent(self):
        """Test progress formatting when current exceeds total."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(150, 100)
        
        assert "100.0%" in result  # Should cap at 100%
    
    def test_format_progress_negative_values(self):
        """Test progress formatting with negative values."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(-10, 100)
        
        assert "0.0%" in result  # Should floor at 0%
    
    def test_format_progress_custom_width(self):
        """Test progress formatting with custom width."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(50, 100, bar_length=10)
        
        # Should contain a 10-character progress bar
        bar_start = result.find('[')
        bar_end = result.find(']')
        bar_content = result[bar_start+1:bar_end]
        assert len(bar_content) == 10
    
    def test_format_progress_custom_characters(self):
        """Test progress formatting with custom fill and empty characters."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(50, 100, fill_char="*", empty_char="-")
        
        assert "*" in result
        assert "-" in result
    
    def test_format_progress_unicode_characters(self):
        """Test progress formatting with Unicode characters when supported."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_progress(50, 100)
        
        # Should contain Unicode progress characters
        assert any(char in result for char in ["█", "░"])
    
    def test_format_progress_ascii_fallback(self):
        """Test progress formatting with ASCII fallback."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_progress(50, 100)
        
        # Should contain ASCII progress characters
        assert "#" in result or "." in result


class TestSectionFormatting:
    """Test cases for section header formatting."""
    
    def test_format_section_level_1(self):
        """Test level 1 section formatting (full border box)."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test Header", level=1)
        
        lines = result.split('\n')
        assert len(lines) == 3  # Top border, title, bottom border
        assert "Test Header" in lines[1]
    
    def test_format_section_level_2(self):
        """Test level 2 section formatting (title with underline)."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test Header", level=2)
        
        lines = result.split('\n')
        assert len(lines) == 2  # Title and underline
        assert "Test Header" in lines[0]
        assert len(lines[1]) == len("Test Header")  # Underline same length as title
    
    def test_format_section_level_3(self):
        """Test level 3 section formatting (simple prefix)."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test Header", level=3)
        
        assert "Test Header" in result
        assert result.startswith(".")  # Should have prefix (ASCII fallback for ·)
    
    def test_format_section_custom_width(self):
        """Test section formatting with custom width."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test", level=1, width=60)
        
        lines = result.split('\n')
        assert len(lines[0]) == 60  # Top border should be specified width
        assert len(lines[2]) == 60  # Bottom border should be specified width
    
    def test_format_section_custom_border_char(self):
        """Test section formatting with custom border character."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test", level=1, border_char="*")
        
        # "*" is ASCII so should remain unchanged
        assert "*" in result
    
    def test_format_section_unicode_borders(self):
        """Test section formatting with Unicode borders when supported."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output.format_section("Test", level=1)
        
        # Should contain Unicode border characters
        assert "═" in result
    
    def test_format_section_ascii_borders(self):
        """Test section formatting with ASCII borders when Unicode not supported."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output.format_section("Test", level=1)
        
        # Should contain ASCII border characters
        assert "=" in result


class TestTextSafety:
    """Test cases for text safety and Unicode handling."""
    
    def test_make_text_safe_unicode_supported(self):
        """Test _make_text_safe when Unicode is supported."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        result = output._make_text_safe("Test ✅ Unicode")
        
        assert result == "Test ✅ Unicode"  # Should remain unchanged
    
    def test_make_text_safe_unicode_not_supported(self):
        """Test _make_text_safe when Unicode is not supported."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        result = output._make_text_safe("Test ✅ Unicode")
        
        assert "✅" not in result
        assert "[OK]" in result


class TestCustomOutputStream:
    """Test cases for custom output stream functionality."""
    
    def test_custom_output_stream(self):
        """Test SafeOutput with custom output stream."""
        custom_stream = io.StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=custom_stream)
        
        output.safe_print("Test message")
        
        result = custom_stream.getvalue()
        assert "Test message" in result


class TestOutputTesting:
    """Test cases for the test_output method."""
    
    def test_test_output_runs_without_error(self):
        """Test that test_output method runs without throwing exceptions."""
        output = SafeOutput(enable_unicode=False, auto_setup=False)
        
        captured_output = io.StringIO()
        
        # Patch safe_print to capture output
        with patch.object(output, 'safe_print') as mock_print:
            mock_print.side_effect = lambda *args, **kwargs: None
            
            # This should not raise any exceptions
            output.test_output()
            
            # Should have made multiple calls to safe_print
            assert mock_print.call_count > 10


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    @patch('sys.stderr')
    @patch('src.utils.unicode_utils.safe_output.logger')
    def test_logging_on_unicode_error(self, mock_logger, mock_stderr):
        """Test that Unicode errors are properly logged."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        with patch('builtins.print') as mock_print:
            # Make print fail on first call, succeed on second (fallback)
            mock_print.side_effect = [UnicodeEncodeError('utf-8', '✅', 0, 1, 'test error'), None]
            
            # This should not raise an exception
            output.safe_print("Test ✅")
            
            # Should have logged the debug message
            mock_logger.debug.assert_called()
    
    @patch('sys.stderr')
    @patch('src.utils.unicode_utils.safe_output.logger')
    def test_logging_on_general_error(self, mock_logger, mock_stderr):
        """Test that general errors are properly logged."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = Exception("General error")
            
            output.safe_print("Test message")
            
            # Should have logged the error
            mock_logger.error.assert_called()
    
    def test_initialization_error_handling(self):
        """Test error handling during SafeOutput initialization."""
        with patch('src.utils.unicode_utils.safe_output.ConsoleHandler.setup_unicode_console') as mock_setup:
            mock_setup.side_effect = Exception("Handler error")
            
            # Should not raise exception, should fall back gracefully
            output = SafeOutput(auto_setup=True)
            assert output is not None


if __name__ == '__main__':
    pytest.main([__file__])