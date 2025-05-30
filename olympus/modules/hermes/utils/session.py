from requests import session
from typing import Dict, Any

from ... import kronos


class SessionManager:
    """
    Manages the session pool and cookies persistence
    """
    
    def __init__(self, logger: kronos.Logger, config: Dict[str, Any]):
        """
        ...

        Args:
            logger: kronos.Logger instance to use
            config: https://github.com/devKaos117/Olympus.py/blob/main/olympus/modules/hermes/config/httpy.schema.json#session
        """
        pass