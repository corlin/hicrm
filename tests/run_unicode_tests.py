"""
Comprehensive test runner for Unicode utilities.

This script runs all Unicode-related tests including cross-platform,
performance, backwards compatibility, and CI/CD tests.
"""

import sys
import os
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class UnicodeTestRunner:
    """Comprehensive test runner for Unicode utilities."""
    
    def __init__(self):
        """Initialize the test runner."""
        self.test_dir = Path(__file__).parent
        self.project_root = self.test_dir.parent
        self.results = {}
        
    def run_test_suite(self, suite_name: str, test_files: List[str], 
                      extra_args: List[str] = None) -> Dict[str, Any]:
        """
        Run a test suite and return results.
        
        Args:
            suite_name: Name of the test suite
            test_files: List of test files to run
            extra_args: Additional pytest arguments
            
        Returns:
            Dictionary with test results
        """
        print(f"\n{'='*60}")
        print(f"Running {suite_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Build pytest command
        cmd = ['python', '-m', 'pytest']
        
        # Add test files
        for test_file in test_files:
            test_path = self.test_dir / test_file
            if test_path.exists():
                cmd.append(str(test_path))
            else:
                print(f"Warning: Test file not found: {test_file}")
        
        # Add extra arguments
        if extra_args:
            cmd.extend(extra_args)
        
        # Add common arguments
        cmd.extend([
            '-v',  # Verbose output
            '--tb=short',  # Short traceback format
            '--strict-markers',  # Strict marker checking
        ])
        
        print(f"Command: {' '.join(cmd)}")
        print()
        
        # Run tests
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse results
            test_results = {
                'suite_name': suite_name,
                'duration': duration,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
            }
            
            # Print results
            if test_results['success']:
                print(f"✅ {suite_name} PASSED ({duration:.2f}s)")
            else:
                print(f"❌ {suite_name} FAILED ({duration:.2f}s)")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print("STDERR:")
                    print(result.stderr)
            
            # Show output if verbose or failed
            if not test_results['success'] or '--verbose' in sys.argv:
                print("\nTest Output:")
                print(result.stdout)
            
            return test_results
            
        except subprocess.TimeoutExpired:
            print(f"❌ {suite_name} TIMEOUT (>300s)")
            return {
                'suite_name': suite_name,
                'duration': 300,
                'return_code': -1,
                'success': False,
                'error': 'Timeout'
            }
        except Exception as e:
            print(f"❌ {suite_name} ERROR: {e}")
            return {
                'suite_name': suite_name,
                'duration': 0,
                'return_code': -1,
                'success': False,
                'error': str(e)
            }
    
    def run_all_tests(self, quick: bool = False) -> Dict[str, Any]:
        """
        Run all Unicode test suites.
        
        Args:
            quick: If True, run only essential tests
            
        Returns:
            Dictionary with all test results
        """
        print("🧪 Starting Comprehensive Unicode Test Suite")
        print(f"Project root: {self.project_root}")
        print(f"Test directory: {self.test_dir}")
        
        # Define test suites
        test_suites = [
            {
                'name': 'Unit Tests',
                'files': [
                    'test_character_map.py',
                    'test_console_handler.py', 
                    'test_safe_output.py',
                ],
                'args': ['--tb=short'],
            },
            {
                'name': 'Integration Tests',
                'files': ['test_unicode_utils_integration.py'],
                'args': ['--tb=short'],
            },
            {
                'name': 'Cross-Platform Tests',
                'files': ['test_unicode_cross_platform.py'],
                'args': ['--tb=short'],
            },
            {
                'name': 'Backwards Compatibility Tests',
                'files': ['test_unicode_backwards_compatibility.py'],
                'args': ['--tb=short'],
            },
        ]
        
        # Add performance and CI tests if not quick mode
        if not quick:
            test_suites.extend([
                {
                    'name': 'Performance Tests',
                    'files': ['test_performance/test_unicode_performance.py'],
                    'args': ['--tb=short', '-x'],  # Stop on first failure for performance
                },
                {
                    'name': 'CI/CD Tests',
                    'files': ['test_unicode_ci_cd.py'],
                    'args': ['--tb=short'],
                },
            ])
        
        # Run each test suite
        all_results = {}
        total_start_time = time.time()
        
        for suite_config in test_suites:
            suite_results = self.run_test_suite(
                suite_config['name'],
                suite_config['files'],
                suite_config.get('args', [])
            )
            all_results[suite_config['name']] = suite_results
        
        total_duration = time.time() - total_start_time
        
        # Print summary
        self.print_summary(all_results, total_duration)
        
        return all_results
    
    def print_summary(self, results: Dict[str, Any], total_duration: float):
        """Print test results summary."""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        passed = 0
        failed = 0
        total_tests = len(results)
        
        for suite_name, suite_results in results.items():
            status = "✅ PASS" if suite_results['success'] else "❌ FAIL"
            duration = suite_results.get('duration', 0)
            print(f"{status} {suite_name:<30} ({duration:.2f}s)")
            
            if suite_results['success']:
                passed += 1
            else:
                failed += 1
        
        print(f"\n{'='*60}")
        print(f"Total: {total_tests} suites")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Duration: {total_duration:.2f}s")
        
        if failed == 0:
            print("🎉 All tests passed!")
        else:
            print(f"💥 {failed} test suite(s) failed")
        
        print(f"{'='*60}")
    
    def run_specific_tests(self, test_patterns: List[str]) -> Dict[str, Any]:
        """
        Run specific tests matching patterns.
        
        Args:
            test_patterns: List of test file patterns or names
            
        Returns:
            Dictionary with test results
        """
        print(f"🎯 Running specific tests: {', '.join(test_patterns)}")
        
        # Find matching test files
        test_files = []
        for pattern in test_patterns:
            if pattern.endswith('.py'):
                test_files.append(pattern)
            else:
                # Look for files containing the pattern
                for test_file in self.test_dir.glob(f"*{pattern}*.py"):
                    test_files.append(test_file.name)
        
        if not test_files:
            print("❌ No matching test files found")
            return {}
        
        return self.run_test_suite("Specific Tests", test_files)
    
    def run_performance_benchmark(self) -> Dict[str, Any]:
        """Run performance benchmark tests."""
        print("🚀 Running Performance Benchmarks")
        
        return self.run_test_suite(
            "Performance Benchmarks",
            ['test_performance/test_unicode_performance.py'],
            ['--tb=short', '--benchmark-only', '-v']
        )


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Unicode utilities test runner')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only essential tests (skip performance and CI tests)')
    parser.add_argument('--performance', action='store_true',
                       help='Run only performance tests')
    parser.add_argument('--ci', action='store_true',
                       help='Run only CI/CD tests')
    parser.add_argument('--specific', nargs='+', metavar='PATTERN',
                       help='Run specific tests matching patterns')
    parser.add_argument('--verbose', action='store_true',
                       help='Show verbose output')
    
    args = parser.parse_args()
    
    runner = UnicodeTestRunner()
    
    try:
        if args.specific:
            results = runner.run_specific_tests(args.specific)
        elif args.performance:
            results = runner.run_performance_benchmark()
        elif args.ci:
            results = runner.run_test_suite("CI/CD Tests", ['test_unicode_ci_cd.py'])
        else:
            results = runner.run_all_tests(quick=args.quick)
        
        # Exit with appropriate code
        if results:
            failed_suites = [name for name, result in results.items() if not result['success']]
            if failed_suites:
                print(f"\n❌ Failed suites: {', '.join(failed_suites)}")
                sys.exit(1)
            else:
                print("\n✅ All tests passed!")
                sys.exit(0)
        else:
            print("\n❌ No tests were run")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()