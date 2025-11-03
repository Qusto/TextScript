# AICODE-NOTE: T019 - DatasetConfig Pydantic model from data-model.md
# AICODE-NOTE: Validates m_style_texts + k_test_cases <= min_texts_per_author
# AICODE-NOTE: T020 - TopicData Pydantic model with topic and theses validation

"""Configuration models for dataset builder.

Pydantic models for:
- DatasetConfig: Configuration for dataset generation from corpus
- TopicData: Neutralized topic and theses extracted from articles
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TopicData(BaseModel):
    """Neutralized topic and theses from article.

    AICODE-NOTE: T020 - Validates 5-10 theses, max 100 char topic
    AICODE-NOTE: Used in topic.json files in dataset
    AICODE-NOTE: Ensures topic is stylistically neutral for generation
    """

    topic: str = Field(
        min_length=1,
        max_length=100,
        description="Brief topic description (1-50 words, max 100 chars)"
    )

    theses: List[str] = Field(
        min_length=5,
        max_length=10,
        description="Key factual points from article (5-10 theses)"
    )

    @field_validator('theses')
    @classmethod
    def validate_theses_length(cls, v: List[str]) -> List[str]:
        """Validate each thesis is not too long.

        AICODE-NOTE: Maximum 500 characters per thesis
        AICODE-NOTE: Prevents excessively verbose theses
        """
        for i, thesis in enumerate(v):
            if len(thesis) > 500:
                raise ValueError(
                    f"Thesis {i+1} is too long ({len(thesis)} chars, max 500): "
                    f"{thesis[:50]}..."
                )
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "topic": "Journey through Paris during adverse weather conditions",
            "theses": [
                "Narrator is located in Paris",
                "Weather conditions: strong wind and rain",
                "Narrator experiences negative emotions",
                "Movement occurs on foot through city streets",
                "Time period: evening or night"
            ]
        }
    })


class DatasetConfig(BaseModel):
    """Configuration for dataset builder.

    AICODE-NOTE: T019 - Validates configuration from dataset_config.yml
    AICODE-NOTE: Critical validation: m_style_texts + k_test_cases <= min_texts_per_author
    AICODE-NOTE: Ensures enough texts available for dataset generation
    """

    corpus_path: str = Field(
        description="Path to input corpus directory with author subdirectories"
    )

    output_path: str = Field(
        description="Path to output directory for generated dataset"
    )

    min_texts_per_author: int = Field(
        ge=5,
        description="Minimum texts required per author (must be >= 5)"
    )

    m_style_texts: int = Field(
        ge=1,
        description="Number of texts to use for style reference (M)"
    )

    k_test_cases: int = Field(
        ge=1,
        description="Number of test cases to generate per author (K)"
    )

    neutralizer_model_id: str = Field(
        description="Model ID for topic neutralization (e.g., anthropic/claude-3-5-sonnet)"
    )

    max_tokens_for_neutralizer: int = Field(
        gt=0,
        description="Maximum tokens to send to neutralizer (for cost control)"
    )

    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility (optional)"
    )

    @model_validator(mode='after')
    def validate_text_allocation(self) -> 'DatasetConfig':
        """Validate that enough texts are available for dataset generation.

        AICODE-NOTE: Critical constraint validation
        AICODE-NOTE: m_style_texts + k_test_cases must not exceed min_texts_per_author
        AICODE-NOTE: Example: If min=10, m=5, k=5 is valid; m=6, k=5 is invalid
        """
        m = self.m_style_texts
        k = self.k_test_cases
        min_total = self.min_texts_per_author

        if m + k > min_total:
            raise ValueError(
                f"Text allocation invalid: m_style_texts ({m}) + k_test_cases ({k}) = {m+k} "
                f"exceeds min_texts_per_author ({min_total}). "
                f"Reduce m or k, or increase min_texts_per_author."
            )

        return self

    @field_validator('corpus_path', 'output_path')
    @classmethod
    def validate_paths(cls, v: str) -> str:
        """Validate that paths are non-empty strings.

        AICODE-NOTE: Basic path validation
        AICODE-NOTE: Directory existence is checked at runtime by builder
        """
        if not v or not v.strip():
            raise ValueError("Path cannot be empty")
        return v.strip()

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "corpus_path": "./corpus/gutenberg/",
            "output_path": "./eval_dataset/",
            "min_texts_per_author": 10,
            "m_style_texts": 5,
            "k_test_cases": 5,
            "neutralizer_model_id": "anthropic/claude-3-5-sonnet-20240620",
            "max_tokens_for_neutralizer": 4000,
            "random_seed": 42
        }
    })
