# AICODE-NOTE: T079 - EvaluationRunner class - Main evaluation orchestrator
# AICODE-NOTE: Implements complete pipeline: load case → generate → compute metrics → save
# AICODE-NOTE: T085 - Main loop with tqdm progress tracking per author

"""Main evaluation runner for StyleGuard eval harness."""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from loguru import logger
from tqdm import tqdm

from src.evaluator.config import EvalConfig, NumericMetrics
from src.evaluator.integration import UglyScriptAdapter
from src.evaluator.metrics.numeric import NumericMetrics as NumericMetricsComputer
from src.evaluator.metrics.judge import JudgeEvaluator


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
        logger.debug(f"Loading test case from {case_path}")

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

        logger.success(f"Loaded test case: {len(source_texts)} chars source, {len(ground_truth_article)} chars ground truth")

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
        """
        # AICODE-NOTE: Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # AICODE-NOTE: Save generated article
        generated_file = output_path / "generated_article.txt"
        generated_file.write_text(generated_article, encoding="utf-8")
        logger.debug(f"Saved generated article: {generated_file}")

        # AICODE-NOTE: Save numeric metrics (if available)
        if numeric_metrics is not None:
            metrics_file = output_path / "metrics_numeric.json"
            with open(metrics_file, 'w', encoding="utf-8") as f:
                json.dump(numeric_metrics.model_dump(mode='json'), f, indent=2)
            logger.debug(f"Saved numeric metrics: {metrics_file}")

        # AICODE-NOTE: Save content judge result (if available)
        if content_judge is not None:
            content_file = output_path / "metrics_judge_content.json"
            with open(content_file, 'w', encoding="utf-8") as f:
                json.dump(content_judge.model_dump(mode='json'), f, indent=2)
            logger.debug(f"Saved content judge: {content_file}")

        # AICODE-NOTE: Save style judge result (if available)
        if style_judge is not None:
            style_file = output_path / "metrics_judge_style.json"
            with open(style_file, 'w', encoding="utf-8") as f:
                json.dump(style_judge.model_dump(mode='json'), f, indent=2)
            logger.debug(f"Saved style judge: {style_file}")

        logger.success(f"Saved all results to {output_path}")

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
            perfect_test: If True, use ground truth as generated output (no generation)

        Returns:
            Dict with evaluation results, or None on failure

        AICODE-NOTE: T082 - Implements full pipeline: load → generate → compute → save
        AICODE-NOTE: T086 - Error recovery to continue on failures
        AICODE-NOTE: T117 - Perfect test mode support for baseline calibration
        """
        try:
            # AICODE-NOTE: Step 1 - Load test case
            case_data = self._load_test_case(case_path)

            # AICODE-NOTE: T118 - Step 2 - Generate article OR use ground truth (perfect test mode)
            if perfect_test:
                # AICODE-NOTE: Perfect test mode - copy ground truth as generated output
                logger.info("Perfect test mode: using ground truth as generated article")
                generated_article = case_data["ground_truth_article"]
                logger.success(f"Using ground truth: {len(generated_article)} chars")
            else:
                # AICODE-NOTE: Normal mode - Generate article using UglyScriptAdapter
                logger.info("Generating article...")
                generated_article = self.adapter.generate_article(
                    source_texts=case_data["source_texts"],
                    topic_data=case_data["topic_data"]
                )

                if not generated_article or not generated_article.strip():
                    logger.error("Generated article is empty")
                    return None

                logger.success(f"Generated article: {len(generated_article)} chars")

            # AICODE-NOTE: Step 3 - Compute metrics (conditionally based on config)
            numeric_metrics_result = None
            content_judge_result = None
            style_judge_result = None

            # AICODE-NOTE: T083 - Conditional metric computation based on config
            # Numeric metrics
            if self.numeric_metrics is not None:
                logger.info("Computing numeric metrics...")

                cosine_result = None
                bert_result = None

                # AICODE-NOTE: Compute cosine similarity if enabled
                if self.config.metrics_numeric.get("cosine_similarity", False):
                    try:
                        logger.debug("Computing cosine similarity...")
                        cosine_result = self.numeric_metrics.compute_cosine_similarity(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                        if cosine_result:
                            logger.success(f"Cosine similarity: {cosine_result.score:.3f}")
                    except Exception as e:
                        logger.warning(f"Cosine similarity failed: {e}")
                else:
                    logger.info("Cosine similarity disabled in config")

                # AICODE-NOTE: Compute BERTScore if enabled
                if self.config.metrics_numeric.get("bert_score", False):
                    try:
                        logger.debug("Computing BERTScore...")
                        bert_result = self.numeric_metrics.compute_bert_score(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                        if bert_result:
                            logger.success(f"BERTScore F1: {bert_result.f1:.3f}")
                    except Exception as e:
                        logger.warning(f"BERTScore failed: {e}")
                else:
                    logger.info("BERTScore disabled in config")

                # AICODE-NOTE: Create NumericMetrics object if any metric succeeded
                if cosine_result or bert_result:
                    numeric_metrics_result = NumericMetrics(
                        cosine_similarity=cosine_result,
                        bert_score=bert_result
                    )

            # Judge evaluations
            if self.judge_evaluator is not None:
                logger.info("Computing judge evaluations...")

                # AICODE-NOTE: Content judge if enabled
                if self.config.metrics_judge.get("content_judge", False):
                    try:
                        logger.debug("Evaluating content accuracy...")
                        content_judge_result = self.judge_evaluator.evaluate_content(
                            generated_article,
                            case_data["ground_truth_article"]
                        )
                        if content_judge_result:
                            logger.success(f"Content score: {content_judge_result.score}/5")
                    except Exception as e:
                        logger.warning(f"Content judge failed: {e}")
                else:
                    logger.info("Content judge disabled in config")

                # AICODE-NOTE: Style judge if enabled
                if self.config.metrics_judge.get("style_judge", False):
                    try:
                        logger.debug("Evaluating style fidelity...")
                        style_judge_result = self.judge_evaluator.evaluate_style(
                            generated_article,
                            case_data["source_texts"]
                        )
                        if style_judge_result:
                            logger.success(f"Style score: {style_judge_result.score}/5")
                    except Exception as e:
                        logger.warning(f"Style judge failed: {e}")
                else:
                    logger.info("Style judge disabled in config")

            # AICODE-NOTE: Step 4 - Save results
            self._save_case_results(
                output_path=output_path,
                generated_article=generated_article,
                numeric_metrics=numeric_metrics_result,
                content_judge=content_judge_result,
                style_judge=style_judge_result
            )

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
            perfect_test: If True, use ground truth as generated output

        Returns:
            Dict with summary of evaluation results

        AICODE-NOTE: T085 - Main loop with tqdm progress tracking per author
        AICODE-NOTE: Iterates all test cases, handles errors per case
        AICODE-NOTE: T117 - Perfect test mode support
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

                    logger.info(f"Processing {author_name}/{case_name}")

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
