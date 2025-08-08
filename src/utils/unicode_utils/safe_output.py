"""
Safe output utility for Unicode-aware printing with automatic fallback.

This module provides the SafeOutput class that handles Unicode characters
gracefully across different console encodings, with automatic fallback to
ASCII alternatives when Unicode is not supported.

The SafeOutput class is the main interface for Unicode-safe output operations.
It automatically detects console capabilities and provides methods for:
- Safe printing with Unicode fallback
- Formatted status messages with appropriate symbols
- Progress bars with cross-platform compatibility
- Section headers with consistent styling

Error Handling:
    - Catches UnicodeEncodeError and falls back to ASCII
    - Handles platform-specific encoding issues gracefully
    - Provides ultimate fallback for critical output failures
    - Logs encoding issues for debugging

Example:
    >>> output = SafeOutput()
    >>> output.safe_print("Status: ✅ Success")  # Works on all platforms
    >>> status = output.format_status("success", "Operation completed")
    >>> progress = output.format_progress(75, 100, "Progress: ")
"""

import sys
import logging
from typing import Any, Optional, TextIO, Union
from .console_handler import ConsoleHandler
from .character_map import CharacterMap

logger = logging.getLogger(__name__)


class SafeOutput:
    """
    Unicode-safe output utility with automatic ASCII fallback.
    
    This class provides methods for safe printing and formatting that automatically
    handle Unicode encoding issues by falling back to ASCII alternatives when needed.
    """
    
    def __init__(self, enable_unicode: Optional[bool] = None, 
                 auto_setup: bool = True, output_stream: Optional[TextIO] = None):
        """
        Initialize the SafeOutput utility.
        
        Args:
            enable_unicode: Force enable/disable Unicode. If None, auto-detect
                based on console capabilities. True forces Unicode mode,
                False forces ASCII mode.
            auto_setup: Whether to automatically setup Unicode console support
                by calling ConsoleHandler.setup_unicode_console(). Recommended
                for most use cases.
            output_stream: Custom output stream (defaults to sys.stdout).
                Useful for redirecting output to files or custom streams.
        
        Raises:
            No exceptions are raised during initialization. Setup failures
            are logged but do not prevent object creation.
        
        Note:
            The Unicode support detection is performed during initialization
            and cached for performance. If console settings change after
            initialization, create a new SafeOutput instance.
        """
        self._output_stream = output_stream or sys.stdout
        self._character_map = CharacterMap()
        
        # Setup console if requested
        if auto_setup:
            try:
                ConsoleHandler.setup_unicode_console()
            except Exception as e:
                logger.warning(f"Failed to setup Unicode console: {e}")
        
        # Determine Unicode support
        if enable_unicode is None:
            self._unicode_supported = ConsoleHandler.is_unicode_supported()
        else:
            self._unicode_supported = enable_unicode
            
        logger.debug(f"SafeOutput initialized with Unicode support: {self._unicode_supported}")
    
    @property
    def unicode_supported(self) -> bool:
        """Whether Unicode output is supported."""
        return self._unicode_supported
    
    def safe_print(self, *args, sep: str = ' ', end: str = '\n', 
                   file: Optional[TextIO] = None, flush: bool = False, **kwargs) -> None:
        """
        Unicode-safe print function with automatic fallback.
        
        This method works like the built-in print() function but handles Unicode
        encoding errors gracefully by falling back to ASCII alternatives.
        
        Args:
            *args: Values to print
            sep: String inserted between values
            end: String appended after the last value
            file: File object to write to (defaults to configured output stream)
            flush: Whether to forcibly flush the stream
            **kwargs: Additional keyword arguments (for compatibility)
        """
        output_file = file or self._output_stream
        
        try:
            # Convert all arguments to strings and handle Unicode
            safe_args = []
            for arg in args:
                arg_str = str(arg)
                safe_str = self._make_text_safe(arg_str)
                safe_args.append(safe_str)
            
            # Make separator and end safe too
            safe_sep = self._make_text_safe(sep)
            safe_end = self._make_text_safe(end)
            
            # Try to print with Unicode first
            try:
                print(*safe_args, sep=safe_sep, end=safe_end, file=output_file, flush=flush)
            except UnicodeEncodeError:
                # Fall back to ASCII-only output
                ascii_args = [self._character_map.replace_unicode_in_text(arg, False) for arg in safe_args]
                ascii_sep = self._character_map.replace_unicode_in_text(safe_sep, False)
                ascii_end = self._character_map.replace_unicode_in_text(safe_end, False)
                
                print(*ascii_args, sep=ascii_sep, end=ascii_end, file=output_file, flush=flush)
                logger.debug("Fell back to ASCII output due to UnicodeEncodeError")
                
        except Exception as e:
            # Ultimate fallback - try to print error message safely
            try:
                error_msg = f"[OUTPUT ERROR: {str(e)}]"
                print(error_msg, file=output_file)
            except Exception:
                # If even error printing fails, write to stderr
                try:
                    sys.stderr.write(f"[CRITICAL OUTPUT ERROR: {str(e)}]\n")
                except Exception:
                    pass  # Give up gracefully
            
            logger.error(f"Failed to print safely: {e}")
    
    def format_status(self, status: str, message: str, 
                     status_symbol: Optional[str] = None) -> str:
        """
        Format status messages with appropriate symbols.
        
        Args:
            status: Status type ('success', 'error', 'warning', 'info', 'processing')
            message: The status message text
            status_symbol: Custom symbol to use (overrides default)
            
        Returns:
            Formatted status string with appropriate symbol
        """
        # Default status symbols
        status_symbols = {
            'success': '✅',
            'ok': '✅', 
            'pass': '✅',
            'error': '❌',
            'fail': '❌',
            'failed': '❌',
            'warning': '⚠️',
            'warn': '⚠️',
            'info': 'ℹ️',
            'processing': '⏳',
            'loading': '⏳',
        }
        
        # Get the appropriate symbol
        if status_symbol:
            symbol = status_symbol
        else:
            symbol = status_symbols.get(status.lower(), '•')
        
        # Make symbol safe for output
        safe_symbol = self._character_map.get_symbol(symbol, 'status', self._unicode_supported)
        safe_message = self._make_text_safe(message)
        
        return f"{safe_symbol} {safe_message}"
    
    def format_progress(self, current: int, total: int, prefix: str = "", 
                       suffix: str = "", bar_length: int = 20, 
                       fill_char: Optional[str] = None, 
                       empty_char: Optional[str] = None) -> str:
        """
        Format progress indicators with safe Unicode/ASCII characters.
        
        Args:
            current: Current progress value
            total: Total/maximum progress value
            prefix: Text to show before the progress bar
            suffix: Text to show after the progress bar
            bar_length: Length of the progress bar in characters
            fill_char: Character to use for filled portion (defaults to █ or #)
            empty_char: Character to use for empty portion (defaults to ░ or -)
            
        Returns:
            Formatted progress string
        """
        # Calculate progress percentage
        if total <= 0:
            percent = 0
        else:
            percent = min(100, max(0, (current / total) * 100))
        
        # Calculate filled length
        filled_length = int(bar_length * current // total) if total > 0 else 0
        
        # Get appropriate characters
        if fill_char is None:
            fill_char = '█' if self._unicode_supported else '#'
        if empty_char is None:
            empty_char = '░' if self._unicode_supported else '-'
        
        # Make characters safe
        safe_fill = self._character_map.get_symbol(fill_char, 'progress', self._unicode_supported)
        safe_empty = self._character_map.get_symbol(empty_char, 'progress', self._unicode_supported)
        
        # Build progress bar
        bar = safe_fill * filled_length + safe_empty * (bar_length - filled_length)
        
        # Make prefix and suffix safe
        safe_prefix = self._make_text_safe(prefix)
        safe_suffix = self._make_text_safe(suffix)
        
        # Format the complete progress string
        progress_str = f"{safe_prefix}[{bar}] {percent:.1f}%"
        if safe_suffix:
            progress_str += f" {safe_suffix}"
            
        return progress_str
    
    def format_section(self, title: str, level: int = 1, 
                      width: Optional[int] = None, 
                      border_char: Optional[str] = None) -> str:
        """
        Format section headers with appropriate styling.
        
        Args:
            title: The section title text
            level: Header level (1-3, affects styling)
            width: Width of the section header (auto-calculated if None)
            border_char: Character to use for borders
            
        Returns:
            Formatted section header string
        """
        safe_title = self._make_text_safe(title)
        
        # Determine border character based on level
        if border_char is None:
            if level == 1:
                border_char = '═' if self._unicode_supported else '='
            elif level == 2:
                border_char = '─' if self._unicode_supported else '-'
            else:  # level 3+
                border_char = '·' if self._unicode_supported else '.'
        
        # Make border character safe
        safe_border = self._character_map.get_symbol(border_char, 'decoration', self._unicode_supported)
        
        # Calculate width
        if width is None:
            width = max(len(safe_title) + 4, 40)  # Minimum width of 40
        
        # Format based on level
        if level == 1:
            # Level 1: Full border box
            border_line = safe_border * width
            padding = (width - len(safe_title) - 2) // 2
            title_line = safe_border + ' ' * padding + safe_title + ' ' * (width - len(safe_title) - padding - 2) + safe_border
            return f"{border_line}\n{title_line}\n{border_line}"
        
        elif level == 2:
            # Level 2: Title with underline
            underline = safe_border * len(safe_title)
            return f"{safe_title}\n{underline}"
        
        else:
            # Level 3+: Simple prefix
            prefix = safe_border * 3
            return f"{prefix} {safe_title}"
    
    def _make_text_safe(self, text: str) -> str:
        """
        Make text safe for output by handling Unicode characters.
        
        Args:
            text: Input text that may contain Unicode characters
            
        Returns:
            Text with Unicode characters handled appropriately
        """
        if self._unicode_supported:
            return text
        else:
            return self._character_map.replace_unicode_in_text(text, False)
    
    def test_output(self) -> None:
        """
        Test the output capabilities and print diagnostic information.
        
        This method prints various Unicode characters and their fallbacks
        to help diagnose output issues.
        """
        self.safe_print("=== SafeOutput Test ===")
        self.safe_print(f"Unicode supported: {self._unicode_supported}")
        self.safe_print(f"Console encoding: {ConsoleHandler.detect_console_encoding()}")
        self.safe_print()
        
        # Test status symbols
        self.safe_print("Status symbols:")
        self.safe_print(self.format_status("success", "Operation completed successfully"))
        self.safe_print(self.format_status("error", "Something went wrong"))
        self.safe_print(self.format_status("warning", "This is a warning"))
        self.safe_print(self.format_status("info", "Informational message"))
        self.safe_print()
        
        # Test progress bar
        self.safe_print("Progress indicators:")
        for i in [0, 25, 50, 75, 100]:
            progress = self.format_progress(i, 100, "Progress: ")
            self.safe_print(progress)
        self.safe_print()
        
        # Test section headers
        self.safe_print("Section headers:")
        self.safe_print(self.format_section("Level 1 Header", 1))
        self.safe_print()
        self.safe_print(self.format_section("Level 2 Header", 2))
        self.safe_print()
        self.safe_print(self.format_section("Level 3 Header", 3))
        self.safe_print()
        
        # Test various Unicode characters
        self.safe_print("Unicode character test:")
        test_chars = ['✅', '❌', '⚠️', '⏳', '🔍', '⚡', '█', '░', '→', '•']
        for char in test_chars:
            safe_char = self._character_map.get_symbol(char, None, self._unicode_supported)
            self.safe_print(f"  {char} → {safe_char}")