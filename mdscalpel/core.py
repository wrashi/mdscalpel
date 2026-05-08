import re
import difflib
import sys
import tempfile
from pathlib import Path


class MdScalpel:
    """Section-aware Markdown file access. Read and write individual sections
    without loading the entire file into context."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._load()

    def _load(self):
        self._lines = self.path.read_text(encoding="utf-8").splitlines(keepends=True)
        self._headings = self._parse_headings()
        self._fm_end = self._parse_frontmatter_end()

    def _parse_headings(self) -> list[dict]:
        headings = []
        in_fence = False
        for i, line in enumerate(self._lines):
            if re.match(r"^(`{3,}|~{3,})", line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = re.match(r"^(#+)\s+(.*)", line)
            if m:
                headings.append({
                    "text": m.group(2).strip(),
                    "level": len(m.group(1)),
                    "line": i,
                })
        return headings

    def _parse_frontmatter_end(self) -> int:
        """Return the line index AFTER the closing --- of YAML front matter, or 0."""
        if not self._lines or self._lines[0].strip() != "---":
            return 0
        for i in range(1, len(self._lines)):
            if self._lines[i].strip() == "---":
                return i + 1
        return 0

    def _heading_by_name(self, name: str) -> dict | None:
        for h in self._headings:
            if h["text"] == name:
                return h
        return None

    def _section_bounds(self, name: str) -> tuple[int, int]:
        """Return (start, end) line indices for the content of a named section.
        start is the line after the heading; end is exclusive (next same-or-higher heading, or EOF).
        Raises KeyError if heading not found.
        """
        h = self._heading_by_name(name)
        if h is None:
            raise KeyError(f"Heading not found: {name!r}")
        start = h["line"] + 1
        end = len(self._lines)
        for candidate in self._headings:
            if candidate["line"] > h["line"] and candidate["level"] <= h["level"]:
                end = candidate["line"]
                break
        return start, end

    def _write_atomic(self, lines: list[str]) -> None:
        """Write lines to file atomically via a temp file + rename."""
        content = "".join(lines)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            tmp.write_text(content, encoding="utf-8")
            tmp.replace(self.path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    def _confirm(self) -> bool:
        """Prompt for confirmation via /dev/tty so stdin can be a pipe."""
        try:
            with open("/dev/tty", "r+") as tty:
                tty.write("Write changes? [y/N] ")
                tty.flush()
                return tty.readline().strip().lower() == "y"
        except OSError:
            print("Write changes? [y/N] ", end="", flush=True)
            return sys.stdin.readline().strip().lower() == "y"

    # ── Public API ────────────────────────────────────────────────────────────

    def headings(self, level: int | None = None) -> list[dict]:
        """Return all headings as a list of {text, level, line} dicts."""
        if level is None:
            return list(self._headings)
        return [h for h in self._headings if h["level"] == level]

    def read(self, section: str) -> str:
        """Return the content of a named section (heading line excluded)."""
        start, end = self._section_bounds(section)
        return "".join(self._lines[start:end])

    def write(self, section: str, content: str, *, confirm: bool = True) -> bool:
        """Replace a section's content. Shows a diff and prompts before writing
        unless confirm=False. Returns True if the file was written."""
        start, end = self._section_bounds(section)
        if not content.endswith("\n"):
            content += "\n"

        new_lines = self._lines[:start] + [content] + self._lines[end:]

        if confirm:
            old = "".join(self._lines)
            new = "".join(new_lines)
            diff = list(difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=str(self.path),
                tofile=str(self.path) + " (proposed)",
            ))
            if diff:
                print("".join(diff))
            if not self._confirm():
                print("Aborted.")
                return False

        self._write_atomic(new_lines)
        self._load()
        return True

    def append(self, section: str, content: str, *, confirm: bool = True) -> bool:
        """Append content to the end of a named section."""
        existing = self.read(section).rstrip("\n")
        if not content.startswith("\n"):
            content = "\n" + content
        return self.write(section, existing + content + "\n", confirm=confirm)

    def frontmatter(self) -> dict[str, str]:
        """Return front matter as a dict of raw key: value strings."""
        if self._fm_end == 0:
            return {}
        result = {}
        for line in self._lines[1:self._fm_end - 1]:
            if ":" in line:
                key, _, value = line.partition(":")
                result[key.strip()] = value.strip()
        return result

    def set_frontmatter(self, key: str, value: str, *, confirm: bool = True) -> bool:
        """Set a front matter key. Adds the key if absent."""
        fm = self.frontmatter()
        fm[key] = value

        new_fm_lines = ["---\n"]
        for k, v in fm.items():
            new_fm_lines.append(f"{k}: {v}\n")
        new_fm_lines.append("---\n")

        new_lines = new_fm_lines + self._lines[self._fm_end:]

        if confirm:
            old = "".join(self._lines)
            new = "".join(new_lines)
            diff = list(difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=str(self.path),
                tofile=str(self.path) + " (proposed)",
            ))
            if diff:
                print("".join(diff))
            if not self._confirm():
                print("Aborted.")
                return False

        self._write_atomic(new_lines)
        self._load()
        return True
