import re, difflib, string
from enum import Enum
from typing import List, Tuple, Optional, Dict, Set, Union, Callable
from collections import Counter


class Normalize:
    """
    """

    @staticmethod
    def space(txt: str) -> str:
        """
        Removes blank spaces and common separators

        Args:
            txt: The string to be normalized
        
        Returns:
            The normalized string
        """
        if not txt:
            return ""
        
        return re.sub(r"[\s\-_.~/]+", "_", txt.strip())
    
    @staticmethod
    def alphanumeric(txt: str) -> str:
        """
        
        Args:
            txt: The string to be normalized
        
        Returns:
            The normalized string
        """
        if not txt:
            return ""
        
        return re.sub(r'[^a-zA-Z0-9]', '', txt)
    
    @staticmethod
    def password(txt: str) -> str:
        """
        
        Args:
            txt: The string to be normalized
        
        Returns:
            The normalized string
        """
        if not txt:
            return ""
        
        return txt
    
    @staticmethod
    def product_name(txt: str) -> str:
        """
        
        Args:
            txt: The string to be normalized
        
        Returns:
            The normalized string
        """
        if not txt:
            return ""
        
        txt = Normalize.space(txt.lower())
        
        return re.sub(r'[^a-zA-Z0-9_\-\.~/]', '', txt)
    