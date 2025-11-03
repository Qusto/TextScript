# AICODE-NOTE: T067 - NumericMetrics class for cosine similarity and BERTScore
# AICODE-NOTE: Uses sentence-transformers for embeddings, bert-score library for BERTScore
# AICODE-NOTE: Downloads models on first run, caches locally for performance

"""Numeric similarity metrics: cosine similarity and BERTScore."""

from datetime import datetime
from typing import Optional

import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from eval_harness.src.evaluator.config import (
    CosineSimilarityResult,
    BERTScoreResult
)


class NumericMetrics:
    """Computes numeric similarity metrics between texts.

    AICODE-NOTE: T067-T071 - Implements cosine similarity and BERTScore
    AICODE-NOTE: Cosine similarity: [0.0-1.0] semantic similarity
    AICODE-NOTE: BERTScore: [0.0-1.0] token-level matching (P/R/F1)
    """

    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        bert_model: str = "bert-base-uncased"
    ):
        """Initialize numeric metrics with models.

        Args:
            embedding_model: Sentence transformer model for cosine similarity
            bert_model: BERT model for BERTScore computation

        AICODE-NOTE: T068 - Loads models on initialization
        AICODE-NOTE: Models are downloaded on first use, then cached
        """
        self.embedding_model_name = embedding_model
        self.bert_model_name = bert_model

        # AICODE-NOTE: Lazy loading - only load when compute methods are called
        self._embedding_model: Optional[SentenceTransformer] = None

        logger.info(
            f"NumericMetrics initialized "
            f"(embedding={embedding_model}, bert={bert_model})"
        )

    def _get_embedding_model(self) -> SentenceTransformer:
        """Get or load sentence transformer model.

        AICODE-NOTE: Lazy loading to avoid unnecessary model downloads
        """
        if self._embedding_model is None:
            logger.info(f"Loading embedding model: {self.embedding_model_name}")
            self._embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.success("Embedding model loaded")

        return self._embedding_model

    def compute_cosine_similarity(
        self,
        generated_text: str,
        ground_truth_text: str
    ) -> Optional[CosineSimilarityResult]:
        """Compute cosine similarity between generated and ground truth texts.

        Args:
            generated_text: Generated article text
            ground_truth_text: Ground truth article text

        Returns:
            CosineSimilarityResult with score [0.0-1.0], or None on error

        AICODE-NOTE: T069 - Computes cosine similarity using sentence embeddings
        AICODE-NOTE: Higher score = more semantically similar
        """
        # AICODE-NOTE: T071 - Validate inputs (empty or very short texts)
        if not generated_text or not generated_text.strip():
            logger.warning("Cannot compute cosine similarity: generated text is empty")
            return None

        if not ground_truth_text or not ground_truth_text.strip():
            logger.warning("Cannot compute cosine similarity: ground truth is empty")
            return None

        if len(generated_text.strip()) < 10 or len(ground_truth_text.strip()) < 10:
            logger.warning(
                "Cannot compute cosine similarity: texts too short "
                f"(gen={len(generated_text)}, gt={len(ground_truth_text)})"
            )
            return None

        try:
            logger.debug("Computing cosine similarity...")

            # Load model
            model = self._get_embedding_model()

            # AICODE-NOTE: Encode texts to embeddings
            # sentence-transformers returns numpy arrays
            embedding1 = model.encode([generated_text], convert_to_numpy=True)
            embedding2 = model.encode([ground_truth_text], convert_to_numpy=True)

            # AICODE-NOTE: Compute cosine similarity
            # Formula: cos(θ) = (A · B) / (||A|| × ||B||)
            dot_product = np.dot(embedding1[0], embedding2[0])
            norm1 = np.linalg.norm(embedding1[0])
            norm2 = np.linalg.norm(embedding2[0])

            if norm1 == 0 or norm2 == 0:
                logger.warning("Cannot compute cosine similarity: zero norm vector")
                return None

            cosine_sim = float(dot_product / (norm1 * norm2))

            # AICODE-NOTE: Clamp to [0.0, 1.0] range (should already be there)
            cosine_sim = max(0.0, min(1.0, cosine_sim))

            logger.success(f"Cosine similarity computed: {cosine_sim:.3f}")

            return CosineSimilarityResult(
                score=cosine_sim,
                model=self.embedding_model_name,
                computed_at=datetime.now()
            )

        except Exception as e:
            # AICODE-NOTE: T071 - Error handling logs warning, returns None
            logger.exception(f"Error computing cosine similarity: {e}")
            return None

    def compute_bert_score(
        self,
        generated_text: str,
        ground_truth_text: str
    ) -> Optional[BERTScoreResult]:
        """Compute BERTScore between generated and ground truth texts.

        Args:
            generated_text: Generated article text
            ground_truth_text: Ground truth article text

        Returns:
            BERTScoreResult with precision/recall/F1 [0.0-1.0], or None on error

        AICODE-NOTE: T070 - Computes BERTScore using bert-score library
        AICODE-NOTE: Precision: how much of generated matches ground truth
        AICODE-NOTE: Recall: how much of ground truth covered by generated
        AICODE-NOTE: F1: harmonic mean of precision and recall
        """
        # AICODE-NOTE: T071 - Validate inputs
        if not generated_text or not generated_text.strip():
            logger.warning("Cannot compute BERTScore: generated text is empty")
            return None

        if not ground_truth_text or not ground_truth_text.strip():
            logger.warning("Cannot compute BERTScore: ground truth is empty")
            return None

        if len(generated_text.strip()) < 10 or len(ground_truth_text.strip()) < 10:
            logger.warning(
                "Cannot compute BERTScore: texts too short "
                f"(gen={len(generated_text)}, gt={len(ground_truth_text)})"
            )
            return None

        try:
            logger.debug("Computing BERTScore...")

            # AICODE-NOTE: Import bert_score here (lazy import)
            # This avoids loading if metric is disabled in config
            import bert_score

            # AICODE-NOTE: bert_score.score returns (P, R, F1) as PyTorch tensors
            P, R, F1 = bert_score.score(
                [generated_text],
                [ground_truth_text],
                model_type=self.bert_model_name,
                verbose=False
            )

            # AICODE-NOTE: Convert tensors to float values
            precision = float(P[0].item())
            recall = float(R[0].item())
            f1 = float(F1[0].item())

            logger.success(
                f"BERTScore computed: P={precision:.3f}, R={recall:.3f}, F1={f1:.3f}"
            )

            return BERTScoreResult(
                precision=precision,
                recall=recall,
                f1=f1,
                model=self.bert_model_name,
                computed_at=datetime.now()
            )

        except Exception as e:
            # AICODE-NOTE: T071 - Error handling logs warning, returns None
            logger.exception(f"Error computing BERTScore: {e}")
            return None
