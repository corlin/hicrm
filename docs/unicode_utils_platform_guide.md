# Platform-Specific Guide for Unicode Utils

This document provides detailed information about how the Unicode utilities package behaves on different platforms and how to handle platform-specific issues.

## Windows Platform

### Common Encoding Issues

**GBK Encoding (Chinese Windows)**
- Default encoding on Chinese Windows systems
- Limited Unicode character support
- Causes `UnicodeEncodeError` for most emoji and symbols

**Code Page 936 (GBK)**
```python
# Detection example
from src.utils.unicode_utils import get_console_info

info = get_console_info()
print(f"Encoding: {info['detected_encoding']}")  # Often shows 'gbk'
```

**Code Page 65001 (UTF-8)**
- Modern Windows UTF-8 support
- Package automatically attempts to set this
- May require administrator privileges

### Windows-Specific Solutions

**Automatic Code Page Setup**
```python
from src.utils.unicode_utils import setup_unicode_console

# This attempts to run: chcp 65001
success = setup_unicode_console()
if success:
    print("✅ UTF-8 console configured")
else:
    print("[OK] Using ASCII fallback")
```

**Manual Code Page Setup**
```cmd
# Run in Command Prompt before Python script
chcp 65001

# Then run your Python script
python your_script.py
```

**PowerShell Configuration**
```powershell
# Set UTF-8 encoding in PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

# Run Python script
python your_script.py
```

### Windows Terminal vs Command Prompt

**Windows Terminal (Recommended)**
- Better Unicode support
- Modern font rendering
- UTF-8 by default in newer versions

**Command Prompt (Legacy)**
- Limited Unicode support
- May require manual code page setup
- Font limitations

**PowerShell**
- Good Unicode support
- May need encoding configuration
- Better than Command Prompt

### Windows-Specific Code Examples

```python
import platform
from src.utils.unicode_utils import SafeOutput, get_console_info

def windows_unicode_setup():
    """Windows-specific Unicode setup example."""
    
    if platform.system() != 'Windows':
        return
    
    output = SafeOutput()
    
    # Display current console information
    output.safe_print("Windows Console Information:")
    info = get_console_info()
    
    for key, value in info.items():
        output.safe_print(f"  {key}: {value}")
    
    # Test Unicode capabilities
    output.safe_print("\nTesting Unicode output:")
    test_chars = ['✅', '❌', '⚠️', '⏳', '🔍']
    
    for char in test_chars:
        try:
            output.safe_print(f"  {char} - Unicode test")
        except Exception as e:
            output.safe_print(f"  [?] - Failed: {e}")

if __name__ == "__main__":
    windows_unicode_setup()
```

## macOS Platform

### Characteristics

**Default Encoding**
- UTF-8 by default
- Excellent Unicode support
- Minimal configuration needed

**Terminal Applications**
- Terminal.app: Good Unicode support
- iTerm2: Excellent Unicode support
- VS Code terminal: Good support

### macOS-Specific Considerations

**Font Support**
```python
# Some Unicode characters may not display due to font limitations
from src.utils.unicode_utils import SafeOutput

output = SafeOutput()

# These usually work well on macOS
output.safe_print("✅ Success")
output.safe_print("❌ Error") 
output.safe_print("⚠️ Warning")

# Complex emoji might have font issues
output.safe_print("🚀 Rocket")  # May not display in all terminals
```

**SSH Sessions**
```python
import os
from src.utils.unicode_utils import get_console_info

def check_ssh_encoding():
    """Check encoding in SSH sessions."""
    
    is_ssh = 'SSH_CLIENT' in os.environ or 'SSH_TTY' in os.environ
    
    if is_ssh:
        print("Running in SSH session")
        info = get_console_info()
        print(f"Encoding: {info['detected_encoding']}")
        print(f"LANG: {info['environment_lang']}")
    else:
        print("Running locally")
```

### macOS Code Examples

```python
import subprocess
from src.utils.unicode_utils import SafeOutput

def macos_unicode_info():
    """Display macOS-specific Unicode information."""
    
    output = SafeOutput()
    
    # Check locale settings
    try:
        result = subprocess.run(['locale'], capture_output=True, text=True)
        output.safe_print("Locale settings:")
        for line in result.stdout.strip().split('\n'):
            output.safe_print(f"  {line}")
    except Exception as e:
        output.safe_print(f"Failed to get locale info: {e}")
    
    # Check terminal info
    term = os.environ.get('TERM', 'unknown')
    term_program = os.environ.get('TERM_PROGRAM', 'unknown')
    
    output.safe_print(f"\nTerminal: {term}")
    output.safe_print(f"Terminal Program: {term_program}")
    
    # Test Unicode
    output.safe_print("\nUnicode test:")
    output.safe_print("Basic: ✅ ❌ ⚠️")
    output.safe_print("Progress: ████░░░░")
    output.safe_print("Borders: ┌─────┐")
    output.safe_print("         │ Box │")
    output.safe_print("         └─────┘")
```

## Linux Platform

### Distribution Differences

**Ubuntu/Debian**
- UTF-8 by default
- Good Unicode support
- Standard locale configuration

**CentOS/RHEL**
- May need locale configuration
- Check LANG environment variable
- UTF-8 usually available

**Alpine Linux**
- Minimal installation
- May lack Unicode fonts
- Check locale support

### Locale Configuration

**Check Current Locale**
```bash
locale
echo $LANG
```

**Set UTF-8 Locale**
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

**Install Locale Support**
```bash
# Ubuntu/Debian
sudo apt-get install locales
sudo locale-gen en_US.UTF-8

# CentOS/RHEL
sudo yum install glibc-locale-source glibc-langpack-en
```

### Linux-Specific Code Examples

```python
import os
import subprocess
from src.utils.unicode_utils import SafeOutput, get_console_info

def linux_unicode_setup():
    """Linux-specific Unicode setup and diagnostics."""
    
    output = SafeOutput()
    
    # Check distribution
    try:
        with open('/etc/os-release', 'r') as f:
            for line in f:
                if line.startswith('PRETTY_NAME='):
                    distro = line.split('=')[1].strip().strip('"')
                    output.safe_print(f"Distribution: {distro}")
                    break
    except FileNotFoundError:
        output.safe_print("Distribution: Unknown")
    
    # Check locale
    lang = os.environ.get('LANG', 'Not set')
    lc_all = os.environ.get('LC_ALL', 'Not set')
    
    output.safe_print(f"LANG: {lang}")
    output.safe_print(f"LC_ALL: {lc_all}")
    
    # Check available locales
    try:
        result = subprocess.run(['locale', '-a'], capture_output=True, text=True)
        utf8_locales = [l for l in result.stdout.split('\n') if 'utf8' in l.lower()]
        output.safe_print(f"UTF-8 locales available: {len(utf8_locales)}")
        if utf8_locales:
            output.safe_print("Examples:")
            for locale in utf8_locales[:3]:
                output.safe_print(f"  {locale}")
    except Exception as e:
        output.safe_print(f"Failed to check locales: {e}")
    
    # Console info
    info = get_console_info()
    output.safe_print(f"\nDetected encoding: {info['detected_encoding']}")
    output.safe_print(f"Unicode supported: {info['unicode_supported']}")

def fix_linux_locale():
    """Attempt to fix locale issues on Linux."""
    
    output = SafeOutput()
    
    # Set environment variables
    utf8_locales = ['en_US.UTF-8', 'C.UTF-8', 'en_GB.UTF-8']
    
    for locale_name in utf8_locales:
        os.environ['LANG'] = locale_name
        os.environ['LC_ALL'] = locale_name
        
        # Test if it works
        try:
            import locale
            locale.setlocale(locale.LC_ALL, locale_name)
            output.safe_print(f"✅ Successfully set locale to {locale_name}")
            break
        except locale.Error:
            output.safe_print(f"❌ Failed to set locale to {locale_name}")
            continue
    else:
        output.safe_print("⚠️ Could not set UTF-8 locale")
```

### Docker Considerations

**Dockerfile Example**
```dockerfile
FROM python:3.9-slim

# Set locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install locale support if needed
RUN apt-get update && apt-get install -y locales && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

CMD ["python", "your_script.py"]
```

**Docker Run Example**
```bash
# Run with proper locale environment
docker run -e LANG=C.UTF-8 -e LC_ALL=C.UTF-8 your-image
```

## Cross-Platform Best Practices

### 1. Always Use the Unicode Utils Package

```python
# Good: Cross-platform safe
from src.utils.unicode_utils import safe_print
safe_print("Status: ✅ Success")

# Bad: Platform-dependent
print("Status: ✅ Success")  # May fail on Windows GBK
```

### 2. Test on Target Platforms

```python
def test_unicode_on_platform():
    """Test Unicode support on current platform."""
    
    from src.utils.unicode_utils import test_unicode_output, get_console_info
    
    print("Platform Unicode Test")
    print("=" * 50)
    
    # Show platform info
    info = get_console_info()
    for key, value in info.items():
        print(f"{key}: {value}")
    
    print("\nUnicode Output Test:")
    test_unicode_output()
```

### 3. Provide Fallback Options

```python
from src.utils.unicode_utils import SafeOutput, is_unicode_supported

def display_with_fallback():
    """Display content with appropriate fallback."""
    
    output = SafeOutput()
    
    if is_unicode_supported():
        # Rich Unicode output
        output.safe_print("✨ Unicode Mode Active ✨")
        output.safe_print("Progress: ████████░░ 80%")
    else:
        # ASCII fallback
        output.safe_print("=== ASCII Mode Active ===")
        output.safe_print("Progress: [########..] 80%")
```

### 4. Handle Environment Variables

```python
import os
from src.utils.unicode_utils import configure

def setup_environment():
    """Setup environment for Unicode support."""
    
    # Force UTF-8 for Python I/O
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Configure the package
    configure(
        auto_setup=True,
        enable_unicode=None,  # Auto-detect
    )
```

### 5. Logging and Debugging

```python
import logging
from src.utils.unicode_utils import configure, get_console_info

def debug_unicode_issues():
    """Debug Unicode-related issues."""
    
    # Enable debug logging
    configure(log_level=logging.DEBUG)
    
    # Get detailed console information
    info = get_console_info()
    
    print("Unicode Debug Information:")
    print("=" * 40)
    
    for key, value in info.items():
        print(f"{key:25}: {value}")
    
    # Test specific characters
    from src.utils.unicode_utils import CharacterMap
    
    char_map = CharacterMap()
    test_chars = ['✅', '❌', '⚠️', '⏳', '🔍']
    
    print("\nCharacter Mapping Test:")
    for char in test_chars:
        unicode_ver = char_map.get_symbol(char, unicode_supported=True)
        ascii_ver = char_map.get_symbol(char, unicode_supported=False)
        print(f"{char} → Unicode: {unicode_ver}, ASCII: {ascii_ver}")
```

## Troubleshooting Common Issues

### Issue 1: Characters Display as Question Marks

**Symptoms:**
- Unicode characters show as `?` or `□`
- No error messages

**Causes:**
- Font doesn't support the characters
- Terminal encoding issues

**Solutions:**
```python
# Check if it's a font or encoding issue
from src.utils.unicode_utils import SafeOutput

output = SafeOutput(enable_unicode=False)  # Force ASCII mode
output.safe_print("Test: ✅")  # Should show "[OK]"

# If ASCII works, it's a font/display issue
# If ASCII doesn't work, it's an encoding issue
```

### Issue 2: UnicodeEncodeError Still Occurs

**Symptoms:**
- Getting `UnicodeEncodeError` despite using the package

**Causes:**
- Not using the safe output functions
- Custom output streams with encoding issues

**Solutions:**
```python
# Make sure you're using the safe functions
from src.utils.unicode_utils import safe_print

# Instead of print()
safe_print("✅ Success")

# For custom streams
from src.utils.unicode_utils import SafeOutput
import io

custom_stream = io.StringIO()
output = SafeOutput(output_stream=custom_stream)
output.safe_print("✅ Test")
```

### Issue 3: Performance Issues

**Symptoms:**
- Slow output with large amounts of text

**Causes:**
- Encoding detection overhead
- Character replacement overhead

**Solutions:**
```python
# Use buffered output
from src.utils.unicode_utils import SafeOutput

output = SafeOutput()

# Batch output and flush periodically
lines = []
for i in range(1000):
    lines.append(f"Line {i}: ✅")
    
    if len(lines) >= 100:
        for line in lines:
            output.safe_print(line, flush=False)
        output.safe_print("", flush=True)  # Flush batch
        lines.clear()
```

### Issue 4: SSH/Remote Session Issues

**Symptoms:**
- Works locally but fails over SSH

**Causes:**
- Different locale settings
- Terminal type differences

**Solutions:**
```python
import os
from src.utils.unicode_utils import SafeOutput, get_console_info

def handle_ssh_session():
    """Handle SSH session encoding issues."""
    
    # Check if we're in SSH
    is_ssh = 'SSH_CLIENT' in os.environ
    
    if is_ssh:
        # Force ASCII mode for SSH
        output = SafeOutput(enable_unicode=False)
    else:
        # Auto-detect for local sessions
        output = SafeOutput()
    
    output.safe_print("Status: ✅ Connected")
```

This platform-specific guide should help users understand and handle the various encoding challenges they might encounter across different operating systems and environments.