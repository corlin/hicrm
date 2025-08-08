# Unicode Utils Usage Examples

This document provides practical examples of how to use the Unicode utilities package in real-world scenarios.

## Example 1: File Processing Script

```python
#!/usr/bin/env python3
"""
Example: File processing script with Unicode-safe output
"""

import os
import time
from pathlib import Path
from src.utils.unicode_utils import safe_print, print_status, print_progress, print_section

def process_files(directory: str):
    """Process all files in a directory with progress tracking."""
    
    print_section("File Processing Report", level=1)
    safe_print()
    
    # Get list of files
    files = list(Path(directory).glob("*.txt"))
    
    if not files:
        print_status("warning", f"No .txt files found in {directory}")
        return
    
    print_status("info", f"Found {len(files)} files to process")
    safe_print()
    
    # Process each file
    processed = 0
    errors = 0
    
    for i, file_path in enumerate(files):
        # Update progress
        print_progress(i, len(files), "Processing: ", end='\r')
        
        try:
            # Simulate file processing
            time.sleep(0.1)  # Simulate work
            
            # Process the file (placeholder)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Do something with content...
            
            processed += 1
            
        except Exception as e:
            errors += 1
            safe_print()  # New line after progress
            print_status("error", f"Failed to process {file_path.name}: {e}")
    
    # Final progress update
    print_progress(len(files), len(files), "Processing: ")
    safe_print()
    
    # Summary
    print_section("Summary", level=2)
    print_status("success", f"Successfully processed {processed} files")
    if errors > 0:
        print_status("error", f"Failed to process {errors} files")
    else:
        print_status("success", "No errors encountered")

if __name__ == "__main__":
    process_files("./data")
```

## Example 2: Download Progress Tracker

```python
#!/usr/bin/env python3
"""
Example: Download progress tracker with Unicode-safe output
"""

import time
import random
from src.utils.unicode_utils import SafeOutput, print_status

class DownloadTracker:
    def __init__(self):
        self.output = SafeOutput()
    
    def download_file(self, url: str, filename: str, total_size: int):
        """Simulate file download with progress tracking."""
        
        self.output.safe_print(f"Downloading: {filename}")
        self.output.safe_print(f"URL: {url}")
        self.output.safe_print(f"Size: {total_size:,} bytes")
        self.output.safe_print()
        
        downloaded = 0
        chunk_size = max(1, total_size // 50)  # 50 updates
        
        try:
            while downloaded < total_size:
                # Simulate download chunk
                time.sleep(0.05)  # Simulate network delay
                chunk = min(chunk_size + random.randint(-100, 100), total_size - downloaded)
                downloaded += chunk
                
                # Update progress
                progress = self.output.format_progress(
                    downloaded, 
                    total_size, 
                    "Progress: ",
                    f"({downloaded:,}/{total_size:,} bytes)"
                )
                self.output.safe_print(progress, end='\r')
            
            # Final update
            progress = self.output.format_progress(
                total_size, 
                total_size, 
                "Progress: ",
                f"({total_size:,}/{total_size:,} bytes)"
            )
            self.output.safe_print(progress)
            
            print_status("success", f"Download completed: {filename}")
            
        except KeyboardInterrupt:
            self.output.safe_print()
            print_status("warning", "Download cancelled by user")
        except Exception as e:
            self.output.safe_print()
            print_status("error", f"Download failed: {e}")

def main():
    tracker = DownloadTracker()
    
    # Simulate multiple downloads
    downloads = [
        ("https://example.com/file1.zip", "file1.zip", 1024000),
        ("https://example.com/file2.pdf", "file2.pdf", 2048000),
        ("https://example.com/file3.mp4", "file3.mp4", 5120000),
    ]
    
    for url, filename, size in downloads:
        tracker.download_file(url, filename, size)
        print()  # Space between downloads

if __name__ == "__main__":
    main()
```

## Example 3: System Status Monitor

```python
#!/usr/bin/env python3
"""
Example: System status monitor with Unicode-safe output
"""

import psutil
import time
from datetime import datetime
from src.utils.unicode_utils import SafeOutput, print_section

class SystemMonitor:
    def __init__(self):
        self.output = SafeOutput()
    
    def get_status_symbol(self, value: float, warning_threshold: float, critical_threshold: float):
        """Get appropriate status symbol based on thresholds."""
        if value >= critical_threshold:
            return self.output.format_status("error", f"{value:.1f}%")
        elif value >= warning_threshold:
            return self.output.format_status("warning", f"{value:.1f}%")
        else:
            return self.output.format_status("success", f"{value:.1f}%")
    
    def display_system_status(self):
        """Display comprehensive system status."""
        
        # Header
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.output.safe_print(self.output.format_section(f"System Status - {timestamp}", level=1))
        self.output.safe_print()
        
        # CPU Usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.output.safe_print("CPU Usage:")
        self.output.safe_print(f"  {self.get_status_symbol(cpu_percent, 70, 90)}")
        
        # CPU per core
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        for i, core_percent in enumerate(cpu_per_core):
            core_bar = self.output.format_progress(
                int(core_percent), 100, f"  Core {i}: ", bar_length=20
            )
            self.output.safe_print(core_bar)
        
        self.output.safe_print()
        
        # Memory Usage
        memory = psutil.virtual_memory()
        self.output.safe_print("Memory Usage:")
        self.output.safe_print(f"  {self.get_status_symbol(memory.percent, 80, 95)}")
        
        memory_bar = self.output.format_progress(
            memory.used, memory.total, "  RAM: ",
            f"({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)",
            bar_length=30
        )
        self.output.safe_print(memory_bar)
        self.output.safe_print()
        
        # Disk Usage
        self.output.safe_print("Disk Usage:")
        for partition in psutil.disk_partitions():
            try:
                disk_usage = psutil.disk_usage(partition.mountpoint)
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                
                self.output.safe_print(f"  {partition.device} ({partition.mountpoint}):")
                self.output.safe_print(f"    {self.get_status_symbol(disk_percent, 80, 95)}")
                
                disk_bar = self.output.format_progress(
                    disk_usage.used, disk_usage.total, "    ",
                    f"({disk_usage.used // (1024**3):.1f}GB / {disk_usage.total // (1024**3):.1f}GB)",
                    bar_length=25
                )
                self.output.safe_print(disk_bar)
                
            except PermissionError:
                self.output.safe_print(f"  {partition.device}: Permission denied")
        
        self.output.safe_print()
        
        # Network Statistics
        net_io = psutil.net_io_counters()
        self.output.safe_print(self.output.format_section("Network Statistics", level=2))
        self.output.safe_print(f"Bytes sent: {net_io.bytes_sent:,}")
        self.output.safe_print(f"Bytes received: {net_io.bytes_recv:,}")
        self.output.safe_print(f"Packets sent: {net_io.packets_sent:,}")
        self.output.safe_print(f"Packets received: {net_io.packets_recv:,}")
    
    def monitor_continuously(self, interval: int = 5):
        """Monitor system continuously with specified interval."""
        try:
            while True:
                self.display_system_status()
                self.output.safe_print(f"\nRefreshing in {interval} seconds... (Ctrl+C to stop)")
                self.output.safe_print("=" * 60)
                time.sleep(interval)
        except KeyboardInterrupt:
            self.output.safe_print("\nMonitoring stopped by user")

def main():
    monitor = SystemMonitor()
    
    # Single status check
    monitor.display_system_status()
    
    # Uncomment for continuous monitoring
    # monitor.monitor_continuously(interval=10)

if __name__ == "__main__":
    main()
```

## Example 4: Log File Analyzer

```python
#!/usr/bin/env python3
"""
Example: Log file analyzer with Unicode-safe output
"""

import re
from collections import defaultdict, Counter
from pathlib import Path
from src.utils.unicode_utils import SafeOutput, print_section, print_status

class LogAnalyzer:
    def __init__(self):
        self.output = SafeOutput()
        self.log_patterns = {
            'error': re.compile(r'\b(error|exception|failed|failure)\b', re.IGNORECASE),
            'warning': re.compile(r'\b(warning|warn)\b', re.IGNORECASE),
            'info': re.compile(r'\b(info|information)\b', re.IGNORECASE),
            'debug': re.compile(r'\b(debug)\b', re.IGNORECASE),
        }
    
    def analyze_log_file(self, log_file_path: str):
        """Analyze a log file and display statistics."""
        
        log_path = Path(log_file_path)
        if not log_path.exists():
            print_status("error", f"Log file not found: {log_file_path}")
            return
        
        print_section(f"Log Analysis: {log_path.name}", level=1)
        self.output.safe_print()
        
        # Initialize counters
        line_count = 0
        level_counts = defaultdict(int)
        hourly_stats = defaultdict(int)
        error_messages = []
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    line_count += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    # Count log levels
                    for level, pattern in self.log_patterns.items():
                        if pattern.search(line):
                            level_counts[level] += 1
                            
                            # Collect error messages
                            if level == 'error':
                                error_messages.append((line_num, line[:100]))
                    
                    # Extract timestamp for hourly stats (basic pattern)
                    timestamp_match = re.search(r'(\d{2}):(\d{2}):(\d{2})', line)
                    if timestamp_match:
                        hour = int(timestamp_match.group(1))
                        hourly_stats[hour] += 1
                    
                    # Progress update for large files
                    if line_num % 10000 == 0:
                        self.output.safe_print(f"Processed {line_num:,} lines...", end='\r')
        
        except Exception as e:
            print_status("error", f"Failed to read log file: {e}")
            return
        
        # Clear progress line
        if line_count > 10000:
            self.output.safe_print(" " * 50, end='\r')
        
        # Display results
        self.display_analysis_results(log_path, line_count, level_counts, hourly_stats, error_messages)
    
    def display_analysis_results(self, log_path, line_count, level_counts, hourly_stats, error_messages):
        """Display the analysis results."""
        
        # Basic statistics
        print_section("Basic Statistics", level=2)
        print_status("info", f"Total lines: {line_count:,}")
        print_status("info", f"File size: {log_path.stat().st_size:,} bytes")
        self.output.safe_print()
        
        # Log level distribution
        print_section("Log Level Distribution", level=2)
        total_log_entries = sum(level_counts.values())
        
        if total_log_entries > 0:
            for level in ['error', 'warning', 'info', 'debug']:
                count = level_counts[level]
                if count > 0:
                    percentage = (count / total_log_entries) * 100
                    
                    # Choose appropriate status symbol
                    if level == 'error':
                        status_msg = self.output.format_status("error", f"{count:,} entries ({percentage:.1f}%)")
                    elif level == 'warning':
                        status_msg = self.output.format_status("warning", f"{count:,} entries ({percentage:.1f}%)")
                    else:
                        status_msg = self.output.format_status("info", f"{count:,} entries ({percentage:.1f}%)")
                    
                    self.output.safe_print(f"{level.upper()}: {status_msg}")
                    
                    # Progress bar for visual representation
                    progress_bar = self.output.format_progress(
                        count, total_log_entries, "  ", bar_length=30
                    )
                    self.output.safe_print(progress_bar)
        else:
            print_status("warning", "No log level patterns found")
        
        self.output.safe_print()
        
        # Hourly activity
        if hourly_stats:
            print_section("Hourly Activity", level=2)
            max_hourly = max(hourly_stats.values()) if hourly_stats else 1
            
            for hour in range(24):
                count = hourly_stats.get(hour, 0)
                if count > 0:
                    hour_bar = self.output.format_progress(
                        count, max_hourly, f"{hour:02d}:00 ", 
                        f"({count:,} entries)", bar_length=20
                    )
                    self.output.safe_print(hour_bar)
        
        self.output.safe_print()
        
        # Error summary
        if error_messages:
            print_section("Recent Errors (First 10)", level=2)
            for line_num, message in error_messages[:10]:
                self.output.safe_print(f"Line {line_num}: {message}")
                if len(message) == 100:  # Truncated
                    self.output.safe_print("  [... truncated]")
        
        # Summary
        self.output.safe_print()
        print_section("Summary", level=2)
        
        if level_counts['error'] > 0:
            print_status("error", f"Found {level_counts['error']} errors - requires attention")
        elif level_counts['warning'] > 0:
            print_status("warning", f"Found {level_counts['warning']} warnings - review recommended")
        else:
            print_status("success", "No errors or warnings found")

def main():
    analyzer = LogAnalyzer()
    
    # Example usage
    log_files = [
        "logs/application.log",
        "logs/error.log", 
        "logs/access.log"
    ]
    
    for log_file in log_files:
        if Path(log_file).exists():
            analyzer.analyze_log_file(log_file)
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
```

## Example 5: Test Runner with Results

```python
#!/usr/bin/env python3
"""
Example: Test runner with Unicode-safe output
"""

import time
import random
from dataclasses import dataclass
from typing import List, Callable
from src.utils.unicode_utils import SafeOutput, print_section, print_status

@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    error_message: str = ""

class TestRunner:
    def __init__(self):
        self.output = SafeOutput()
        self.tests: List[Callable] = []
        self.results: List[TestResult] = []
    
    def add_test(self, test_func: Callable):
        """Add a test function to the runner."""
        self.tests.append(test_func)
    
    def run_all_tests(self):
        """Run all registered tests and display results."""
        
        print_section("Test Execution", level=1)
        self.output.safe_print()
        
        self.results.clear()
        start_time = time.time()
        
        for i, test_func in enumerate(self.tests):
            # Progress update
            self.output.safe_print(
                self.output.format_progress(i, len(self.tests), "Running tests: "),
                end='\r'
            )
            
            # Run individual test
            result = self.run_single_test(test_func)
            self.results.append(result)
            
            # Display immediate result
            self.output.safe_print(" " * 50, end='\r')  # Clear progress line
            
            if result.passed:
                print_status("success", f"{result.name} ({result.duration:.3f}s)")
            else:
                print_status("error", f"{result.name} ({result.duration:.3f}s)")
                if result.error_message:
                    self.output.safe_print(f"  Error: {result.error_message}")
        
        # Final progress
        self.output.safe_print(
            self.output.format_progress(len(self.tests), len(self.tests), "Running tests: ")
        )
        
        total_time = time.time() - start_time
        self.display_test_summary(total_time)
    
    def run_single_test(self, test_func: Callable) -> TestResult:
        """Run a single test function."""
        test_name = test_func.__name__
        start_time = time.time()
        
        try:
            test_func()
            duration = time.time() - start_time
            return TestResult(test_name, True, duration)
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(test_name, False, duration, str(e))
    
    def display_test_summary(self, total_time: float):
        """Display comprehensive test results summary."""
        
        self.output.safe_print()
        print_section("Test Results Summary", level=1)
        self.output.safe_print()
        
        # Basic statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        
        print_status("info", f"Total tests: {total_tests}")
        print_status("success", f"Passed: {passed_tests}")
        if failed_tests > 0:
            print_status("error", f"Failed: {failed_tests}")
        
        self.output.safe_print(f"Total execution time: {total_time:.3f}s")
        self.output.safe_print()
        
        # Success rate visualization
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            success_bar = self.output.format_progress(
                passed_tests, total_tests, "Success rate: ",
                f"({success_rate:.1f}%)", bar_length=30
            )
            self.output.safe_print(success_bar)
            self.output.safe_print()
        
        # Failed tests details
        if failed_tests > 0:
            print_section("Failed Tests", level=2)
            for result in self.results:
                if not result.passed:
                    self.output.safe_print(f"❌ {result.name}")
                    self.output.safe_print(f"   Duration: {result.duration:.3f}s")
                    self.output.safe_print(f"   Error: {result.error_message}")
                    self.output.safe_print()
        
        # Performance analysis
        if self.results:
            print_section("Performance Analysis", level=2)
            durations = [r.duration for r in self.results]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            self.output.safe_print(f"Average test duration: {avg_duration:.3f}s")
            self.output.safe_print(f"Slowest test: {max_duration:.3f}s")
            self.output.safe_print(f"Fastest test: {min_duration:.3f}s")
            
            # Find slowest tests
            slowest_tests = sorted(self.results, key=lambda r: r.duration, reverse=True)[:3]
            self.output.safe_print("\nSlowest tests:")
            for result in slowest_tests:
                status_symbol = "✅" if result.passed else "❌"
                self.output.safe_print(f"  {status_symbol} {result.name}: {result.duration:.3f}s")
        
        # Final status
        self.output.safe_print()
        if failed_tests == 0:
            print_status("success", "All tests passed! 🎉")
        else:
            print_status("error", f"{failed_tests} test(s) failed")

# Example test functions
def test_example_1():
    """Example test that always passes."""
    time.sleep(random.uniform(0.1, 0.3))  # Simulate test work
    assert 1 + 1 == 2

def test_example_2():
    """Example test that sometimes fails."""
    time.sleep(random.uniform(0.05, 0.2))
    if random.random() < 0.8:  # 80% chance of passing
        assert True
    else:
        raise AssertionError("Random failure for demonstration")

def test_example_3():
    """Example slow test."""
    time.sleep(random.uniform(0.5, 1.0))
    assert "hello".upper() == "HELLO"

def test_example_4():
    """Example test with calculation."""
    time.sleep(random.uniform(0.1, 0.4))
    result = sum(range(100))
    expected = 99 * 100 // 2
    assert result == expected, f"Expected {expected}, got {result}"

def main():
    runner = TestRunner()
    
    # Register tests
    runner.add_test(test_example_1)
    runner.add_test(test_example_2)
    runner.add_test(test_example_3)
    runner.add_test(test_example_4)
    
    # Add more tests for demonstration
    for i in range(5, 15):
        def make_test(n):
            def test_func():
                time.sleep(random.uniform(0.05, 0.3))
                if random.random() < 0.9:  # 90% pass rate
                    assert n > 0
                else:
                    raise ValueError(f"Test {n} failed randomly")
            test_func.__name__ = f"test_example_{n}"
            return test_func
        
        runner.add_test(make_test(i))
    
    # Run all tests
    runner.run_all_tests()

if __name__ == "__main__":
    main()
```

## Example 6: Configuration Validator

```python
#!/usr/bin/env python3
"""
Example: Configuration validator with Unicode-safe output
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from src.utils.unicode_utils import SafeOutput, print_section, print_status

class ConfigValidator:
    def __init__(self):
        self.output = SafeOutput()
        self.validation_rules = {
            'required_fields': [],
            'field_types': {},
            'value_ranges': {},
            'custom_validators': {}
        }
    
    def add_required_field(self, field_path: str):
        """Add a required field to validation rules."""
        self.validation_rules['required_fields'].append(field_path)
    
    def add_type_check(self, field_path: str, expected_type: type):
        """Add type validation for a field."""
        self.validation_rules['field_types'][field_path] = expected_type
    
    def add_range_check(self, field_path: str, min_val=None, max_val=None):
        """Add range validation for numeric fields."""
        self.validation_rules['value_ranges'][field_path] = (min_val, max_val)
    
    def validate_config_file(self, config_path: str) -> bool:
        """Validate a configuration file."""
        
        config_file = Path(config_path)
        print_section(f"Configuration Validation: {config_file.name}", level=1)
        self.output.safe_print()
        
        # Check if file exists
        if not config_file.exists():
            print_status("error", f"Configuration file not found: {config_path}")
            return False
        
        # Load configuration
        try:
            config_data = self.load_config_file(config_file)
            print_status("success", "Configuration file loaded successfully")
        except Exception as e:
            print_status("error", f"Failed to load configuration: {e}")
            return False
        
        self.output.safe_print()
        
        # Run validations
        validation_results = []
        
        # Check required fields
        print_section("Required Fields Check", level=2)
        for field_path in self.validation_rules['required_fields']:
            result = self.check_required_field(config_data, field_path)
            validation_results.append(result)
            
            if result:
                print_status("success", f"Required field present: {field_path}")
            else:
                print_status("error", f"Missing required field: {field_path}")
        
        self.output.safe_print()
        
        # Check field types
        if self.validation_rules['field_types']:
            print_section("Type Validation", level=2)
            for field_path, expected_type in self.validation_rules['field_types'].items():
                result = self.check_field_type(config_data, field_path, expected_type)
                validation_results.append(result)
                
                if result:
                    print_status("success", f"Correct type for {field_path}: {expected_type.__name__}")
                else:
                    actual_type = type(self.get_nested_value(config_data, field_path))
                    print_status("error", f"Wrong type for {field_path}: expected {expected_type.__name__}, got {actual_type.__name__}")
        
        self.output.safe_print()
        
        # Check value ranges
        if self.validation_rules['value_ranges']:
            print_section("Range Validation", level=2)
            for field_path, (min_val, max_val) in self.validation_rules['value_ranges'].items():
                result = self.check_value_range(config_data, field_path, min_val, max_val)
                validation_results.append(result)
                
                if result:
                    range_str = f"[{min_val}, {max_val}]"
                    print_status("success", f"Value in range for {field_path}: {range_str}")
                else:
                    actual_val = self.get_nested_value(config_data, field_path)
                    range_str = f"[{min_val}, {max_val}]"
                    print_status("error", f"Value out of range for {field_path}: {actual_val} not in {range_str}")
        
        # Summary
        self.output.safe_print()
        self.display_validation_summary(validation_results)
        
        return all(validation_results)
    
    def load_config_file(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from JSON or YAML file."""
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() in ['.yml', '.yaml']:
                return yaml.safe_load(f)
            elif config_file.suffix.lower() == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {config_file.suffix}")
    
    def get_nested_value(self, data: Dict[str, Any], field_path: str):
        """Get value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def check_required_field(self, config_data: Dict[str, Any], field_path: str) -> bool:
        """Check if a required field is present."""
        value = self.get_nested_value(config_data, field_path)
        return value is not None
    
    def check_field_type(self, config_data: Dict[str, Any], field_path: str, expected_type: type) -> bool:
        """Check if a field has the expected type."""
        value = self.get_nested_value(config_data, field_path)
        if value is None:
            return False
        return isinstance(value, expected_type)
    
    def check_value_range(self, config_data: Dict[str, Any], field_path: str, min_val, max_val) -> bool:
        """Check if a numeric value is within the specified range."""
        value = self.get_nested_value(config_data, field_path)
        if value is None:
            return False
        
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        
        return True
    
    def display_validation_summary(self, results: List[bool]):
        """Display validation summary."""
        print_section("Validation Summary", level=2)
        
        total_checks = len(results)
        passed_checks = sum(results)
        failed_checks = total_checks - passed_checks
        
        if total_checks == 0:
            print_status("warning", "No validation rules defined")
            return
        
        # Statistics
        success_rate = (passed_checks / total_checks) * 100
        
        print_status("info", f"Total validation checks: {total_checks}")
        print_status("success", f"Passed: {passed_checks}")
        if failed_checks > 0:
            print_status("error", f"Failed: {failed_checks}")
        
        # Success rate bar
        success_bar = self.output.format_progress(
            passed_checks, total_checks, "Success rate: ",
            f"({success_rate:.1f}%)", bar_length=30
        )
        self.output.safe_print(success_bar)
        self.output.safe_print()
        
        # Final status
        if failed_checks == 0:
            print_status("success", "Configuration validation passed! ✅")
        else:
            print_status("error", f"Configuration validation failed with {failed_checks} error(s)")

def main():
    # Example usage
    validator = ConfigValidator()
    
    # Define validation rules
    validator.add_required_field("database.host")
    validator.add_required_field("database.port")
    validator.add_required_field("database.name")
    validator.add_required_field("api.key")
    
    validator.add_type_check("database.host", str)
    validator.add_type_check("database.port", int)
    validator.add_type_check("database.name", str)
    validator.add_type_check("api.timeout", (int, float))
    
    validator.add_range_check("database.port", 1, 65535)
    validator.add_range_check("api.timeout", 0.1, 300.0)
    validator.add_range_check("api.max_retries", 0, 10)
    
    # Create example config file for testing
    example_config = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "name": "myapp",
            "username": "user",
            "password": "secret"
        },
        "api": {
            "key": "abc123",
            "timeout": 30.0,
            "max_retries": 3
        }
    }
    
    # Save example config
    config_path = "example_config.json"
    with open(config_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    # Validate the configuration
    is_valid = validator.validate_config_file(config_path)
    
    # Clean up
    Path(config_path).unlink()
    
    return is_valid

if __name__ == "__main__":
    main()
```

These examples demonstrate various real-world scenarios where the Unicode utilities package can be used effectively:

1. **File Processing Script** - Shows progress tracking and status reporting
2. **Download Progress Tracker** - Demonstrates progress bars and error handling
3. **System Status Monitor** - Complex status displays with multiple metrics
4. **Log File Analyzer** - Text processing with statistical output
5. **Test Runner** - Test execution with detailed results reporting
6. **Configuration Validator** - Validation workflows with comprehensive reporting

Each example showcases different aspects of the Unicode utilities package while providing practical, reusable code patterns.