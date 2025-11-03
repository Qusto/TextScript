# AICODE-NOTE: T072 - JudgeEvaluator for LLM-as-Judge content and style evaluation
# AICODE-NOTE: Uses prompts from prompt-content-judge.md and prompt-style-judge.md
# AICODE-NOTE: Implements retry logic (max 2 retries) for malformed responses

"""LLM-as-Judge evaluation for content accuracy and style fidelity."""

import json
from datetime import datetime
from typing import Optional

from loguru import logger

from src.evaluator.config import JudgeResult
from src.shared.llm_client import LLMClient


class JudgeEvaluator:
    """LLM-as-Judge evaluator for content and style metrics.

    AICODE-NOTE: T072-T078 - Implements judge evaluation with retry logic
    AICODE-NOTE: Content judge: compares generated vs ground truth (1-5 scale)
    AICODE-NOTE: Style judge: compares generated vs source texts (1-5 scale)
    """

    def __init__(self, llm_client: LLMClient, judge_model_id: str):
        """Initialize judge evaluator.

        Args:
            llm_client: LLM client for API calls
            judge_model_id: Model ID for judging (e.g., "openai/gpt-4o")

        AICODE-NOTE: T073 - Initializes with LLM client injection
        """
        self.llm_client = llm_client
        self.judge_model_id = judge_model_id
        self.max_retries = 2  # AICODE-NOTE: Max 2 retries for malformed responses

        logger.info(f"JudgeEvaluator initialized (model={judge_model_id})")

    def evaluate_content(
        self,
        generated_article: str,
        ground_truth_article: str
    ) -> Optional[JudgeResult]:
        """Evaluate content accuracy of generated article vs ground truth.

        Args:
            generated_article: Generated article text
            ground_truth_article: Ground truth article text

        Returns:
            JudgeResult with score [1-5] and reasoning, or None on error

        AICODE-NOTE: T074 - Implements content judge with prompt from prompt-content-judge.md
        AICODE-NOTE: Compares generated vs ground truth for content coverage
        """
        # AICODE-NOTE: Validate inputs
        if not generated_article or not generated_article.strip():
            logger.warning("Cannot evaluate content: generated article is empty")
            return None

        if not ground_truth_article or not ground_truth_article.strip():
            logger.warning("Cannot evaluate content: ground truth is empty")
            return None

        logger.debug("Evaluating content accuracy...")

        # AICODE-NOTE: T074 - Construct prompt from contract
        system_message = (
            "You are an AI assistant acting as a strict editor. "
            "Your task is to evaluate how completely and accurately the generated article (TEXT_A) "
            "covers the same topic and ideas as the reference article (TEXT_B).\n\n"
            "You must return a JSON object with two keys: \"score\" (number from 1 to 5) "
            "and \"reasoning\" (brief explanation)."
        )

        user_message = f"""Evaluate the **completeness and accuracy of content** in TEXT_A relative to TEXT_B.
Ignore style, grammar, or formatting. Focus only on whether **all key ideas, facts, and theses** from TEXT_B are present and correctly presented in TEXT_A.

**Scoring Scale:**
* 1: TEXT_A is completely about something else. Ideas from TEXT_B are absent.
* 2: TEXT_A mentions the topic but misses >50% of key ideas from TEXT_B.
* 3: TEXT_A covers the topic but with notable gaps (25-50% of ideas) or inaccuracies.
* 4: TEXT_A covers the topic well, missing only minor details (<25% of ideas).
* 5: TEXT_A perfectly covers the topic, including all key ideas from TEXT_B.

**Response Format:** JSON only.

<TEXT_A>
{generated_article}
</TEXT_A>

<TEXT_B>
{ground_truth_article}
</TEXT_B>

Evaluate TEXT_A on the 5-point scale."""

        # AICODE-NOTE: T076, T078 - Retry logic for malformed responses
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{self.max_retries} for content judge")
                    # AICODE-NOTE: Add format reminder on retry
                    user_message += "\n\nREMINDER: Return ONLY valid JSON with 'score' and 'reasoning' fields."

                # Call LLM
                response = self.llm_client.generate(
                    model_id=self.judge_model_id,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.2,  # Low temperature for consistency
                    max_tokens=500
                )

                # AICODE-NOTE: T076 - Parse and validate JSON response
                result_data = self._parse_judge_response(response)

                # AICODE-NOTE: T077 - Validate score and reasoning
                if not self._validate_judge_result(result_data):
                    raise ValueError("Invalid judge result format")

                logger.success(
                    f"Content judge evaluated: score={result_data['score']}/5"
                )

                return JudgeResult(
                    score=result_data["score"],
                    reasoning=result_data["reasoning"],
                    model=self.judge_model_id,
                    prompt_version="content_judge_v1",
                    computed_at=datetime.now()
                )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse content judge response: {e}")
                if attempt == self.max_retries:
                    # AICODE-NOTE: T078 - Max retries exceeded
                    logger.error(
                        f"Failed to get valid content judge response after "
                        f"{self.max_retries + 1} attempts"
                    )
                    raise RuntimeError(
                        f"Failed to get valid judge response after {self.max_retries + 1} attempts"
                    ) from e
                continue

        return None

    def evaluate_style(
        self,
        generated_article: str,
        source_texts: str
    ) -> Optional[JudgeResult]:
        """Evaluate style fidelity of generated article vs source texts.

        Args:
            generated_article: Generated article text
            source_texts: Combined source texts (style reference)

        Returns:
            JudgeResult with score [1-5] and reasoning, or None on error

        AICODE-NOTE: T075 - Implements style judge with prompt from prompt-style-judge.md
        AICODE-NOTE: Compares generated vs source texts for style similarity
        """
        # AICODE-NOTE: Validate inputs
        if not generated_article or not generated_article.strip():
            logger.warning("Cannot evaluate style: generated article is empty")
            return None

        if not source_texts or not source_texts.strip():
            logger.warning("Cannot evaluate style: source texts are empty")
            return None

        logger.debug("Evaluating style fidelity...")

        # AICODE-NOTE: T075 - Construct prompt from contract
        system_message = (
            "You are an AI assistant acting as an experienced literary critic. "
            "Your task is to evaluate the stylistic similarity between two texts. "
            "You must return a JSON object with two keys: \"score\" (number from 1 to 5) "
            "and \"reasoning\" (brief explanation)."
        )

        user_message = f"""You are given two texts:
* TEXT_A (Generated Article): An article that *should* imitate the authorial style.
* TEXT_B (Style Reference): A large corpus of texts by the same author, defining the reference style.

Your task: Evaluate how well TEXT_A **imitates the style** of TEXT_B.
**Ignore topic and content.** Focus only on "HOW it is written":
* Rhythm and sentence structure (short/long, simple/complex)
* Vocabulary (word choice, terminology, metaphors)
* Tone (formal, ironic, gloomy, enthusiastic, etc.)

**Scoring Scale:**
* 1: Completely unlike. Styles are diametrically opposed.
* 2: Weak similarity. Perhaps 1 of 3 aspects matches (e.g., tone), but vocabulary and structure are completely different.
* 3: Moderate similarity. Text "tries" to imitate but often falls back to generic, faceless style.
* 4: Good similarity. Style is recognizable, most aspects (tone, vocabulary, structure) copied correctly.
* 5: Perfect similarity. Text looks like it was actually written by the same author as TEXT_B.

**Response Format:** JSON only.

<TEXT_A>
{generated_article}
</TEXT_A>

<TEXT_B>
{source_texts}
</TEXT_B>

Evaluate the stylistic similarity of TEXT_A to TEXT_B on the 5-point scale."""

        # AICODE-NOTE: Retry logic (same as content judge)
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.warning(f"Retry attempt {attempt}/{self.max_retries} for style judge")
                    user_message += "\n\nREMINDER: Return ONLY valid JSON with 'score' and 'reasoning' fields."

                response = self.llm_client.generate(
                    model_id=self.judge_model_id,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.2,
                    max_tokens=500
                )

                result_data = self._parse_judge_response(response)

                if not self._validate_judge_result(result_data):
                    raise ValueError("Invalid judge result format")

                logger.success(
                    f"Style judge evaluated: score={result_data['score']}/5"
                )

                return JudgeResult(
                    score=result_data["score"],
                    reasoning=result_data["reasoning"],
                    model=self.judge_model_id,
                    prompt_version="style_judge_v1",
                    computed_at=datetime.now()
                )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse style judge response: {e}")
                if attempt == self.max_retries:
                    logger.error(
                        f"Failed to get valid style judge response after "
                        f"{self.max_retries + 1} attempts"
                    )
                    raise RuntimeError(
                        f"Failed to get valid judge response after {self.max_retries + 1} attempts"
                    ) from e
                continue

        return None

    def _parse_judge_response(self, response: str) -> dict:
        """Parse JSON response from LLM judge.

        AICODE-NOTE: T076 - Handles markdown code blocks and extracts JSON
        AICODE-NOTE: Claude often returns ```json ... ``` format
        """
        # Strip whitespace
        response = response.strip()

        # AICODE-NOTE: Remove markdown code blocks if present
        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # AICODE-NOTE: Find JSON object in response
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(f"No JSON object found in response: {response[:100]}")

        json_str = response[json_start:json_end]

        # Parse JSON
        return json.loads(json_str)

    def _validate_judge_result(self, data: dict) -> bool:
        """Validate judge result has required fields and correct types.

        AICODE-NOTE: T077 - Validates score [1-5] and reasoning [50-500 chars]
        """
        # Check required fields
        if "score" not in data or "reasoning" not in data:
            logger.warning("Judge result missing required fields")
            return False

        # Validate score type and range
        score = data["score"]
        if not isinstance(score, int) or not (1 <= score <= 5):
            logger.warning(f"Invalid score: {score} (must be integer 1-5)")
            return False

        # Validate reasoning type and length
        reasoning = data["reasoning"]
        if not isinstance(reasoning, str):
            logger.warning("Reasoning must be string")
            return False

        if len(reasoning) < 50:
            logger.warning(f"Reasoning too short: {len(reasoning)} chars (min 50)")
            return False

        if len(reasoning) > 500:
            logger.warning(f"Reasoning too long: {len(reasoning)} chars (max 500)")
            # AICODE-NOTE: Log warning but don't fail - truncate if needed
            data["reasoning"] = reasoning[:500]

        return True
