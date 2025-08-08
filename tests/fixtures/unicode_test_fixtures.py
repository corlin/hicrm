"""
Test fixtures for Unicode utilities testing.

Provides reusable test fixtures for different console encoding scenarios,
mock objects, and test data for comprehensive Unicode testing.
"""

import pytest
import sys
import os
from io import StringIO
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List, Tuple

from src.utils.unicode_utils import SafeOutput, ConsoleHandler, CharacterMap


class MockConsoleEnvironment:
    """Mock console environment for testing different encoding scenarios."""
    
    def __init__(self, platform: str, encoding: str, unicode_support: bool = None):
        """
        Initialize mock console environment.
        
        Args:
            platform: Platform name ('Windows', 'Linux', 'Darwin')
            encoding: Console encoding ('utf-8', 'gbk', 'cp1252', etc.)
            unicode_support: Whether Unicode is supported (auto-detected if None)
        """
        self.platform = platform
        self.encoding = encoding
        self.unicode_support = unicode_support if unicode_support is not None else ('utf' in encoding.lower())
        
        # Create mock stdout/stderr
        self.mock_stdout = MagicMock()
        self.mock_stdout.encoding = encoding
        self.mock_stderr = MagicMock()
        self.mock_stderr.encoding = encoding
        
        # Create mock subprocess result for Windows
        self.mock_subprocess_result = MagicMock()
        self.mock_subprocess_result.returncode = 0
        if platform == 'Windows':
            if encoding == 'gbk':
                self.mock_subprocess_result.stdout = 'Active code page: 936'
            elif encoding == 'utf-8':
                self.mock_subprocess_result.stdout = 'Active code page: 65001'
            else:
                self.mock_subprocess_result.stdout = 'Active code page: 1252'
    
    def __enter__(self):
        """Enter context manager and apply mocks."""
        self.patches = []
        
        # Mock platform
        platform_patch = patch('platform.system', return_value=self.platform)
        self.patches.append(platform_patch)
        platform_patch.start()
        
        # Mock stdout/stderr
        stdout_patch = patch.object(sys, 'stdout', self.mock_stdout)
        stderr_patch = patch.object(sys, 'stderr', self.mock_stderr)
        self.patches.extend([stdout_patch, stderr_patch])
        stdout_patch.start()
        stderr_patch.start()
        
        # Mock subprocess for Windows
        if self.platform == 'Windows':
            subprocess_patch = patch('subprocess.run', return_value=self.mock_subprocess_result)
            self.patches.append(subprocess_patch)
            subprocess_patch.start()
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and clean up mocks."""
        for patch_obj in reversed(self.patches):
            patch_obj.stop()


@pytest.fixture
def windows_gbk_environment():
    """Fixture for Windows GBK console environment."""
    return MockConsoleEnvironment('Windows', 'gbk', unicode_support=False)


@pytest.fixture
def windows_utf8_environment():
    """Fixture for Windows UTF-8 console environment."""
    return MockConsoleEnvironment('Windows', 'utf-8', unicode_support=True)


@pytest.fixture
def linux_utf8_environment():
    """Fixture for Linux UTF-8 console environment."""
    return MockConsoleEnvironment('Linux', 'utf-8', unicode_support=True)


@pytest.fixture
def macos_environment():
    """Fixture for macOS console environment."""
    return MockConsoleEnvironment('Darwin', 'utf-8', unicode_support=True)


@pytest.fixture
def ascii_only_environment():
    """Fixture for ASCII-only console environment."""
    return MockConsoleEnvironment('Linux', 'ascii', unicode_support=False)


class UnicodeTestData:
    """Test data for Unicode character testing."""
    
    # Status symbols with their expected ASCII fallbacks
    STATUS_SYMBOLS = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        'ℹ️': '[INFO]',
        '⏳': '[PROCESSING]',
        '🔍': '[SEARCH]',
        '🤖': '[BOT]',
        '💡': '[INFO]',
        '🎯': '[TARGET]',
    }
    
    # Progress symbols with their expected ASCII fallbacks
    PROGRESS_SYMBOLS = {
        '█': '#',
        '░': '.',
        '→': '->',
        '←': '<-',
        '•': '*',
        '○': 'o',
        '●': '*',
        '▸': '>',
    }
    
    # Decoration symbols with their expected ASCII fallbacks
    DECORATION_SYMBOLS = {
        '═': '=',
        '─': '-',
        '│': '|',
        '┌': '+',
        '┐': '+',
        '└': '+',
        '┘': '+',
        '★': '*',
        '♦': '*',
    }
    
    # Combined symbols for comprehensive testing
    ALL_SYMBOLS = {**STATUS_SYMBOLS, **PROGRESS_SYMBOLS, **DECORATION_SYMBOLS}
    
    # Sample text with various Unicode characters
    SAMPLE_TEXTS = [
        "Status: ✅ Success",
        "Error: ❌ Failed",
        "Progress: █████░░░░░ 50%",
        "Navigation: ← Back | Next →",
        "Border: ═══════════",
        "List: • Item 1 • Item 2",
        "Rating: ★★★★☆",
        "🤖 AI Assistant: Hello! 👋",
        "⚡ Fast processing ⏳ Please wait...",
        "📊 Statistics: 95% complete ✅",
    ]
    
    # Complex text with mixed Unicode
    COMPLEX_TEXT = """
🤖 RAG Service Demo
═══════════════════

✅ Connection established
⚡ Processing query...
📊 Results:
  • Item 1: Success ✅
  • Item 2: Warning ⚠️
  • Item 3: Error ❌

Progress: █████░░░░░ 50%
Navigation: ← Back | Next →

★ Rating: 4/5 stars
⏳ Processing time: 2.3s
✅ Demo completed successfully
"""


@pytest.fixture
def unicode_test_data():
    """Fixture providing Unicode test data."""
    return UnicodeTestData()


@pytest.fixture
def test_output_stream():
    """Fixture providing a test output stream."""
    return StringIO()


@pytest.fixture
def safe_output_unicode(test_output_stream):
    """Fixture providing SafeOutput with Unicode enabled."""
    return SafeOutput(enable_unicode=True, auto_setup=False, output_stream=test_output_stream)


@pytest.fixture
def safe_output_ascii(test_output_stream):
    """Fixture providing SafeOutput with Unicode disabled."""
    return SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_output_stream)


@pytest.fixture
def character_map():
    """Fixture providing a CharacterMap instance."""
    return CharacterMap()


class EncodingTestScenarios:
    """Predefined encoding test scenarios."""
    
    SCENARIOS = [
        {
            'name': 'Windows GBK',
            'platform': 'Windows',
            'encoding': 'gbk',
            'unicode_support': False,
            'codepage': '936',
        },
        {
            'name': 'Windows UTF-8',
            'platform': 'Windows', 
            'encoding': 'utf-8',
            'unicode_support': True,
            'codepage': '65001',
        },
        {
            'name': 'Windows CP1252',
            'platform': 'Windows',
            'encoding': 'cp1252',
            'unicode_support': False,
            'codepage': '1252',
        },
        {
            'name': 'Linux UTF-8',
            'platform': 'Linux',
            'encoding': 'utf-8',
            'unicode_support': True,
            'lang': 'en_US.UTF-8',
        },
        {
            'name': 'Linux ASCII',
            'platform': 'Linux',
            'encoding': 'ascii',
            'unicode_support': False,
            'lang': 'C',
        },
        {
            'name': 'macOS UTF-8',
            'platform': 'Darwin',
            'encoding': 'utf-8',
            'unicode_support': True,
        },
        {
            'name': 'CI/CD ASCII',
            'platform': 'Linux',
            'encoding': 'ascii',
            'unicode_support': False,
            'ci_environment': True,
        },
    ]


@pytest.fixture(params=EncodingTestScenarios.SCENARIOS)
def encoding_scenario(request):
    """Parametrized fixture for different encoding scenarios."""
    scenario = request.param
    
    # Create mock environment based on scenario
    mock_env = MockConsoleEnvironment(
        scenario['platform'],
        scenario['encoding'],
        scenario['unicode_support']
    )
    
    # Add scenario-specific environment variables
    env_patches = []
    if 'lang' in scenario:
        env_patch = patch.dict(os.environ, {'LANG': scenario['lang']})
        env_patches.append(env_patch)
        env_patch.start()
    
    if scenario.get('ci_environment'):
        ci_patch = patch.dict(os.environ, {'CI': 'true', 'TERM': 'dumb'})
        env_patches.append(ci_patch)
        ci_patch.start()
    
    # Return scenario with mock environment and cleanup function
    def cleanup():
        for patch_obj in reversed(env_patches):
            patch_obj.stop()
    
    scenario['mock_env'] = mock_env
    scenario['cleanup'] = cleanup
    
    return scenario


class PerformanceTestData:
    """Test data for performance testing."""
    
    # Small test data
    SMALL_TEXT = "Test ✅"
    SMALL_ITERATIONS = 100
    
    # Medium test data
    MEDIUM_TEXT = "Status: ✅ Success → Progress: █████░░░░░ 50% ⚠️ Warning"
    MEDIUM_ITERATIONS = 1000
    
    # Large test data
    LARGE_TEXT = ("Test message with Unicode ✅ " * 100)
    LARGE_ITERATIONS = 10000
    
    # Performance thresholds (in seconds)
    THRESHOLDS = {
        'encoding_detection': 0.01,  # Per detection
        'symbol_lookup': 0.0001,     # Per lookup
        'text_replacement': 0.001,   # Per replacement
        'safe_print': 0.002,         # Per print
        'formatting': 0.0005,        # Per format operation
    }


@pytest.fixture
def performance_test_data():
    """Fixture providing performance test data."""
    return PerformanceTestData()


class MockFailingStream:
    """Mock stream that fails on Unicode characters."""
    
    def __init__(self, fail_on_unicode: bool = True):
        """
        Initialize failing stream.
        
        Args:
            fail_on_unicode: Whether to fail on Unicode characters
        """
        self.fail_on_unicode = fail_on_unicode
        self.written_data = []
    
    def write(self, text: str) -> int:
        """Write text, potentially failing on Unicode."""
        if self.fail_on_unicode and any(ord(c) > 127 for c in text):
            raise UnicodeEncodeError('test', text, 0, 1, 'Mock Unicode error')
        
        self.written_data.append(text)
        return len(text)
    
    def flush(self):
        """Flush the stream (no-op)."""
        pass
    
    def getvalue(self) -> str:
        """Get all written data."""
        return ''.join(self.written_data)


@pytest.fixture
def failing_unicode_stream():
    """Fixture providing a stream that fails on Unicode."""
    return MockFailingStream(fail_on_unicode=True)


@pytest.fixture
def working_stream():
    """Fixture providing a stream that works with all characters."""
    return MockFailingStream(fail_on_unicode=False)


class TestDataGenerator:
    """Generator for various test data patterns."""
    
    @staticmethod
    def generate_unicode_text_samples(count: int = 10) -> List[str]:
        """Generate sample texts with Unicode characters."""
        samples = []
        unicode_chars = ['✅', '❌', '⚠️', '⏳', '🔍', '█', '░', '→', '★', '═']
        
        for i in range(count):
            char = unicode_chars[i % len(unicode_chars)]
            samples.append(f"Sample {i}: {char} Test message")
        
        return samples
    
    @staticmethod
    def generate_status_messages(count: int = 5) -> List[Tuple[str, str]]:
        """Generate status message pairs."""
        statuses = ['success', 'error', 'warning', 'info', 'processing']
        messages = []
        
        for i in range(count):
            status = statuses[i % len(statuses)]
            message = f"Test message {i} for {status}"
            messages.append((status, message))
        
        return messages
    
    @staticmethod
    def generate_progress_data(count: int = 10) -> List[Tuple[int, int, str]]:
        """Generate progress data tuples."""
        progress_data = []
        
        for i in range(count):
            current = i * 10
            total = 100
            prefix = f"Task {i}: "
            progress_data.append((current, total, prefix))
        
        return progress_data


@pytest.fixture
def test_data_generator():
    """Fixture providing test data generator."""
    return TestDataGenerator()


# Utility functions for test fixtures

def create_mock_console_with_encoding(encoding: str, platform: str = 'Linux') -> MockConsoleEnvironment:
    """Create a mock console environment with specific encoding."""
    return MockConsoleEnvironment(platform, encoding)


def assert_unicode_replacement(original_text: str, processed_text: str, unicode_supported: bool):
    """Assert that Unicode replacement happened correctly."""
    if unicode_supported:
        # Unicode should be preserved
        assert original_text == processed_text
    else:
        # Unicode should be replaced
        unicode_chars = ['✅', '❌', '⚠️', '⏳', '🔍', '█', '░', '→', '★', '═']
        for char in unicode_chars:
            if char in original_text:
                assert char not in processed_text, f"Unicode character {char} should have been replaced"


def measure_performance(func, *args, **kwargs) -> float:
    """Measure the performance of a function call."""
    import time
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    return end_time - start_time, result


# Export commonly used fixtures and utilities
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