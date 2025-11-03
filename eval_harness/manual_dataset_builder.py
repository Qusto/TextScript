#!/usr/bin/env python3
"""
Manual dataset builder without API calls - for testing in restricted regions.
Creates eval dataset by manually selecting texts and creating simple topics.
"""

from pathlib import Path
import json
import random

def create_manual_dataset(corpus_dir: Path, output_dir: Path, authors=None, k_cases=3):
    """Create dataset manually without API calls."""
    
    if authors is None:
        authors = ["mark_twain", "charles_dickens"]  # Just 2 authors for quick test
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Creating manual dataset: {len(authors)} authors × {k_cases} cases")
    
    for author in authors:
        author_corpus = corpus_dir / author
        if not author_corpus.exists():
            print(f"⚠️  Skipping {author} - not found")
            continue
            
        texts = sorted(author_corpus.glob("*.txt"))
        if len(texts) < k_cases * 2:
            print(f"⚠️  Skipping {author} - not enough texts")
            continue
        
        # Use first 3 for style, next k_cases for test
        style_texts = texts[:3]
        test_texts = texts[3:3+k_cases]
        
        author_out = output_dir / author
        
        for idx, test_text in enumerate(test_texts, 1):
            case_dir = author_out / f"case_{idx:03d}"
            case_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Combine style texts
            combined_style = ""
            for style_file in style_texts:
                combined_style += style_file.read_text(encoding='utf-8') + "\n\n"
            
            (case_dir / "source_texts.txt").write_text(combined_style, encoding='utf-8')
            
            # 2. Copy ground truth
            ground_truth = test_text.read_text(encoding='utf-8')
            (case_dir / "ground_truth_article.txt").write_text(ground_truth, encoding='utf-8')
            
            # 3. Create simple topic.json (without API)
            topic_data = {
                "topic": f"Literary work {idx} by {author.replace('_', ' ').title()}",
                "theses": [
                    "This is a classic literary work",
                    "Written in the author's distinctive style",
                    "Contains narrative elements",
                    "Features character development",
                    "Demonstrates thematic depth"
                ]
            }
            
            (case_dir / "topic.json").write_text(json.dumps(topic_data, indent=2), encoding='utf-8')
            
            print(f"✓ Created {author}/case_{idx:03d}")
    
    print(f"\n✅ Manual dataset created in {output_dir}")

if __name__ == "__main__":
    corpus = Path("./corpus")
    output = Path("./eval_dataset")
    create_manual_dataset(corpus, output, authors=["mark_twain", "charles_dickens"], k_cases=3)
