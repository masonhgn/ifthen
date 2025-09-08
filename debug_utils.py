"""
Debug utilities for the MysticGrid server.
"""
import functools
import json
import os
from datetime import datetime
from typing import Any, Callable


# global debug flag
DEBUG = True  # set to false to disable debug output
DEBUG_LOG_FILE = "debug.log"  # file to write debug output to


def write_debug_log(message: str):
    """Write a debug message to the log file."""
    if not DEBUG:
        return
    
    try:
        with open(DEBUG_LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except Exception as e:
        print(f"Error writing to debug log: {e}")


def clear_debug_log():
    """Clear the debug log file."""
    try:
        if os.path.exists(DEBUG_LOG_FILE):
            os.remove(DEBUG_LOG_FILE)
        print(f"Debug log cleared: {DEBUG_LOG_FILE}")
    except Exception as e:
        print(f"Error clearing debug log: {e}")


def debug_function(func: Callable) -> Callable:
    """
    Decorator that logs function calls, arguments, and return values when DEBUG=True.
    
    Usage:
        @debug_function
        def my_function(arg1, arg2=None):
            return arg1 + arg2
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not DEBUG:
            return func(*args, **kwargs)
        
        # get function name and module
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        # format arguments
        args_str = ", ".join([repr(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        
        # log function call
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        call_msg = f"[{timestamp}] CALL: {func_name}({all_args})"
        print(call_msg)
        write_debug_log(call_msg)
        
        try:
            # call the function
            result = func(*args, **kwargs)
            
            # log return value
            if result is None:
                return_msg = f"[{timestamp}] RETURN: {func_name}() -> None"
                print(return_msg)
                write_debug_log(return_msg)
            else:
                # try to format the result nicely
                try:
                    if hasattr(result, 'to_dict'):
                        result_str = json.dumps(result.to_dict(), indent=2)
                    elif isinstance(result, (dict, list)):
                        result_str = json.dumps(result, indent=2)
                    else:
                        result_str = repr(result)
                    
                    # truncate very long results
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "... (truncated)"
                    
                    return_msg = f"[{timestamp}] RETURN: {func_name}() -> {result_str}"
                    print(return_msg)
                    write_debug_log(return_msg)
                except Exception:
                    # fallback to repr if json serialization fails
                    result_str = repr(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "... (truncated)"
                    return_msg = f"[{timestamp}] RETURN: {func_name}() -> {result_str}"
                    print(return_msg)
                    write_debug_log(return_msg)
            
            return result
            
        except Exception as e:
            # log exceptions
            error_msg = f"[{timestamp}] ERROR: {func_name}() -> Exception: {type(e).__name__}: {str(e)}"
            print(error_msg)
            write_debug_log(error_msg)
            raise
    
    return wrapper


def debug_method(func: Callable) -> Callable:
    """
    Decorator specifically for class methods that includes self information.
    
    Usage:
        class MyClass:
            @debug_method
            def my_method(self, arg1):
                return self.value + arg1
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not DEBUG:
            return func(self, *args, **kwargs)
        
        # get method name and class
        class_name = self.__class__.__name__
        method_name = func.__name__
        full_name = f"{class_name}.{method_name}"
        
        # format arguments (skip self)
        args_str = ", ".join([repr(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={repr(v)}" for k, v in kwargs.items()])
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        
        # log method call
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        call_msg = f"[{timestamp}] CALL: {full_name}({all_args})"
        print(call_msg)
        write_debug_log(call_msg)
        
        try:
            # call the method
            result = func(self, *args, **kwargs)
            
            # log return value
            if result is None:
                return_msg = f"[{timestamp}] RETURN: {full_name}() -> None"
                print(return_msg)
                write_debug_log(return_msg)
            else:
                # try to format the result nicely
                try:
                    if hasattr(result, 'to_dict'):
                        result_str = json.dumps(result.to_dict(), indent=2)
                    elif isinstance(result, (dict, list)):
                        result_str = json.dumps(result, indent=2)
                    else:
                        result_str = repr(result)
                    
                    # truncate very long results
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "... (truncated)"
                    
                    return_msg = f"[{timestamp}] RETURN: {full_name}() -> {result_str}"
                    print(return_msg)
                    write_debug_log(return_msg)
                except Exception:
                    # fallback to repr if json serialization fails
                    result_str = repr(result)
                    if len(result_str) > 500:
                        result_str = result_str[:500] + "... (truncated)"
                    return_msg = f"[{timestamp}] RETURN: {full_name}() -> {result_str}"
                    print(return_msg)
                    write_debug_log(return_msg)
            
            return result
            
        except Exception as e:
            # log exceptions
            error_msg = f"[{timestamp}] ERROR: {full_name}() -> Exception: {type(e).__name__}: {str(e)}"
            print(error_msg)
            write_debug_log(error_msg)
            raise
    
    return wrapper


def set_debug(enabled: bool):
    """Enable or disable debug output globally."""
    global DEBUG
    DEBUG = enabled
    if enabled:
        clear_debug_log()  # clear the log when enabling debug
    print(f"Debug mode {'enabled' if enabled else 'disabled'}")


def is_debug_enabled() -> bool:
    """Check if debug mode is currently enabled."""
    return DEBUG


def get_debug_log_path() -> str:
    """Get the path to the debug log file."""
    return DEBUG_LOG_FILE
