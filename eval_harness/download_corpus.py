#!/usr/bin/env python3
"""
Download real texts from Project Gutenberg via Hugging Face datasets.
Selects 10 texts per author for evaluation corpus.
"""

from datasets import load_dataset
from pathlib import Path
import re
from collections import defaultdict

# Target authors with many works
TARGET_AUTHORS = [
    "Mark Twain",
    "Charles Dickens",
    "Jane Austen",
    "Edgar Allan Poe",
    "Oscar Wilde"
]

def clean_author_name(author: str) -> str:
    """Convert author name to directory-safe format."""
    # Remove dates like "(1835-1910)"
    author = re.sub(r'\s*\(\d{4}-\d{4}\)', '', author)
    # Convert to lowercase, replace spaces with underscores
    author = author.lower().replace(' ', '_').replace(',', '').replace('.', '')
    return author

def download_gutenberg_corpus(output_dir: Path, texts_per_author: int = 10):
    """Download Project Gutenberg texts for specified authors."""

    print("Loading Project Gutenberg dataset from Hugging Face...")
    print("This may take a few minutes on first run...")

    # Load dataset (streaming to avoid downloading everything)
    dataset = load_dataset("manu/project_gutenberg", split="train", streaming=True)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Track texts per author
    author_texts = defaultdict(list)
    authors_found = set()

    print(f"\nSearching for texts by: {', '.join(TARGET_AUTHORS)}")
    print(f"Need {texts_per_author} texts per author\n")

    # Iterate through dataset
    for idx, item in enumerate(dataset):
        # Progress indicator
        if idx % 1000 == 0:
            print(f"Processed {idx} texts... Found authors: {len(authors_found)}/{len(TARGET_AUTHORS)}")

        # Check if we've found all authors
        if len(authors_found) == len(TARGET_AUTHORS):
            all_complete = all(
                len(author_texts[clean_author_name(author)]) >= texts_per_author
                for author in TARGET_AUTHORS
            )
            if all_complete:
                print("\n✅ All authors complete!")
                break

        # Check author
        author = item.get('author', '').strip()
        if not author or author not in TARGET_AUTHORS:
            continue

        author_key = clean_author_name(author)

        # Skip if we have enough texts for this author
        if len(author_texts[author_key]) >= texts_per_author:
            continue

        # Get text
        text = item.get('text', '').strip()
        if not text or len(text) < 1000:  # Skip very short texts
            continue

        # Truncate very long texts (keep first 10000 chars)
        if len(text) > 10000:
            text = text[:10000]

        # Save text
        author_dir = output_dir / author_key
        author_dir.mkdir(exist_ok=True)

        text_num = len(author_texts[author_key]) + 1
        text_file = author_dir / f"text_{text_num:03d}.txt"

        text_file.write_text(text, encoding='utf-8')
        author_texts[author_key].append(text_file)

        if len(author_texts[author_key]) == 1:
            authors_found.add(author)
            print(f"✓ Found first text for {author}")

        if len(author_texts[author_key]) == texts_per_author:
            print(f"✅ Completed {author}: {texts_per_author} texts")

    # Summary
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)
    for author in TARGET_AUTHORS:
        author_key = clean_author_name(author)
        count = len(author_texts[author_key])
        status = "✅" if count >= texts_per_author else "⚠️"
        print(f"{status} {author}: {count}/{texts_per_author} texts")
    print(f"\nCorpus saved to: {output_dir}")
    print("="*60)

if __name__ == "__main__":
    corpus_dir = Path("./corpus")
    download_gutenberg_corpus(corpus_dir, texts_per_author=10)
