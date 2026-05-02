"""
Smart Folder Router - cosine-similarity folder matching, confidence-threshold
decision logic, and correction learning.

Legacy: predates VFS. Only used for backward-compat suggest UI.
Do not add new callers — use VirtualPath / HierarchyTemplate instead.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

logger = logging.getLogger(__name__)

# Decision outcomes
DECISION_AUTO    = 'auto'       # confidence >= HIGH threshold → place automatically
DECISION_SUGGEST = 'suggest'    # MEDIUM <= confidence < HIGH → suggest, ask user
DECISION_UNSURE  = 'unsure'     # confidence < MEDIUM → show all options, ask user


@dataclass
class FolderMatch:
    folder: str
    score: float          # cosine similarity (0-1)
    confidence: float     # classifier confidence (0-1)
    is_new: bool = False  # folder doesn't exist yet


@dataclass
class RoutingDecision:
    decision: str                        # DECISION_* constant
    primary_folder: str                  # best match
    primary_score: float
    primary_confidence: float
    alternatives: list[FolderMatch] = field(default_factory=list)
    needs_confirmation: bool = False
    message: str = ''


class FolderRouter:
    """
    Routes a document to the most suitable folder using:
    1. ML classifier label (from DocumentClassifier)
    2. Cosine similarity between document text and existing folder names/descriptions
    3. Confidence thresholds to decide auto-place vs. ask-user
    """

    def __init__(self,
                 high_threshold: float = 0.80,
                 medium_threshold: float = 0.60,
                 cosine_threshold: float = 0.70):
        self.high_threshold    = high_threshold
        self.medium_threshold  = medium_threshold
        self.cosine_threshold  = cosine_threshold

    # ------------------------------------------------------------------
    # Core routing
    # ------------------------------------------------------------------

    def route(self,
              document_text: str,
              predicted_label: str,
              confidence_score: float,
              existing_folders: list[str],
              all_predictions: list[dict] | None = None) -> RoutingDecision:
        """
        Decide where to place a document.

        Args:
            document_text:    preprocessed document text
            predicted_label:  top label from DocumentClassifier
            confidence_score: probability for predicted_label (0-1)
            existing_folders: list of folder names already on disk/db
            all_predictions:  [{'label': str, 'confidence': float}, ...]

        Returns:
            RoutingDecision
        """
        if not existing_folders:
            # No folders yet – always create new
            return RoutingDecision(
                decision=DECISION_AUTO,
                primary_folder=predicted_label,
                primary_score=1.0,
                primary_confidence=confidence_score,
                is_new=True if predicted_label not in existing_folders else False,
                message=f'Creating new folder "{predicted_label}".',
            )

        # Step 1 – cosine similarity between doc text and folder names
        folder_scores = self._cosine_match(document_text, existing_folders)

        # Step 2 – find best folder (blend classifier + cosine)
        best_match = self._best_match(
            predicted_label, confidence_score, folder_scores, existing_folders
        )

        # Step 3 – build alternatives list from all_predictions + cosine
        alternatives = self._build_alternatives(
            predicted_label, folder_scores, existing_folders, all_predictions
        )
        alternatives = [a for a in alternatives if a.folder != best_match.folder][:3]

        # Step 4 – apply threshold decision logic
        if confidence_score >= self.high_threshold:
            decision = DECISION_AUTO
            needs_confirmation = False
            message = (f'High confidence ({confidence_score:.0%}). '
                       f'Placing in "{best_match.folder}" automatically.')
        elif confidence_score >= self.medium_threshold:
            decision = DECISION_SUGGEST
            needs_confirmation = True
            message = (f'Moderate confidence ({confidence_score:.0%}). '
                       f'Suggested folder: "{best_match.folder}". Please confirm.')
        else:
            decision = DECISION_UNSURE
            needs_confirmation = True
            message = (f'Low confidence ({confidence_score:.0%}). '
                       f'Please choose a folder manually.')

        return RoutingDecision(
            decision=decision,
            primary_folder=best_match.folder,
            primary_score=best_match.score,
            primary_confidence=confidence_score,
            alternatives=alternatives,
            needs_confirmation=needs_confirmation,
            message=message,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cosine_match(self, document_text: str,
                      folders: list[str]) -> dict[str, float]:
        """Return {folder_name: cosine_similarity} using TF-IDF."""
        if not document_text or not folders:
            return {f: 0.0 for f in folders}
        try:
            corpus = [document_text] + folders
            vec = TfidfVectorizer(stop_words='english', lowercase=True)
            tfidf = vec.fit_transform(corpus)
            doc_vec  = tfidf[0]
            fold_vec = tfidf[1:]
            sims = cosine_similarity(doc_vec, fold_vec)[0]
            return {folders[i]: float(sims[i]) for i in range(len(folders))}
        except Exception as e:
            logger.warning(f"Cosine match failed: {e}")
            return {f: 0.0 for f in folders}

    def _best_match(self, predicted_label: str, confidence: float,
                    cosine_scores: dict[str, float],
                    folders: list[str]) -> FolderMatch:
        """
        Blend classifier label + cosine score.
        If predicted_label already exists as a folder, boost its cosine score
        by the classifier confidence and pick highest combined score.
        """
        combined: dict[str, float] = {}
        for folder in folders:
            cos = cosine_scores.get(folder, 0.0)
            # Boost folder that matches predicted label
            label_match = 1.0 if folder.lower() == predicted_label.lower() else 0.0
            combined[folder] = 0.5 * cos + 0.5 * (label_match * confidence)

        if not combined:
            return FolderMatch(folder=predicted_label, score=1.0,
                               confidence=confidence, is_new=True)

        best_folder = max(combined, key=combined.__getitem__)
        is_new = predicted_label not in folders and best_folder != predicted_label

        return FolderMatch(
            folder=best_folder,
            score=combined[best_folder],
            confidence=confidence,
            is_new=is_new,
        )

    def _build_alternatives(self, predicted_label: str,
                            cosine_scores: dict[str, float],
                            folders: list[str],
                            all_predictions: list[dict] | None) -> list[FolderMatch]:
        """Build ranked alternative folder suggestions."""
        seen: set[str] = set()
        matches: list[FolderMatch] = []

        # From classifier all_predictions
        if all_predictions:
            for pred in all_predictions:
                label = pred.get('label', '')
                conf  = pred.get('confidence', 0.0)
                if label and label not in seen:
                    seen.add(label)
                    cos = cosine_scores.get(label, 0.0)
                    matches.append(FolderMatch(
                        folder=label,
                        score=cos,
                        confidence=conf,
                        is_new=label not in folders,
                    ))

        # From top cosine matches
        for folder, score in sorted(cosine_scores.items(),
                                     key=lambda x: x[1], reverse=True):
            if folder not in seen:
                seen.add(folder)
                matches.append(FolderMatch(folder=folder, score=score,
                                           confidence=0.0, is_new=False))

        # Sort by confidence desc, then score desc
        matches.sort(key=lambda m: (m.confidence, m.score), reverse=True)
        return matches
