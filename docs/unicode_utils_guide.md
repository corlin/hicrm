# Unicode Utils Package Documentation

## Overview

The `unicode_utils` package provides cross-platform Unicode character handling with automatic fallback to ASCII alternatives when Unicode is not supported by the console. This package was specifically designed to solve Unicode encoding errors that occur when running Python scripts on Windows systems with GBK or other non-UTF8 console encodings.

## Key Features

- **Automatic encoding detection** - Detects console encoding capabilities across platforms
- **Graceful fallback** - Automatically falls back to ASCII alternatives when Unicode fails
- **Cross-platform support** - Works on Windows, macOS, and Linux
- **Easy integration** - Simple API that can replace standard print statements
- **Comprehensive character mapping** - Extensive Unicode to ASCII symbol mappings
- **Backwards compatibility** - Preserves existing functionality while adding Unicode safety

## Quick Start

### Basic Usage

```python
from src.utils.unicode_utils import safe_print, print_status

# Replace regular print statements
safe_print("Status: ✅ Success")  # Works on all platforms

# Use formatted status messages
print_status("success", "Operation completed")
print_status("error", "Something went wrong")
```

### Using the SafeOutput Class

```python
from src.utils.unicode_utils import SafeOutput

# Create an output handler
output = SafeOutput()

# Safe printing with Unicode characters
output.safe_print("Processing: ⏳ Please wait...")

# Format status messages
status_msg = output.format_status("warning", "Low disk space")
output.safe_print(status_msg)

# Create progress bars
progress = output.format_progress(75, 100, "Download: ")
output.safe_print(progress)
```

## API Reference

### Convenience Functions

#### `safe_print(*args, **kwargs)`
Unicode-safe replacement for the built-in `print()` function.

```python
safe_print("Hello", "World", "✅")  # Handles Unicode automatically
safe_print("Status:", "✅", sep=" - ", end="\n\n")
```

#### `print_status(status: str, message: str, **kwargs)`
Print formatted status messages with appropriate symbols.

**Status types:**
- `"success"`, `"ok"`, `"pass"` → ✅ (or [OK])
- `"error"`, `"fail"`, `"failed"` → ❌ (or [ERROR])
- `"warning"`, `"warn"` → ⚠️ (or [WARNING])
- `"info"` → ℹ️ (or [INFO])
- `"processing"`, `"loading"` → ⏳ (or [PROCESSING])

```python
print_status("success", "File uploaded successfully")
print_status("error", "Connection failed")
print_status("warning", "Disk space low")
```

#### `print_progress(current: int, total: int, prefix: str = "", **kwargs)`
Print formatted progress indicators.

```python
print_progress(50, 100, "Processing: ")
# Output: Processing: [██████████░░░░░░░░░░] 50.0%
```

#### `print_section(title: str, level: int = 1, **kwargs)`
Print formatted section headers.

```python
print_section("Main Section", level=1)
print_section("Subsection", level=2)
print_section("Sub-subsection", level=3)
```

### Utility Functions

#### `is_unicode_supported() -> bool`
Check if Unicode output is supported by the console.

```python
if is_unicode_supported():
    print("Unicode is supported! ✅")
else:
    print("Using ASCII fallback [OK]")
```

#### `get_console_encoding() -> str`
Get the detected console encoding.

```python
encoding = get_console_encoding()
print(f"Console encoding: {encoding}")  # e.g., "utf-8", "gbk", "cp1252"
```

#### `setup_unicode_console() -> bool`
Attempt to setup Unicode console support.

```python
if setup_unicode_console():
    print("Unicode console setup successful")
else:
    print("Unicode console setup failed, using fallback")
```

#### `test_unicode_output()`
Test Unicode output capabilities and print diagnostic information.

```python
test_unicode_output()  # Prints comprehensive test output
```

### Configuration

#### `configure(**options)`
Configure the Unicode utilities package.

```python
from src.utils.unicode_utils import configure

configure(
    auto_setup=True,           # Automatically setup Unicode console
    enable_unicode=None,       # None for auto-detect, True/False to force
    log_level=logging.WARNING, # Logging level
    output_stream=None         # Custom output stream
)
```

## Core Classes

### SafeOutput

The main utility class for Unicode-safe output operations.

#### Constructor

```python
SafeOutput(
    enable_unicode: Optional[bool] = None,  # Force Unicode on/off
    auto_setup: bool = True,                # Auto-setup console
    output_stream: Optional[TextIO] = None  # Custom output stream
)
```

#### Methods

##### `safe_print(*args, **kwargs)`
Unicode-safe print function with automatic fallback.

```python
output = SafeOutput()
output.safe_print("Status: ✅ Complete")
output.safe_print("Progress:", "█" * 10, "░" * 10)
```

##### `format_status(status: str, message: str, status_symbol: Optional[str] = None) -> str`
Format status messages with appropriate symbols.

```python
# Using predefined status types
msg = output.format_status("success", "Upload complete")

# Using custom symbol
msg = output.format_status("custom", "Custom message", "🎯")
```

##### `format_progress(current: int, total: int, **options) -> str`
Format progress indicators with customizable appearance.

```python
# Basic progress bar
progress = output.format_progress(75, 100)

# Customized progress bar
progress = output.format_progress(
    current=75,
    total=100,
    prefix="Download: ",
    suffix="(75/100)",
    bar_length=30,
    fill_char="█",
    empty_char="░"
)
```

##### `format_section(title: str, level: int = 1, **options) -> str`
Format section headers with different styling levels.

```python
# Level 1: Full border box
header1 = output.format_section("Main Title", level=1)

# Level 2: Title with underline
header2 = output.format_section("Subtitle", level=2)

# Level 3: Simple prefix
header3 = output.format_section("Sub-item", level=3)

# Custom width and border
header = output.format_section("Custom", level=1, width=60, border_char="*")
```

### ConsoleHandler

Handles console encoding detection and setup.

#### Static Methods

##### `detect_console_encoding() -> str`
Detect the current console encoding using multiple detection methods.

```python
encoding = ConsoleHandler.detect_console_encoding()
print(f"Detected encoding: {encoding}")
```

##### `setup_unicode_console() -> bool`
Configure console for Unicode output when possible.

```python
success = ConsoleHandler.setup_unicode_console()
if success:
    print("Console configured for Unicode")
```

##### `is_unicode_supported() -> bool`
Test if the console supports Unicode output by attempting to encode test characters.

```python
if ConsoleHandler.is_unicode_supported():
    print("✅ Unicode supported")
else:
    print("[OK] Using ASCII fallback")
```

##### `get_console_info() -> dict`
Get comprehensive console information for debugging.

```python
info = ConsoleHandler.get_console_info()
for key, value in info.items():
    print(f"{key}: {value}")
```

### CharacterMap

Manages Unicode to ASCII character mappings.

#### Methods

##### `get_symbol(unicode_char: str, category: Optional[str] = None, unicode_supported: bool = True) -> str`
Get the appropriate symbol based on Unicode support.

```python
char_map = CharacterMap()

# Get symbol with Unicode support
symbol = char_map.get_symbol("✅", unicode_supported=True)  # Returns "✅"

# Get symbol without Unicode support
symbol = char_map.get_symbol("✅", unicode_supported=False)  # Returns "[OK]"

# Category-specific lookup
symbol = char_map.get_symbol("✅", category="status", unicode_supported=False)
```

##### `replace_unicode_in_text(text: str, unicode_supported: bool = True) -> str`
Replace all Unicode characters in text with ASCII alternatives.

```python
text = "Status: ✅ Success! Progress: █████░░░░░"
ascii_text = char_map.replace_unicode_in_text(text, unicode_supported=False)
# Result: "Status: [OK] Success! Progress: #####....."
```

##### `get_available_categories() -> List[str]`
Get list of available symbol categories.

```python
categories = char_map.get_available_categories()
# Returns: ['status', 'progress', 'decoration']
```

##### `get_symbols_in_category(category: str) -> Dict[str, str]`
Get all symbols in a specific category.

```python
status_symbols = char_map.get_symbols_in_category("status")
for unicode_char, ascii_fallback in status_symbols.items():
    print(f"{unicode_char} → {ascii_fallback}")
```

##### `add_custom_mapping(unicode_char: str, ascii_fallback: str, category: str = 'decoration')`
Add custom Unicode to ASCII mappings.

```python
char_map.add_custom_mapping("🚀", "[ROCKET]", "status")
symbol = char_map.get_symbol("🚀", unicode_supported=False)  # Returns "[ROCKET]"
```

## Platform-Specific Considerations

### Windows

**Common Issues:**
- GBK encoding (Chinese Windows) doesn't support many Unicode characters
- Console code page may need to be changed to UTF-8 (65001)
- Some terminals may not display Unicode even with UTF-8 encoding

**Solutions:**
- The package automatically attempts to set console code page to UTF-8
- Falls back to ASCII alternatives when Unicode fails
- Uses `codecs.getwriter()` to reconfigure output streams

**Example Windows behavior:**
```python
# On Windows with GBK encoding
safe_print("Status: ✅ Success")
# Output: "Status: [OK] Success"

# After Unicode console setup (if successful)
safe_print("Status: ✅ Success")  
# Output: "Status: ✅ Success"
```

### macOS

**Characteristics:**
- Generally excellent Unicode support
- UTF-8 encoding by default
- Most Unicode characters display correctly

**Considerations:**
- Some terminal applications may have font limitations
- SSH sessions might have different encoding settings

### Linux

**Characteristics:**
- Usually UTF-8 encoding by default
- Good Unicode support in most distributions
- Locale settings affect character display

**Considerations:**
- Locale must be properly configured (e.g., `en_US.UTF-8`)
- SSH sessions may inherit different locale settings
- Some minimal installations might lack Unicode fonts

## Common Usage Patterns

### Replacing Existing Print Statements

**Before:**
```python
print("✅ Success")
print("❌ Error occurred")
print("Progress: " + "█" * 10 + "░" * 10)
```

**After:**
```python
from src.utils.unicode_utils import safe_print

safe_print("✅ Success")
safe_print("❌ Error occurred")
safe_print("Progress: " + "█" * 10 + "░" * 10)
```

### Status Reporting

```python
from src.utils.unicode_utils import print_status

def process_files(files):
    for file in files:
        try:
            # Process file
            result = process_file(file)
            print_status("success", f"Processed {file}")
        except Exception as e:
            print_status("error", f"Failed to process {file}: {e}")
```

### Progress Tracking

```python
from src.utils.unicode_utils import print_progress

def download_with_progress(url, filename):
    total_size = get_file_size(url)
    downloaded = 0
    
    with open(filename, 'wb') as f:
        for chunk in download_chunks(url):
            f.write(chunk)
            downloaded += len(chunk)
            print_progress(downloaded, total_size, "Downloading: ")
```

### Structured Output

```python
from src.utils.unicode_utils import SafeOutput

def generate_report():
    output = SafeOutput()
    
    # Main title
    output.safe_print(output.format_section("System Report", level=1))
    output.safe_print()
    
    # Subsections
    output.safe_print(output.format_section("Status Check", level=2))
    output.safe_print(output.format_status("success", "All systems operational"))
    output.safe_print(output.format_status("warning", "Disk usage at 85%"))
    output.safe_print()
    
    # Progress section
    output.safe_print(output.format_section("Current Tasks", level=2))
    output.safe_print(output.format_progress(3, 5, "Tasks completed: "))
```

## Error Handling

The package includes comprehensive error handling:

### Encoding Errors
- Automatically catches `UnicodeEncodeError` exceptions
- Falls back to ASCII alternatives
- Logs encoding issues for debugging

### Platform Detection Failures
- Gracefully handles platform detection failures
- Uses conservative fallbacks when detection fails
- Continues operation with reduced functionality

### Console Setup Failures
- Continues operation even if Unicode console setup fails
- Provides fallback ASCII mode
- Logs setup attempts for troubleshooting

## Debugging and Troubleshooting

### Enable Debug Logging

```python
import logging
from src.utils.unicode_utils import configure

# Enable debug logging
configure(log_level=logging.DEBUG)

# Now all operations will be logged
safe_print("Test message ✅")
```

### Get Console Information

```python
from src.utils.unicode_utils import get_console_info

info = get_console_info()
for key, value in info.items():
    print(f"{key}: {value}")
```

### Test Unicode Capabilities

```python
from src.utils.unicode_utils import test_unicode_output

# Run comprehensive Unicode test
test_unicode_output()
```

### Manual Testing

```python
from src.utils.unicode_utils import SafeOutput, CharacterMap

# Test specific characters
output = SafeOutput()
char_map = CharacterMap()

test_chars = ['✅', '❌', '⚠️', '⏳', '🔍']
for char in test_chars:
    unicode_version = char_map.get_symbol(char, unicode_supported=True)
    ascii_version = char_map.get_symbol(char, unicode_supported=False)
    print(f"Unicode: {unicode_version} | ASCII: {ascii_version}")
```

## Performance Considerations

### Encoding Detection Overhead
- Encoding detection is performed once during initialization
- Results are cached for subsequent operations
- Minimal performance impact after initial setup

### Character Mapping Performance
- Character mappings are stored in dictionaries for O(1) lookup
- Text replacement uses efficient string operations
- Performance impact is negligible for typical usage

### Memory Usage
- Character mappings are loaded once and reused
- No significant memory overhead
- Global instances are used for convenience functions

## Best Practices

### 1. Use Convenience Functions for Simple Cases
```python
# Good: Simple and clean
from src.utils.unicode_utils import safe_print, print_status

safe_print("Hello ✅")
print_status("success", "Operation completed")
```

### 2. Use SafeOutput Class for Complex Scenarios
```python
# Good: More control and customization
from src.utils.unicode_utils import SafeOutput

output = SafeOutput(enable_unicode=True)
formatted_msg = output.format_status("warning", "Check disk space")
output.safe_print(formatted_msg)
```

### 3. Configure Once at Application Startup
```python
# Good: Configure once at the beginning
from src.utils.unicode_utils import configure
import logging

configure(
    auto_setup=True,
    log_level=logging.INFO
)

# Then use throughout the application
from src.utils.unicode_utils import safe_print
safe_print("Application started ✅")
```

### 4. Handle Edge Cases Gracefully
```python
# Good: Defensive programming
from src.utils.unicode_utils import safe_print, is_unicode_supported

def display_fancy_output():
    if is_unicode_supported():
        safe_print("✨ Fancy Unicode output ✨")
    else:
        safe_print("=== Standard ASCII output ===")
```

### 5. Test on Target Platforms
```python
# Good: Platform-specific testing
from src.utils.unicode_utils import get_console_info, test_unicode_output

def debug_unicode_support():
    print("Console Information:")
    info = get_console_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    print("\nUnicode Test:")
    test_unicode_output()
```

## Migration Guide

### From Standard Print Statements

**Step 1:** Import the utilities
```python
from src.utils.unicode_utils import safe_print, print_status
```

**Step 2:** Replace print statements
```python
# Before
print("✅ Success")

# After  
safe_print("✅ Success")
```

**Step 3:** Use specialized functions where appropriate
```python
# Before
print("✅ File processed successfully")

# After
print_status("success", "File processed successfully")
```

### From Custom Unicode Handling

**Step 1:** Remove custom encoding logic
```python
# Before - remove this
try:
    print("✅ Success")
except UnicodeEncodeError:
    print("[OK] Success")
```

**Step 2:** Use the utilities
```python
# After - much simpler
from src.utils.unicode_utils import safe_print
safe_print("✅ Success")
```

## Extending the Package

### Adding Custom Character Mappings

```python
from src.utils.unicode_utils import CharacterMap

# Get the global character map instance
char_map = CharacterMap()

# Add custom mappings
char_map.add_custom_mapping("🚀", "[ROCKET]", "status")
char_map.add_custom_mapping("🎯", "[TARGET]", "status")

# Use the custom mappings
from src.utils.unicode_utils import SafeOutput
output = SafeOutput()
output.safe_print("Launch status: 🚀")  # Will show "[ROCKET]" on ASCII systems
```

### Creating Custom Output Classes

```python
from src.utils.unicode_utils import SafeOutput

class CustomOutput(SafeOutput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def print_header(self, text: str):
        """Custom header format."""
        border = self.format_section("", level=1, width=len(text) + 10)
        self.safe_print(border)
        self.safe_print(f"     {text}")
        self.safe_print(border)

# Usage
output = CustomOutput()
output.print_header("My Custom Header")
```

## Troubleshooting Common Issues

### Issue: Unicode characters still not displaying

**Possible causes:**
- Terminal/console doesn't support Unicode fonts
- Locale settings are incorrect
- SSH session with different encoding

**Solutions:**
```python
# Check Unicode support
from src.utils.unicode_utils import is_unicode_supported, get_console_info

if not is_unicode_supported():
    print("Unicode not supported, using ASCII fallback")
    info = get_console_info()
    print("Console info:", info)
```

### Issue: Performance problems with large outputs

**Solution:**
```python
# Use buffered output for large amounts of text
from src.utils.unicode_utils import SafeOutput
import sys

output = SafeOutput()
# Process in chunks and flush periodically
for i in range(1000):
    output.safe_print(f"Line {i}: ✅", flush=(i % 100 == 0))
```

### Issue: Custom characters not working

**Solution:**
```python
# Add custom mappings before use
from src.utils.unicode_utils import CharacterMap

char_map = CharacterMap()
char_map.add_custom_mapping("🎮", "[GAME]", "status")

# Verify the mapping
symbol = char_map.get_symbol("🎮", unicode_supported=False)
print(f"Custom symbol: {symbol}")  # Should print "[GAME]"
```

This comprehensive documentation covers all aspects of the Unicode utilities package, from basic usage to advanced customization and troubleshooting.