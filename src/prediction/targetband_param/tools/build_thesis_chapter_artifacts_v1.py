from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARCHIVED_SCRIPT = (
    ROOT
    / "archive"
    / "oneoff_thesis_scripts"
    / "encoding_damaged"
    / "build_thesis_chapter_artifacts_v1.py"
)


def main() -> None:
    message = (
        "The old thesis chapter artifact builder was archived because its "
        "Chinese figure labels were encoding-damaged and the script no longer "
        "compiled reliably. Use the public figure/report wrappers under "
        "scripts/make_figures/ and the result indexes under docs/reproducibility/ "
        "for the final public workflow.\n\n"
        f"Archived historical script: {ARCHIVED_SCRIPT}"
    )
    print(message)


if __name__ == "__main__":
    main()
