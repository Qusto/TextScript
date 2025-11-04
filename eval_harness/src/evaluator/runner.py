# AICODE-NOTE: T079 - EvaluationRunner class - Main evaluation orchestrator
# AICODE-NOTE: Implements complete pipeline: load case → generate → compute metrics → save
# AICODE-NOTE: T085 - Main loop with tqdm progress tracking per author

"""Main evaluation runner for StyleGuard eval harness."""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from src.evaluator.config import EvalConfig, NumericMetrics
from src.evaluator.integration import UglyScriptAdapter
from src.evaluator.metrics.numeric import NumericMetrics as NumericMetricsComputer
from src.evaluator.metrics.judge import JudgeEvaluator


# AICODE-NOTE: Stage icons for colorful logging
STAGE_ICONS = {
    "load": "📦",
    "generate": "⚙️",
    "metrics": "📊",
    "save": "💾"
}


class EvaluationRunner:
    """Main orchestrator for evaluation runs.

    AICODE-NOTE: T079-T086 - Coordinates all evaluation components
    AICODE-NOTE: Handles loading, generation, metric computation, and saving
    AICODE-NOTE: Implements error recovery to continue on failures
    """

    def __init__(
        self,
        config: EvalConfig,
        adapter: UglyScriptAdapter,
        numeric_metrics: Optional[NumericMetricsComputer] = None,
        judge_evaluator: Optional[JudgeEvaluator] = None
    ):
        """Initialize evaluation runner with all components.

        Args:
            config: Evaluation configuration
            adapter: UglyScriptAdapter for article generation
            numeric_metrics: NumericMetrics computer (optional)
            judge_evaluator: JudgeEvaluator for LLM-as-Judge (optional)

        AICODE-NOTE: T080 - Initializes all components based on EvalConfig
        AICODE-NOTE: Components are optional to support disabled metrics
        """
        self.config = config
        self.adapter = adapter
        self.numeric_metrics = numeric_metrics
        self.judge_evaluator = judge_evaluator

        logger.info("EvaluationRunner initialized")

    def _format_size(self, num_chars: int) -> str:
        """Format text size in KB or MB.

        Args:
            num_chars: Number of characters

        Returns:
            Formatted string like "50KB" or "1.5MB"

        AICODE-NOTE: Helper for compact size display
        """
        kb = num_chars / 1024
        if kb < 1024:
            return f"{kb:.0f}KB"
        else:
            mb = kb / 1024
            return f"{mb:.1f}MB"

    def _get_text_stats(self, text: str) -> str:
        """Get compact text statistics.

        Args:
            text: Text to analyze

        Returns:
            Formatted string like "150KB (120,000 chars)"

        AICODE-NOTE: Combines size and char count
        """
        return f"{self._format_size(len(text))} ({len(text):,} chars)"

    def _log_stage(self, stage_num: int, total: int, icon: str, message: str) -> None:
        """Log evaluation stage with color and icon.

        Args:
            stage_num: Current stage number (1-4)
            total: Total stages (4)
            icon: Emoji icon from STAGE_ICONS
            message: Stage description

        AICODE-NOTE: Uses Loguru markup for cyan color
        """
        logger.info(f"<cyan>[{stage_num}/{total}] {icon} {message}</cyan>")

    def _load_test_case(self, case_path: Path) -> Dict[str, Any]:
        """Load test case files from dataset directory.

        Args:
            case_path: Path to test case directory

        Returns:
            Dict with source_texts, ground_truth_article, and topic_data

        Raises:
            FileNotFoundError: If required files are missing

        AICODE-NOTE: T081 - Loads 3 required files from test case directory
        AICODE-NOTE: Returns dict with all data needed for evaluation
        """
        # AICODE-NOTE: Load source_texts.txt
        source_texts_file = case_path / "source_texts.txt"
        if not source_texts_file.exists():
            raise FileNotFoundError(f"Missing source_texts.txt in {case_path}")

        source_texts = source_texts_file.read_text(encoding="utf-8")

        # AICODE-NOTE: Load ground_truth_article.txt
        ground_truth_file = case_path / "ground_truth_article.txt"
        if not ground_truth_file.exists():
            raise FileNotFoundError(f"Missing ground_truth_article.txt in {case_path}")

        ground_truth_article = ground_truth_file.read_text(encoding="utf-8")

        # AICODE-NOTE: Load topic.json
        topic_file = case_path / "topic.json"
        if not topic_file.exists():
            raise FileNotFoundError(f"Missing topic.json in {case_path}")

        with open(topic_file, 'r', encoding="utf-8") as f:
            topic_data = json.load(f)

        # AICODE-NOTE: Log compact input summary with yellow color
        topic_name = topic_data.get("topic", "Unknown")[:40]  # Truncate long topics
        if len(topic_data.get("topic", "")) > 40:
            topic_name += "..."

        logger.info(
            f"  <yellow>Input: source={self._format_size(len(source_texts))} "
            f"ground_truth={self._format_size(len(ground_truth_article))} "
            f"topic=\"{topic_name}\"</yellow>"
        )

        return {
            "source_texts": source_texts,
            "ground_truth_article": ground_truth_article,
            "topic_data": topic_data
        }

    def _save_case_results(
        self,
        output_path: Path,
        generated_article: str,
        numeric_metrics: Optional[NumericMetrics] = None,
        content_judge: Optional[Any] = None,
        style_judge: Optional[Any] = None
    ) -> None:
        """Save evaluation results to output directory.

        Args:
            output_path: Directory to save results
            generated_article: Generated article text
            numeric_metrics: Numeric metrics results (optional)
            content_judge: Content judge result (optional)
            style_judge: Style judge result (optional)

        AICODE-NOTE: T084 - Writes 4 files to output directory
        AICODE-NOTE: Creates output directory if it doesn't exist
        AICODE-NOTE: Simplified logging - no DEBUG messages
        """
        # AICODE-NOTE: Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # AICODE-NOTE: Save generated article
        generated_file = output_path / "generated_article.txt"
        generated_file.write_text(generated_article, encoding="utf-8")

        # AICODE-NOTE: Save numeric metrics (if available)
        if numeric_metrics is not None:
            metrics_file = output_path / "metrics_numeric.json"
            with open(metrics_file, 'w', encoding="utf-8") as f:
                json.dump(numeric_metrics.model_dump(mode='json'), f, indent=2)

        # AICODE-NOTE: Save content judge result (if available)
        if content_judge is not None:
            content_file = output_path / "metrics_judge_content.json"
            with open(content_file, 'w', encoding="utf-8") as f:
                json.dump(content_judge.model_dump(mode='json'), f, indent=2)

        # AICODE-NOTE: Save style judge result (if available)
        if style_judge is not None:
            style_file = output_path / "metrics_judge_style.json"
            with open(style_file, 'w', encoding="utf-8") as f:
                json.dump(style_judge.model_dump(mode='json'), f, indent=2)

    def _evaluate_case(
        self,
        case_path: Path,
        output_path: Path,
        perfect_test: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Evaluate single test case with full pipeline.

        Args:
            case_path: Path to test case directory
            output_path: Path to save results
            perfect_test: If True, use source texts as generated output for author baseline

        Returns:
            Dict with evaluation results, or None on failure

        AICODE-NOTE: T082 - Implements full pipeline: load → generate → compute → save
        AICODE-NOTE: T086 - Error recovery to continue on failures
        AICODE-NOTE: T117 - Perfect test mode: compares source texts vs ground truth
        AICODE-NOTE: Perfect test measures author style consistency (same author, different works)
        AICODE-NOTE: Enhanced with colorful stage-based logging
        """
        try:
            # AICODE-NOTE: Stage 1 - Load test case
            self._log_stage(1, 4, STAGE_ICONS["load"], "Loading test case")
            case_data = self._load_test_case(case_path)

            # AICODE-NOTE: Stage 2 - Generate article OR use source texts (perfect test mode)
            if perfect_test:
                self._log_stage(2, 4, STAGE_ICONS["generate"], "Using source texts for author baseline")
                generated_article = case_data["source_texts"]
                logger.info(
                    f"  <green>Comparing source texts {self._format_size(len(case_data['source_texts']))} "
                    f"vs ground truth {self._format_size(len(case_data['ground_truth_article']))}</green>"
                )
            else:
                self._log_stage(2, 4, STAGE_ICONS["generate"], "Generating article")
                start_time = time.time()

                generated_article = self.adapter.generate_article(
                    source_texts=case_data["source_texts"],
                    topic_data=case_data["topic_data"]
                )

                if not generated_article or not generated_article.strip():
                    logger.error("Generated article is empty")
                    return None

                elapsed = time.time() - start_time
                logger.info(
                    f"  <green>Generated: {self._get_text_stats(generated_article)} "
                    f"in {elapsed:.1f}s</green>"
                )

            # AICODE-NOTE: Stage 3 - Compute metrics (conditionally based on config)
            self._log_stage(3, 4, STAGE_ICONS["metrics"], "Computing metrics")

            numeric_metrics_result = None
            content_judge_result = None
            style_judge_result = None

            # AICODE-NOTE: T083 - Conditional metric computation (silent execution)
            # Numeric metrics
            if self.numeric_metrics is not None:
                cosine_result = None
                bert_result = None
                char_ngrams_result = None

                # AICODE-NOTE: Compute cosine similarity if enabled
                if self.config.metrics_numeric.get("cosine_similarity", False):
                    try:
                        cosine_result = self.numeric_metrics.compute_cosine_similarity(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                    except Exception as e:
                        logger.warning(f"Cosine similarity failed: {e}")

                # AICODE-NOTE: Compute BERTScore if enabled
                if self.config.metrics_numeric.get("bert_score", False):
                    try:
                        bert_result = self.numeric_metrics.compute_bert_score(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                    except Exception as e:
                        logger.warning(f"BERTScore failed: {e}")

                # AICODE-NOTE: Compute character n-grams if enabled
                if self.config.metrics_numeric.get("char_ngrams", False):
                    try:
                        char_ngrams_result = self.numeric_metrics.compute_char_ngrams(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                    except Exception as e:
                        logger.warning(f"Character n-grams failed: {e}")

                # AICODE-NOTE: Create NumericMetrics object if any metric succeeded
                if cosine_result or bert_result or char_ngrams_result:
                    numeric_metrics_result = NumericMetrics(
                        cosine_similarity=cosine_result,
                        bert_score=bert_result,
                        char_ngrams=char_ngrams_result
                    )

            # Judge evaluations
            if self.judge_evaluator is not None:
                # AICODE-NOTE: Content judge if enabled
                if self.config.metrics_judge.get("content_judge", False):
                    try:
                        content_judge_result = self.judge_evaluator.evaluate_content(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                    except Exception as e:
                        logger.warning(f"Content judge failed: {e}")

                # AICODE-NOTE: Style judge if enabled
                if self.config.metrics_judge.get("style_judge", False):
                    try:
                        style_judge_result = self.judge_evaluator.evaluate_style(
                            generated_article,
                            case_data["source_texts"]
                        )
                    except Exception as e:
                        logger.warning(f"Style judge failed: {e}")

            # AICODE-NOTE: Stage 4 - Save results
            self._log_stage(4, 4, STAGE_ICONS["save"], "Saving results")
            self._save_case_results(
                output_path=output_path,
                generated_article=generated_article,
                numeric_metrics=numeric_metrics_result,
                content_judge=content_judge_result,
                style_judge=style_judge_result
            )
            logger.info(f"  <magenta>Output: {output_path}</magenta>")

            # AICODE-NOTE: Log results summary in one line with bold green
            metrics_parts = []
            if numeric_metrics_result and numeric_metrics_result.cosine_similarity:
                score = numeric_metrics_result.cosine_similarity.score
                metrics_parts.append(f"cosine={score:.3f}")
            if numeric_metrics_result and numeric_metrics_result.bert_score:
                f1 = numeric_metrics_result.bert_score.f1
                metrics_parts.append(f"bert_f1={f1:.3f}")
            if numeric_metrics_result and numeric_metrics_result.char_ngrams:
                score = numeric_metrics_result.char_ngrams.score
                metrics_parts.append(f"char_ngrams={score:.3f}")
            if content_judge_result:
                metrics_parts.append(f"content={content_judge_result.score}/5")
            if style_judge_result:
                metrics_parts.append(f"style={style_judge_result.score}/5")

            if metrics_parts:
                metrics_str = " ".join(metrics_parts)
                logger.info(f"<green><bold>✅ Results: {metrics_str}</bold></green>")
            logger.info("")  # Empty line for visual separation

            # AICODE-NOTE: Return summary of results
            return {
                "generated_article": generated_article,
                "numeric_metrics": numeric_metrics_result,
                "content_judge": content_judge_result,
                "style_judge": style_judge_result
            }

        except Exception as e:
            # AICODE-NOTE: T086 - Error recovery: log error, return None, continue
            logger.exception(f"Failed to evaluate case {case_path}: {e}")
            return None

    def run_evaluation(
        self,
        author_filter: Optional[str] = None,
        perfect_test: bool = False
    ) -> Dict[str, Any]:
        """Run evaluation on all test cases in dataset.

        Args:
            author_filter: Optional author name to filter cases
            perfect_test: If True, use source texts for author baseline comparison

        Returns:
            Dict with summary of evaluation results

        AICODE-NOTE: T085 - Main loop with tqdm progress tracking per author
        AICODE-NOTE: Iterates all test cases, handles errors per case
        AICODE-NOTE: T117 - Perfect test: compares source vs ground truth (same author)
        """
        logger.info("Starting evaluation run...")

        # AICODE-NOTE: Load dataset directory
        dataset_path = Path(self.config.dataset_path)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset directory not found: {dataset_path}")

        # AICODE-NOTE: Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_base = Path(self.config.output_path) / timestamp
        output_base.mkdir(parents=True, exist_ok=True)

        logger.info(f"Output directory: {output_base}")

        # AICODE-NOTE: Find all test cases (author/case_NNN directories)
        all_cases = []
        for author_dir in sorted(dataset_path.iterdir()):
            if not author_dir.is_dir():
                continue

            # AICODE-NOTE: Apply author filter if specified
            if author_filter and author_dir.name != author_filter:
                logger.debug(f"Skipping author {author_dir.name} (filtered)")
                continue

            # AICODE-NOTE: Find all case directories for this author
            author_cases = []
            for case_dir in sorted(author_dir.iterdir()):
                if case_dir.is_dir() and case_dir.name.startswith("case_"):
                    author_cases.append(case_dir)

            if author_cases:
                all_cases.append((author_dir.name, author_cases))

        if not all_cases:
            logger.error("No test cases found in dataset")
            raise ValueError("No test cases found in dataset")

        total_cases = sum(len(cases) for _, cases in all_cases)
        logger.info(f"Found {len(all_cases)} authors, {total_cases} test cases")

        # AICODE-NOTE: Evaluate all cases with progress tracking
        results_summary = {
            "total_cases": 0,
            "successful_cases": 0,
            "failed_cases": 0,
            "timestamp": timestamp,
            "output_path": str(output_base)
        }

        for author_name, author_cases in all_cases:
            logger.info(f"Evaluating author: {author_name} ({len(author_cases)} cases)")

            # AICODE-NOTE: Progress bar per author showing "Evaluating {author}: N/M"
            with tqdm(
                total=len(author_cases),
                desc=f"Evaluating {author_name}",
                unit="case"
            ) as pbar:
                for case_dir in author_cases:
                    case_name = case_dir.name
                    output_case_path = output_base / author_name / case_name

                    # AICODE-NOTE: Bold header for each case with emoji
                    logger.info(f"<bold>📋 Processing {author_name}/{case_name}</bold>")
                    logger.info("")  # Empty line for visual separation

                    # AICODE-NOTE: Evaluate case (with error recovery)
                    result = self._evaluate_case(
                        case_path=case_dir,
                        output_path=output_case_path,
                        perfect_test=perfect_test  # AICODE-NOTE: T117 - Pass perfect test flag
                    )

                    results_summary["total_cases"] += 1

                    if result is not None:
                        results_summary["successful_cases"] += 1
                        logger.success(f"✓ {author_name}/{case_name} completed")
                    else:
                        results_summary["failed_cases"] += 1
                        logger.error(f"✗ {author_name}/{case_name} failed")

                    pbar.update(1)

        logger.success(
            f"Evaluation complete: {results_summary['successful_cases']}/{results_summary['total_cases']} cases succeeded"
        )

        return results_summary
