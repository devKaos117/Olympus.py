import re, difflib
from typing import List, Tuple, Optional, Dict, Set, Union

from .normalize import Normalize


class Similarity:
    """
    """

    WEIGHTS = {
        "levenshtein": 0.2,
        "jaro_winkler": 0.25,
        "sequence_matcher": 0.2,
        "ngram": 0.15,
        "abbreviation": 0.1,
        "word_overlap": 0.1
    }

    STOP_WORDS = {"the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "a", "an", "as", "is", "was", "are", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}

    def levenshtein_distance(s1: str, s2: str, substitution_cost: int = 1, insertion_cost: int = 1, deletion_cost: int = 1) -> int:
        """
        Calculate weighted Levenshtein distance

        Args:
            s1:
            s2:
        
        Returns:
            similarity
        """        
        if len(s1) < len(s2):
            s1, s2 = s2, s1
            insertion_cost, deletion_cost = deletion_cost, insertion_cost
        
        if len(s2) == 0:
            return len(s1) * deletion_cost
        
        previous_row = list(range(0, (len(s2) + 1) * insertion_cost, insertion_cost))
        
        for i, c1 in enumerate(s1):
            current_row = [(i + 1) * deletion_cost]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + insertion_cost
                deletions = current_row[j] + deletion_cost
                substitutions = previous_row[j] + (substitution_cost if c1 != c2 else 0)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def jaro_winkler(s1: str, s2: str, prefix_scale: float = 0.1) -> float:
        """
        Calculate Jaro-Winkler similarity

        Args:
            s1:
            s2:
        
        Returns:
            similarity
        """
        if not s1 or not s2:
            return 0.0 if s1 != s2 else 1.0
        
        if s1 == s2:
            return 1.0
        
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
        
        return jaro + (prefix_scale * prefix * (1 - jaro))
    
    @staticmethod
    def ngram(s1: str, s2: str, n: int = 2) -> float:
        """
        Calculate n-gram Jaccard similarity

        Args:
            s1:
            s2:
        
        Returns:
            similarity
        """
        if not s1 or not s2:
            return 0.0 if s1 != s2 else 1.0
        
        def get_ngrams(s: str, n: int) -> List[str]:
            if len(s) < n:
                return [s]
            return [s[i:i+n] for i in range(len(s) - n + 1)]
        
        ngrams1 = set(get_ngrams(s1, n))
        ngrams2 = set(get_ngrams(s2, n))
        
        if not ngrams1 and not ngrams2:
            return 1.0
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def word_overlap(s1: str, s2: str, remove_stop_words: bool = True) -> float:
        """
        Calculate word-level overlap similarity (Jaccard index of words)

        Args:
            s1:
            s2:
        
        Returns:
            similarity
        """
        def tokenize(text: str) -> Set[str]:
            words = set(re.findall(r"\b\w+\b", text.lower()))
            if remove_stop_words:
                words = words - Normalize.stop_words
            return words
        
        words1 = tokenize(s1)
        words2 = tokenize(s2)
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def abbreviation_similarity(short: str, full: str, strict_abbreviation: bool = False) -> float:
        """
        Calculate abbreviation similarity with multiple strategies
        
        Args:
            short: Normalized
            full: Normalized

        """
        if not short or not full:
            return 0.0
        
        if short == full:
            return 1.0
        
        # Direct containment
        if short in full:
            return 0.8
        
        # Acronym matching (first letters of words)
        full_words = re.findall(r"\b\w+\b", full)
        if full_words:
            acronym = "".join(word[0] for word in full_words if word)
            if short == acronym:
                return 0.9
        
        # Character-by-character matching (subsequence)
        if not strict_abbreviation:
            short_idx = 0
            for char in full:
                if short_idx < len(short) and char == short[short_idx]:
                    short_idx += 1
            
            coverage = short_idx / len(short) if short else 0.0
            return coverage * 0.7
        
        return 0.0
    
    def password_similarity(pwd1: str, pwd2: str) -> float:
        """
        Specialized password similarity considering common patterns
        
        Args:
            pwd1:
            pwd2:
        
        Returns:
            similarity
        """
        if not pwd1 or not pwd2:
            return 0.0 if pwd1 != pwd2 else 1.0
        
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
    
    def calculate(txt: str, source: str, weights: Optional[Dict[str, float]] = None, ngram_size = 2, strict_abbreviation = False, remove_stop_words = True) -> float:
        """
        Calculate comprehensive similarity score based on use case
        
        Args:
            txt: Query string
            source: Target string to compare against
            weights: Custom weights for similarity methods
            case_sensitive:
            ngram_size:
            strict_abbreviation:
            remove_stop_words:
        """
        if not txt or not source:
            return 0.0 if txt != source else 1.0
        
        weights = weights or Similarity.WEIGHTS
        
        # Calculate individual similarities
        scores = {}
        
        # Levenshtein
        if "levenshtein" in weights:
            lev_dist = Similarity.levenshtein_distance(txt, source)
            max_len = max(len(txt), len(source), 1)
            scores['levenshtein'] = 1.0 - (lev_dist / max_len)
        
        # Jaro-Winkler
        if "jaro_winkler" in weights:
            scores['jaro_winkler'] = Similarity.jaro_winkler(txt, source)
        
        # Sequence Matcher
        if "sequence_matcher" in weights:
            scores['sequence_matcher'] = difflib.SequenceMatcher(None, txt, source).ratio()
        
        # N-gram
        if "ngram" in weights:
            scores['ngram'] = Similarity.ngram(txt, source, n=ngram_size)
        
        # Abbreviation
        if "abbreviation" in weights:
            scores['abbreviation'] = Similarity.abbreviation_similarity(txt, source, strict_abbreviation)
        
        # Word overlap
        if "word_overlap" in weights:
            scores['word_overlap'] = Similarity.word_overlap(txt, source, remove_stop_words)
        
        # Weighted combination
        total_score = sum(weights.get(method, 0) * score for method, score in scores.items())
        
        return min(1.0, max(0.0, total_score))
    
    def best_matches(self, txt: str, map: Union[List[str], Dict[str, str]],  top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find best matching candidates with support for different data structures
        
        Args:
            txt: String to evaluate
            map: List of strings or dict mapping keys to values
            top_k: Maximum number of results
        
        Returns:
            Best matches in descending order
        """
        if not txt:
            return []
        
        scores = []
        
        if isinstance(map, dict):
            items = map.items()
        elif isinstance(map, list):
            items = [(item, item) for item in map]
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