"""
Test fixtures package for Unicode utilities testing.

This package provides reusable test fixtures, mock objects, and test data
for comprehensive testing of the Unicode utilities across different platforms
and encoding scenarios.
"""

from .unicode_test_fixtures import *

__all__ = [
    'MockConsoleEnvironment',
    'UnicodeTestData', 
    'EncodingTestScenarios',
    'PerformanceTestData',
    'MockFailingStream',
    'TestDataGenerator',
    'windows_gbk_environment',
    'windows_utf8_environment', 
    'linux_utf8_environment',
    'macos_environment',
    'ascii_only_environment',
    'unicode_test_data',
    'test_output_stream',
    'safe_output_unicode',
    'safe_output_ascii',
    'character_map',
    'encoding_scenario',
    'performance_test_data',
    'failing_unicode_stream',
    'working_stream',
    'test_data_generator',
    'create_mock_console_with_encoding',
    'assert_unicode_replacement',
    'measure_performance',
]