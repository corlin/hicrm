"""
Backwards compatibility tests for Unicode utilities.

Tests that existing functionality is preserved and that the Unicode utilities
don't break existing code or introduce regressions.
"""

import pytest
import sys
import os
from io import StringIO
from unittest.mock import patch, MagicMock

from src.utils.unicode_utils import SafeOutput, ConsoleHandler, CharacterMap
from src.utils.unicode_utils import safe_print, print_status, print_progress, print_section


class TestExistingFunctionalityPreservation:
    """Test that existing functionality continues to work as expected."""
    
    def test_basic_print_functionality(self):
        """Test that basic print functionality is preserved."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test basic print operations that should work exactly like print()
        output.safe_print("Hello, World!")
        output.safe_print("Multiple", "arguments", "test")
        output.safe_print("Custom separator", "test", sep=" | ")
        output.safe_print("Custom ending", end=" END\n")
        
        result = test_stream.getvalue()
        
        # Should behave like standard print
        assert "Hello, World!" in result
        assert "Multiple arguments test" in result
        assert "Custom separator | test" in result
        assert "Custom ending END" in result
    
    def test_print_parameters_compatibility(self):
        """Test that all print() parameters are supported."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test all standard print parameters
        output.safe_print("Test", "message", sep="-", end="!\n", flush=True)
        
        result = test_stream.getvalue()
        assert "Test-message!" in result
    
    def test_exception_handling_preservation(self):
        """Test that exception handling doesn't break existing behavior."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test with various data types that might cause issues
        test_values = [
            None,
            42,
            3.14,
            True,
            [],
            {},
            object(),
        ]
        
        for value in test_values:
            # Should not raise exceptions
            try:
                output.safe_print(f"Value: {value}")
            except Exception as e:
                pytest.fail(f"safe_print should handle {type(value)} without exception: {e}")
        
        result = test_stream.getvalue()
        assert "Value: None" in result
        assert "Value: 42" in result
        assert "Value: 3.14" in result


class TestAPICompatibility:
    """Test that the public API remains compatible."""
    
    def test_class_initialization_compatibility(self):
        """Test that class initialization remains compatible."""
        # Test default initialization
        output1 = SafeOutput()
        assert output1 is not None
        
        # Test with parameters
        test_stream = StringIO()
        output2 = SafeOutput(enable_unicode=True, auto_setup=False, output_stream=test_stream)
        assert output2 is not None
        assert output2.unicode_supported is True
        
        # Test with None parameters (should not break)
        output3 = SafeOutput(enable_unicode=None, output_stream=None)
        assert output3 is not None
    
    def test_method_signatures_compatibility(self):
        """Test that method signatures remain compatible."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test that all expected methods exist and are callable
        assert hasattr(output, 'safe_print')
        assert callable(output.safe_print)
        
        assert hasattr(output, 'format_status')
        assert callable(output.format_status)
        
        assert hasattr(output, 'format_progress')
        assert callable(output.format_progress)
        
        assert hasattr(output, 'format_section')
        assert callable(output.format_section)
        
        # Test method calls with various parameter combinations
        output.safe_print("test")
        output.safe_print("test", "multiple")
        output.safe_print("test", sep=" ", end="\n")
        
        status = output.format_status("success", "message")
        assert isinstance(status, str)
        
        progress = output.format_progress(50, 100)
        assert isinstance(progress, str)
        
        section = output.format_section("title")
        assert isinstance(section, str)
    
    def test_property_compatibility(self):
        """Test that properties remain accessible."""
        output = SafeOutput(enable_unicode=True, auto_setup=False)
        
        # Test that unicode_supported property exists and works
        assert hasattr(output, 'unicode_supported')
        assert isinstance(output.unicode_supported, bool)
    
    def test_convenience_function_compatibility(self):
        """Test that convenience functions remain compatible."""
        test_stream = StringIO()
        
        from src.utils.unicode_utils import configure
        configure(output_stream=test_stream, auto_setup=False)
        
        # Test that all convenience functions exist and work
        safe_print("test message")
        print_status("success", "test status")
        print_progress(50, 100, "test progress")
        print_section("test section")
        
        result = test_stream.getvalue()
        assert "test message" in result
        assert "test status" in result
        assert "test progress" in result
        assert "test section" in result


class TestConsoleHandlerCompatibility:
    """Test that ConsoleHandler maintains compatibility."""
    
    def test_static_method_compatibility(self):
        """Test that static methods remain accessible."""
        # Test that all expected static methods exist
        assert hasattr(ConsoleHandler, 'detect_console_encoding')
        assert callable(ConsoleHandler.detect_console_encoding)
        
        assert hasattr(ConsoleHandler, 'is_unicode_supported')
        assert callable(ConsoleHandler.is_unicode_supported)
        
        assert hasattr(ConsoleHandler, 'setup_unicode_console')
        assert callable(ConsoleHandler.setup_unicode_console)
        
        assert hasattr(ConsoleHandler, 'get_console_info')
        assert callable(ConsoleHandler.get_console_info)
        
        # Test that methods return expected types
        encoding = ConsoleHandler.detect_console_encoding()
        assert isinstance(encoding, str)
        
        unicode_support = ConsoleHandler.is_unicode_supported()
        assert isinstance(unicode_support, bool)
        
        setup_result = ConsoleHandler.setup_unicode_console()
        assert isinstance(setup_result, bool)
        
        console_info = ConsoleHandler.get_console_info()
        assert isinstance(console_info, dict)
    
    def test_console_info_structure_compatibility(self):
        """Test that console info maintains expected structure."""
        info = ConsoleHandler.get_console_info()
        
        # Test that expected keys exist
        expected_keys = [
            'platform',
            'detected_encoding',
            'unicode_supported',
            'safe_encoding',
            'stdout_encoding',
            'stderr_encoding',
        ]
        
        for key in expected_keys:
            assert key in info, f"Expected key '{key}' missing from console info"


class TestCharacterMapCompatibility:
    """Test that CharacterMap maintains compatibility."""
    
    def test_character_map_initialization(self):
        """Test that CharacterMap initializes correctly."""
        char_map = CharacterMap()
        assert char_map is not None
    
    def test_character_map_methods(self):
        """Test that CharacterMap methods work as expected."""
        char_map = CharacterMap()
        
        # Test get_symbol method
        symbol = char_map.get_symbol('✅', unicode_supported=False)
        assert isinstance(symbol, str)
        assert symbol == '[OK]'
        
        # Test replace_unicode_in_text method
        text = "Status: ✅ Success"
        result = char_map.replace_unicode_in_text(text, unicode_supported=False)
        assert isinstance(result, str)
        assert "✅" not in result
        assert "[OK]" in result
    
    def test_character_map_categories(self):
        """Test that character map categories work correctly."""
        char_map = CharacterMap()
        
        # Test category methods
        categories = char_map.get_available_categories()
        assert isinstance(categories, list)
        assert 'status' in categories
        assert 'progress' in categories
        assert 'decoration' in categories
        
        # Test getting symbols by category
        status_symbols = char_map.get_symbols_in_category('status')
        assert isinstance(status_symbols, dict)
        assert '✅' in status_symbols


class TestRegressionPrevention:
    """Test that specific issues don't regress."""
    
    def test_unicode_encode_error_handling(self):
        """Test that UnicodeEncodeError is handled without breaking functionality."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=True, auto_setup=False, output_stream=test_stream)
        
        # Mock print to raise UnicodeEncodeError
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = [
                UnicodeEncodeError('utf-8', '✅', 0, 1, 'test error'),
                None  # Second call succeeds
            ]
            
            # Should not raise exception
            output.safe_print("Test ✅ message")
            
            # Should have attempted fallback
            assert mock_print.call_count == 2
    
    def test_none_encoding_handling(self):
        """Test that None encoding values don't break functionality."""
        mock_stdout = MagicMock()
        mock_stdout.encoding = None
        mock_stderr = MagicMock()
        mock_stderr.encoding = None
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr):
            
            # Should not raise exception
            encoding = ConsoleHandler.detect_console_encoding()
            assert isinstance(encoding, str)
            
            # Should not break SafeOutput initialization
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            output.safe_print("Test message")
            
            result = test_stream.getvalue()
            assert "Test message" in result
    
    def test_missing_attributes_handling(self):
        """Test that missing attributes don't break functionality."""
        # Mock stdout without encoding attribute
        mock_stdout = MagicMock()
        del mock_stdout.encoding  # Remove encoding attribute
        
        with patch.object(sys, 'stdout', mock_stdout):
            # Should not raise AttributeError
            try:
                encoding = ConsoleHandler.detect_console_encoding()
                assert isinstance(encoding, str)
            except AttributeError:
                pytest.fail("Should handle missing encoding attribute gracefully")
    
    def test_platform_detection_failure_handling(self):
        """Test that platform detection failures don't break functionality."""
        with patch('platform.system', side_effect=Exception("Platform detection failed")):
            # Should not raise exception
            encoding = ConsoleHandler.detect_console_encoding()
            assert isinstance(encoding, str)
            
            # Should still be able to create SafeOutput
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            output.safe_print("Test message")
            
            result = test_stream.getvalue()
            assert "Test message" in result


class TestExistingScriptCompatibility:
    """Test that existing scripts continue to work."""
    
    def test_example_script_patterns(self):
        """Test common patterns used in example scripts."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Common patterns from example scripts
        output.safe_print("🤖 Starting RAG Service Demo")
        output.safe_print("✅ Connection established")
        output.safe_print("⚡ Processing query...")
        output.safe_print("📊 Results:")
        output.safe_print("  • Item 1")
        output.safe_print("  • Item 2")
        output.safe_print("✅ Demo completed successfully")
        
        result = test_stream.getvalue()
        
        # Should produce output without errors
        assert "RAG Service Demo" in result
        assert "Connection established" in result
        assert "Processing query" in result
        assert "Results:" in result
        assert "Item 1" in result
        assert "Demo completed" in result
    
    def test_status_message_patterns(self):
        """Test common status message patterns."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Common status patterns
        statuses = [
            ("success", "Operation completed"),
            ("error", "Something went wrong"),
            ("warning", "This is a warning"),
            ("info", "Information message"),
            ("processing", "Working on it..."),
        ]
        
        for status, message in statuses:
            formatted = output.format_status(status, message)
            output.safe_print(formatted)
        
        result = test_stream.getvalue()
        
        # Should contain all messages
        for _, message in statuses:
            assert message in result
    
    def test_progress_indicator_patterns(self):
        """Test common progress indicator patterns."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Common progress patterns
        for i in range(0, 101, 25):
            progress = output.format_progress(i, 100, f"Step {i//25 + 1}: ")
            output.safe_print(progress)
        
        result = test_stream.getvalue()
        
        # Should contain progress indicators
        assert "Step 1:" in result
        assert "Step 5:" in result
        assert "0.0%" in result
        assert "100.0%" in result


class TestConfigurationCompatibility:
    """Test that configuration system maintains compatibility."""
    
    def test_configuration_functions(self):
        """Test that configuration functions work correctly."""
        from src.utils.unicode_utils import configure, reset_configuration
        
        test_stream = StringIO()
        
        # Test configuration
        configure(
            auto_setup=False,
            enable_unicode=True,
            output_stream=test_stream
        )
        
        safe_print("Configured test")
        result = test_stream.getvalue()
        assert "Configured test" in result
        
        # Test reset
        reset_configuration()
        
        # Should still work after reset
        safe_print("Reset test")
    
    def test_module_level_imports(self):
        """Test that module-level imports continue to work."""
        # Test that all expected symbols can be imported
        from src.utils.unicode_utils import (
            SafeOutput, ConsoleHandler, CharacterMap,
            safe_print, print_status, print_progress, print_section,
            is_unicode_supported, get_console_encoding, setup_unicode_console,
            configure, reset_configuration
        )
        
        # Test that they are all callable/usable
        assert SafeOutput is not None
        assert ConsoleHandler is not None
        assert CharacterMap is not None
        assert callable(safe_print)
        assert callable(print_status)
        assert callable(print_progress)
        assert callable(print_section)
        assert callable(is_unicode_supported)
        assert callable(get_console_encoding)
        assert callable(setup_unicode_console)
        assert callable(configure)
        assert callable(reset_configuration)


class TestVersionCompatibility:
    """Test compatibility across different Python versions."""
    
    def test_python_version_compatibility(self):
        """Test that the code works with current Python version."""
        # Test basic functionality
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        output.safe_print("Python version test")
        result = test_stream.getvalue()
        assert "Python version test" in result
        
        # Test that version-specific features work
        assert sys.version_info >= (3, 8), "Unicode utilities require Python 3.8+"
    
    def test_typing_compatibility(self):
        """Test that type hints don't break functionality."""
        # Test that classes can be instantiated despite type hints
        char_map = CharacterMap()
        assert char_map is not None
        
        handler = ConsoleHandler()
        assert handler is not None
        
        test_stream = StringIO()
        output = SafeOutput(output_stream=test_stream)
        assert output is not None


if __name__ == '__main__':
    pytest.main([__file__])