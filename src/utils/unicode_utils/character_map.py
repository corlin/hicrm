"""
Character mapping system for Unicode to ASCII fallbacks.

This module provides comprehensive mappings from Unicode characters to ASCII
alternatives, organized by symbol categories for easy maintenance and extension.
"""

from typing import Dict, Optional, Union


class CharacterMap:
    """
    Manages Unicode to ASCII character mappings with category-based organization.
    
    Provides methods to retrieve appropriate symbols based on encoding support
    and perform bulk text replacement for Unicode characters.
    """
    
    def __init__(self):
        """Initialize the character mapping system with predefined mappings."""
        self._status_symbols = {
            # Success/positive status symbols
            '✅': '[OK]',
            '✓': '[OK]', 
            '☑': '[OK]',
            '✔': '[OK]',
            
            # Error/negative status symbols
            '❌': '[ERROR]',
            '✗': '[ERROR]',
            '✘': '[ERROR]',
            '❎': '[ERROR]',
            
            # Warning symbols
            '⚠': '[WARNING]',
            '⚠️': '[WARNING]',
            '⚡': '[WARNING]',
            
            # Info symbols
            'ℹ': '[INFO]',
            'ℹ️': '[INFO]',
            '💡': '[INFO]',
            
            # Processing symbols
            '⏳': '[PROCESSING]',
            '🔄': '[PROCESSING]',
            '⚙': '[PROCESSING]',
            '⚙️': '[PROCESSING]',
        }
        
        self._progress_symbols = {
            # Progress bars and indicators
            '█': '#',
            '▓': '#',
            '▒': '-',
            '░': '.',
            '▪': '*',
            '▫': '-',
            
            # Arrows and directional
            '→': '->',
            '←': '<-',
            '↑': '^',
            '↓': 'v',
            '⇒': '=>',
            '⇐': '<=',
            
            # Bullets and list markers
            '•': '*',
            '◦': '-',
            '▸': '>',
            '▹': '>',
            '‣': '>',
            
            # Geometric shapes for progress
            '●': '*',
            '○': 'o',
            '◆': '*',
            '◇': 'o',
            '■': '#',
            '□': '-',
        }
        
        self._decoration_symbols = {
            # Borders and frames
            '─': '-',
            '━': '=',
            '│': '|',
            '┃': '|',
            '┌': '+',
            '┐': '+',
            '└': '+',
            '┘': '+',
            '├': '+',
            '┤': '+',
            '┬': '+',
            '┴': '+',
            '┼': '+',
            
            # Double line borders
            '═': '=',
            '║': '|',
            '╔': '+',
            '╗': '+',
            '╚': '+',
            '╝': '+',
            '╠': '+',
            '╣': '+',
            '╦': '+',
            '╩': '+',
            '╬': '+',
            
            # Curved borders
            '╭': '+',
            '╮': '+',
            '╯': '+',
            '╰': '+',
            
            # Miscellaneous decorative
            '★': '*',
            '☆': '*',
            '♦': '*',
            '♢': 'o',
            '◊': '*',
            '⬥': '*',
        }
        
        # Combine all mappings for easy access
        self._all_mappings = {
            **self._status_symbols,
            **self._progress_symbols, 
            **self._decoration_symbols
        }
    
    def get_symbol(self, unicode_char: str, category: Optional[str] = None, 
                   unicode_supported: bool = True) -> str:
        """
        Get the appropriate symbol based on Unicode support and category.
        
        Args:
            unicode_char: The Unicode character to get a symbol for
            category: Optional category hint ('status', 'progress', 'decoration')
            unicode_supported: Whether Unicode is supported by the output system
            
        Returns:
            The Unicode character if supported, otherwise ASCII fallback
            
        Raises:
            ValueError: If the character is not found in any mapping
        """
        if unicode_supported:
            return unicode_char
            
        # Try category-specific lookup first if category is provided
        if category:
            category_map = self._get_category_map(category)
            if category_map and unicode_char in category_map:
                return category_map[unicode_char]
        
        # Fall back to general lookup
        if unicode_char in self._all_mappings:
            return self._all_mappings[unicode_char]
            
        # If no mapping found, return a generic placeholder
        return f"[{ord(unicode_char):04X}]"
    
    def replace_unicode_in_text(self, text: str, unicode_supported: bool = True) -> str:
        """
        Replace all Unicode characters in text with appropriate alternatives.
        
        Args:
            text: The text containing Unicode characters
            unicode_supported: Whether Unicode is supported by the output system
            
        Returns:
            Text with Unicode characters replaced if not supported
        """
        if unicode_supported:
            return text
            
        result = text
        for unicode_char, ascii_fallback in self._all_mappings.items():
            result = result.replace(unicode_char, ascii_fallback)
            
        return result
    
    def _get_category_map(self, category: str) -> Optional[Dict[str, str]]:
        """
        Get the mapping dictionary for a specific category.
        
        Args:
            category: The category name ('status', 'progress', 'decoration')
            
        Returns:
            The mapping dictionary for the category, or None if invalid
        """
        category_maps = {
            'status': self._status_symbols,
            'progress': self._progress_symbols,
            'decoration': self._decoration_symbols
        }
        return category_maps.get(category.lower())
    
    def get_available_categories(self) -> list[str]:
        """
        Get list of available symbol categories.
        
        Returns:
            List of category names
        """
        return ['status', 'progress', 'decoration']
    
    def get_symbols_in_category(self, category: str) -> Dict[str, str]:
        """
        Get all symbols in a specific category.
        
        Args:
            category: The category name
            
        Returns:
            Dictionary of Unicode to ASCII mappings for the category
            
        Raises:
            ValueError: If the category is not valid
        """
        category_map = self._get_category_map(category)
        if category_map is None:
            raise ValueError(f"Invalid category: {category}. "
                           f"Available categories: {self.get_available_categories()}")
        return category_map.copy()
    
    def add_custom_mapping(self, unicode_char: str, ascii_fallback: str, 
                          category: str = 'decoration') -> None:
        """
        Add a custom Unicode to ASCII mapping.
        
        Args:
            unicode_char: The Unicode character
            ascii_fallback: The ASCII fallback string
            category: The category to add the mapping to
            
        Raises:
            ValueError: If the category is not valid
        """
        category_map = self._get_category_map(category)
        if category_map is None:
            raise ValueError(f"Invalid category: {category}. "
                           f"Available categories: {self.get_available_categories()}")
        
        category_map[unicode_char] = ascii_fallback
        self._all_mappings[unicode_char] = ascii_fallback