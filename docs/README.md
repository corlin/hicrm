# Unicode Utils Documentation

This directory contains comprehensive documentation for the Unicode utilities package, which provides cross-platform Unicode character handling with automatic fallback to ASCII alternatives.

## Documentation Files

### 📖 [Unicode Utils Guide](unicode_utils_guide.md)
**Complete API reference and usage guide**
- Detailed API documentation for all classes and functions
- Comprehensive examples and usage patterns
- Configuration options and best practices
- Error handling and troubleshooting
- Migration guide from standard print statements

### ⚡ [Quick Reference](unicode_utils_quick_reference.md)
**Fast lookup for common tasks**
- Essential imports and basic usage
- Common patterns and code snippets
- Character mapping reference table
- Platform-specific notes
- Migration checklist

### 💻 [Platform-Specific Guide](unicode_utils_platform_guide.md)
**Platform-specific considerations and solutions**
- Windows encoding issues (GBK, UTF-8, code pages)
- macOS terminal compatibility
- Linux locale configuration
- Docker and SSH considerations
- Troubleshooting platform-specific problems

### 🔧 [Usage Examples](unicode_utils_examples.md)
**Real-world implementation examples**
- File processing scripts with progress tracking
- Download progress indicators
- System monitoring with status displays
- Log file analysis with Unicode-safe output
- Test runners with formatted results
- Configuration validators

## Quick Start

### Basic Usage
```python
from src.utils.unicode_utils import safe_print, print_status

# Replace regular print statements
safe_print("Status: ✅ Success")

# Use formatted status messages
print_status("success", "Operation completed")
print_status("error", "Something went wrong")
```

### Advanced Usage
```python
from src.utils.unicode_utils import SafeOutput

# Create custom output handler
output = SafeOutput()

# Format progress bars
progress = output.format_progress(75, 100, "Processing: ")
output.safe_print(progress)

# Format section headers
header = output.format_section("Results", level=1)
output.safe_print(header)
```

## Problem Solved

This package solves the common issue where Python scripts containing Unicode characters (like emoji or special symbols) fail with `UnicodeEncodeError` on systems with limited console encoding support, particularly:

- **Windows with GBK encoding** (Chinese systems)
- **Legacy terminal environments**
- **SSH sessions with encoding mismatches**
- **Docker containers with minimal locale support**

## Key Features

- ✅ **Automatic encoding detection** across platforms
- ✅ **Graceful fallback** to ASCII alternatives
- ✅ **Cross-platform compatibility** (Windows, macOS, Linux)
- ✅ **Easy integration** - drop-in replacement for print()
- ✅ **Comprehensive character mapping** for common symbols
- ✅ **Backwards compatibility** with existing code
- ✅ **Performance optimized** with caching and efficient lookups

## Character Mappings

The package includes extensive Unicode to ASCII mappings:

| Category | Unicode Examples | ASCII Fallbacks |
|----------|------------------|------------------|
| Status | ✅ ❌ ⚠️ ℹ️ ⏳ | [OK] [ERROR] [WARNING] [INFO] [PROCESSING] |
| Progress | █ ░ → • ▸ | # . -> * > |
| Decoration | ─ ═ │ ┌ ┐ | - = \| + + |

## Architecture Overview

```
unicode_utils/
├── __init__.py           # Public API and convenience functions
├── safe_output.py        # Main SafeOutput class
├── console_handler.py    # Platform-specific console setup
└── character_map.py      # Unicode to ASCII mappings
```

### Core Components

1. **SafeOutput**: Main utility class for Unicode-safe printing
2. **ConsoleHandler**: Detects and configures console encoding
3. **CharacterMap**: Manages Unicode to ASCII character mappings
4. **Convenience Functions**: Simple replacements for common operations

## Documentation Navigation

### For New Users
1. Start with [Quick Reference](unicode_utils_quick_reference.md)
2. Review [Usage Examples](unicode_utils_examples.md) for your use case
3. Check [Platform-Specific Guide](unicode_utils_platform_guide.md) for your OS

### For Detailed Implementation
1. Read the complete [Unicode Utils Guide](unicode_utils_guide.md)
2. Review API documentation for specific classes
3. Check troubleshooting sections for common issues

### For Platform-Specific Issues
1. Go directly to [Platform-Specific Guide](unicode_utils_platform_guide.md)
2. Find your platform (Windows/macOS/Linux)
3. Follow the specific setup instructions

## Common Use Cases

### 1. Script Output with Status Indicators
```python
from src.utils.unicode_utils import print_status

print_status("success", "File uploaded successfully")
print_status("error", "Connection failed")
print_status("warning", "Disk space low")
```

### 2. Progress Tracking
```python
from src.utils.unicode_utils import print_progress

for i in range(101):
    print_progress(i, 100, "Processing: ", end='\r')
```

### 3. Structured Output
```python
from src.utils.unicode_utils import SafeOutput

output = SafeOutput()
output.safe_print(output.format_section("Report", level=1))
output.safe_print(output.format_status("success", "All systems OK"))
```

## Testing and Validation

### Test Unicode Support
```python
from src.utils.unicode_utils import test_unicode_output, is_unicode_supported

# Quick check
print(f"Unicode supported: {is_unicode_supported()}")

# Comprehensive test
test_unicode_output()
```

### Get Diagnostic Information
```python
from src.utils.unicode_utils import get_console_info

info = get_console_info()
for key, value in info.items():
    print(f"{key}: {value}")
```

## Contributing to Documentation

When updating documentation:

1. **Keep examples practical** - Use real-world scenarios
2. **Test on multiple platforms** - Verify examples work everywhere
3. **Include error cases** - Show what happens when things go wrong
4. **Update cross-references** - Keep links between documents current
5. **Maintain consistency** - Use the same style and terminology

### Documentation Standards

- Use clear, concise language
- Include code examples for all features
- Provide both basic and advanced usage patterns
- Document platform-specific behavior
- Include troubleshooting information
- Keep examples up-to-date with the API

## Support and Troubleshooting

### Common Issues

1. **Characters display as question marks**
   - Check font support in your terminal
   - Verify console encoding detection

2. **Still getting UnicodeEncodeError**
   - Ensure you're using `safe_print()` instead of `print()`
   - Check custom output stream configurations

3. **Performance issues with large output**
   - Use batched output with periodic flushing
   - Consider disabling Unicode for bulk operations

### Getting Help

1. Check the [troubleshooting sections](unicode_utils_guide.md#troubleshooting-common-issues) in the main guide
2. Review [platform-specific solutions](unicode_utils_platform_guide.md)
3. Run diagnostic functions to gather system information
4. Look at [usage examples](unicode_utils_examples.md) for similar use cases

## Version Information

This documentation is for Unicode Utils Package v1.0.0

### Compatibility
- Python 3.8+
- Windows 10+, macOS 10.14+, Linux (most distributions)
- Compatible with major terminals and IDEs

### Dependencies
- No external dependencies required
- Uses only Python standard library modules
- Optional: `psutil` for system monitoring examples

---

*For the most up-to-date information, always refer to the individual documentation files and the package source code.*