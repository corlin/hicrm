"""
Unicode utilities package for handling cross-platform Unicode output.

This package provides utilities for safe Unicode character output with automatic
fallback to ASCII alternatives when Unicode is not supported by the console.

Main components:
- SafeOutput: Main utility class for Unicode-safe printing
- ConsoleHandler: Console encoding detection and setup
- CharacterMap: Unicode to ASCII character mappings

Usage:
    from src.utils.unicode_utils import SafeOutput, safe_print
    
    # Using the class directly
    output = SafeOutput()
    output.safe_print("Status: ✅ Success")
    
    # Using convenience functions
    safe_print("Status: ✅ Success")
    print_status("success", "Operation completed")
    print_progress(75, 100, "Processing: ")
"""

import logging
from typing import Optional, Any, TextIO
from .safe_output import SafeOutput
from .console_handler import ConsoleHandler  
from .character_map import CharacterMap

# Module-level configuration
_config = {
    'auto_setup': True,
    'enable_unicode': None,  # None means auto-detect
    'log_level': logging.WARNING,
    'default_output_stream': None,  # None means sys.stdout
}

# Global SafeOutput instance for convenience functions
_global_output: Optional[SafeOutput] = None

# Configure logging
logger = logging.getLogger(__name__)


def configure(auto_setup: bool = True, 
              enable_unicode: Optional[bool] = None,
              log_level: int = logging.WARNING,
              output_stream: Optional[TextIO] = None) -> None:
    """
    Configure the Unicode utilities package.
    
    Args:
        auto_setup: Whether to automatically setup Unicode console support
        enable_unicode: Force enable/disable Unicode (None for auto-detect)
        log_level: Logging level for the package
        output_stream: Default output stream (None for sys.stdout)
    """
    global _config, _global_output
    
    _config.update({
        'auto_setup': auto_setup,
        'enable_unicode': enable_unicode,
        'log_level': log_level,
        'default_output_stream': output_stream,
    })
    
    # Configure logging
    logging.getLogger(__name__).setLevel(log_level)
    
    # Reset global output instance to pick up new config
    _global_output = None
    
    logger.debug(f"Unicode utilities configured: {_config}")


def _get_global_output() -> SafeOutput:
    """Get or create the global SafeOutput instance."""
    global _global_output
    
    if _global_output is None:
        _global_output = SafeOutput(
            enable_unicode=_config['enable_unicode'],
            auto_setup=_config['auto_setup'],
            output_stream=_config['default_output_stream']
        )
        logger.debug("Created global SafeOutput instance")
    
    return _global_output


# Convenience functions for common use cases
def safe_print(*args, **kwargs) -> None:
    """
    Unicode-safe print function with automatic fallback.
    
    This is a convenience function that uses the global SafeOutput instance.
    It automatically handles Unicode characters that might cause encoding
    errors on systems with limited console support (like Windows GBK).
    
    All arguments are passed through to SafeOutput.safe_print(), which
    means it supports all the same parameters as the built-in print()
    function, including sep, end, file, and flush.
    
    Args:
        *args: Values to print (any objects that can be converted to strings)
        **kwargs: Keyword arguments for print function:
            - sep: String inserted between values (default: ' ')
            - end: String appended after the last value (default: '\n')
            - file: File object to write to (default: sys.stdout)
            - flush: Whether to forcibly flush the stream (default: False)
    
    Example:
        >>> safe_print("Status:", "✅", "Success")
        Status: ✅ Success
        
        >>> safe_print("Progress:", "█" * 5, "░" * 5)
        Progress: █████░░░░░
        
        >>> safe_print("Error:", "❌", "Failed", file=sys.stderr)
        Error: ❌ Failed
    
    Note:
        On systems that don't support Unicode, characters like ✅ will
        automatically be replaced with ASCII alternatives like [OK].
    """
    _get_global_output().safe_print(*args, **kwargs)


def print_status(status: str, message: str, **kwargs) -> None:
    """
    Print a formatted status message with appropriate symbol.
    
    This function automatically selects an appropriate symbol based on the
    status type and formats it consistently. On Unicode-capable systems,
    it uses emoji symbols; on limited systems, it uses ASCII alternatives.
    
    Args:
        status: Status type. Supported values:
            - 'success', 'ok', 'pass' → ✅ (or [OK])
            - 'error', 'fail', 'failed' → ❌ (or [ERROR])
            - 'warning', 'warn' → ⚠️ (or [WARNING])
            - 'info' → ℹ️ (or [INFO])
            - 'processing', 'loading' → ⏳ (or [PROCESSING])
        message: The status message text to display
        **kwargs: Additional arguments passed to safe_print() such as
            file, flush, etc.
    
    Example:
        >>> print_status("success", "File uploaded successfully")
        ✅ File uploaded successfully
        
        >>> print_status("error", "Connection timeout")
        ❌ Connection timeout
        
        >>> print_status("warning", "Disk space low")
        ⚠️ Disk space low
    
    Note:
        The status parameter is case-insensitive. Unknown status types
        will use a generic bullet point symbol (• or *).
    """
    output = _get_global_output()
    formatted_message = output.format_status(status, message)
    output.safe_print(formatted_message, **kwargs)


def print_progress(current: int, total: int, prefix: str = "", **kwargs) -> None:
    """
    Print a formatted progress indicator with visual progress bar.
    
    Creates a progress bar using Unicode block characters on supported
    systems, or ASCII characters (#, -) on limited systems. The progress
    bar shows both visual progress and percentage completion.
    
    Args:
        current: Current progress value (should be <= total)
        total: Total/maximum progress value (should be > 0)
        prefix: Text to show before the progress bar (default: "")
        **kwargs: Additional arguments passed to safe_print(), such as:
            - end: Use '\r' for updating progress in place
            - file: Redirect to different output stream
            - flush: Force immediate output (useful with end='\r')
    
    Example:
        >>> print_progress(50, 100, "Processing: ")
        Processing: [██████████░░░░░░░░░░] 50.0%
        
        >>> # Update progress in place
        >>> for i in range(101):
        ...     print_progress(i, 100, "Loading: ", end='\r', flush=True)
        Loading: [████████████████████] 100.0%
        
        >>> # With custom prefix
        >>> print_progress(75, 100, "Download: ")
        Download: [███████████████░░░░░] 75.0%
    
    Note:
        - On Unicode systems: Uses █ for filled and ░ for empty portions
        - On ASCII systems: Uses # for filled and - for empty portions
        - Progress bar length is fixed at 20 characters
        - Percentage is displayed with one decimal place
    """
    output = _get_global_output()
    progress_str = output.format_progress(current, total, prefix)
    output.safe_print(progress_str, **kwargs)


def print_section(title: str, level: int = 1, **kwargs) -> None:
    """
    Print a formatted section header.
    
    Args:
        title: The section title text
        level: Header level (1-3, affects styling)
        **kwargs: Additional arguments passed to safe_print()
    """
    output = _get_global_output()
    section_str = output.format_section(title, level)
    output.safe_print(section_str, **kwargs)


def is_unicode_supported() -> bool:
    """
    Check if Unicode output is supported by the console.
    
    Returns:
        True if Unicode is supported, False otherwise
    """
    return ConsoleHandler.is_unicode_supported()


def get_console_encoding() -> str:
    """
    Get the detected console encoding.
    
    Returns:
        The console encoding name (e.g., 'utf-8', 'gbk', 'cp1252')
    """
    return ConsoleHandler.detect_console_encoding()


def setup_unicode_console() -> bool:
    """
    Setup Unicode console support.
    
    Returns:
        True if setup was successful, False otherwise
    """
    return ConsoleHandler.setup_unicode_console()


def get_console_info() -> dict:
    """
    Get comprehensive console information for debugging.
    
    Returns:
        Dictionary containing console encoding information
    """
    return ConsoleHandler.get_console_info()


def test_unicode_output() -> None:
    """
    Test Unicode output capabilities and print diagnostic information.
    
    This function prints various Unicode characters and their fallbacks
    to help diagnose output issues.
    """
    _get_global_output().test_output()


def reset_configuration() -> None:
    """
    Reset the package configuration to defaults.
    
    This will also reset the global SafeOutput instance.
    """
    global _config, _global_output
    
    _config = {
        'auto_setup': True,
        'enable_unicode': None,
        'log_level': logging.WARNING,
        'default_output_stream': None,
    }
    
    _global_output = None
    logging.getLogger(__name__).setLevel(logging.WARNING)
    
    logger.debug("Unicode utilities configuration reset to defaults")


# Automatic initialization when imported
def _auto_initialize() -> None:
    """Automatically initialize the package when imported."""
    try:
        if _config['auto_setup']:
            # Try to setup Unicode console support
            setup_success = setup_unicode_console()
            logger.debug(f"Auto-initialization: Unicode console setup {'succeeded' if setup_success else 'failed'}")
        
        # Create global output instance to test configuration
        _get_global_output()
        logger.debug("Auto-initialization completed successfully")
        
    except Exception as e:
        logger.warning(f"Auto-initialization failed: {e}")


# Public API exports
__all__ = [
    # Main classes
    'SafeOutput',
    'ConsoleHandler', 
    'CharacterMap',
    
    # Configuration functions
    'configure',
    'reset_configuration',
    
    # Convenience functions
    'safe_print',
    'print_status',
    'print_progress', 
    'print_section',
    
    # Utility functions
    'is_unicode_supported',
    'get_console_encoding',
    'setup_unicode_console',
    'get_console_info',
    'test_unicode_output',
]

# Version information
__version__ = "1.0.0"

# Perform automatic initialization
_auto_initialize()