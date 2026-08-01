import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_public_onboarding_has_no_author_machine_path():
    drive_bound = re.compile(r"\b[A-Z]:[\\/]")
    for relative_path in (
        "README.md",
        "GETTING_STARTED.md",
        "STANDALONE_USAGE.md",
        "USAGE.md",
        "RELEASE.md",
        "docs/PRODUCTION_READINESS.md",
    ):
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert not drive_bound.search(text), f"drive-bound path in {relative_path}"


def test_readme_uses_the_current_product_checkout():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "SENESCHAL-by-Ethernium" in readme
    assert "Experimentos" not in readme
