# AICODE-NOTE: T039 [P] [US1] DatasetBuilder class - main orchestrator for dataset generation
# AICODE-NOTE: T040 - Loads DatasetConfig from YAML, initializes Neutralizer
# AICODE-NOTE: T041 - Recursive directory traversal for corpus scanning
# AICODE-NOTE: T042 - Author filtering by min_texts_per_author
# AICODE-NOTE: T043 - Random split with fixed seed for reproducibility
# AICODE-NOTE: T044 - Text concatenation with newlines
# AICODE-NOTE: T045 - Case directory creation and file I/O
# AICODE-NOTE: T046 - Neutralizer error handling (log and continue)
# AICODE-NOTE: T047 - Main loop with tqdm progress bar
# AICODE-NOTE: T048 - Logging with loguru (INFO/DEBUG/WARNING levels)

"""DatasetBuilder component for generating evaluation datasets from text corpus.

This module orchestrates the dataset generation process:
1. Scan corpus directory for authors and texts
2. Filter authors by minimum text count
3. Split texts into style reference and test sets
4. Generate test cases with neutralized topics
5. Save structured dataset to output directory

Output structure:
    eval_dataset/
    └── {author_name}/
        └── case_{NNN}/
            ├── source_texts.txt      # M style reference texts
            ├── ground_truth_article.txt  # Original article
            └── topic.json            # Neutralized topic and theses
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger
from tqdm import tqdm

from src.dataset_builder.config import DatasetConfig, TopicData
from src.dataset_builder.neutralizer import Neutralizer
from src.shared.file_utils import ensure_directory, read_text_file, write_text_file
from src.shared.llm_client import LLMClient


class DatasetBuilder:
    """Build evaluation dataset from text corpus.

    AICODE-NOTE: T039 - Main orchestrator for dataset generation
    AICODE-NOTE: Implements User Story 1 from spec.md
    """

    def __init__(self, config: DatasetConfig, llm_client: LLMClient):
        """Initialize DatasetBuilder with configuration and LLM client.

        Args:
            config: DatasetConfig from YAML file
            llm_client: LLM client for neutralization

        AICODE-NOTE: T040 - Loads DatasetConfig, initializes Neutralizer
        """
        self.config = config
        self.llm_client = llm_client

        # AICODE-NOTE: Initialize Neutralizer with LLM client
        self.neutralizer = Neutralizer(
            llm_client=llm_client,
            max_tokens=config.max_tokens_for_neutralizer,
            model_id=config.neutralizer_model_id
        )

        logger.info(
            f"DatasetBuilder initialized: "
            f"corpus={config.corpus_path}, "
            f"output={config.output_path}, "
            f"min_texts={config.min_texts_per_author}, "
            f"m={config.m_style_texts}, k={config.k_test_cases}"
        )

    def scan_corpus(self) -> Dict[str, List[Path]]:
        """Scan corpus directory and discover authors with text files.

        Returns:
            Dictionary mapping author_name -> list of text file paths
            Only includes authors with >= min_texts_per_author files

        Raises:
            FileNotFoundError: If corpus directory doesn't exist

        AICODE-NOTE: T041 - Recursive directory traversal
        AICODE-NOTE: Returns dict[author_name, List[Path]]
        AICODE-NOTE: T042 - Filters by min_texts_per_author
        """
        corpus_path = Path(self.config.corpus_path)

        if not corpus_path.exists():
            raise FileNotFoundError(
                f"Corpus directory not found: {corpus_path}"
            )

        logger.info(f"Scanning corpus at {corpus_path}")

        # AICODE-NOTE: Scan for author directories
        authors: Dict[str, List[Path]] = {}

        for author_dir in corpus_path.iterdir():
            if not author_dir.is_dir():
                continue

            author_name = author_dir.name

            # AICODE-NOTE: Find all .txt files in author directory
            text_files = sorted(author_dir.glob("*.txt"))

            if len(text_files) == 0:
                logger.debug(f"Skipping {author_name}: no .txt files found")
                continue

            logger.debug(
                f"Found author: {author_name} ({len(text_files)} texts)"
            )

            # AICODE-NOTE: T042 - Filter by min_texts_per_author
            if len(text_files) < self.config.min_texts_per_author:
                logger.warning(
                    f"Skipping author '{author_name}': only {len(text_files)} texts "
                    f"found (minimum: {self.config.min_texts_per_author})"
                )
                continue

            authors[author_name] = text_files

        logger.info(
            f"Found {len(authors)} authors with >= "
            f"{self.config.min_texts_per_author} texts"
        )

        return authors

    def _split_texts(
        self,
        text_files: List[Path],
        m_style: int,
        k_test: int
    ) -> Tuple[List[Path], List[Path]]:
        """Split texts into disjoint style reference and test sets.

        Args:
            text_files: List of text file paths
            m_style: Number of texts for style reference
            k_test: Number of texts for test cases

        Returns:
            Tuple of (style_set, test_set) as lists of Paths

        AICODE-NOTE: T043 - Random split with fixed seed
        AICODE-NOTE: Returns (style_set, test_set) tuple
        AICODE-NOTE: Uses config.random_seed if set for reproducibility
        """
        # AICODE-NOTE: Set random seed if configured
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        # AICODE-NOTE: Shuffle and split
        shuffled = text_files.copy()
        random.shuffle(shuffled)

        style_set = shuffled[:m_style]
        test_set = shuffled[m_style:m_style + k_test]

        logger.debug(
            f"Split {len(text_files)} texts: "
            f"{len(style_set)} for style, {len(test_set)} for test"
        )

        return style_set, test_set

    def _combine_style_texts(self, text_files: List[Path]) -> str:
        """Combine multiple text files into single string.

        Args:
            text_files: List of text file paths to combine

        Returns:
            Combined text with files separated by newlines

        AICODE-NOTE: T044 - Concatenates M texts with newlines
        AICODE-NOTE: Returns single string
        """
        combined_parts = []

        for text_file in text_files:
            try:
                content = read_text_file(text_file)
                combined_parts.append(content)
            except Exception as e:
                logger.error(f"Failed to read {text_file}: {e}")
                continue

        # AICODE-NOTE: Join with double newlines for clear separation
        combined = "\n\n".join(combined_parts)

        logger.debug(
            f"Combined {len(text_files)} texts into {len(combined)} chars"
        )

        return combined

    def _create_case(
        self,
        author_name: str,
        case_num: int,
        style_texts: List[Path],
        ground_truth_file: Path
    ) -> None:
        """Create single test case with all required files.

        Args:
            author_name: Author identifier
            case_num: Case number (1-indexed)
            style_texts: List of style reference text files
            ground_truth_file: Ground truth article file

        AICODE-NOTE: T045 - Creates case_NNN/ dir, writes 3 files
        AICODE-NOTE: T046 - Neutralizer API call with error handling
        """
        # AICODE-NOTE: Create case directory
        case_dir = (
            Path(self.config.output_path) /
            author_name /
            f"case_{case_num:03d}"
        )
        ensure_directory(case_dir)

        logger.debug(f"Creating case {case_dir}")

        try:
            # AICODE-NOTE: 1. Combine and save source texts
            source_texts = self._combine_style_texts(style_texts)
            write_text_file(case_dir / "source_texts.txt", source_texts)

            # AICODE-NOTE: 2. Copy ground truth article
            ground_truth = read_text_file(ground_truth_file)
            write_text_file(case_dir / "ground_truth_article.txt", ground_truth)

            # AICODE-NOTE: 3. Neutralize and save topic
            # AICODE-NOTE: T046 - Error handling for API failure
            try:
                topic_data = self.neutralizer.neutralize(ground_truth)

                topic_json = json.dumps(
                    topic_data.model_dump(),
                    indent=2,
                    ensure_ascii=False
                )
                write_text_file(case_dir / "topic.json", topic_json)

                logger.info(f"Case {case_num:03d} complete: {case_dir}")

            except Exception as e:
                # AICODE-NOTE: Log error but don't crash entire generation
                logger.error(
                    f"Failed to neutralize case {case_num:03d} for {author_name}: {e}"
                )
                logger.warning(
                    f"Continuing with next case (case {case_num:03d} incomplete)"
                )

                # AICODE-NOTE: Don't raise - allow partial dataset generation
                # Missing topic.json will be obvious during dataset usage

        except Exception as e:
            logger.error(
                f"Failed to create case {case_num:03d} for {author_name}: {e}"
            )
            # AICODE-NOTE: Continue to next case even if this one fails

    def generate_dataset(self) -> None:
        """Generate complete evaluation dataset from corpus.

        Main entry point that orchestrates the entire process:
        1. Scan corpus for authors
        2. For each author:
           a. Split texts into style and test sets
           b. Generate k test cases
           c. Create all required files

        AICODE-NOTE: T047 - Main loop with tqdm progress bar
        AICODE-NOTE: Iterates authors with progress tracking
        AICODE-NOTE: Calls _split_texts() and _create_case() for each
        AICODE-NOTE: T048 - Logging at INFO/DEBUG/WARNING levels
        """
        logger.info("Starting dataset generation")

        # AICODE-NOTE: Scan corpus
        try:
            authors = self.scan_corpus()
        except FileNotFoundError as e:
            logger.error(f"Corpus scan failed: {e}")
            raise

        if len(authors) == 0:
            logger.error(
                f"No authors found with >= {self.config.min_texts_per_author} texts"
            )
            raise ValueError("No qualifying authors found in corpus")

        # AICODE-NOTE: Ensure output directory exists
        ensure_directory(self.config.output_path)

        # AICODE-NOTE: Process each author with progress bar
        total_cases = 0

        for author_name, text_files in authors.items():
            logger.info(f"Processing author: {author_name}")

            # AICODE-NOTE: Split texts into style and test sets
            style_set, test_set = self._split_texts(
                text_files,
                m_style=self.config.m_style_texts,
                k_test=self.config.k_test_cases
            )

            # AICODE-NOTE: Generate k test cases with progress bar
            with tqdm(
                total=len(test_set),
                desc=f"Processing {author_name}",
                unit="case"
            ) as pbar:
                for case_idx, test_file in enumerate(test_set, start=1):
                    self._create_case(
                        author_name=author_name,
                        case_num=case_idx,
                        style_texts=style_set,
                        ground_truth_file=test_file
                    )

                    pbar.update(1)
                    total_cases += 1

        # AICODE-NOTE: Log final summary
        logger.success(
            f"Dataset generation complete! "
            f"Authors processed: {len(authors)}, "
            f"Total test cases: {total_cases}, "
            f"Output directory: {self.config.output_path}"
        )
