# AICODE-NOTE: T022 - EvalConfig Pydantic model from data-model.md
# AICODE-NOTE: Validates at least one metric enabled
# AICODE-NOTE: T023 - NumericMetrics, JudgeResult models with score bounds validation

"""Configuration models for evaluator.

Pydantic models for:
- EvalConfig: Configuration for evaluation runs
- NumericMetrics: Results from numeric similarity metrics
- JudgeResult: Results from LLM-as-Judge evaluation
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CosineSimilarityResult(BaseModel):
    """Cosine similarity metric result.

    AICODE-NOTE: T023 - Score bounds validation [0.0-1.0]
    AICODE-NOTE: Higher score = more semantically similar
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Cosine similarity score (0.0-1.0)"
    )

    model: str = Field(
        description="Embedding model used (e.g., all-MiniLM-L6-v2)"
    )

    computed_at: datetime = Field(
        description="Timestamp when metric was computed"
    )


class BERTScoreResult(BaseModel):
    """BERTScore metric result.

    AICODE-NOTE: T023 - Score bounds validation [0.0-1.0] for all scores
    AICODE-NOTE: Precision: how much of generated matches ground truth
    AICODE-NOTE: Recall: how much of ground truth covered by generated
    AICODE-NOTE: F1: harmonic mean of precision and recall
    """

    precision: float = Field(
        ge=0.0,
        le=1.0,
        description="BERTScore precision (0.0-1.0)"
    )

    recall: float = Field(
        ge=0.0,
        le=1.0,
        description="BERTScore recall (0.0-1.0)"
    )

    f1: float = Field(
        ge=0.0,
        le=1.0,
        description="BERTScore F1 (0.0-1.0)"
    )

    model: str = Field(
        description="BERT model used (e.g., bert-base-uncased)"
    )

    computed_at: datetime = Field(
        description="Timestamp when metric was computed"
    )


class NumericMetrics(BaseModel):
    """All numeric metrics for a test case.

    AICODE-NOTE: T023 - Container for numeric similarity metrics
    AICODE-NOTE: Both metrics are optional (can be disabled in config)
    AICODE-NOTE: Saved as metrics_numeric.json in eval results
    """

    cosine_similarity: Optional[CosineSimilarityResult] = Field(
        default=None,
        description="Cosine similarity result (optional)"
    )

    bert_score: Optional[BERTScoreResult] = Field(
        default=None,
        description="BERTScore result (optional)"
    )


class JudgeResult(BaseModel):
    """LLM-as-Judge evaluation result.

    AICODE-NOTE: T023 - Score bounds validation [1-5] for integer scores
    AICODE-NOTE: Used for both content and style judge metrics
    AICODE-NOTE: Score interpretation:
    - 1: Completely different (0-20% match)
    - 2: Weak similarity (20-40% match)
    - 3: Moderate similarity (40-60% match)
    - 4: Good similarity (60-80% match)
    - 5: Excellent similarity (80-100% match)
    """

    score: int = Field(
        ge=1,
        le=5,
        description="Judge score (1-5 integer)"
    )

    reasoning: str = Field(
        min_length=50,
        max_length=500,
        description="Explanation for the score (50-500 chars)"
    )

    model: str = Field(
        description="Judge model ID used"
    )

    prompt_version: str = Field(
        description="Version identifier for prompt used"
    )

    computed_at: datetime = Field(
        description="Timestamp when judgment was made"
    )


class EvalConfig(BaseModel):
    """Configuration for evaluator.

    AICODE-NOTE: T022 - Validates configuration from eval_config.yml
    AICODE-NOTE: Critical validation: at least one metric must be enabled
    AICODE-NOTE: Supports selective metric computation for cost/time optimization
    """

    dataset_path: str = Field(
        description="Path to input dataset directory (from prepare_dataset.py)"
    )

    output_path: str = Field(
        description="Path to output directory for evaluation results"
    )

    generation_model_id: str = Field(
        description="Model ID for article generation (Ugly Script)"
    )

    judge_model_id: str = Field(
        description="Model ID for LLM-as-Judge evaluation"
    )

    metrics_numeric: Dict[str, bool] = Field(
        description="Numeric metrics to compute (cosine_similarity, bert_score)"
    )

    metrics_judge: Dict[str, bool] = Field(
        description="LLM judge metrics to compute (content_judge, style_judge)"
    )

    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence embedding model for cosine similarity"
    )

    llm_timeout: int = Field(
        gt=0,
        default=120,
        description="Timeout for LLM API calls in seconds"
    )

    max_retries: int = Field(
        ge=0,
        default=3,
        description="Maximum retry attempts for failed API calls"
    )

    @model_validator(mode='after')
    def validate_metrics_enabled(self) -> 'EvalConfig':
        """Validate that at least one metric is enabled.

        AICODE-NOTE: Critical validation - prevents empty evaluation runs
        AICODE-NOTE: At least one numeric OR judge metric must be enabled
        """
        numeric_enabled = any(self.metrics_numeric.values())
        judge_enabled = any(self.metrics_judge.values())

        if not numeric_enabled and not judge_enabled:
            raise ValueError(
                "At least one metric must be enabled. "
                "Enable at least one of: cosine_similarity, bert_score, "
                "content_judge, or style_judge"
            )

        return self

    @field_validator('dataset_path', 'output_path')
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Validate that paths are non-empty strings.

        AICODE-NOTE: Basic path validation
        AICODE-NOTE: Directory existence is checked at runtime by runner
        """
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "dataset_path": "./eval_dataset/",
            "output_path": "./eval_results/",
            "generation_model_id": "meta-llama/llama-3-8b-instruct",
            "judge_model_id": "openai/gpt-4o",
            "metrics_numeric": {
                "cosine_similarity": True,
                "bert_score": True
            },
            "metrics_judge": {
                "content_judge": True,
                "style_judge": True
            },
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_timeout": 120,
            "max_retries": 3
        }
    })
