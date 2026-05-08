# mdscalpel

Token-efficient, section-aware Markdown file access for AI workflows.

## The problem

When an AI tool needs to edit one section of a 5,000-word Markdown file, it typically loads the entire file into context. For large structured documents — course content, research notes, documentation — that's thousands of wasted tokens per operation.

**mdscalpel** inverts this: survey the structure cheaply, then read or write exactly the section you need.

```bash
# 20 tokens to see the whole map
mdscalpel notes.md headings

# 300 tokens for just the section you need
mdscalpel notes.md read "Problem / Opportunity"

# Replace it in place — diff preview before any write commits
echo "Updated content." | mdscalpel notes.md write "Problem / Opportunity"
```

## Install

```bash
pip install mdscalpel
```

## CLI usage

```bash
# List all headings with line numbers
mdscalpel FILE headings
mdscalpel FILE headings --level 2          # filter by level

# Read a section
mdscalpel FILE read "Section Name"

# Replace a section (shows diff, prompts before writing)
echo "New content." | mdscalpel FILE write "Section Name"
mdscalpel FILE write "Section Name" -y     # skip confirmation

# Append to a section
echo "- new bullet" | mdscalpel FILE append "Section Name"

# Read front matter
mdscalpel FILE frontmatter                 # all keys
mdscalpel FILE frontmatter updated         # one key

# Set a front matter key
mdscalpel FILE set-frontmatter updated 2026-05-08
```

## Python API

```python
from mdscalpel import MdScalpel

doc = MdScalpel("notes.md")

# Survey structure
doc.headings()               # [{"text": "...", "level": 2, "line": 14}, ...]
doc.headings(level=2)        # filter by level

# Read
doc.read("Hypothesis")       # returns section content as string

# Write (diff preview + confirmation by default)
doc.write("Hypothesis", "New content.\n")
doc.write("Hypothesis", "New content.\n", confirm=False)  # skip prompt

# Append
doc.append("Data / Insights", "- new finding\n")

# Front matter
doc.frontmatter()                              # {"type": "idea", ...}
doc.set_frontmatter("updated", "2026-05-08")
```

## How section boundaries work

A section runs from its heading line to the next heading at the same or higher level (lower `#` count). Reading `## Beta` in this file:

```markdown
## Alpha
...
## Beta
Beta content.
### Beta Child
Child content.
## Gamma
...
```

returns `Beta content.\n### Beta Child\nChild content.\n` — Beta and all its children, stopping before Gamma. Writing to `## Beta` leaves Alpha and Gamma untouched.

## Diff preview

Every write operation prints a unified diff and prompts for confirmation before touching the file. Pass `-y` (CLI) or `confirm=False` (API) to skip.

## License

MIT
