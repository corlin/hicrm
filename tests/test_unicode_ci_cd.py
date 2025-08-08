"""
CI/CD-specific tests for Unicode utilities.

Tests that ensure the Unicode utilities work correctly in automated
testing environments, continuous integration systems, and deployment pipelines.
"""

import pytest
import os
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

from src.utils.unicode_utils import SafeOutput, ConsoleHandler
from src.utils.unicode_utils import safe_print, print_status, print_progress, print_section
from tests.fixtures import (
    MockConsoleEnvironment, 
    unicode_test_data,
    test_output_stream,
    performance_test_data
)


class TestCIEnvironmentCompatibility:
    """Test compatibility with CI/CD environments."""
    
    def test_github_actions_environment(self):
        """Test compatibility with GitHub Actions environment."""
        ci_env = {
            'CI': 'true',
            'GITHUB_ACTIONS': 'true',
            'RUNNER_OS': 'Linux',
            'TERM': 'dumb',
        }
        
        with patch.dict(os.environ, ci_env), \
             patch('platform.system', return_value='Linux'):
            
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test typical CI output patterns
            output.safe_print("🚀 Starting CI build")
            output.safe_print(output.format_status("success", "Tests passed"))
            output.safe_print(output.format_status("error", "Build failed"))
            output.safe_print(output.format_progress(100, 100, "Deploy: "))
            
            result = test_stream.getvalue()
            
            # Should work without Unicode errors
            assert "Starting CI build" in result
            assert "Tests passed" in result
            assert "Build failed" in result
            assert "Deploy:" in result
            assert "100.0%" in result
    
    def test_jenkins_environment(self):
        """Test compatibility with Jenkins environment."""
        jenkins_env = {
            'JENKINS_URL': 'http://jenkins.example.com',
            'BUILD_NUMBER': '123',
            'JOB_NAME': 'test-job',
            'TERM': 'dumb',
        }
        
        with patch.dict(os.environ, jenkins_env), \
             patch('platform.system', return_value='Linux'):
            
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test Jenkins-style output
            output.safe_print(f"Build #{os.environ['BUILD_NUMBER']}")
            output.safe_print(output.format_status("success", "Unit tests ✅"))
            output.safe_print(output.format_status("warning", "Coverage below threshold ⚠️"))
            
            result = test_stream.getvalue()
            
            assert "Build #123" in result
            assert "Unit tests" in result
            assert "Coverage below threshold" in result
    
    def test_gitlab_ci_environment(self):
        """Test compatibility with GitLab CI environment."""
        gitlab_env = {
            'GITLAB_CI': 'true',
            'CI_JOB_NAME': 'test',
            'CI_PIPELINE_ID': '456',
            'TERM': 'xterm',
        }
        
        with patch.dict(os.environ, gitlab_env), \
             patch('platform.system', return_value='Linux'):
            
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test GitLab CI output
            output.safe_print("🔧 Running tests")
            output.safe_print(output.format_progress(75, 100, "Testing: "))
            output.safe_print(output.format_status("success", "All tests passed ✅"))
            
            result = test_stream.getvalue()
            
            assert "Running tests" in result
            assert "Testing:" in result
            assert "75.0%" in result
            assert "All tests passed" in result
    
    def test_azure_devops_environment(self):
        """Test compatibility with Azure DevOps environment."""
        azure_env = {
            'TF_BUILD': 'True',
            'AGENT_NAME': 'Azure Pipelines',
            'BUILD_BUILDNUMBER': '20231201.1',
            'TERM': 'dumb',
        }
        
        with patch.dict(os.environ, azure_env), \
             patch('platform.system', return_value='Linux'):
            
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test Azure DevOps output
            output.safe_print("⚙️ Azure Pipeline Build")
            output.safe_print(output.format_section("Test Results", level=1))
            output.safe_print(output.format_status("success", "Build succeeded"))
            
            result = test_stream.getvalue()
            
            assert "Azure Pipeline Build" in result
            assert "Test Results" in result
            assert "Build succeeded" in result


class TestDockerEnvironmentCompatibility:
    """Test compatibility with Docker containers."""
    
    def test_docker_container_environment(self):
        """Test behavior in Docker containers."""
        docker_env = {
            'container': 'docker',
            'HOSTNAME': 'container-id',
        }
        
        with patch.dict(os.environ, docker_env), \
             patch('platform.system', return_value='Linux'):
            
            # Mock limited encoding support typical in containers
            with patch.object(ConsoleHandler, 'detect_console_encoding', return_value='ascii'), \
                 patch.object(ConsoleHandler, 'is_unicode_supported', return_value=False):
                
                test_stream = StringIO()
                output = SafeOutput(auto_setup=False, output_stream=test_stream)
                
                # Test container-typical output
                output.safe_print("🐳 Container startup")
                output.safe_print(output.format_status("success", "Service ready ✅"))
                output.safe_print(output.format_status("error", "Health check failed ❌"))
                
                result = test_stream.getvalue()
                
                # Should use ASCII fallbacks
                assert "Container startup" in result
                assert "[OK]" in result or "Service ready" in result
                assert "[ERROR]" in result or "Health check failed" in result
                # Should not contain Unicode
                assert "🐳" not in result
                assert "✅" not in result
                assert "❌" not in result
    
    def test_kubernetes_pod_environment(self):
        """Test behavior in Kubernetes pods."""
        k8s_env = {
            'KUBERNETES_SERVICE_HOST': '10.0.0.1',
            'KUBERNETES_SERVICE_PORT': '443',
            'HOSTNAME': 'pod-name-12345',
        }
        
        with patch.dict(os.environ, k8s_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test Kubernetes pod output
            output.safe_print("☸️ Pod initialization")
            output.safe_print(output.format_progress(100, 100, "Startup: "))
            output.safe_print(output.format_status("success", "Ready to serve traffic"))
            
            result = test_stream.getvalue()
            
            assert "Pod initialization" in result
            assert "Startup:" in result
            assert "100.0%" in result
            assert "Ready to serve traffic" in result


class TestAutomatedTestingCompatibility:
    """Test compatibility with automated testing frameworks."""
    
    def test_pytest_environment(self):
        """Test compatibility when running under pytest."""
        # This test is running under pytest, so we can test real behavior
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test pytest-style output
        output.safe_print("🧪 Running tests")
        output.safe_print(output.format_status("success", "test_example.py::test_function PASSED"))
        output.safe_print(output.format_status("error", "test_example.py::test_failure FAILED"))
        output.safe_print(output.format_progress(85, 100, "Test progress: "))
        
        result = test_stream.getvalue()
        
        assert "Running tests" in result
        assert "PASSED" in result
        assert "FAILED" in result
        assert "Test progress:" in result
        assert "85.0%" in result
    
    def test_unittest_environment(self):
        """Test compatibility with unittest framework."""
        test_stream = StringIO()
        output = SafeOutput(auto_setup=False, output_stream=test_stream)
        
        # Test unittest-style output
        output.safe_print("Running unittest suite")
        output.safe_print(output.format_status("success", "test_method (TestClass) ... ok"))
        output.safe_print(output.format_status("error", "test_failure (TestClass) ... FAIL"))
        
        result = test_stream.getvalue()
        
        assert "Running unittest suite" in result
        assert "ok" in result
        assert "FAIL" in result
    
    def test_coverage_reporting_environment(self):
        """Test compatibility with coverage reporting tools."""
        coverage_env = {
            'COVERAGE_PROCESS_START': '.coveragerc',
        }
        
        with patch.dict(os.environ, coverage_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test coverage reporting output
            output.safe_print("📊 Coverage Report")
            output.safe_print(output.format_progress(92, 100, "Coverage: "))
            output.safe_print(output.format_status("success", "Coverage threshold met ✅"))
            
            result = test_stream.getvalue()
            
            assert "Coverage Report" in result
            assert "Coverage:" in result
            assert "92.0%" in result
            assert "Coverage threshold met" in result


class TestCrossEnvironmentConsistency:
    """Test that behavior is consistent across different CI environments."""
    
    @pytest.mark.parametrize("ci_config", [
        {'CI': 'true', 'GITHUB_ACTIONS': 'true', 'TERM': 'dumb'},
        {'JENKINS_URL': 'http://jenkins', 'TERM': 'dumb'},
        {'GITLAB_CI': 'true', 'TERM': 'xterm'},
        {'TF_BUILD': 'True', 'TERM': 'dumb'},
        {'container': 'docker'},
    ])
    def test_consistent_behavior_across_ci_environments(self, ci_config):
        """Test that Unicode utilities behave consistently across CI environments."""
        with patch.dict(os.environ, ci_config):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Standard test output that should work everywhere
            test_messages = [
                "Starting process",
                output.format_status("success", "Operation completed"),
                output.format_status("error", "Something failed"),
                output.format_progress(50, 100, "Progress: "),
                output.format_section("Results", level=1),
            ]
            
            for message in test_messages:
                output.safe_print(message)
            
            result = test_stream.getvalue()
            
            # All messages should be present
            assert "Starting process" in result
            assert "Operation completed" in result
            assert "Something failed" in result
            assert "Progress:" in result
            assert "50.0%" in result
            assert "Results" in result
            
            # Should not contain any error indicators
            assert "[OUTPUT ERROR" not in result
            assert "[CRITICAL OUTPUT ERROR" not in result


class TestPerformanceInCIEnvironments:
    """Test performance characteristics in CI environments."""
    
    def test_ci_performance_requirements(self, performance_test_data):
        """Test that performance meets CI requirements."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            import time
            
            # Test initialization performance
            start_time = time.time()
            for _ in range(10):
                SafeOutput(auto_setup=False, output_stream=StringIO())
            init_time = time.time() - start_time
            
            # Should initialize quickly in CI
            assert init_time < 1.0, f"Initialization too slow in CI: {init_time:.3f}s"
            
            # Test output performance
            start_time = time.time()
            for i in range(100):
                output.safe_print(f"CI test message {i} ✅")
            output_time = time.time() - start_time
            
            # Should output quickly in CI
            assert output_time < 2.0, f"Output too slow in CI: {output_time:.3f}s"
    
    def test_memory_usage_in_ci(self):
        """Test that memory usage is reasonable in CI environments."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            import gc
            
            # Force garbage collection
            gc.collect()
            
            # Create many instances (simulating CI test runs)
            outputs = []
            for _ in range(50):
                test_stream = StringIO()
                output = SafeOutput(auto_setup=False, output_stream=test_stream)
                outputs.append((output, test_stream))
            
            # Use them
            for output, stream in outputs:
                output.safe_print("CI memory test ✅")
                result = stream.getvalue()
                assert "CI memory test" in result
            
            # Clean up
            del outputs
            gc.collect()
            
            # Test passes if no memory errors occur
            assert True


class TestErrorHandlingInCIEnvironments:
    """Test error handling in CI/CD environments."""
    
    def test_encoding_errors_in_ci(self):
        """Test that encoding errors are handled gracefully in CI."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            # Mock encoding detection failure
            with patch.object(ConsoleHandler, 'detect_console_encoding', 
                            side_effect=Exception("CI encoding detection failed")):
                
                test_stream = StringIO()
                
                # Should not crash
                try:
                    output = SafeOutput(auto_setup=False, output_stream=test_stream)
                    output.safe_print("CI error handling test ✅")
                    
                    result = test_stream.getvalue()
                    assert "CI error handling test" in result
                    
                except Exception as e:
                    pytest.fail(f"Should handle encoding errors gracefully in CI: {e}")
    
    def test_console_setup_errors_in_ci(self):
        """Test that console setup errors don't break CI runs."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            # Mock console setup failure
            with patch.object(ConsoleHandler, 'setup_unicode_console',
                            side_effect=Exception("CI console setup failed")):
                
                test_stream = StringIO()
                
                # Should not crash
                try:
                    output = SafeOutput(auto_setup=True, output_stream=test_stream)
                    output.safe_print("CI console setup test")
                    
                    result = test_stream.getvalue()
                    assert "CI console setup test" in result
                    
                except Exception as e:
                    pytest.fail(f"Should handle console setup errors gracefully in CI: {e}")


class TestCIOutputFormatting:
    """Test output formatting for CI/CD environments."""
    
    def test_ci_friendly_status_messages(self):
        """Test that status messages are CI-friendly."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test CI-friendly status messages
            statuses = [
                ("success", "Build passed"),
                ("error", "Build failed"),
                ("warning", "Deprecated API used"),
                ("info", "Starting deployment"),
                ("processing", "Running tests"),
            ]
            
            for status, message in statuses:
                formatted = output.format_status(status, message)
                output.safe_print(formatted)
            
            result = test_stream.getvalue()
            
            # Should contain readable status indicators
            for _, message in statuses:
                assert message in result
            
            # Should not contain problematic characters that might break CI parsing
            problematic_chars = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05']
            for char in problematic_chars:
                assert char not in result
    
    def test_ci_progress_indicators(self):
        """Test that progress indicators work well in CI."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test progress indicators
            for i in range(0, 101, 20):
                progress = output.format_progress(i, 100, f"Step {i//20 + 1}: ")
                output.safe_print(progress)
            
            result = test_stream.getvalue()
            
            # Should contain progress percentages
            assert "0.0%" in result
            assert "20.0%" in result
            assert "100.0%" in result
            
            # Should contain step indicators
            assert "Step 1:" in result
            assert "Step 6:" in result
    
    def test_ci_section_headers(self):
        """Test that section headers are appropriate for CI."""
        ci_env = {'CI': 'true', 'TERM': 'dumb'}
        
        with patch.dict(os.environ, ci_env):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            
            # Test section headers
            sections = [
                ("Build Phase", 1),
                ("Test Results", 2),
                ("Deployment Status", 3),
            ]
            
            for title, level in sections:
                section = output.format_section(title, level)
                output.safe_print(section)
            
            result = test_stream.getvalue()
            
            # Should contain section titles
            for title, _ in sections:
                assert title in result
            
            # Should have appropriate formatting for CI logs
            lines = result.split('\n')
            assert len([line for line in lines if line.strip()]) >= len(sections)


if __name__ == '__main__':
    pytest.main([__file__])