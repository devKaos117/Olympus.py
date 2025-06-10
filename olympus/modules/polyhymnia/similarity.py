import re, difflib
from typing import Dict, List, Tuple, Set, Union, Callable, Any
from .normalize import Normalize

from ..utils.configuration import ConfigManager


class Similarity:
    """
    """

    _config = None

    @staticmethod
    def configuration() -> Dict[str, Any]:
        """
        Returns the configuration
        """
        if Similarity._config is None:
            Similarity._config = ConfigManager.load()

        return Similarity._config

    @staticmethod
    def levenshtein(s1: str, s2: str, normalizer: Callable[[str], str] = lambda s: s) -> int:
        """
        Calculate weighted Levenshtein distance

        Args:
            s1:
            s2:
            normalizer: 
        
        Returns:
            similarity
        """
        if not s1:
            raise TypeError("Similarity.levenshtein() missing 1 required positional argument: 's1'")
        if not s2:
            raise TypeError("Similarity.levenshtein() missing 1 required positional argument: 's2'")
        
        if len(s1) < len(s2):
            return Similarity.levenshtein(s2, s1)
        
        # Load configuration
        config = Similarity.configuration()['levenshtein']

        # Normalize input
        s1 = normalizer(s1)
        s2 = normalizer(s2)

        if len(s2) == 0:
            return len(s1) * config['deletion']
        
        previous_row = list(range(0, (len(s2) + 1) * config['insertion'], config['insertion']))
        
        for i, c1 in enumerate(s1):
            current_row = [(i + 1) * config['deletion']]
            
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + config['insertion']
                deletions = current_row[j] + config['deletion']
                substitutions = previous_row[j] + (config['substitution'] if c1 != c2 else 0)

                current_row.append(min(insertions, deletions, substitutions))
            
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def jaro_winkler(s1: str, s2: str, normalizer: Callable[[str], str] = lambda s: s) -> float:
        """
        Calculate Jaro-Winkler similarity

        Args:
            s1:
            s2:
            normalizer: 
        
        Returns:
            similarity
        """
        if not s1:
            raise TypeError("Similarity.jaro_winkler() missing 1 required positional argument: 's1'")
        if not s2:
            raise TypeError("Similarity.jaro_winkler() missing 1 required positional argument: 's2'")
        
        if s1 == s2:
            return 1.0
        
        # Load configuration
        config = Similarity.configuration()['jaro_winkler']

        # Normalize input
        s1 = normalizer(s1)
        s2 = normalizer(s2)
        
        match_window = max(len(s1), len(s2)) // 2 - 1
        match_window = max(0, match_window)
        
        s1_matches = [False] * len(s1)
        s2_matches = [False] * len(s2)
        
        matches = 0
        transpositions = 0
        
        # Find matches
        for i in range(len(s1)):
            start = max(0, i - match_window)
            end = min(i + match_window + 1, len(s2))
            
            for j in range(start, end):
                if s2_matches[j] or s1[i] != s2[j]:
                    continue
                s1_matches[i] = s2_matches[j] = True
                matches += 1
                break
        
        if matches == 0:
            return 0.0
        
        # Count transpositions
        k = 0
        for i in range(len(s1)):
            if not s1_matches[i]:
                continue
            while not s2_matches[k]:
                k += 1
            if s1[i] != s2[k]:
                transpositions += 1
            k += 1
        
        jaro = (matches / len(s1) + matches / len(s2) + (matches - transpositions / 2) / matches) / 3
        
        # Winkler prefix boost
        prefix = 0
        for i in range(min(len(s1), len(s2), 4)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        
        return jaro + (config['prefix_scale'] * prefix * (1 - jaro))
    
    @staticmethod
    def ngram(s1: str, s2: str, normalizer: Callable[[str], str] = lambda s: s) -> float:
        """
        Calculate n-gram Jaccard similarity

        Args:
            s1:
            s2:
            normalizer: 
        
        Returns:
            similarity
        """
        if not s1:
            raise TypeError("Similarity.ngram() missing 1 required positional argument: 's1'")
        if not s2:
            raise TypeError("Similarity.ngram() missing 1 required positional argument: 's2'")
        
        # Load configuration
        config = Similarity.configuration()['ngram']

        # Normalize input
        s1 = normalizer(s1)
        s2 = normalizer(s2)
        
        def get_ngrams(s: str, n: int) -> List[str]:
            if len(s) < n:
                return [s]
            return [s[i:i+n] for i in range(len(s) - n + 1)]
        
        ngrams1 = set(get_ngrams(s1, config['n']))
        ngrams2 = set(get_ngrams(s2, config['n']))
        
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def jaccard(s1: str, s2: str, normalizer: Callable[[str], str] = lambda s: s) -> float:
        """
        Calculate word-level overlap Jaccard similarity

        Args:
            s1:
            s2:
            normalizer: 
        
        Returns:
            similarity
        """
        if not s1:
            raise TypeError("Similarity.jaccard() missing 1 required positional argument: 's1'")
        if not s2:
            raise TypeError("Similarity.jaccard() missing 1 required positional argument: 's2'")
        
        # Load configuration
        config = Similarity.configuration()['jaccard']

        # Normalize input
        s1 = normalizer(s1)
        s2 = normalizer(s2)

        def tokenize(text: str) -> Set[str]:
            return set(re.findall(r"\b\w+\b", Normalize.stop_words(txt=text, words=config['stop_words'])))
        
        words1 = tokenize(s1)
        words2 = tokenize(s2)
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def abbreviation(short: str, full: str, normalizer: Callable[[str], str] = lambda s: s) -> float:
        """
        Calculate abbreviation similarity with multiple strategies
        
        Args:
            short: Normalized
            full: Normalized
            normalizer:

        Returns:

        """
        if not short:
            raise TypeError("Similarity.abbreviation() missing 1 required positional argument: 'short'")
        if not full:
            raise TypeError("Similarity.abbreviation() missing 1 required positional argument: 'full'")
        
        if short == full:
            return 1.0
        
        # Direct containment
        if short in full:
            return 0.8
        
        # Load configuration
        config = Similarity.configuration()['abbreviation']

        # Normalize input
        short = normalizer(short)
        full = normalizer(full)
        
        # Acronym matching (first letters of words)
        full_words = re.findall(r"\b\w+\b", full)
        if full_words:
            acronym = "".join(word[0] for word in full_words if word)
            if short == acronym:
                return 0.9
        
        # Character-by-character matching (subsequence)
        if not config['strict_mode']:
            short_idx = 0
            for char in full:
                if short_idx < len(short) and char == short[short_idx]:
                    short_idx += 1
            
            coverage = short_idx / len(short) if short else 0.0
            return coverage * 0.7
        
        return 0.0
    
    def password(pwd1: str, pwd2: str) -> float:
        """
        Specialized password similarity considering common patterns
        
        Args:
            pwd1:
            pwd2:
        
        Returns:
            similarity
        """
        if not pwd1:
            raise TypeError("Similarity.password() missing 1 required positional argument: 'pwd1'")
        if not pwd2:
            raise TypeError("Similarity.password() missing 1 required positional argument: 'pwd2'")
        
        # Exact match
        if pwd1 == pwd2:
            return 1.0
        
        # Character composition similarity
        def char_composition(pwd: str) -> Dict[str, int]:
            comp = {"digits": 0, "lower": 0, "upper": 0, "special": 0}
            for char in pwd:
                if char.isdigit():
                    comp['digits'] += 1
                elif char.islower():
                    comp['lower'] += 1
                elif char.isupper():
                    comp['upper'] += 1
                else:
                    comp['special'] += 1
            return comp
        
        comp1 = char_composition(pwd1)
        comp2 = char_composition(pwd2)
        
        # Length similarity
        len_sim = 1.0 - abs(len(pwd1) - len(pwd2)) / max(len(pwd1), len(pwd2))
        
        # Composition similarity
        total_chars = sum(comp1.values()) + sum(comp2.values())
        if total_chars == 0:
            comp_sim = 1.0
        else:
            comp_diff = sum(abs(comp1[k] - comp2[k]) for k in comp1)
            comp_sim = 1.0 - (comp_diff / total_chars)
        
        # Character-level similarity (case-sensitive)
        char_sim = difflib.SequenceMatcher(None, pwd1, pwd2).ratio()
        
        return (len_sim * 0.3 + comp_sim * 0.3 + char_sim * 0.4)
    
    def calculate(s1: str, s2: str, normalizer: Callable[[str], str] = lambda s: s) -> float:
        """
        Calculate comprehensive similarity score based on multiple algorithms
        
        Args:
            s1:
            s2:
            normalizer: 
        
        Returns:
            similarity
        """
        if not s1:
            raise TypeError("Similarity.calculate() missing 1 required positional argument: 's1'")
        if not s2:
            raise TypeError("Similarity.calculate() missing 1 required positional argument: 's2'")
        
        # Load configuration
        weights = Similarity.configuration()['weights']

        # Normalize input
        s1 = normalizer(s1)
        s2 = normalizer(s2)

        # Calculate individual similarities
        scores = {}
        
        # Levenshtein
        if weights['levenshtein'] != 0:
            lev_dist = Similarity.levenshtein(s1, s2)
            scores['levenshtein'] = 1.0 - (lev_dist / max(len(s1), len(s2), 1))
        
        # Jaro-Winkler
        if weights['jaro_winkler'] != 0:
            scores['jaro_winkler'] = Similarity.jaro_winkler(s1, s2)
        
        # N-gram
        if weights['ngram'] != 0:
            scores['ngram'] = Similarity.ngram(s1, s2)
        
        # Word overlap
        if weights['jaccard'] != 0:
            scores['jaccard'] = Similarity.jaccard(s1, s2)
        
        # Abbreviation
        if weights['abbreviation'] != 0:
            scores['abbreviation'] = max(Similarity.abbreviation(s1, s2), Similarity.abbreviation(s2, s1))
        
        # Sequence Matcher
        if weights['sequence_matcher'] != 0:
            scores['sequence_matcher'] = difflib.SequenceMatcher(None, s1, s2).ratio()
        
        # Weighted combination
        total_score = sum(weights.get(method, 0) * score for method, score in scores.items())

        return min(1.0, max(0.0, total_score / sum(weights.values())))
    
    def best_matches(txt: str, references: Union[List[str], Dict[str, str]], top_k: int = 5, normalizer: Callable[[str], str] = lambda s: s) -> List[Tuple[str, float]]:
        """
        Find best matching candidates with support for different data structures
        
        Args:
            txt: String to evaluate
            references: List of strings or dict mapping keys to values
            top_k: Maximum number of results
            normalizer: 
        
        Returns:
            Best matches in descending order
        """
        if not txt:
            raise TypeError("Similarity.best_matches() missing 1 required positional argument: 'txt'")
        
        # Normalize input
        txt = normalizer(txt)
        
        scores = []
        
        if isinstance(references, dict):
            items = references.items()
        elif isinstance(references, list):
            items = [(item, item) for item in references]
        else:
            return []
        
        for key, value in items:
            # Calculate similarity against both key and value
            key_sim = Similarity.calculate(txt, key)
            val_sim = Similarity.calculate(txt, value)
            
            # Use the higher similarity
            scores.append((key, max(key_sim, val_sim)))
        
        # Sort by similarity score (descending) and return top_k
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]