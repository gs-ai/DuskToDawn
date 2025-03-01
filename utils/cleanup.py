import os
import sys
import signal
import atexit
import threading
import multiprocessing
import gc
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger('cleanup')

class ResourceManager:
    """
    A utility class to manage resources and ensure proper cleanup on shutdown.
    Helps prevent resource leaks, particularly with multiprocessing semaphores.
    """
    def __init__(self):
        self.resources = []
        self.executors = []
        self.cleanup_handlers = []
        self.is_shutting_down = False
        self._lock = threading.Lock()
        self._install_handlers()
        
    def _install_handlers(self):
        """Install signal handlers and atexit hooks."""
        # Register signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, self._signal_handler)
            
        # Register atexit handler
        atexit.register(self._atexit_handler)
        
    def register_resource(self, resource, cleanup_func=None):
        """Register a resource that needs cleanup on shutdown."""
        with self._lock:
            self.resources.append((resource, cleanup_func))
            
    def register_executor(self, executor):
        """Register a ThreadPoolExecutor for proper shutdown."""
        with self._lock:
            self.executors.append(executor)
            
    def register_cleanup_handler(self, handler):
        """Register a function to be called during cleanup."""
        with self._lock:
            self.cleanup_handlers.append(handler)
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        sig_name = signal.Signals(signum).name
        print(f"\n[INFO] Received {sig_name}, initiating graceful shutdown...")
        self._cleanup()
        # Allow normal signal handling to continue
        sys.exit(0)
        
    def _atexit_handler(self):
        """Handle normal program exit."""
        if not self.is_shutting_down:
            self._cleanup()
    
    def _cleanup(self):
        """Perform cleanup operations."""
        with self._lock:
            if self.is_shutting_down:
                return
            self.is_shutting_down = True
            
            # First run custom cleanup handlers
            for handler in self.cleanup_handlers:
                try:
                    handler()
                except Exception as e:
                    print(f"Error in cleanup handler: {e}")
            
            # Shutdown executors
            for executor in self.executors:
                try:
                    print("Shutting down executor...")
                    executor.shutdown(wait=False, cancel_futures=True)
                except Exception as e:
                    print(f"Error shutting down executor: {e}")
            
            # Clean up registered resources
            for resource, cleanup_func in self.resources:
                try:
                    if cleanup_func is not None:
                        cleanup_func(resource)
                except Exception as e:
                    print(f"Error cleaning up resource: {e}")
            
            # Explicitly run garbage collection to help clean up resources
            gc.collect()
            
            # Special handling for multiprocessing cleanup
            self._cleanup_multiprocessing()
    
    def _cleanup_multiprocessing(self):
        """Special handling for multiprocessing resources."""
        try:
            # Force the resource tracker to shut down cleanly
            if hasattr(multiprocessing, 'resource_tracker'):
                resource_tracker = multiprocessing.resource_tracker._resource_tracker
                if resource_tracker is not None:
                    resource_tracker._stop = True
                    if hasattr(resource_tracker, '_check_process'):
                        resource_tracker._check_process.join(timeout=1.0)
        except Exception as e:
            print(f"Error cleaning up multiprocessing: {e}")

# Create a singleton instance
resource_manager = ResourceManager()

def register_for_cleanup(resource, cleanup_func=None):
    """Register a resource for cleanup."""
    resource_manager.register_resource(resource, cleanup_func)

def register_executor(executor):
    """Register a ThreadPoolExecutor for cleanup."""
    resource_manager.register_executor(executor)

def register_cleanup_handler(handler):
    """Register a cleanup handler function."""
    resource_manager.register_cleanup_handler(handler)

def cleanup_files(paths):
    """Clean up temporary files."""
    def _cleanup():
        for path in paths:
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        # Could use shutil.rmtree for directories
                        pass
                    else:
                        os.unlink(path)
            except Exception as e:
                print(f"Error cleaning up file {path}: {e}")
    
    register_cleanup_handler(_cleanup)
