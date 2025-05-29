import json, logging, os, sys, traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union

from .utils.configuration import ConfigManager
from .utils.http import format_http_response
from .utils.tracing import get_call_info, get_process_info


class Logger:
    """
    A comprehensive custom logger for Python applications that supports
    multiple output formats, destinations and special handling for HTTP requests
    """

    # Log level constants
    NONE = 99
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    # Map level numbers to names
    _LEVEL_NAMES = {
        NONE: "NONE",
        CRITICAL: "CRITICAL",
        ERROR: "ERROR",
        WARNING: "WARNING",
        INFO: "INFO",
        DEBUG: "DEBUG",
        NOTSET: "NOTSET"
    }

    _LEVEL_VALUES = {
        "NONE": 99,
        "CRITICAL": 50,
        "ERROR": 40,
        "WARNING": 30,
        "INFO": 20,
        "DEBUG": 10,
        "NOTSET": 0,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = {}):
        """
        Initialize the logger

        Args:
            config: Configuration dictionary
        """
        self._config = ConfigManager.load(input=config)

        self._config['console_level'] = self._convert_level(self._config['console_level'])
        self._config['file_level'] = self._convert_level(self._config['file_level'])

        # Configure console handler
        self._console_handler = logging.StreamHandler(sys.stdout)

        # Configure file handler if log_directory is provided
        self._file_handler = None
        if self._config['log_directory'] and self._config['file_level']:
            if not os.path.exists(self._config['log_directory']):
                os.makedirs(self._config['log_directory'])
            timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            log_file_path = os.path.join(self._config['log_directory'], f"{timestamp}.log")
            self._file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        
        self.debug("Logger config", self._config)
        self.info("Logger initialized")

    def _convert_level(self, level: Union[int, str]) -> int:
        """
        Convert log level to integer if it's a string

        Args:
            level: Log level as integer or string

        Returns:
            Integer log level

        Raises:
            ValueError: If string level is invalid
        """
        if isinstance(level, str):
            level_upper = level.upper()
            if level_upper in self._LEVEL_VALUES:
                return self._LEVEL_VALUES[level_upper]
            raise ValueError(f"Invalid log level string: {level}. Valid levels are: {', '.join(self._LEVEL_VALUES.keys())}")
        return level

    def _format_log_message(self, level: int, msg: str, module: str, filename: str, lineno: int, process_name: str, thread_name: str, process_id: int) -> str:
        """
        Format the log message according to the standard format

        Args:
            level: Log level
            msg: Message to log
            module: Module name
            filename: Filename
            lineno: Line number
            process_name: Process name
            thread_name: Thread name
            process_id: Process ID

        Returns:
            Formatted log message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        level_name = self._LEVEL_NAMES.get(level, "UNKNOWN")

        return f"[{timestamp}] {level_name} - {process_name} / {thread_name} ({process_id}) - {module}:{filename}:{lineno} - {msg}"

    def _log(self, level: int, msg: Union[str, Exception], json_payload: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a message at the specified level

        Args:
            level: Log level
            msg: Message to log (can be an exception object)
            json_payload: Optional JSON payload for DEBUG level
        """
        # Check if we should log to console
        log_to_console = level >= self._config['console_level'] if self._config['console_level'] else False
        # Check if we should log to file
        log_to_file = self._file_handler is not None

        if not (log_to_console or log_to_file):
            return

        if isinstance(msg, Exception):
            msg = f"{type(msg).__name__}: {str(msg)}"

        # Get call information
        module, filename, lineno = get_call_info()

        # Get process information
        process_name, thread_name, process_id = get_process_info()

        # Format the log message
        formatted_msg = self._format_log_message(level, msg, module, filename, lineno, process_name, thread_name, process_id)

        # Write to console
        if log_to_console:
            print(formatted_msg)
            if self._config['console_level'] <= self.DEBUG and json_payload:
                print(json.dumps(json_payload, indent=2))

        # Write to file if enabled
        if log_to_file:
            self._file_handler.stream.write(formatted_msg + "\n")
            if self._config['file_level'] <= self.DEBUG and json_payload:
                json_str = json.dumps(json_payload, indent=2)
                self._file_handler.stream.write(json_str + "\n")
            self._file_handler.stream.flush()

    def critical(self, msg: Union[str, Exception]) -> None:
        """Log a CRITICAL level message."""
        self._log(self.CRITICAL, msg)

    def error(self, msg: Union[str, Exception]) -> None:
        """Log an ERROR level message."""
        self._log(self.ERROR, msg)

    def warning(self, msg: Union[str, Exception]) -> None:
        """Log a WARNING level message."""
        self._log(self.WARNING, msg)

    def info(self, msg: Union[str, Exception]) -> None:
        """Log an INFO level message."""
        self._log(self.INFO, msg)

    def debug(self, msg: Union[str, Exception], json_payload: Optional[Dict[str, Any]] = None) -> None:
        """Log a DEBUG level message."""
        self._log(self.DEBUG, msg, json_payload)

    def exception(self, msg: Union[str, Exception] = "Exception occurred") -> None:
        """
        Log an exception with traceback at ERROR level

        Args:
            msg: Message to log along with the exception
        """
        if isinstance(msg, Exception):
            exc_info = (type(msg), msg, None)
        else:
            exc_info = sys.exc_info()

        if exc_info[0] is not None:
            exception_msg = f"{msg}: {exc_info[0].__name__}: {str(exc_info[1])}"
            tb_str = "".join(traceback.format_exception(*exc_info))
            full_msg = f"{exception_msg}\n{tb_str}"
            self._log(self.ERROR, full_msg)
        else:
            self._log(self.ERROR, msg)

    def log_http_response(self, response, message: str = "HTTP Response") -> None:
        """
        Log an HTTP response with all details at DEBUG level following https://github.com/devKaos117/Kronos.py/blob/main/documentation/schema/http_log.schema.json

        Args:
            response: HTTP response object (from requests library)
            message: Optional message to include with the log
        """
        if (self._config['console_level'] and self._config['console_level'] <= self.DEBUG) or (self._config['file_level'] and self._config['file_level'] <= self.DEBUG):
            http_details = format_http_response(response)
            self.debug(message, http_details)