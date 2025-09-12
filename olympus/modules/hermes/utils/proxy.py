from typing import Dict, Any

from ... import kronos


class ProxyManager:
    """
    Handles proxy rotation and health checking
    """

    def __init__(self, logger: kronos.Logger, config: Dict[str, Any]):
        """
        ...

        Args:
            logger: kronos.Logger instance to use
            config: https://github.com/devKaos117/Olympus.py/blob/main/olympus/modules/hermes/config/httpy.schema.json#proxy
        """
        pass