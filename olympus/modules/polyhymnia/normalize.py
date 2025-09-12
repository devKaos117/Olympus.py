import re
from typing import List, Optional


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
        
        return re.sub(r"[^a-zA-Z0-9]", "", txt)
    
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
        
        return re.sub(r"[^a-zA-Z0-9_\-\.~/]", "", txt)
    
    @staticmethod
    def stop_words(txt: str, words: Optional[List[str]] = None) -> str:
        """
        
        Args:
            txt: The string to be normalized
        
        Returns:
            The normalized string
        """
        if not txt:
            return ""
        
        default = ["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "will", "with", "or", "but", "not", "no", "yes", "i", "you", "we", "they", "she", "him", "her", "his", "this", "these", "those", "them", "there", "their", "what", "when","where", "who", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "only", "own","same", "so", "than", "too", "very", "can", "could", "should", "would", "have", "had", "been", "being", "do", "does", "did","am", "is", "are", "was", "were"]

        stop_words = words if (words is not None) else default

        words = re.findall(r"\b\w+\b", txt)
    
        # Filter out stop words
        filtered_words = [word for word in words if word not in stop_words]
        
        # Join the remaining words back into a string
        return " ".join(filtered_words)