import json, inspect
from pathlib import Path
from jsonschema import validate, ValidationError
from typing import Dict, Mapping, Any, Optional


class ConfigManager:
    """
    Static class for managing configuration loading and validation
    Automatically detects calling class and loads appropriate config/schema files
    """

    @staticmethod
    def load(input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Automatically load and validate configuration for the calling class
        
        Args:
            input: Alterations for the configuration

        Returns:
            Dict: Validated configuration dictionary
            
        Raises:
            Exception: If configuration or schema files are not found, or validation fails
        """
        # Get the calling class information
        invoker_info = ConfigManager._get_invoker_info()
        
        # Load the schema file
        schema = ConfigManager._load_schema(invoker_info)
        
        # Load the configuration file
        config = ConfigManager._load_config(invoker_info)

        # Merge the config with the given input
        if input:
            config = ConfigManager.deep_merge(source=config, target=input, merge_free=False)
        
        # Validate configuration against schema
        ConfigManager._validate_config(config, schema, invoker_info)
        
        return config
    
    @staticmethod
    def deep_merge(source: Dict[str, Any], target: Dict[str, Any], merge_free: Optional[bool] = False) -> Dict[str, Any]:
        """
        Recursively merge the values of two dictionaries, altering the source with the target

        Args:
            source: Source dictionary to merge from
            target: Target dictionary to merge into
            merge_free: Ignore the source keys and merge both dictionaries, one into another

        Returns:
            Dict: Merged dictionary
        """
        result = source.copy()

        for key, value in target.items():
            if key in source or merge_free:
                if isinstance(target[key], dict) and isinstance(value, Mapping):
                    result[key] = ConfigManager.deep_merge(result[key], value)
                else:
                    result[key] = value
        return result

    @staticmethod
    def _get_invoker_info() -> Dict[str, str]:
        """
        Get information about the calling class by traversing the call stack
        
        Returns:
            Dict: Contains "module", "class", "name", and "full_name" of the invoker
            
        Raises:
            Exception: If calling class cannot be determined
        """
        frame = inspect.currentframe()
        try:
            # Traverse the call stack to find the calling class
            while frame is not None:
                frame = frame.f_back
                if frame is None:
                    break
                
                # Check if we're in a class method (has "self")
                if "self" in frame.f_locals:
                    cls = frame.f_locals['self'].__class__
                    module_name = cls.__module__.split(".")[-2]  # Get module name (e.g., "hermes" from "olympus.modules.hermes.http")
                    class_name = cls.__name__.lower()
                    
                    return {
                        "module": module_name,
                        "class": class_name,
                        "name": f"{module_name}.{class_name}",
                        "full_name": cls.__module__
                    }
                
                # Check if we're in a class method (has "cls")
                elif "cls" in frame.f_locals:
                    cls = frame.f_locals['cls']
                    module_name = cls.__module__.split(".")[-2]  # Get module name
                    class_name = cls.__name__.lower()
                    
                    return {
                        "module": module_name,
                        "class": class_name,
                        "name": f"{module_name}.{class_name}",
                        "full_name": cls.__module__
                    }
                
                # Check if we're in a static method by examining the code context
                elif frame.f_code.co_name != '<module>' and frame.f_code.co_name != 'load':
                    # Try to get the class from the frame's globals by examining qualname
                    frame_globals = frame.f_globals
                    
                    # Look for classes in the current module that contain this method
                    for _, obj in frame_globals.items():
                        if (inspect.isclass(obj) and 
                            hasattr(obj, frame.f_code.co_name) and
                            getattr(obj, frame.f_code.co_name).__code__ is frame.f_code):
                            
                            module_name = obj.__module__.split(".")[-2]
                            class_name = obj.__name__.lower()
                            
                            return {
                                "module": module_name,
                                "class": class_name,
                                "name": f"{module_name}.{class_name}",
                                "full_name": obj.__module__
                            }
        finally:
            del frame
        
        raise Exception("Unable to determine calling class. ConfigManager.load() must be called from within a class method")

    @staticmethod
    def _get_project_root(project_name: str) -> Path:
        """
        Get the project root directory (olympus/)
        
        Args:
            project_name: the name for the project

        Returns:
            Path: Project root directory
        """
        # Start from the current file's directory and traverse up to find olympus/
        current_path = Path(__file__).resolve()
        
        # Traverse up the directory tree to find the project root
        while current_path.name != project_name and current_path.parent != current_path:
            current_path = current_path.parent
            
        if current_path.name == project_name:
            return current_path
        
        # Fallback: assume we're already in the olympus directory structure
        return Path(__file__).resolve().parents[2]  # Go up from modules/utils/ to olympus/

    @staticmethod
    def _load_schema(invoker_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Load the schema file for the calling class
        
        Args:
            invoker_info: Information about the calling class
            
        Returns:
            Optional[Dict]: Schema data if found
            
        Raises:
            Exception: If schema file is not found or cannot be loaded
        """
        project_root = ConfigManager._get_project_root(invoker_info['full_name'])
        
        # Construct schema file path: olympus/modules/{module}/config/{class}.schema.json
        schema_path = project_root / "modules" / invoker_info['module'] / "config" / f"{invoker_info['class']}.schema.json"
        
        if not schema_path.exists():
            raise Exception(f"Configuration schema for {invoker_info['name']} not found")
        
        try:
            with open(schema_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Failed to load schema file {schema_path}: {e}")

    @staticmethod
    def _load_config(invoker_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Load the configuration file for the calling class
        
        Args:
            invoker_info: Information about the calling class
            
        Returns:
            Dict: Configuration data
            
        Raises:
            Exception: If configuration file is not found or cannot be loaded
        """
        project_root = ConfigManager._get_project_root(invoker_info['full_name'])
        
        # Construct config file path: olympus/config/{class}.json
        config_path = project_root / "config" / f"{invoker_info['name']}.json"
        
        if not config_path.exists():
            raise Exception(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise Exception(f"Failed to load configuration file {config_path}: {e}")

    @staticmethod
    def _validate_config(config: Dict[str, Any], schema: Dict[str, Any], invoker_info: Dict[str, str]):
        """
        Validate configuration against schema
        
        Args:
            config: Configuration dictionary to validate
            schema: JSON schema dictionary
            invoker_info: Information about the calling class
            
        Raises:
            Exception: If validation fails
        """
        try:
            validate(instance=config, schema=schema)
        except ValidationError as e:
            raise Exception(f"Configuration validation failed for {invoker_info['name']}: {e.message}")
        except Exception as e:
            raise Exception(f"Schema validation error for {invoker_info['name']}: {e}")