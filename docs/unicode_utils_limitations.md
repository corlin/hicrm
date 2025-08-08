# Unicode Utils Limitations and Known Issues

This document outlines the current limitations, known issues, and considerations when using the Unicode utilities package.

## Current Limitations

### 1. Character Mapping Coverage

**Limited Emoji Support**
- The package focuses on common symbols and technical indicators
- Complex emoji sequences (👨‍💻, 🏳️‍🌈) are not fully mapped
- New emoji from recent Unicode versions may not be included

```python
# Supported
from src.utils.unicode_utils import safe_print
safe_print("✅ ❌ ⚠️ ⏳ 🔍")  # These work well

# Limited support
safe_print("👨‍💻 🏳️‍🌈 🧑‍🚀")  # May show as [?] on ASCII systems
```

**Regional and Language-Specific Characters**
- Focus is on technical/status symbols
- Limited support for non-Latin scripts
- No specialized mappings for mathematical symbols

### 2. Performance Considerations

**Character Replacement Overhead**
- Text replacement is performed character by character
- Large text blocks may have noticeable performance impact
- No optimization for repeated character patterns

```python
# Performance impact example
large_text = "✅ " * 10000  # 10,000 checkmarks
safe_print(large_text)  # May be slower than expected
```

**Encoding Detection Cost**
- Console encoding detection runs on each SafeOutput initialization
- Multiple instances may repeat detection unnecessarily
- No caching across different processes

### 3. Platform-Specific Limitations

**Windows Limitations**
- Code page changes require administrator privileges in some cases
- Windows Terminal vs Command Prompt behavior differences
- Some Unicode characters may display incorrectly even with UTF-8

**SSH/Remote Session Issues**
- Terminal type detection may be unreliable
- Locale settings can be inherited incorrectly
- Network latency may affect real-time progress updates

**Docker Container Limitations**
- Base images may lack locale support
- Font availability varies by container
- Environment variable inheritance issues

### 4. Output Stream Limitations

**File Output**
- Unicode detection is based on console, not file encoding
- File encoding must be handled separately
- No automatic encoding detection for file streams

```python
# Limitation example
with open('output.txt', 'w', encoding='utf-8') as f:
    output = SafeOutput(output_stream=f)
    output.safe_print("✅ Test")  # May still use ASCII fallback
```

**Custom Stream Handling**
- Limited support for custom TextIO implementations
- Encoding detection may not work with wrapped streams
- Buffer flushing behavior may vary

## Known Issues

### 1. Windows-Specific Issues

**Issue: Code Page Reset**
- **Symptom**: Console reverts to original code page after script ends
- **Cause**: Windows automatically resets code page
- **Workaround**: Set code page in batch file or PowerShell script

```batch
@echo off
chcp 65001 > nul
python your_script.py
```

**Issue: Administrator Privileges**
- **Symptom**: Code page change fails silently
- **Cause**: Some Windows configurations require admin rights
- **Workaround**: Run terminal as administrator or use Windows Terminal

**Issue: Font Rendering**
- **Symptom**: Unicode characters display as boxes or question marks
- **Cause**: Console font doesn't support Unicode characters
- **Workaround**: Change console font to "Consolas" or "Cascadia Code"

### 2. macOS-Specific Issues

**Issue: Terminal.app Font Limitations**
- **Symptom**: Some Unicode characters don't display
- **Cause**: Default font lacks certain Unicode ranges
- **Workaround**: Use iTerm2 or change font to one with better Unicode support

**Issue: SSH Session Encoding**
- **Symptom**: Unicode works locally but fails over SSH
- **Cause**: SSH client/server locale mismatch
- **Workaround**: Set locale in SSH configuration

```bash
# In ~/.ssh/config
Host *
    SendEnv LANG LC_*
```

### 3. Linux-Specific Issues

**Issue: Minimal Docker Images**
- **Symptom**: Locale errors in Alpine or minimal containers
- **Cause**: Missing locale packages
- **Workaround**: Install locale support in Dockerfile

```dockerfile
RUN apk add --no-cache musl-locales musl-locales-lang
ENV LANG=C.UTF-8
```

**Issue: Headless Server Environments**
- **Symptom**: Unicode detection fails on servers without display
- **Cause**: No terminal attached or DISPLAY variable set
- **Workaround**: Force ASCII mode or set appropriate environment variables

### 4. Cross-Platform Issues

**Issue: Inconsistent Progress Bar Updates**
- **Symptom**: Progress bars flicker or don't update smoothly
- **Cause**: Different terminal handling of carriage return (\r)
- **Workaround**: Use flush=True and appropriate delays

```python
import time
from src.utils.unicode_utils import print_progress

for i in range(101):
    print_progress(i, 100, "Progress: ", end='\r', flush=True)
    time.sleep(0.01)  # Small delay for smooth updates
```

**Issue: Mixed Output Streams**
- **Symptom**: Unicode and ASCII output mixed inconsistently
- **Cause**: Different parts of application using different output methods
- **Workaround**: Consistent use of SafeOutput throughout application

## Workarounds and Solutions

### 1. Performance Optimization

**Batch Processing**
```python
from src.utils.unicode_utils import SafeOutput

output = SafeOutput()
lines = []

# Collect output
for i in range(1000):
    lines.append(f"Item {i}: ✅")

# Output in batches
batch_size = 100
for i in range(0, len(lines), batch_size):
    batch = lines[i:i+batch_size]
    for line in batch:
        output.safe_print(line, flush=False)
    output.safe_print("", flush=True)  # Flush batch
```

**Disable Unicode for Bulk Operations**
```python
# For large text processing, disable Unicode
output = SafeOutput(enable_unicode=False)
for i in range(10000):
    output.safe_print(f"Processing item {i}: ✅")  # Uses [OK]
```

### 2. Reliable Platform Detection

**Force Specific Behavior**
```python
import platform
from src.utils.unicode_utils import SafeOutput

# Platform-specific configuration
if platform.system() == 'Windows':
    # Conservative approach for Windows
    output = SafeOutput(enable_unicode=False)
elif 'SSH_CLIENT' in os.environ:
    # ASCII mode for SSH sessions
    output = SafeOutput(enable_unicode=False)
else:
    # Auto-detect for other cases
    output = SafeOutput()
```

**Environment-Based Configuration**
```python
import os
from src.utils.unicode_utils import configure

# Configure based on environment
if os.environ.get('FORCE_ASCII', '').lower() == 'true':
    configure(enable_unicode=False)
elif os.environ.get('FORCE_UNICODE', '').lower() == 'true':
    configure(enable_unicode=True)
else:
    configure(enable_unicode=None)  # Auto-detect
```

### 3. Robust Error Handling

**Graceful Degradation**
```python
from src.utils.unicode_utils import SafeOutput, is_unicode_supported

def robust_output(message: str):
    """Output with multiple fallback levels."""
    try:
        # Try Unicode-aware output
        output = SafeOutput()
        output.safe_print(message)
    except Exception as e1:
        try:
            # Fallback to basic safe_print
            from src.utils.unicode_utils import safe_print
            safe_print(message)
        except Exception as e2:
            try:
                # Ultimate fallback to standard print
                print(message.encode('ascii', errors='replace').decode('ascii'))
            except Exception as e3:
                # Last resort
                print("[OUTPUT ERROR]")
```

### 4. Testing and Validation

**Comprehensive Testing Function**
```python
def test_unicode_compatibility():
    """Test Unicode compatibility across different scenarios."""
    
    from src.utils.unicode_utils import (
        SafeOutput, is_unicode_supported, get_console_info,
        safe_print, print_status, print_progress
    )
    
    print("Unicode Compatibility Test")
    print("=" * 40)
    
    # Basic info
    info = get_console_info()
    print(f"Platform: {info['platform']}")
    print(f"Encoding: {info['detected_encoding']}")
    print(f"Unicode supported: {info['unicode_supported']}")
    print()
    
    # Test basic output
    try:
        safe_print("Basic test: ✅ Success")
        print("✓ Basic output works")
    except Exception as e:
        print(f"✗ Basic output failed: {e}")
    
    # Test status output
    try:
        print_status("success", "Status test")
        print("✓ Status output works")
    except Exception as e:
        print(f"✗ Status output failed: {e}")
    
    # Test progress output
    try:
        print_progress(50, 100, "Progress test: ")
        print("✓ Progress output works")
    except Exception as e:
        print(f"✗ Progress output failed: {e}")
    
    # Test with different modes
    for unicode_mode in [True, False, None]:
        try:
            output = SafeOutput(enable_unicode=unicode_mode)
            output.safe_print(f"Mode {unicode_mode}: ✅ Test")
            print(f"✓ Mode {unicode_mode} works")
        except Exception as e:
            print(f"✗ Mode {unicode_mode} failed: {e}")

if __name__ == "__main__":
    test_unicode_compatibility()
```

## Future Improvements

### Planned Enhancements

1. **Extended Character Mapping**
   - More comprehensive emoji support
   - Mathematical and scientific symbols
   - Regional character support

2. **Performance Optimization**
   - Caching for repeated character replacements
   - Batch processing optimizations
   - Lazy loading of character maps

3. **Enhanced Platform Support**
   - Better Windows Terminal detection
   - Improved SSH session handling
   - Container-specific optimizations

4. **Configuration Management**
   - Configuration file support
   - Environment-based settings
   - Runtime configuration updates

### Contributing

If you encounter issues not listed here:

1. **Check existing documentation** for similar problems
2. **Test on multiple platforms** to isolate platform-specific issues
3. **Provide detailed environment information** when reporting issues
4. **Include minimal reproduction examples** for bug reports

### Reporting Issues

When reporting issues, please include:

```python
# Run this diagnostic script and include output
from src.utils.unicode_utils import get_console_info
import platform
import sys

print("System Information:")
print(f"Python version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"System: {platform.system()}")

print("\nConsole Information:")
info = get_console_info()
for key, value in info.items():
    print(f"{key}: {value}")

print("\nEnvironment Variables:")
import os
relevant_vars = ['LANG', 'LC_ALL', 'PYTHONIOENCODING', 'TERM', 'SSH_CLIENT']
for var in relevant_vars:
    value = os.environ.get(var, 'Not set')
    print(f"{var}: {value}")
```

This information helps identify the root cause of issues and develop appropriate solutions.