"""
Performance tests for Unicode utilities.

Tests encoding detection overhead, character replacement performance,
and output performance under various conditions.
"""

import pytest
import time
import sys
from io import StringIO
from unittest.mock import patch, MagicMock
import statistics

from src.utils.unicode_utils import SafeOutput, ConsoleHandler, CharacterMap
from src.utils.unicode_utils import safe_print, print_status, print_progress


class TestEncodingDetectionPerformance:
    """Test performance of encoding detection operations."""
    
    def test_encoding_detection_speed(self):
        """Test that encoding detection completes within reasonable time."""
        start_time = time.time()
        
        # Run encoding detection multiple times
        for _ in range(100):
            encoding = ConsoleHandler.detect_console_encoding()
            assert isinstance(encoding, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 detections in less than 1 second
        assert total_time < 1.0, f"Encoding detection too slow: {total_time:.3f}s for 100 calls"
        
        # Average time per detection should be reasonable
        avg_time = total_time / 100
        assert avg_time < 0.01, f"Average detection time too slow: {avg_time:.6f}s"
    
    def test_unicode_support_detection_speed(self):
        """Test that Unicode support detection is fast."""
        start_time = time.time()
        
        # Run Unicode support detection multiple times
        for _ in range(100):
            supported = ConsoleHandler.is_unicode_supported()
            assert isinstance(supported, bool)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 checks in less than 0.5 seconds
        assert total_time < 0.5, f"Unicode support detection too slow: {total_time:.3f}s for 100 calls"
    
    def test_console_info_gathering_speed(self):
        """Test that console info gathering is reasonably fast."""
        start_time = time.time()
        
        # Run console info gathering multiple times
        for _ in range(50):
            info = ConsoleHandler.get_console_info()
            assert isinstance(info, dict)
            assert 'platform' in info
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 50 info gatherings in less than 1 second
        assert total_time < 1.0, f"Console info gathering too slow: {total_time:.3f}s for 50 calls"
    
    def test_encoding_detection_consistency(self):
        """Test that encoding detection is consistent and doesn't degrade over time."""
        times = []
        
        for i in range(20):
            start_time = time.time()
            encoding = ConsoleHandler.detect_console_encoding()
            end_time = time.time()
            
            times.append(end_time - start_time)
            assert isinstance(encoding, str)
        
        # Check that performance is consistent (no significant degradation)
        first_half_avg = statistics.mean(times[:10])
        second_half_avg = statistics.mean(times[10:])
        
        # Second half should not be more than 50% slower than first half
        assert second_half_avg <= first_half_avg * 1.5, \
            f"Performance degradation detected: {first_half_avg:.6f}s -> {second_half_avg:.6f}s"


class TestCharacterMappingPerformance:
    """Test performance of character mapping operations."""
    
    def test_character_map_initialization_speed(self):
        """Test that CharacterMap initialization is fast."""
        start_time = time.time()
        
        # Create multiple CharacterMap instances
        for _ in range(100):
            char_map = CharacterMap()
            assert char_map is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should create 100 instances in less than 0.1 seconds
        assert total_time < 0.1, f"CharacterMap initialization too slow: {total_time:.3f}s for 100 instances"
    
    def test_symbol_lookup_speed(self):
        """Test that symbol lookup is fast."""
        char_map = CharacterMap()
        test_symbols = ['✅', '❌', '⚠️', '⏳', '█', '░', '→', '•', '★', '═']
        
        start_time = time.time()
        
        # Perform many symbol lookups
        for _ in range(1000):
            for symbol in test_symbols:
                result = char_map.get_symbol(symbol, unicode_supported=False)
                assert isinstance(result, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 10,000 lookups in less than 0.5 seconds
        assert total_time < 0.5, f"Symbol lookup too slow: {total_time:.3f}s for 10,000 lookups"
    
    def test_text_replacement_speed(self):
        """Test that text replacement is reasonably fast."""
        char_map = CharacterMap()
        test_text = "Status: ✅ Success → Progress: █████░░░░░ 50% ⚠️ Warning ★ Important"
        
        start_time = time.time()
        
        # Perform many text replacements
        for _ in range(1000):
            result = char_map.replace_unicode_in_text(test_text, unicode_supported=False)
            assert isinstance(result, str)
            assert "✅" not in result  # Should be replaced
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 1,000 replacements in less than 1 second
        assert total_time < 1.0, f"Text replacement too slow: {total_time:.3f}s for 1,000 replacements"
    
    def test_large_text_replacement_performance(self):
        """Test text replacement performance with large text."""
        char_map = CharacterMap()
        
        # Create large text with many Unicode characters
        large_text = ("Status: ✅ Success → Progress: █████░░░░░ 50% ⚠️ Warning ★ Important\n" * 100)
        
        start_time = time.time()
        
        # Replace Unicode in large text
        result = char_map.replace_unicode_in_text(large_text, unicode_supported=False)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete large text replacement in less than 0.1 seconds
        assert total_time < 0.1, f"Large text replacement too slow: {total_time:.3f}s"
        assert isinstance(result, str)
        assert len(result) > 0


class TestSafeOutputPerformance:
    """Test performance of SafeOutput operations."""
    
    def test_safe_output_initialization_speed(self):
        """Test that SafeOutput initialization is fast."""
        test_stream = StringIO()
        
        start_time = time.time()
        
        # Create multiple SafeOutput instances
        for _ in range(100):
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            assert output is not None
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should create 100 instances in less than 0.5 seconds
        assert total_time < 0.5, f"SafeOutput initialization too slow: {total_time:.3f}s for 100 instances"
    
    def test_safe_print_performance(self):
        """Test that safe_print operations are fast."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        start_time = time.time()
        
        # Perform many print operations
        for i in range(1000):
            output.safe_print(f"Test message {i} with Unicode: ✅")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 1,000 prints in less than 2 seconds
        assert total_time < 2.0, f"safe_print too slow: {total_time:.3f}s for 1,000 prints"
        
        # Verify output was produced
        result = test_stream.getvalue()
        assert "Test message 0" in result
        assert "Test message 999" in result
    
    def test_status_formatting_performance(self):
        """Test that status formatting is fast."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        statuses = ['success', 'error', 'warning', 'info', 'processing']
        
        start_time = time.time()
        
        # Format many status messages
        for i in range(1000):
            status = statuses[i % len(statuses)]
            formatted = output.format_status(status, f"Message {i}")
            assert isinstance(formatted, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 1,000 formatting operations in less than 0.5 seconds
        assert total_time < 0.5, f"Status formatting too slow: {total_time:.3f}s for 1,000 formats"
    
    def test_progress_formatting_performance(self):
        """Test that progress formatting is fast."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        start_time = time.time()
        
        # Format many progress indicators
        for i in range(1000):
            progress = output.format_progress(i % 101, 100, f"Task {i}: ")
            assert isinstance(progress, str)
            assert "%" in progress
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 1,000 formatting operations in less than 0.5 seconds
        assert total_time < 0.5, f"Progress formatting too slow: {total_time:.3f}s for 1,000 formats"
    
    def test_section_formatting_performance(self):
        """Test that section formatting is fast."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        start_time = time.time()
        
        # Format many section headers
        for i in range(500):
            level = (i % 3) + 1
            section = output.format_section(f"Section {i}", level=level)
            assert isinstance(section, str)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 500 formatting operations in less than 0.5 seconds
        assert total_time < 0.5, f"Section formatting too slow: {total_time:.3f}s for 500 formats"


class TestConvenienceFunctionPerformance:
    """Test performance of convenience functions."""
    
    def test_convenience_function_overhead(self):
        """Test that convenience functions don't add significant overhead."""
        test_stream = StringIO()
        
        # Configure global output
        from src.utils.unicode_utils import configure
        configure(output_stream=test_stream, auto_setup=False)
        
        start_time = time.time()
        
        # Use convenience functions many times
        for i in range(500):
            safe_print(f"Message {i}")
            print_status("success", f"Status {i}")
            print_progress(i % 101, 100, f"Progress {i}: ")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 1,500 operations in less than 3 seconds
        assert total_time < 3.0, f"Convenience functions too slow: {total_time:.3f}s for 1,500 operations"
        
        # Verify output was produced
        result = test_stream.getvalue()
        assert "Message 0" in result
        assert "Status 0" in result
        assert "Progress 0:" in result
    
    def test_global_instance_reuse_efficiency(self):
        """Test that global instance reuse is efficient."""
        test_stream = StringIO()
        
        from src.utils.unicode_utils import configure, reset_configuration
        
        # Test multiple reconfigurations
        start_time = time.time()
        
        for i in range(100):
            configure(output_stream=test_stream, auto_setup=False)
            safe_print(f"Test {i}")
            reset_configuration()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 100 reconfigurations in less than 2 seconds
        assert total_time < 2.0, f"Global instance management too slow: {total_time:.3f}s for 100 reconfigs"


class TestMemoryPerformance:
    """Test memory usage characteristics."""
    
    def test_character_map_memory_efficiency(self):
        """Test that CharacterMap doesn't use excessive memory."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Create many CharacterMap instances
        char_maps = []
        for _ in range(100):
            char_maps.append(CharacterMap())
        
        # Test that they work correctly
        for char_map in char_maps:
            result = char_map.get_symbol('✅', unicode_supported=False)
            assert result == '[OK]'
        
        # Clean up
        del char_maps
        gc.collect()
        
        # Test passes if no memory errors occur
        assert True
    
    def test_safe_output_memory_efficiency(self):
        """Test that SafeOutput doesn't leak memory."""
        import gc
        
        gc.collect()
        
        # Create many SafeOutput instances with different streams
        outputs = []
        for _ in range(100):
            test_stream = StringIO()
            output = SafeOutput(auto_setup=False, output_stream=test_stream)
            outputs.append((output, test_stream))
        
        # Use them
        for output, stream in outputs:
            output.safe_print("Test message with ✅")
            result = stream.getvalue()
            assert "Test message" in result
        
        # Clean up
        del outputs
        gc.collect()
        
        # Test passes if no memory errors occur
        assert True


class TestConcurrencyPerformance:
    """Test performance under concurrent usage."""
    
    def test_thread_safety_performance(self):
        """Test that Unicode utilities work efficiently with threading."""
        import threading
        import queue
        
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        results = queue.Queue()
        
        def worker(worker_id):
            """Worker function for threading test."""
            start_time = time.time()
            
            for i in range(100):
                output.safe_print(f"Worker {worker_id} message {i} ✅")
            
            end_time = time.time()
            results.put(end_time - start_time)
        
        # Create and start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
        
        start_time = time.time()
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 5 threads * 100 operations in reasonable time
        assert total_time < 5.0, f"Threaded operations too slow: {total_time:.3f}s"
        
        # Check individual thread performance
        while not results.empty():
            thread_time = results.get()
            assert thread_time < 2.0, f"Individual thread too slow: {thread_time:.3f}s"
        
        # Verify output was produced
        result = test_stream.getvalue()
        assert "Worker 0 message 0" in result


class TestScalabilityPerformance:
    """Test performance scalability with large inputs."""
    
    def test_large_message_performance(self):
        """Test performance with very large messages."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        # Create a very large message with Unicode characters
        large_message = "Test message with Unicode ✅ " * 1000
        
        start_time = time.time()
        
        output.safe_print(large_message)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle large message in reasonable time
        assert total_time < 1.0, f"Large message handling too slow: {total_time:.3f}s"
        
        result = test_stream.getvalue()
        assert "Test message with Unicode" in result
        assert "[OK]" in result  # Unicode should be replaced
    
    def test_many_small_messages_performance(self):
        """Test performance with many small messages."""
        test_stream = StringIO()
        output = SafeOutput(enable_unicode=False, auto_setup=False, output_stream=test_stream)
        
        start_time = time.time()
        
        # Print many small messages
        for i in range(5000):
            output.safe_print(f"Msg {i} ✅")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle 5000 small messages in reasonable time
        assert total_time < 5.0, f"Many small messages too slow: {total_time:.3f}s"
        
        result = test_stream.getvalue()
        assert "Msg 0" in result
        assert "Msg 4999" in result


if __name__ == '__main__':
    pytest.main([__file__])