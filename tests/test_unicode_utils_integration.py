"""
Integration tests for the Unicode utilities package.

These tests verify that all components work together correctly and that
the public API functions as expected across different scenarios.
"""

import pytest
import sys
import io
from unittest.mock import patch, MagicMock
import logging

from src.utils.unicode_utils import (
    SafeOutput, ConsoleHandler, CharacterMap,
    configure, reset_configuration,
    safe_print, print_status, print_progress, print_section,
    is_unicode_supported, get_console_encoding, setup_unicode_console,
    get_console_info, test_unicode_output
)


class TestPackageInitialization:
    """Test package initialization and configuration."""
    
    def test_package_imports(self):
        """Test that all public API components can be imported."""
        # Test that main classes are available
        assert SafeOutput is not None
        assert ConsoleHandler is not None
        assert CharacterMap is not None
        
        # Test that convenience functions are available
        assert callable(safe_print)
        assert callable(print_status)
        assert callable(print_progress)
        assert callable(print_section)
        
        # Test that utility functions are available
        assert callable(is_unicode_supported)
        assert callable(get_console_encoding)
        assert callable(setup_unicode_console)
        assert callable(get_console_info)
        assert callable(test_unicode_output)
        
        # Test that configuration functions are available
        assert callable(configure)
        assert callable(reset_configuration)
    
    def test_auto_initialization(self):
        """Test that the package initializes automatically on import."""
        # The package should initialize without errors
        # This is tested by the successful import above
        
        # Test that console encoding can be detected
        encoding = get_console_encoding()
        assert isinstance(encoding, str)
        assert len(encoding) > 0
        
        # Test that Unicode support detection works
        unicode_support = is_unicode_supported()
        assert isinstance(unicode_support, bool)
    
    def test_configuration(self):
        """Test package configuration functionality."""
        # Test default configuration
        reset_configuration()
        
        # Test custom configuration
        test_stream = io.StringIO()
        configure(
            auto_setup=False,
            enable_unicode=True,
            log_level=logging.DEBUG,
            output_stream=test_stream
        )
        
        # Test that configuration affects behavior
        safe_print("Test message")
        output = test_stream.getvalue()
        assert "Test message" in output
        
        # Reset to defaults
        reset_configuration()


class TestConvenienceFunctions:
    """Test the convenience functions provided by the package."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.test_stream = io.StringIO()
        configure(output_stream=self.test_stream)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        reset_configuration()
    
    def test_safe_print(self):
        """Test the safe_print convenience function."""
        safe_print("Hello", "World")
        output = self.test_stream.getvalue()
        assert "Hello World" in output
        
        # Test with Unicode characters
        safe_print("Status: ✅ Success")
        output = self.test_stream.getvalue()
        assert "Status:" in output
        assert ("✅" in output or "[OK]" in output)  # Depends on Unicode support
    
    def test_print_status(self):
        """Test the print_status convenience function."""
        print_status("success", "Operation completed")
        output = self.test_stream.getvalue()
        assert "Operation completed" in output
        assert ("[OK]" in output or "✅" in output)
        
        print_status("error", "Something failed")
        output = self.test_stream.getvalue()
        assert "Something failed" in output
        assert ("[ERROR]" in output or "❌" in output)
    
    def test_print_progress(self):
        """Test the print_progress convenience function."""
        print_progress(50, 100, "Processing: ")
        output = self.test_stream.getvalue()
        assert "Processing:" in output
        assert "50.0%" in output
        assert "[" in output and "]" in output  # Progress bar brackets
    
    def test_print_section(self):
        """Test the print_section convenience function."""
        print_section("Test Section", level=1)
        output = self.test_stream.getvalue()
        assert "Test Section" in output
        
        # Should have some kind of border/formatting
        lines = output.strip().split('\n')
        assert len(lines) >= 2  # At least title and some formatting


class TestCrossComponentIntegration:
    """Test integration between different components."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.test_stream = io.StringIO()
        configure(output_stream=self.test_stream)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        reset_configuration()
    
    def test_unicode_and_ascii_modes(self):
        """Test that the package works in both Unicode and ASCII modes."""
        # Test Unicode mode
        configure(enable_unicode=True, output_stream=self.test_stream)
        safe_print("Unicode test: ✅")
        unicode_output = self.test_stream.getvalue()
        
        # Reset stream
        self.test_stream = io.StringIO()
        configure(enable_unicode=False, output_stream=self.test_stream)
        safe_print("ASCII test: ✅")
        ascii_output = self.test_stream.getvalue()
        
        # Both should contain the message, but with different symbols
        assert "Unicode test:" in unicode_output
        assert "ASCII test:" in ascii_output
        
        # ASCII mode should not contain Unicode characters
        if not is_unicode_supported():
            assert "✅" not in ascii_output
    
    def test_console_handler_integration(self):
        """Test integration with ConsoleHandler."""
        # Test that console info can be retrieved
        info = get_console_info()
        assert isinstance(info, dict)
        assert 'platform' in info
        assert 'detected_encoding' in info
        assert 'unicode_supported' in info
        
        # Test that encoding detection works
        encoding = get_console_encoding()
        assert encoding == info['detected_encoding']
        
        # Test that Unicode support detection is consistent
        unicode_support = is_unicode_supported()
        assert unicode_support == info['unicode_supported']
    
    def test_character_map_integration(self):
        """Test integration with CharacterMap."""
        # Create a SafeOutput instance and test character mapping
        output = SafeOutput(enable_unicode=False, output_stream=self.test_stream)
        
        # Test various Unicode characters
        test_chars = ['✅', '❌', '⚠️', '⏳', '█', '░', '→']
        for char in test_chars:
            output.safe_print(f"Test: {char}")
        
        result = self.test_stream.getvalue()
        
        # Should not contain Unicode characters in ASCII mode
        for char in test_chars:
            # Handle multi-byte Unicode characters properly
            try:
                if len(char) == 1 and ord(char) > 127:  # Single-char Unicode
                    assert char not in result
                elif len(char) > 1:  # Multi-byte Unicode (like emoji)
                    # For multi-byte characters, just check they're replaced
                    assert char not in result
            except (TypeError, ValueError):
                # Skip characters that can't be processed by ord()
                continue
    
    def test_error_handling_integration(self):
        """Test error handling across components."""
        # Test with a mock stream that raises UnicodeEncodeError
        class FailingStream:
            def write(self, text):
                if any(ord(c) > 127 for c in text):
                    raise UnicodeEncodeError('test', text, 0, 1, 'test error')
                return len(text)
            
            def flush(self):
                pass
        
        failing_stream = FailingStream()
        
        # Should handle the error gracefully
        output = SafeOutput(enable_unicode=True, output_stream=failing_stream)
        
        # This should not raise an exception
        try:
            output.safe_print("Test with Unicode: ✅")
        except UnicodeEncodeError:
            pytest.fail("SafeOutput should handle UnicodeEncodeError gracefully")


class TestPlatformCompatibility:
    """Test platform-specific functionality."""
    
    def test_windows_compatibility(self):
        """Test Windows-specific functionality."""
        with patch('platform.system', return_value='Windows'):
            # Test that Windows console setup can be attempted
            # (may fail in test environment, but should not crash)
            try:
                result = setup_unicode_console()
                assert isinstance(result, bool)
            except Exception as e:
                # Should not raise unhandled exceptions
                pytest.fail(f"Windows console setup raised unhandled exception: {e}")
    
    def test_unix_compatibility(self):
        """Test Unix-like system compatibility."""
        with patch('platform.system', return_value='Linux'):
            # Test that Unix console setup works
            try:
                result = setup_unicode_console()
                assert isinstance(result, bool)
            except Exception as e:
                pytest.fail(f"Unix console setup raised unhandled exception: {e}")
    
    def test_encoding_detection_fallback(self):
        """Test encoding detection with various failure scenarios."""
        # Test with encoding detection failure using locale patching
        with patch('locale.getpreferredencoding', side_effect=Exception("Test error")):
            encoding = get_console_encoding()
            assert isinstance(encoding, str)
            assert len(encoding) > 0
        
        # Test with subprocess failure for Windows codepage detection
        with patch('subprocess.run', side_effect=Exception("Test error")):
            encoding = get_console_encoding()
            assert isinstance(encoding, str)
            assert len(encoding) > 0


class TestPerformance:
    """Test performance characteristics of the package."""
    
    def test_initialization_performance(self):
        """Test that package initialization is reasonably fast."""
        import time
        
        start_time = time.time()
        
        # Reset and reconfigure multiple times
        for _ in range(10):
            reset_configuration()
            configure(auto_setup=True)
        
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
    
    def test_output_performance(self):
        """Test that output operations are reasonably fast."""
        import time
        
        test_stream = io.StringIO()
        configure(output_stream=test_stream)
        
        start_time = time.time()
        
        # Perform many output operations
        for i in range(100):
            safe_print(f"Test message {i} with Unicode: ✅")
        
        end_time = time.time()
        
        # Should complete in reasonable time
        assert end_time - start_time < 2.0
        
        reset_configuration()


class TestDocumentationExamples:
    """Test that examples from documentation work correctly."""
    
    def test_basic_usage_example(self):
        """Test the basic usage example from the module docstring."""
        test_stream = io.StringIO()
        configure(output_stream=test_stream)
        
        # Test class usage
        output = SafeOutput(output_stream=test_stream)
        output.safe_print("Status: ✅ Success")
        
        # Test convenience function usage
        safe_print("Status: ✅ Success")
        print_status("success", "Operation completed")
        print_progress(75, 100, "Processing: ")
        
        result = test_stream.getvalue()
        assert "Status:" in result
        assert "Success" in result
        assert "Operation completed" in result
        assert "Processing:" in result
        assert "75.0%" in result
        
        reset_configuration()
    
    def test_configuration_example(self):
        """Test configuration usage examples."""
        test_stream = io.StringIO()
        
        # Test configuration
        configure(
            auto_setup=False,
            enable_unicode=True,
            output_stream=test_stream
        )
        
        safe_print("Configured output test")
        result = test_stream.getvalue()
        assert "Configured output test" in result
        
        reset_configuration()
    
    def test_diagnostic_functions(self):
        """Test diagnostic and utility functions."""
        # These should all work without errors
        encoding = get_console_encoding()
        assert isinstance(encoding, str)
        
        unicode_support = is_unicode_supported()
        assert isinstance(unicode_support, bool)
        
        console_info = get_console_info()
        assert isinstance(console_info, dict)
        
        # Test output should work (captures to configured stream)
        test_stream = io.StringIO()
        configure(output_stream=test_stream)
        test_unicode_output()
        
        result = test_stream.getvalue()
        assert len(result) > 0  # Should produce some output
        
        reset_configuration()


if __name__ == '__main__':
    pytest.main([__file__])