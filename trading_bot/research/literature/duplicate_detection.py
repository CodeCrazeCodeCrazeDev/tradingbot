"""
Duplicate Detection Provider implementations for Research OS literature.
Supports Cosine, Levenshtein, and Hybrid ensemble strategies.
"""

from typing import List, Tuple
import numpy as np
from trading_bot.research.core.interfaces import DuplicateDetectionProvider, ResearchPaper


class LevenshteinDuplicateDetector(DuplicateDetectionProvider):
    """
    Duplicate detector using Normalized Levenshtein edit distance on titles.
    """

    def __init__(self, threshold: float = 0.8):
        """
        threshold: minimum similarity ratio (0 to 1) to be flagged as a duplicate.
        """
        self.threshold = threshold

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def _similarity_ratio(self, s1: str, s2: str) -> float:
        s1 = s1.lower().strip()
        s2 = s2.lower().strip()
        if not s1 or not s2:
            return 0.0
        dist = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1.0 - (dist / max_len)

    def find_duplicates(self, new_paper: ResearchPaper, existing_papers: List[ResearchPaper]) -> List[Tuple[ResearchPaper, float]]:
        duplicates = []
        for paper in existing_papers:
            sim = self._similarity_ratio(new_paper.title, paper.title)
            if sim >= self.threshold:
                duplicates.append((paper, sim))
        return sorted(duplicates, key=lambda x: x[1], reverse=True)


class CosineDuplicateDetector(DuplicateDetectionProvider):
    """
    Duplicate detector using cosine similarity on embeddings.
    """

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        if v1 is None or v2 is None:
            return 0.0
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def find_duplicates(self, new_paper: ResearchPaper, existing_papers: List[ResearchPaper]) -> List[Tuple[ResearchPaper, float]]:
        if new_paper.embeddings is None:
            return []

        duplicates = []
        for paper in existing_papers:
            if paper.embeddings is None:
                continue
            sim = self._cosine_similarity(new_paper.embeddings, paper.embeddings)
            if sim >= self.threshold:
                duplicates.append((paper, sim))
        return sorted(duplicates, key=lambda x: x[1], reverse=True)


class HybridEnsembleDuplicateDetector(DuplicateDetectionProvider):
    """
    Combines Levenshtein title matching and Cosine embedding similarity
    with weighted parameters.
    """

    def __init__(self, threshold: float = 0.8, levenshtein_weight: float = 0.4, cosine_weight: float = 0.6):
        self.threshold = threshold
        self.lev_detector = LevenshteinDuplicateDetector(threshold=0.0)
        self.cos_detector = CosineDuplicateDetector(threshold=0.0)
        self.lev_weight = levenshtein_weight
        self.cos_weight = cosine_weight

    def find_duplicates(self, new_paper: ResearchPaper, existing_papers: List[ResearchPaper]) -> List[Tuple[ResearchPaper, float]]:
        duplicates = []

        # Calculate scores
        for paper in existing_papers:
            lev_score = 0.0
            cos_score = 0.0

            # Title edit distance
            lev_score = self.lev_detector._similarity_ratio(new_paper.title, paper.title)

            # Abstract similarity
            if new_paper.embeddings is not None and paper.embeddings is not None:
                cos_score = self.cos_detector._cosine_similarity(new_paper.embeddings, paper.embeddings)
            else:
                # Fallback to character/word-based overlap similarity if embeddings are not populated
                abstract_overlap = set(new_paper.abstract.lower().split()) & set(paper.abstract.lower().split())
                cos_score = len(abstract_overlap) / max(1, min(len(new_paper.abstract.split()), len(paper.abstract.split())))

            hybrid_score = (self.lev_weight * lev_score) + (self.cos_weight * cos_score)

            if hybrid_score >= self.threshold:
                duplicates.append((paper, hybrid_score))

        return sorted(duplicates, key=lambda x: x[1], reverse=True)
