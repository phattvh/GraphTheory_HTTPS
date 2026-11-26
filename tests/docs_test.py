"""Automated documentation integrity tests for GraphTheory_HTTPS.

Verifies:
1. Required open-source governance and index files exist and are non-empty.
2. Every documentation file in docs/ is indexed in docs/README.md.
3. Every relative Markdown link/image in root docs and docs/*.md resolves to an existing path.
4. Every test suite in tests/*_test.py is wired into Makefile.
"""

from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT_DIR / "docs"
TESTS_DIR = ROOT_DIR / "tests"

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "Makefile",
    "LICENSE",
    "docs/README.md",
]

ROOT_MARKDOWN_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "CHANGELOG.md",
]

FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_SCHEMES = ("http://", "https://", "mailto:", "tel:", "file://")


def strip_fenced_code(text: str) -> str:
    return FENCED_CODE_RE.sub("", text)


def extract_relative_targets(md_text: str) -> list[str]:
    targets: list[str] = []
    cleaned = strip_fenced_code(md_text)
    for raw_target in MARKDOWN_LINK_RE.findall(cleaned):
        target = raw_target.strip()
        if not target or target.startswith("#"):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1].strip()
        if any(target.startswith(scheme) for scheme in EXTERNAL_SCHEMES):
            continue
        # Strip optional markdown link title: path/to/file.md "title"
        if ' "' in target:
            target = target.split(' "', 1)[0].strip()
        elif " '" in target:
            target = target.split(" '", 1)[0].strip()
        # Strip anchor fragment
        path_part = target.split("#", 1)[0].strip()
        if not path_part:
            continue
        targets.append(unquote(path_part))
    return targets


def test_required_files_exist() -> None:
    missing = []
    empty = []
    for rel_path in REQUIRED_FILES:
        file_path = ROOT_DIR / rel_path
        if not file_path.is_file():
            missing.append(rel_path)
        elif file_path.stat().st_size == 0:
            empty.append(rel_path)

    assert not missing, f"Missing required files: {missing}"
    assert not empty, f"Empty required files: {empty}"
    print(f"[PASS] All {len(REQUIRED_FILES)} required OSS & docs files exist and are non-empty.")


def test_docs_index_covers_all_docs() -> None:
    index_path = DOCS_DIR / "README.md"
    index_text = index_path.read_text(encoding="utf-8")
    linked_names = {
        (DOCS_DIR / target).resolve().name
        for target in extract_relative_targets(index_text)
    }

    doc_files = sorted(
        p.name for p in DOCS_DIR.glob("*.md") if p.name != "README.md"
    )
    unindexed = [name for name in doc_files if name not in linked_names]
    assert not unindexed, f"docs/README.md is missing links to: {unindexed}"
    print(f"[PASS] docs/README.md indexes all {len(doc_files)} documentation files.")


def test_no_broken_relative_markdown_links() -> None:
    md_files = [ROOT_DIR / name for name in ROOT_MARKDOWN_FILES]
    md_files.extend(sorted(DOCS_DIR.glob("*.md")))

    broken: list[str] = []
    checked_links = 0

    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        for target in extract_relative_targets(text):
            checked_links += 1
            resolved = (md_file.parent / target).resolve()
            if not resolved.exists():
                rel_src = md_file.relative_to(ROOT_DIR)
                broken.append(f"{rel_src} -> {target}")

    assert not broken, "Broken relative Markdown links found:\n  - " + "\n  - ".join(broken)
    print(
        f"[PASS] Verified {checked_links} relative Markdown links across "
        f"{len(md_files)} files (0 broken)."
    )


def test_makefile_registers_all_tests() -> None:
    makefile_text = (ROOT_DIR / "Makefile").read_text(encoding="utf-8")
    test_files = sorted(p.name for p in TESTS_DIR.glob("*_test.py"))
    unregistered = [
        f"tests/{name}"
        for name in test_files
        if f"tests/{name}" not in makefile_text
    ]
    assert not unregistered, (
        f"Test suites not registered in Makefile: {unregistered}"
    )
    print(f"[PASS] All {len(test_files)} test suites in tests/ are registered in Makefile.")


def main() -> int:
    test_required_files_exist()
    test_docs_index_covers_all_docs()
    test_no_broken_relative_markdown_links()
    test_makefile_registers_all_tests()
    print("ALL DOCS INTEGRITY TESTS PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
