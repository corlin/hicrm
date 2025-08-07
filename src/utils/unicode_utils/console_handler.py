"""
Console encoding detection and setup utilities.

This module provides platform-specific console encoding detection and setup
functionality to handle Unicode characters properly across different systems.
"""

import sys
import os
import platform
import codecs
import locale
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ConsoleHandler:
    """Handles console encoding detection and setup for Unicode support."""
    
    @staticmethod
    def detect_console_encoding() -> str:
        """
        Detect the current console encoding.
        
        Returns:
            str: The detected console encoding name (e.g., 'utf-8', 'gbk', 'cp1252')
        """
        try:
            # Try to get encoding from stdout first
            if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                encoding = sys.stdout.encoding.lower()
                logger.debug(f"Detected stdout encoding: {encoding}")
                return encoding
            
            # Try to get encoding from stderr
            if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding:
                encoding = sys.stderr.encoding.lower()
                logger.debug(f"Detected stderr encoding: {encoding}")
                return encoding
            
            # Try locale encoding
            try:
                encoding = locale.getpreferredencoding().lower()
                logger.debug(f"Detected locale encoding: {encoding}")
                return encoding
            except Exception as e:
                logger.warning(f"Failed to get locale encoding: {e}")
            
            # Platform-specific fallbacks
            system = platform.system().lower()
            if system == 'windows':
                # Windows common encodings
                try:
                    import subprocess
                    result = subprocess.run(['chcp'], capture_output=True, text=True, shell=True)
                    if result.returncode == 0 and 'Active code page:' in result.stdout:
                        codepage = result.stdout.split(':')[-1].strip()
                        if codepage == '65001':
                            return 'utf-8'
                        elif codepage == '936':
                            return 'gbk'
                        elif codepage == '1252':
                            return 'cp1252'
                        else:
                            return f'cp{codepage}'
                except Exception as e:
                    logger.warning(f"Failed to detect Windows codepage: {e}")
                
                # Windows fallback
                return 'gbk'  # Common Windows Chinese encoding
            
            elif system == 'darwin':  # macOS
                return 'utf-8'
            
            elif system == 'linux':
                # Try to get from environment
                lang = os.environ.get('LANG', '')
                if 'utf-8' in lang.lower() or 'utf8' in lang.lower():
                    return 'utf-8'
                return 'utf-8'  # Most Linux systems use UTF-8
            
            # Ultimate fallback
            return 'ascii'
            
        except Exception as e:
            logger.error(f"Failed to detect console encoding: {e}")
            return 'ascii'
    
    @staticmethod
    def setup_unicode_console() -> bool:
        """
        Configure console for Unicode output when possible.
        
        Returns:
            bool: True if Unicode console setup was successful, False otherwise
        """
        try:
            system = platform.system().lower()
            
            if system == 'windows':
                return ConsoleHandler._setup_windows_unicode_console()
            else:
                # For Unix-like systems, try to ensure UTF-8 locale
                return ConsoleHandler._setup_unix_unicode_console()
                
        except Exception as e:
            logger.error(f"Failed to setup Unicode console: {e}")
            return False
    
    @staticmethod
    def _setup_windows_unicode_console() -> bool:
        """
        Setup Unicode console for Windows using codecs.getwriter().
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            # Try to set console code page to UTF-8
            try:
                import subprocess
                result = subprocess.run(['chcp', '65001'], capture_output=True, shell=True)
                if result.returncode == 0:
                    logger.debug("Successfully set Windows console to UTF-8")
                else:
                    logger.warning("Failed to set Windows console to UTF-8")
            except Exception as e:
                logger.warning(f"Failed to change Windows codepage: {e}")
            
            # Reconfigure stdout and stderr with UTF-8 writer
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, errors='replace')
                logger.debug("Reconfigured stdout with UTF-8 writer")
            
            if hasattr(sys.stderr, 'buffer'):
                sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, errors='replace')
                logger.debug("Reconfigured stderr with UTF-8 writer")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Windows Unicode console: {e}")
            return False
    
    @staticmethod
    def _setup_unix_unicode_console() -> bool:
        """
        Setup Unicode console for Unix-like systems.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        try:
            # For Unix systems, usually just need to ensure proper locale
            current_encoding = ConsoleHandler.detect_console_encoding()
            
            if 'utf' in current_encoding:
                logger.debug(f"Unix console already supports UTF-8: {current_encoding}")
                return True
            
            # Try to set UTF-8 environment variables
            os.environ['PYTHONIOENCODING'] = 'utf-8'
            logger.debug("Set PYTHONIOENCODING to utf-8")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Unix Unicode console: {e}")
            return False
    
    @staticmethod
    def is_unicode_supported() -> bool:
        """
        Test if the console supports Unicode output.
        
        Returns:
            bool: True if Unicode is supported, False otherwise
        """
        try:
            # Test by trying to encode a Unicode character
            test_char = '✓'  # Simple Unicode checkmark
            
            # Try encoding with current stdout encoding
            if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding:
                try:
                    test_char.encode(sys.stdout.encoding)
                    logger.debug(f"Unicode test passed with encoding: {sys.stdout.encoding}")
                    return True
                except UnicodeEncodeError:
                    logger.debug(f"Unicode test failed with encoding: {sys.stdout.encoding}")
                    return False
            
            # Try with detected encoding
            detected_encoding = ConsoleHandler.detect_console_encoding()
            try:
                test_char.encode(detected_encoding)
                logger.debug(f"Unicode test passed with detected encoding: {detected_encoding}")
                return True
            except UnicodeEncodeError:
                logger.debug(f"Unicode test failed with detected encoding: {detected_encoding}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to test Unicode support: {e}")
            return False
    
    @staticmethod
    def get_safe_encoding() -> str:
        """
        Get a safe encoding that can be used for output.
        
        Returns:
            str: A safe encoding name ('utf-8' if Unicode is supported, 'ascii' otherwise)
        """
        if ConsoleHandler.is_unicode_supported():
            return 'utf-8'
        else:
            return 'ascii'
    
    @staticmethod
    def get_console_info() -> dict:
        """
        Get comprehensive console information for debugging.
        
        Returns:
            dict: Dictionary containing console encoding information
        """
        info = {
            'platform': platform.system(),
            'detected_encoding': ConsoleHandler.detect_console_encoding(),
            'unicode_supported': ConsoleHandler.is_unicode_supported(),
            'safe_encoding': ConsoleHandler.get_safe_encoding(),
            'stdout_encoding': getattr(sys.stdout, 'encoding', None),
            'stderr_encoding': getattr(sys.stderr, 'encoding', None),
            'locale_encoding': None,
            'environment_lang': os.environ.get('LANG', ''),
            'environment_pythonioencoding': os.environ.get('PYTHONIOENCODING', ''),
        }
        
        try:
            info['locale_encoding'] = locale.getpreferredencoding()
        except Exception:
            pass
        
        return info