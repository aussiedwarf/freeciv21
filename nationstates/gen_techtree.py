#!/usr/bin/env python3
"""Parse techs.ruleset and generate a Mermaid tech tree diagram and table."""

import re
from pathlib import Path


def parse_techs(ruleset_path):
    """Parse techs.ruleset and return list of tech dicts.

    Each dict has keys: name, req1, req2, year, wiki_url.
    Year and wiki_url come from comment lines like:
        ; 1799 - https://en.wikipedia.org/wiki/Aerodynamics
    """
    text = ruleset_path.read_text()
    techs = []

    # Build a map from section header position to (year, wiki_url)
    # by finding comment lines that precede [advance_*] headers.
    comment_map = {}
    for m in re.finditer(
        r'; (\d{4}) - (https://\S+)\s*\n\[advance_\w+\]', text
    ):
        # Map the start of the [advance_*] header to (year, url)
        header_start = text.index('[advance_', m.start())
        comment_map[header_start] = (m.group(1), m.group(2))

    # Split into sections by [advance_*] headers, tracking positions
    for m in re.finditer(r'\[advance_\w+\]', text):
        # Find the end of this section (next header or end of file)
        next_header = re.search(r'\[advance_\w+\]', text[m.end():])
        if next_header:
            section = text[m.end():m.end() + next_header.start()]
        else:
            section = text[m.end():]

        name_match = re.search(r'name\s*=\s*_\("(?:\?tech:)?(.+?)"\)', section)
        req1_match = re.search(r'req1\s*=\s*"(.+?)"', section)
        req2_match = re.search(r'req2\s*=\s*"(.+?)"', section)

        if name_match:
            year, wiki_url = comment_map.get(m.start(), ("", ""))
            techs.append({
                "name": name_match.group(1),
                "req1": req1_match.group(1) if req1_match else "None",
                "req2": req2_match.group(1) if req2_match else "None",
                "year": year,
                "wiki_url": wiki_url,
            })

    return techs


def sanitize_id(name):
    """Convert a tech name to a valid Mermaid node ID."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)


def generate_mermaid(techs):
    """Generate Mermaid flowchart from tech list."""
    lines = ["flowchart LR"]

    # Collect all tech names for node declarations
    all_names = {t["name"] for t in techs}

    # Node declarations with readable labels
    for name in sorted(all_names):
        sid = sanitize_id(name)
        lines.append(f"    {sid}[\"{name}\"]")

    lines.append("")

    # Edges: requirement --> tech
    for t in sorted(techs, key=lambda t: t["name"]):
        tid = sanitize_id(t["name"])
        for req in (t["req1"], t["req2"]):
            if req not in ("None", "Never"):
                lines.append(f"    {sanitize_id(req)} --> {tid}")

    return "\n".join(lines)


def generate_table(techs):
    """Generate a markdown table of all technologies."""
    lines = [
        "| Technology | Requires | Year | Wikipedia |",
        "|---|---|---|---|",
    ]

    def sort_key(t):
        # Techs with year first (sorted by year), then without (alphabetical)
        if t["year"]:
            return (0, int(t["year"]), t["name"])
        return (1, 0, t["name"])

    for t in sorted(techs, key=sort_key):
        reqs = [r for r in (t["req1"], t["req2"]) if r not in ("None", "Never")]
        reqs_str = ", ".join(reqs) if reqs else ""
        year_str = t["year"]
        wiki_str = f"[Link]({t['wiki_url']})" if t["wiki_url"] else ""
        lines.append(f"| {t['name']} | {reqs_str} | {year_str} | {wiki_str} |")

    return "\n".join(lines)


def main():
    script_dir = Path(__file__).resolve().parent
    ruleset_path = script_dir / ".." / "data" / "nationstates" / "techs.ruleset"
    output_path = script_dir / "techtree.md"

    techs = parse_techs(ruleset_path)
    mermaid = generate_mermaid(techs)
    table = generate_table(techs)

    output_path.write_text(
        f"# Nation States Tech Tree\n\n"
        f"```mermaid\n{mermaid}\n```\n\n"
        f"## Technology Reference\n\n{table}\n"
    )
    print(f"Generated {output_path} with {len(techs)} techs")


if __name__ == "__main__":
    main()
