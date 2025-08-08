# Unicode Utils Quick Reference

## Installation & Import

```python
# Basic imports
from src.utils.unicode_utils import safe_print, print_status, print_progress

# Advanced imports
from src.utils.unicode_utils import SafeOutput, ConsoleHandler, CharacterMap

# Configuration
from src.utils.unicode_utils import configure, is_unicode_supported
```

## Quick Start Examples

### Replace print() statements
```python
# Instead of: print("✅ Success")
safe_print("✅ Success")

# Instead of: print("❌ Error:", error_msg)
print_status("error", error_msg)
```

### Progress indicators
```python
# Simple progress
print_progress(50, 100, "Processing: ")
# Output: Processing: [██████████░░░░░░░░░░] 50.0%

# In a loop
for i in range(101):
    print_progress(i, 100, "Loading: ", end='\r')
```

### Status messages
```python
print_status("success", "File uploaded")     # ✅ File uploaded
print_status("error", "Connection failed")   # ❌ Connection failed  
print_status("warning", "Low disk space")    # ⚠️ Low disk space
print_status("info", "Processing started")   # ℹ️ Processing started
```

## Common Patterns

### Error handling with status
```python
try:
    result = risky_operation()
    print_status("success", "Operation completed")
except Exception as e:
    print_status("error", f"Operation failed: {e}")
```

### File processing with progress
```python
files = get_file_list()
for i, file in enumerate(files):
    print_progress(i, len(files), "Processing: ")
    process_file(file)
print_status("success", f"Processed {len(files)} files")
```

### Structured output
```python
from src.utils.unicode_utils import SafeOutput

output = SafeOutput()
output.safe_print(output.format_section("Report", level=1))
output.safe_print(output.format_status("success", "All systems OK"))
output.safe_print(output.format_progress(85, 100, "Completion: "))
```

## Character Mappings

| Unicode | ASCII Fallback | Category |
|---------|----------------|----------|
| ✅      | [OK]           | status   |
| ❌      | [ERROR]        | status   |
| ⚠️      | [WARNING]      | status   |
| ℹ️      | [INFO]         | status   |
| ⏳      | [PROCESSING]   | status   |
| 🔍      | [SEARCH]       | status   |
| █       | #              | progress |
| ░       | .              | progress |
| →       | ->             | progress |
| •       | *              | progress |
| ─       | -              | decoration |
| ═       | =              | decoration |

## Configuration Options

```python
from src.utils.unicode_utils import configure
import logging

configure(
    auto_setup=True,           # Auto-setup Unicode console
    enable_unicode=None,       # None=auto-detect, True/False=force
    log_level=logging.WARNING, # Logging level
    output_stream=None         # Custom output stream
)
```

## Debugging Commands

```python
# Check Unicode support
from src.utils.unicode_utils import is_unicode_supported, get_console_info

print(f"Unicode supported: {is_unicode_supported()}")

# Get detailed console info
info = get_console_info()
for key, value in info.items():
    print(f"{key}: {value}")

# Run comprehensive test
from src.utils.unicode_utils import test_unicode_output
test_unicode_output()
```

## Platform-Specific Notes

### Windows
- May use GBK encoding (Chinese systems)
- Package automatically tries to set UTF-8 console
- Falls back to ASCII if Unicode fails

### macOS/Linux  
- Usually UTF-8 by default
- Good Unicode support
- Check locale settings if issues occur

## Advanced Usage

### Custom SafeOutput instance
```python
output = SafeOutput(enable_unicode=False)  # Force ASCII mode
output.safe_print("Always ASCII: ✅")      # Output: "Always ASCII: [OK]"
```

### Custom character mappings
```python
from src.utils.unicode_utils import CharacterMap

char_map = CharacterMap()
char_map.add_custom_mapping("🚀", "[ROCKET]", "status")
```

### Manual console setup
```python
from src.utils.unicode_utils import setup_unicode_console

if setup_unicode_console():
    print("Unicode console ready")
else:
    print("Using ASCII fallback")
```

## Migration Checklist

- [ ] Replace `print()` with `safe_print()`
- [ ] Replace status prints with `print_status()`
- [ ] Replace progress displays with `print_progress()`
- [ ] Test on target platforms (especially Windows)
- [ ] Add error handling for edge cases
- [ ] Configure logging if needed

## Common Issues & Solutions

**Issue:** Characters still not displaying
```python
# Check support and get info
print(f"Unicode supported: {is_unicode_supported()}")
print(f"Console encoding: {get_console_encoding()}")
```

**Issue:** Performance with large output
```python
# Use flush parameter for better performance
for i in range(1000):
    safe_print(f"Line {i}", flush=(i % 100 == 0))
```

**Issue:** Custom symbols not working
```python
# Add custom mappings first
char_map = CharacterMap()
char_map.add_custom_mapping("🎯", "[TARGET]", "status")
```