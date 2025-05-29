import json, inspect
from pathlib import Path
from typing import Dict, Any, Optional, Mapping, Type
from jsonschema import validate, ValidationError


class ConfigManager:
    """
    Static class for managing configuration loading, validation, and merging
    Supports class-specific configurations and schemas within package structures
    """

    CONFIG_FILENAME = "configuration.json"
    SCHEMA_FILENAME = "configuration.schema.json"

    @staticmethod
    def load(input: Optional[Dict[str, Any]] = None, default: Optional[Dict[str, Any]] = None, invoker: Optional[Type] = None, sought: Optional[str] = None) -> Dict[str, Any]:
        """
        Load and merge configuration with validation

        Args:
            input: User-provided configuration dictionary with tweaks/changes
            default: Fallback default configuration dictionary
            invoker: The class requesting configuration (for class-specific configs)
            sought: Specific configuration name to load (overrides class-based naming)

        Returns:
            Dict: Merged and validated configuration dictionary

        Raises:
            Exception: If no default config is found or validation fails
        """
        if input is None:
            input = {}

        # Determine configuration context
        config_key = ConfigManager._get_config_key(invoker, sought)

        # Load configuration and schema files
        file_config, schema = ConfigManager._load_config_files(config_key)

        # Use file-based default if available
        if file_config:
            default = file_config

        # Throw error if no default config is found
        if default is None:
            raise Exception(f"No default configuration found for '{config_key}'. Provide default parameter or ensure configuration files exists")

        # Validate input against schema if schema exists
        if schema:
            ConfigManager._validate_schema(config=input, schema=schema, config_key=config_key)

        # Merge configurations and return
        return ConfigManager.deep_merge(default.copy(), input)

    @staticmethod
    def deep_merge(target: Dict[str, Any], source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively merge two dictionaries

        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from

        Returns:
            Dict: Merged dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, Mapping):
                target[key] = ConfigManager.deep_merge(target[key], value)
            else:
                target[key] = value
        return target

    @staticmethod
    def _get_config_key(invoker: Optional[Type], sought: Optional[str]) -> str:
        """
        Determine the configuration key based on calling class or provided name

        Args:
            invoker: The class requesting configuration
            sought: Explicit configuration name

        Returns:
            str: Configuration key to use
        """
        if sought:
            return sought

        if invoker:
            return invoker.__name__.lower()

        # Fallback: try to determine calling class from stack
        frame = inspect.currentframe()
        try:
            # Go up the stack to find the calling class
            for _ in range(10):  # Limit stack traversal
                frame = frame.f_back
                if frame is None:
                    break

                # Check if we're in a class method
                if "self" in frame.f_locals:
                    return frame.f_locals['self'].__class__.__name__.lower()
                elif "cls" in frame.f_locals:
                    return frame.f_locals['cls'].__name__.lower()
        finally:
            del frame

        return "default"

    @staticmethod
    def _get_config_directory() -> Path:
        """
        Get the directory containing configuration files

        Returns:
            Path: Directory path for configuration files
        """
        # Start from the directory containing this file
        current_file_dir = Path(__file__).parent

        # Look for config files in current directory first
        if (current_file_dir / ConfigManager.CONFIG_FILENAME).exists():
            return current_file_dir

        # Then check parent_dir/configuration directory
        config_dir = current_file_dir.parent / "config"
        if config_dir.exists() and config_dir.is_dir():
            return config_dir

        # Return current directory as default
        return current_file_dir

    @staticmethod
    def _load_config_files(config_key: str) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Load configuration and schema files

        Args:
            config_key: Configuration key for class-specific schemas

        Returns:
            tuple: (configuration_data, schema_data)
        """
        config_dir = ConfigManager._get_config_directory()

        # Load configuration file using config_key naming
        config_file_path = config_dir / f"{config_key}.json"
        file_config = None
        if config_file_path.exists():
            try:
                file_config = ConfigManager._load_file(config_file_path)
            except (json.JSONDecodeError, IOError) as e:
                raise Exception(f"Failed to load configuration file '{config_key}.json': {e}")

        # Load schema file using config_key naming
        schema = ConfigManager._load_schema_files(config_dir, config_key)

        return file_config, schema

    @staticmethod
    def _load_schema_files(config_dir: Path, config_key: str) -> Optional[Dict[str, Any]]:
        """
        Load schema files with config_key naming convention

        Args:
            config_dir: Directory containing schema files
            config_key: Configuration key for specific schemas

        Returns:
            Optional[Dict]: Schema data if found
        """
        # Load schema file using config_key naming (e.g., myclass.schema.json)
        schema_path = config_dir / f"{config_key}.schema.json"
        if schema_path.exists():
            try:
                return ConfigManager._load_file(schema_path)
            except (json.JSONDecodeError, IOError) as e:
                raise Exception(f"Failed to load schema file '{config_key}.schema.json': {e}")

        return None

    @staticmethod
    def _load_file(file_path: Path) -> Dict[str, Any]:
        """
        Load configuration file from disk

        Args:
            file_path: Path to the configuration file

        Returns:
            Dict: Loaded configuration data

        Raises:
            IOError: If file cannot be read
            json.JSONDecodeError: If JSON is invalid
        """
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def _validate_schema(config: Dict[str, Any], schema: Dict[str, Any], config_key: str):
        """
        Validate configuration against a JSON schema

        Args:
            config: Configuration dictionary to validate
            schema: JSON schema dictionary
            config_key: Configuration key for error messages

        Raises:
            Exception: If validation fails
        """
        try:
            validate(instance=config, schema=schema)
        except ValidationError as e:
            raise Exception(f"Configuration validation failed for '{config_key}': {e.message}")
        except Exception as e:
            raise Exception(f"Schema validation error for '{config_key}': {e}")