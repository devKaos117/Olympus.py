"""
Kronos utilities for tracing calls, processes and threads
"""

import os, sys, threading, multiprocessing

def get_call_info() -> tuple:
    """
    Get information about the calling function

    Returns:
        Tuple containing (module_name, filename, line_number)
    """
    frame = sys._getframe(3)
    module = frame.f_globals.get("__name__", "unknown_module")
    filename = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno

    return module, filename, lineno

def get_process_info() -> tuple:
    """
    Get information about the current process and thread

    Returns:
        Tuple containing (process_name, thread_name, process_id)
    """
    current_process = multiprocessing.current_process()
    current_thread = threading.current_thread()
    process_name = current_process.name
    thread_name = current_thread.name
    process_id = os.getpid()

    return process_name, thread_name, process_id