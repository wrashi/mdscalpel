"""mdscalpel CLI — section-aware Markdown access without loading the whole file."""

import argparse
import sys
from .core import MdScalpel


def cmd_headings(args):
    doc = MdScalpel(args.file)
    headings = doc.headings(level=args.level)
    for h in headings:
        print(f"{'#' * h['level']} {h['text']}  (line {h['line']})")


def cmd_read(args):
    doc = MdScalpel(args.file)
    print(doc.read(args.section), end="")


def cmd_write(args):
    doc = MdScalpel(args.file)
    content = sys.stdin.read() if args.content == "-" else args.content
    doc.write(args.section, content, confirm=not args.yes)


def cmd_append(args):
    doc = MdScalpel(args.file)
    content = sys.stdin.read() if args.content == "-" else args.content
    doc.append(args.section, content, confirm=not args.yes)


def cmd_frontmatter(args):
    doc = MdScalpel(args.file)
    if args.key is None:
        for k, v in doc.frontmatter().items():
            print(f"{k}: {v}")
    else:
        fm = doc.frontmatter()
        if args.key in fm:
            print(fm[args.key])
        else:
            print(f"Key not found: {args.key!r}", file=sys.stderr)
            sys.exit(1)


def cmd_set_frontmatter(args):
    doc = MdScalpel(args.file)
    doc.set_frontmatter(args.key, args.value, confirm=not args.yes)


def main():
    parser = argparse.ArgumentParser(
        prog="mdscalpel",
        description="Token-efficient, section-aware Markdown file access.",
    )
    parser.add_argument("file", help="Path to the Markdown file")
    sub = parser.add_subparsers(dest="command", required=True)

    # headings
    p = sub.add_parser("headings", help="List all headings")
    p.add_argument("--level", type=int, default=None, help="Filter by heading level")
    p.set_defaults(func=cmd_headings)

    # read
    p = sub.add_parser("read", help="Print the content of a named section")
    p.add_argument("section", help="Exact heading text")
    p.set_defaults(func=cmd_read)

    # write
    p = sub.add_parser("write", help="Replace a section's content (reads from stdin if content is -)")
    p.add_argument("section", help="Exact heading text")
    p.add_argument("content", nargs="?", default="-", help="New content (default: stdin)")
    p.add_argument("-y", "--yes", action="store_true", help="Skip diff confirmation")
    p.set_defaults(func=cmd_write)

    # append
    p = sub.add_parser("append", help="Append content to a section (reads from stdin if content is -)")
    p.add_argument("section", help="Exact heading text")
    p.add_argument("content", nargs="?", default="-", help="Content to append (default: stdin)")
    p.add_argument("-y", "--yes", action="store_true", help="Skip diff confirmation")
    p.set_defaults(func=cmd_append)

    # frontmatter
    p = sub.add_parser("frontmatter", help="Read front matter")
    p.add_argument("key", nargs="?", default=None, help="Specific key to read (omit for all)")
    p.set_defaults(func=cmd_frontmatter)

    # set-frontmatter
    p = sub.add_parser("set-frontmatter", help="Set a front matter key")
    p.add_argument("key")
    p.add_argument("value")
    p.add_argument("-y", "--yes", action="store_true", help="Skip diff confirmation")
    p.set_defaults(func=cmd_set_frontmatter)

    args = parser.parse_args()
    try:
        args.func(args)
    except KeyError as e:
        print(f"error: heading not found — {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
