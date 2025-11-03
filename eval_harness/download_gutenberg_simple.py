#!/usr/bin/env python3
"""
Download specific texts from Project Gutenberg for evaluation corpus.
Downloads 10 texts per author (50 texts total).
"""

import requests
from pathlib import Path
import time

# Конкретные произведения из Project Gutenberg (ID)
CORPUS = {
    "mark_twain": [
        (74, "The Adventures of Tom Sawyer"),
        (76, "Adventures of Huckleberry Finn"),
        (86, "The Prince and the Pauper"),
        (119, "A Connecticut Yankee in King Arthur's Court"),
        (142, "The Innocents Abroad"),
        (245, "Life on the Mississippi"),
        (1837, "The Gilded Age"),
        (3176, "The Man That Corrupted Hadleyburg"),
        (3250, "The $30,000 Bequest"),
        (3186, "The Million Pound Bank Note"),
    ],
    "charles_dickens": [
        (98, "A Tale of Two Cities"),
        (730, "Oliver Twist"),
        (766, "David Copperfield"),
        (786, "The Pickwick Papers"),
        (1023, "Bleak House"),
        (1400, "Great Expectations"),
        (580, "A Christmas Carol"),
        (564, "Hard Times"),
        (967, "Our Mutual Friend"),
        (1394, "Little Dorrit"),
    ],
    "jane_austen": [
        (1342, "Pride and Prejudice"),
        (121, "Northanger Abbey"),
        (141, "Mansfield Park"),
        (158, "Emma"),
        (161, "Sense and Sensibility"),
        (105, "Persuasion"),
        (1212, "Love and Freindship [sic]"),
        (946, "Lady Susan"),
        (42078, "The Watsons"),
        (31100, "Sanditon"),
    ],
    "edgar_allan_poe": [
        (2147, "The Raven"),
        (2148, "The Murders in the Rue Morgue"),
        (2149, "The Gold-Bug"),
        (2150, "The Fall of the House of Usher"),
        (2151, "The Masque of the Red Death"),
        (2152, "The Cask of Amontillado"),
        (932, "The Tell-Tale Heart"),
        (1063, "The Black Cat"),
        (1064, "The Pit and the Pendulum"),
        (2038, "The Bells"),
    ],
    "oscar_wilde": [
        (174, "The Picture of Dorian Gray"),
        (844, "The Importance of Being Earnest"),
        (902, "The Happy Prince"),
        (773, "The Canterville Ghost"),
        (885, "Lady Windermere's Fan"),
        (790, "An Ideal Husband"),
        (301, "The Ballad of Reading Gaol"),
        (14522, "Lord Arthur Savile's Crime"),
        (1057, "The Soul of Man"),
        (854, "De Profundis"),
    ],
}

def download_text(gutenberg_id: int, output_file: Path) -> bool:
    """Download a single text from Project Gutenberg."""

    # Try different encodings
    encodings_to_try = ['utf-8', 'iso-8859-1', 'windows-1252']

    for encoding in encodings_to_try:
        url = f"https://www.gutenberg.org/files/{gutenberg_id}/{gutenberg_id}-0.txt"

        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Strip Project Gutenberg header/footer
                text = response.text

                # Find start of actual content (after the header)
                start_markers = [
                    "*** START OF",
                    "***START OF",
                ]
                start_pos = 0
                for marker in start_markers:
                    pos = text.find(marker)
                    if pos != -1:
                        # Skip the marker line
                        start_pos = text.find('\n', pos) + 1
                        break

                # Find end of content (before footer)
                end_markers = [
                    "*** END OF",
                    "***END OF",
                    "End of Project Gutenberg",
                ]
                end_pos = len(text)
                for marker in end_markers:
                    pos = text.find(marker, start_pos)
                    if pos != -1:
                        end_pos = pos
                        break

                clean_text = text[start_pos:end_pos].strip()

                # Save text
                output_file.write_text(clean_text, encoding='utf-8')
                return True

        except Exception:
            pass

        # Try alternative URL format
        url = f"https://www.gutenberg.org/cache/epub/{gutenberg_id}/pg{gutenberg_id}.txt"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                output_file.write_text(response.text, encoding='utf-8')
                return True
        except Exception:
            pass

    return False

def download_corpus(corpus_dir: Path):
    """Download all texts in the corpus."""

    corpus_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("DOWNLOADING PROJECT GUTENBERG CORPUS")
    print("="*60)
    print(f"Target: {len(CORPUS)} authors × 10 texts = {sum(len(texts) for texts in CORPUS.values())} texts")
    print(f"Output: {corpus_dir}")
    print("="*60)
    print()

    total_downloaded = 0
    total_failed = 0

    for author, texts in CORPUS.items():
        print(f"\n📚 {author.replace('_', ' ').title()}")
        print("-" * 40)

        author_dir = corpus_dir / author
        author_dir.mkdir(exist_ok=True)

        for idx, (gutenberg_id, title) in enumerate(texts, 1):
            output_file = author_dir / f"text_{idx:03d}.txt"

            if output_file.exists():
                print(f"  ✓ {idx:2d}. {title[:40]:<40} (cached)")
                total_downloaded += 1
                continue

            print(f"  ⬇ {idx:2d}. {title[:40]:<40} ", end="", flush=True)

            if download_text(gutenberg_id, output_file):
                file_size = output_file.stat().st_size
                print(f"✓ ({file_size:,} bytes)")
                total_downloaded += 1
                time.sleep(0.5)  # Be nice to the server
            else:
                print(f"✗ FAILED")
                total_failed += 1

    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE")
    print("="*60)
    print(f"✅ Downloaded: {total_downloaded}")
    print(f"❌ Failed: {total_failed}")
    print(f"📁 Location: {corpus_dir.absolute()}")
    print("="*60)

if __name__ == "__main__":
    corpus_dir = Path("./corpus")
    download_corpus(corpus_dir)
