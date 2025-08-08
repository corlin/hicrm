"""
Pytest configuration for Unicode utilities tests.

Provides shared fixtures, configuration, and utilities for all Unicode tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add src to path for imports
test_dir = Path(__file__).parent
project_root = test_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

# Import fixtures from the fixtures package
from tests.fixtures import *


def pytest_configure(config):
    """Configure pytest for Unicode tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "cross_platform: marks tests as cross-platform tests"
    )
    config.addinivalue_line(
        "markers", "ci_cd: marks tests as CI/CD specific tests"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Add markers based on test file names
        if "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)
        
        if "cross_platform" in item.fspath.basename:
            item.add_marker(pytest.mark.cross_platform)
        
        if "ci_cd" in item.fspath.basename:
            item.add_marker(pytest.mark.ci_cd)
        
        if "integration" in item.fspath.basename:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ['performance', 'large', 'many', 'benchmark']):
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def project_paths():
    """Provide project path information."""
    return {
        'project_root': project_root,
        'src_dir': src_dir,
        'test_dir': test_dir,
    }


@pytest.fixture(scope="session")
def test_environment_info():
    """Provide information about the test environment."""
    import platform
    
    return {
        'platform': platform.system(),
        'python_version': sys.version,
        'encoding': sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'unknown',
        'is_ci': os.environ.get('CI', '').lower() == 'true',
        'is_docker': os.path.exists('/.dockerenv') or os.environ.get('container') == 'docker',
    }


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary test file."""
    test_file = tmp_path / "test_output.txt"
    yield test_file
    # Cleanup is automatic with tmp_path


@pytest.fixture
def mock_environment_variables():
    """Provide a context manager for mocking environment variables."""
    from unittest.mock import patch
    
    def _mock_env(**env_vars):
        return patch.dict(os.environ, env_vars)
    
    return _mock_env


@pytest.fixture
def capture_logs():
    """Capture log messages during tests."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Add handler to Unicode utils logger
    logger = logging.getLogger('src.utils.unicode_utils')
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    yield log_capture
    
    # Cleanup
    logger.removeHandler(handler)
    logger.setLevel(original_level)


@pytest.fixture
def performance_timer():
    """Provide a performance timer for tests."""
    import time
    
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time is None:
                return 0
            end = self.end_time or time.time()
            return end - self.start_time
    
    return PerformanceTimer()


@pytest.fixture
def unicode_test_strings():
    """Provide various Unicode test strings."""
    return {
        'simple': "Hello ✅ World",
        'complex': "🤖 AI: Processing █████░░░░░ 50% → Complete ✅",
        'mixed': "Status: ✅ Success | Error: ❌ Failed | Warning: ⚠️ Alert",
        'borders': "╔═══════════════╗\n║ Test Section  ║\n╚═══════════════╝",
        'progress': "Progress: █████████░ 90% ⚡ Almost done!",
        'emoji': "🚀 Launch 🎯 Target 💡 Idea 📊 Stats 🔍 Search",
        'symbols': "→ ← ↑ ↓ • ◦ ▸ ★ ☆ ♦ ◊",
        'empty': "",
        'ascii_only': "ASCII only text with no Unicode",
        'long': "Long text with Unicode " + "✅ " * 100,
    }


@pytest.fixture
def expected_ascii_fallbacks():
    """Provide expected ASCII fallbacks for Unicode characters."""
    return {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',
        'ℹ️': '[INFO]',
        '⏳': '[PROCESSING]',
        '🤖': '[BOT]',
        '🔍': '[SEARCH]',
        '🚀': '?',  # No specific mapping, should use fallback
        '█': '#',
        '░': '.',
        '→': '->',
        '←': '<-',
        '•': '*',
        '★': '*',
        '═': '=',
        '─': '-',
        '│': '|',
        '┌': '+',
    }


# Pytest hooks for better test reporting

def pytest_runtest_setup(item):
    """Setup for each test."""
    # Print test name for verbose output
    if item.config.getoption("verbose"):
        print(f"\n🧪 Running: {item.name}")


def pytest_runtest_teardown(item, nextitem):
    """Teardown for each test."""
    # Reset any global state if needed
    from src.utils.unicode_utils import reset_configuration
    try:
        reset_configuration()
    except Exception:
        pass  # Ignore errors during cleanup


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Add custom terminal summary."""
    if exitstatus == 0:
        terminalreporter.write_line("🎉 All Unicode tests passed!", green=True)
    else:
        terminalreporter.write_line("💥 Some Unicode tests failed!", red=True)


# Custom assertion helpers

def assert_unicode_handled_correctly(original_text, processed_text, unicode_supported):
    """Assert that Unicode text was handled correctly."""
    if unicode_supported:
        assert original_text == processed_text, "Unicode should be preserved when supported"
    else:
        # Check that problematic Unicode characters were replaced
        unicode_chars = ['✅', '❌', '⚠️', '⏳', '🤖', '🔍', '█', '░', '→', '★', '═']
        for char in unicode_chars:
            if char in original_text:
                assert char not in processed_text, f"Unicode character {char} should have been replaced"


def assert_no_encoding_errors(func, *args, **kwargs):
    """Assert that a function doesn't raise encoding errors."""
    try:
        result = func(*args, **kwargs)
        return result
    except UnicodeEncodeError as e:
        pytest.fail(f"Function {func.__name__} raised UnicodeEncodeError: {e}")
    except UnicodeDecodeError as e:
        pytest.fail(f"Function {func.__name__} raised UnicodeDecodeError: {e}")


# Make assertion helpers available globally
pytest.assert_unicode_handled_correctly = assert_unicode_handled_correctly
pytest.assert_no_encoding_errors = assert_no_encoding_errors