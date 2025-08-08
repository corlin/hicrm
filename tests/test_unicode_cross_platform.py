"""
Cross-platform integration tests for Unicode utilities.

Tests Unicode handling across different platforms (Windows GBK, Linux UTF-8, macOS)
and various console encoding scenarios.
"""

import pytest
import sys
import os
import platform
from unittest.mock import patch, MagicMock
from io import StringIO

from src.utils.unicode_utils import SafeOutput, ConsoleHandler, CharacterMap
from src.utils.unicode_utils import safe_print, print_status, print_progress, print_section


class TestWindowsGBKIntegration:
    """Test Unicode utilities on Windows with GBK encoding."""
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_windows_gbk_encoding_detection(self, mock_run, mock_platform):
        """Test encoding detection on Windows GBK system."""
        mock_platform.return_value = 'Windows'
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'Active code page: 936'
        mock_run.return_value = mock_result
        
        # Mock stdout/stderr to have no encoding
        mock_stdout = MagicMock()
        mock_stdout.encoding = None
        mock_stderr = MagicMock()
        mock_stderr.encoding = None
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr), \
             patch('locale.getpreferredencoding', side_effect=Exception()):
            
            encoding = ConsoleHandler.detect_console_encoding()
            assert encoding == 'gbk'
    
    @patch('platform.system')
    def test_windows_gbk_unicode_support(self, mock_platform):
        """Test Unicode support detection on Windows GBK."""
        mock_platform.return_value = 'Windows'
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='gbk'):
            # GBK should not support full Unicode
            supported = ConsoleHandler.is_unicode_supported()
            # This depends on the actual test character encoding capability
            assert isinstance(supported, bool)
    
    @patch('platform.system')
    def test_windows_gbk_safe_output(self, mock_platform):
        """Test SafeOutput behavior on Windows GBK system."""
        mock_platform.return_value = 'Windows'
        test_stream = StringIO()
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='gbk'), \
             patch.object(ConsoleHandler, 'is_unicode_supported', return_value=False):
            
            output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
            
            # Test various Unicode characters
            output.safe_print("Status: ✅ Success")
            output.safe_print("Progress: █████░░░░░ 50%")
            output.safe_print("Warning: ⚠️ Be careful")
            
            result = test_stream.getvalue()
            
            # Should contain ASCII fallbacks, not Unicode
            assert "[OK]" in result
            assert "✅" not in result
            assert "#####....." in result
            assert "█" not in result and "░" not in result
            assert "[WARNING]" in result
            assert "⚠️" not in result
    
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('codecs.getwriter')
    def test_windows_unicode_console_setup(self, mock_getwriter, mock_run, mock_platform):
        """Test Unicode console setup on Windows."""
        mock_platform.return_value = 'Windows'
        
        # Mock successful chcp command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock codecs.getwriter
        mock_writer = MagicMock()
        mock_getwriter.return_value = mock_writer
        
        # Mock stdout and stderr with buffer
        mock_stdout = MagicMock()
        mock_stdout.buffer = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.buffer = MagicMock()
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr):
            
            result = ConsoleHandler.setup_unicode_console()
            assert result is True
            
            # Verify chcp was called to set UTF-8
            mock_run.assert_called_with(['chcp', '65001'], capture_output=True, shell=True)
            
            # Verify codecs.getwriter was called for both streams
            assert mock_getwriter.call_count == 2


class TestLinuxUTF8Integration:
    """Test Unicode utilities on Linux with UTF-8 encoding."""
    
    @patch('platform.system')
    @patch.dict(os.environ, {'LANG': 'en_US.UTF-8'})
    def test_linux_utf8_encoding_detection(self, mock_platform):
        """Test encoding detection on Linux UTF-8 system."""
        mock_platform.return_value = 'Linux'
        
        mock_stdout = MagicMock()
        mock_stdout.encoding = None
        mock_stderr = MagicMock()
        mock_stderr.encoding = None
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr), \
             patch('locale.getpreferredencoding', side_effect=Exception()):
            
            encoding = ConsoleHandler.detect_console_encoding()
            assert encoding == 'utf-8'
    
    @patch('platform.system')
    def test_linux_utf8_unicode_support(self, mock_platform):
        """Test Unicode support detection on Linux UTF-8."""
        mock_platform.return_value = 'Linux'
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='utf-8'):
            supported = ConsoleHandler.is_unicode_supported()
            # UTF-8 should support Unicode
            assert supported is True
    
    @patch('platform.system')
    def test_linux_utf8_safe_output(self, mock_platform):
        """Test SafeOutput behavior on Linux UTF-8 system."""
        mock_platform.return_value = 'Linux'
        test_stream = StringIO()
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='utf-8'), \
             patch.object(ConsoleHandler, 'is_unicode_supported', return_value=True):
            
            output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
            
            # Test various Unicode characters
            output.safe_print("Status: ✅ Success")
            output.safe_print("Progress: █████░░░░░ 50%")
            output.safe_print("Warning: ⚠️ Be careful")
            
            result = test_stream.getvalue()
            
            # Should contain Unicode characters
            assert "✅" in result
            assert "█" in result and "░" in result
            assert "⚠️" in result
    
    @patch('platform.system')
    def test_linux_unicode_console_setup(self, mock_platform):
        """Test Unicode console setup on Linux."""
        mock_platform.return_value = 'Linux'
        
        # Clear PYTHONIOENCODING if it exists
        original_env = os.environ.get('PYTHONIOENCODING')
        if 'PYTHONIOENCODING' in os.environ:
            del os.environ['PYTHONIOENCODING']
        
        try:
            with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='ascii'):
                result = ConsoleHandler.setup_unicode_console()
                assert result is True
                assert os.environ.get('PYTHONIOENCODING') == 'utf-8'
        finally:
            # Restore original environment
            if original_env is not None:
                os.environ['PYTHONIOENCODING'] = original_env
            elif 'PYTHONIOENCODING' in os.environ:
                del os.environ['PYTHONIOENCODING']


class TestMacOSIntegration:
    """Test Unicode utilities on macOS."""
    
    @patch('platform.system')
    def test_macos_encoding_detection(self, mock_platform):
        """Test encoding detection on macOS."""
        mock_platform.return_value = 'Darwin'
        
        mock_stdout = MagicMock()
        mock_stdout.encoding = None
        mock_stderr = MagicMock()
        mock_stderr.encoding = None
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr), \
             patch('locale.getpreferredencoding', side_effect=Exception()):
            
            encoding = ConsoleHandler.detect_console_encoding()
            assert encoding == 'utf-8'
    
    @patch('platform.system')
    def test_macos_unicode_support(self, mock_platform):
        """Test Unicode support detection on macOS."""
        mock_platform.return_value = 'Darwin'
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='utf-8'):
            supported = ConsoleHandler.is_unicode_supported()
            assert supported is True
    
    @patch('platform.system')
    def test_macos_safe_output(self, mock_platform):
        """Test SafeOutput behavior on macOS."""
        mock_platform.return_value = 'Darwin'
        test_stream = StringIO()
        
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='utf-8'), \
             patch.object(ConsoleHandler, 'is_unicode_supported', return_value=True):
            
            output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
            
            # Test various Unicode characters
            output.safe_print("Status: ✅ Success")
            output.safe_print("Progress: █████░░░░░ 50%")
            output.safe_print("Border: ═══════════")
            
            result = test_stream.getvalue()
            
            # Should contain Unicode characters
            assert "✅" in result
            assert "█" in result and "░" in result
            assert "═" in result


class TestEncodingScenarios:
    """Test various console encoding scenarios."""
    
    @pytest.mark.parametrize("encoding,expected_unicode_support", [
        ('utf-8', True),
        ('utf-16', True),
        ('gbk', False),
        ('cp1252', False),
        ('ascii', False),
        ('latin1', False),
    ])
    def test_encoding_unicode_support_detection(self, encoding, expected_unicode_support):
        """Test Unicode support detection for various encodings."""
        with patch.object(ConsoleHandler, 'detect_console_encoding', return_value=encoding):
            # Mock the actual encoding test
            if expected_unicode_support:
                with patch('str.encode', return_value=b'test'):
                    supported = ConsoleHandler.is_unicode_supported()
                    assert supported is True
            else:
                with patch('str.encode', side_effect=UnicodeEncodeError('test', '✓', 0, 1, 'test')):
                    supported = ConsoleHandler.is_unicode_supported()
                    assert supported is False
    
    def test_mixed_encoding_environment(self):
        """Test behavior when stdout and stderr have different encodings."""
        mock_stdout = MagicMock()
        mock_stdout.encoding = 'utf-8'
        mock_stderr = MagicMock()
        mock_stderr.encoding = 'gbk'
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr):
            
            # Should prefer stdout encoding
            encoding = ConsoleHandler.detect_console_encoding()
            assert encoding == 'utf-8'
    
    def test_no_encoding_information(self):
        """Test behavior when no encoding information is available."""
        mock_stdout = MagicMock()
        mock_stdout.encoding = None
        mock_stderr = MagicMock()
        mock_stderr.encoding = None
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.object(sys, 'stderr', mock_stderr), \
             patch('locale.getpreferredencoding', side_effect=Exception()), \
             patch('platform.system', side_effect=Exception()):
            
            encoding = ConsoleHandler.detect_console_encoding()
            assert encoding == 'ascii'  # Should fall back to ascii


class TestRealWorldScenarios:
    """Test real-world usage scenarios across platforms."""
    
    def test_example_script_compatibility(self):
        """Test that example scripts work across different encoding scenarios."""
        test_scenarios = [
            ('Windows', 'gbk', False),
            ('Linux', 'utf-8', True),
            ('Darwin', 'utf-8', True),
        ]
        
        for platform_name, encoding, unicode_support in test_scenarios:
            with patch('platform.system', return_value=platform_name), \
                 patch.object(ConsoleHandler, 'detect_console_encoding', return_value=encoding), \
                 patch.object(ConsoleHandler, 'is_unicode_supported', return_value=unicode_support):
                
                test_stream = StringIO()
                output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
                
                # Simulate example script output
                output.safe_print("🤖 RAG Service Demo")
                output.safe_print(output.format_status("success", "✅ Connection established"))
                output.safe_print(output.format_progress(75, 100, "Processing: "))
                output.safe_print(output.format_section("Results", level=1))
                
                result = test_stream.getvalue()
                
                # Should not crash and should produce output
                assert len(result) > 0
                assert "RAG Service Demo" in result
                assert "Connection established" in result
                assert "Processing:" in result
                assert "Results" in result
                
                # Check encoding-appropriate symbols
                if unicode_support:
                    assert ("🤖" in result or "[BOT]" in result)  # May be replaced by character map
                    assert ("✅" in result or "[OK]" in result)
                else:
                    assert "[BOT]" in result
                    assert "[OK]" in result
                    assert "🤖" not in result
                    assert "✅" not in result
    
    def test_ci_cd_environment_compatibility(self):
        """Test compatibility with CI/CD environments."""
        # Simulate CI environment with minimal encoding support
        mock_stdout = MagicMock()
        mock_stdout.encoding = 'ascii'
        
        with patch.object(sys, 'stdout', mock_stdout), \
             patch.dict(os.environ, {'CI': 'true', 'TERM': 'dumb'}):
            
            test_stream = StringIO()
            output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
            
            # Test various output types
            output.safe_print("CI/CD Test Output")
            output.safe_print(output.format_status("success", "Build passed"))
            output.safe_print(output.format_status("error", "Test failed"))
            output.safe_print(output.format_progress(100, 100, "Deploy: "))
            
            result = test_stream.getvalue()
            
            # Should work in CI environment
            assert "CI/CD Test Output" in result
            assert "[OK]" in result
            assert "[ERROR]" in result
            assert "Deploy:" in result
            assert "100.0%" in result
    
    def test_docker_container_compatibility(self):
        """Test compatibility with Docker containers."""
        # Simulate Docker environment
        with patch.dict(os.environ, {'container': 'docker'}), \
             patch('platform.system', return_value='Linux'):
            
            test_stream = StringIO()
            
            # Test with limited encoding
            with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='ascii'), \
                 patch.object(ConsoleHandler, 'is_unicode_supported', return_value=False):
                
                output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
                
                # Test container-typical output
                output.safe_print("Container startup: ✅")
                output.safe_print("Health check: ❌")
                output.safe_print(output.format_progress(50, 100, "Loading: "))
                
                result = test_stream.getvalue()
                
                # Should use ASCII fallbacks
                assert "[OK]" in result
                assert "[ERROR]" in result
                assert "Loading:" in result
                assert "✅" not in result
                assert "❌" not in result


class TestErrorRecovery:
    """Test error recovery across different platform scenarios."""
    
    def test_encoding_detection_failure_recovery(self):
        """Test recovery when encoding detection fails."""
        with patch.object(ConsoleHandler, 'detect_console_encoding', side_effect=Exception("Detection failed")):
            
            test_stream = StringIO()
            
            # Should not crash, should fall back gracefully
            try:
                output = SafeOutput(enable_unicode=None, auto_setup=False, output_stream=test_stream)
                output.safe_print("Test message with ✅")
                
                result = test_stream.getvalue()
                assert "Test message" in result
                
            except Exception as e:
                pytest.fail(f"Should not raise exception on encoding detection failure: {e}")
    
    def test_console_setup_failure_recovery(self):
        """Test recovery when console setup fails."""
        with patch.object(ConsoleHandler, 'setup_unicode_console', side_effect=Exception("Setup failed")):
            
            test_stream = StringIO()
            
            # Should not crash, should continue with auto_setup=True
            try:
                output = SafeOutput(auto_setup=True, output_stream=test_stream)
                output.safe_print("Test message")
                
                result = test_stream.getvalue()
                assert "Test message" in result
                
            except Exception as e:
                pytest.fail(f"Should not raise exception on console setup failure: {e}")
    
    def test_unicode_encode_error_recovery(self):
        """Test recovery from UnicodeEncodeError during output."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=True, auto_setup=False, output_stream=test_stream)
        
        # Mock print to raise UnicodeEncodeError on first call
        with patch('builtins.print') as mock_print:
            mock_print.side_effect = [
                UnicodeEncodeError('utf-8', '✅', 0, 1, 'test error'),
                None  # Second call succeeds
            ]
            
            # Should not raise exception, should fall back
            output.safe_print("Test ✅ message")
            
            # Should have been called twice (original + fallback)
            assert mock_print.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__])