import pytest
from pathlib import Path
from mdscalpel import MdScalpel

FIXTURE = """\
---
type: idea
project: test
author: pytest
---

# Top

## Alpha

Alpha content line 1.
Alpha content line 2.

## Beta

Beta content.

### Beta Child

Child content.

## Gamma

Gamma content.
"""


@pytest.fixture
def md_file(tmp_path):
    f = tmp_path / "test.md"
    f.write_text(FIXTURE, encoding="utf-8")
    return f


def test_headings_all(md_file):
    doc = MdScalpel(md_file)
    texts = [h["text"] for h in doc.headings()]
    assert texts == ["Top", "Alpha", "Beta", "Beta Child", "Gamma"]


def test_headings_by_level(md_file):
    doc = MdScalpel(md_file)
    assert [h["text"] for h in doc.headings(level=2)] == ["Alpha", "Beta", "Gamma"]


def test_read_mid_section(md_file):
    doc = MdScalpel(md_file)
    content = doc.read("Alpha")
    assert "Alpha content line 1." in content
    assert "Beta" not in content


def test_read_last_section(md_file):
    doc = MdScalpel(md_file)
    content = doc.read("Gamma")
    assert "Gamma content." in content


def test_write_mid_section_preserves_neighbors(md_file):
    doc = MdScalpel(md_file)
    doc.write("Alpha", "Replaced.\n", confirm=False)
    doc2 = MdScalpel(md_file)
    assert doc2.read("Alpha").strip() == "Replaced."
    assert "Beta content." in doc2.read("Beta")
    assert "Gamma content." in doc2.read("Gamma")


def test_write_last_section(md_file):
    doc = MdScalpel(md_file)
    doc.write("Gamma", "New gamma.\n", confirm=False)
    doc2 = MdScalpel(md_file)
    assert doc2.read("Gamma").strip() == "New gamma."
    assert "Alpha content" in doc2.read("Alpha")


def test_append_section(md_file):
    doc = MdScalpel(md_file)
    doc.append("Beta", "- appended bullet\n", confirm=False)
    doc2 = MdScalpel(md_file)
    content = doc2.read("Beta")
    assert "Beta content." in content
    assert "appended bullet" in content
    assert "Gamma content." in doc2.read("Gamma")


def test_frontmatter_read(md_file):
    doc = MdScalpel(md_file)
    fm = doc.frontmatter()
    assert fm["type"] == "idea"
    assert fm["project"] == "test"


def test_write_confirm_false_does_not_read_stdin(md_file, monkeypatch):
    """confirm=False must not touch stdin — critical for piped CLI workflows."""
    stdin_read = []
    monkeypatch.setattr("sys.stdin", type("FakeStdin", (), {"read": lambda s: stdin_read.append(True) or "", "readline": lambda s: stdin_read.append(True) or ""})())
    doc = MdScalpel(md_file)
    doc.write("Alpha", "No stdin needed.\n", confirm=False)
    assert not stdin_read, "write(confirm=False) must not read from stdin"


def test_frontmatter_set(md_file):
    doc = MdScalpel(md_file)
    doc.set_frontmatter("updated", "2026-05-08", confirm=False)
    doc2 = MdScalpel(md_file)
    assert doc2.frontmatter()["updated"] == "2026-05-08"
    assert doc2.frontmatter()["type"] == "idea"
    assert "Alpha content" in doc2.read("Alpha")
