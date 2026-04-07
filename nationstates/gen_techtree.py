#!/usr/bin/env python3
"""Parse rulesets and generate a Mermaid tech tree diagram, plus unit and building tables."""

import re
from collections import defaultdict
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
        r'; (-?\d+) - (https://\S+)\s*\n\[advance_\w+\]', text
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


def parse_units(ruleset_path):
    """Parse units.ruleset and return list of unit dicts.

    Each dict has keys: name, class, tech_req, obsolete_by, attack, defense,
    hitpoints, firepower, move_rate, build_cost, pop_cost, transport_cap, fuel,
    year, wiki_url.
    Year and wiki_url come from comment lines like:
        ; 1893 - https://en.wikipedia.org/wiki/HMS_Havock_(1893)
    """
    text = ruleset_path.read_text()
    units = []

    # Build a map from section header position to (year, wiki_url)
    comment_map = {}
    for cm in re.finditer(
        r'; (-?\d+) - (https://\S+)\s*\n\[unit_\w+\]', text
    ):
        header_start = text.index('[unit_', cm.start())
        comment_map[header_start] = (cm.group(1), cm.group(2))

    headers = list(re.finditer(r'\[unit_\w+\]', text))
    for i, m in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[m.end():end]

        name_match = re.search(r'name\s*=\s*_\("(?:\?unit:)?(.+?)"\)', section)
        if not name_match:
            continue

        def get_str(field):
            match = re.search(rf'{field}\s*=\s*"(.+?)"', section)
            return match.group(1) if match else "None"

        def get_int(field):
            match = re.search(rf'{field}\s*=\s*(\d+)', section)
            return int(match.group(1)) if match else 0

        # Parse combat bonuses (e.g. anti-air first strikes, defense dividers)
        bonuses = []
        bonuses_match = re.search(
            r'bonuses\s*=\s*\{([^}]*)\}', section, re.DOTALL
        )
        if bonuses_match:
            for bm in re.finditer(
                r'"(\w+)",\s*"(\w+)",\s*(\d+)',
                bonuses_match.group(1)
            ):
                bonuses.append({
                    "flag": bm.group(1),
                    "type": bm.group(2),
                    "value": int(bm.group(3)),
                })

        year, wiki_url = comment_map.get(m.start(), ("", ""))
        units.append({
            "name": name_match.group(1),
            "class": get_str("class"),
            "tech_req": get_str("tech_req"),
            "obsolete_by": get_str("obsolete_by"),
            "attack": get_int("attack"),
            "defense": get_int("defense"),
            "hitpoints": get_int("hitpoints"),
            "firepower": get_int("firepower"),
            "first_strikes": get_int("first_strikes"),
            "move_rate": get_int("move_rate"),
            "build_cost": get_int("build_cost"),
            "pop_cost": get_int("pop_cost"),
            "transport_cap": get_int("transport_cap"),
            "fuel": get_int("fuel"),
            "bonuses": bonuses,
            "year": year,
            "wiki_url": wiki_url,
        })

    return units


def parse_buildings(ruleset_path):
    """Parse buildings.ruleset and return list of building dicts."""
    text = ruleset_path.read_text()
    buildings = []

    headers = list(re.finditer(r'\[building_\w+\]', text))
    for i, m in enumerate(headers):
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        section = text[m.end():end]

        name_match = re.search(r'name\s*=\s*_\("(.+?)"\)', section)
        if not name_match:
            continue

        genus_match = re.search(r'genus\s*=\s*"(.+?)"', section)
        cost_match = re.search(r'build_cost\s*=\s*(\d+)', section)
        upkeep_match = re.search(r'upkeep\s*=\s*(\d+)', section)

        # Extract tech requirements from reqs block
        tech_reqs = []
        reqs_match = re.search(r'reqs\s*=\s*\{([^}]*)\}', section)
        if reqs_match:
            for tm in re.finditer(
                r'"Tech",\s*"([^"]+)",\s*"[^"]+"(?:,\s*(\w+))?',
                reqs_match.group(1)
            ):
                present = tm.group(2)
                if present is None or present == "TRUE":
                    tech_reqs.append(tm.group(1))

        # Extract obsolete_by tech
        obsolete_tech = ""
        obs_match = re.search(r'obsolete_by\s*=\s*\{([^}]*)\}', section)
        if obs_match:
            obs_tech = re.search(r'"Tech",\s*"([^"]+)"', obs_match.group(1))
            if obs_tech:
                obsolete_tech = obs_tech.group(1)

        buildings.append({
            "name": name_match.group(1),
            "genus": genus_match.group(1) if genus_match else "",
            "tech_reqs": tech_reqs,
            "obsolete_tech": obsolete_tech,
            "build_cost": int(cost_match.group(1)) if cost_match else 0,
            "upkeep": int(upkeep_match.group(1)) if upkeep_match else 0,
        })

    return buildings


def build_enables_map(units, buildings):
    """Build a mapping from tech name to what it enables (units and buildings)."""
    enables = defaultdict(lambda: {"units": [], "buildings": []})

    for u in units:
        if u["tech_req"] not in ("None", "Never"):
            enables[u["tech_req"]]["units"].append(u["name"])

    for b in buildings:
        for tech in b["tech_reqs"]:
            enables[tech]["buildings"].append(b["name"])

    # Sort lists for consistent output
    for v in enables.values():
        v["units"].sort()
        v["buildings"].sort()

    return dict(enables)


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


def generate_unit_upgrade_mermaid(units):
    """Generate a Mermaid flowchart showing unit upgrade chains.

    Each unit is a node. An edge from A to B means A is obsoleted by B.
    Standalone units (no chain) appear as isolated nodes.
    """
    lines = ["flowchart LR"]

    # Build a name set for validation of obsolete_by targets
    unit_names = {u["name"] for u in units}

    # Node declarations
    for u in sorted(units, key=lambda u: u["name"]):
        sid = sanitize_id(u["name"])
        lines.append(f"    {sid}[\"{u['name']}\"]")

    lines.append("")

    # Edges: unit --> obsolete_by
    for u in sorted(units, key=lambda u: u["name"]):
        obs = u["obsolete_by"]
        if obs not in ("None", "Never") and obs in unit_names:
            lines.append(
                f"    {sanitize_id(u['name'])} --> {sanitize_id(obs)}"
            )

    return "\n".join(lines)


def format_year(year_str):
    """Format a year string, converting negative years to 'YYYY BC'."""
    if not year_str:
        return ""
    year = int(year_str)
    if year < 0:
        return f"{abs(year)} BC"
    return year_str


def generate_table(techs, enables_map):
    """Generate a markdown table of all technologies with what they enable."""
    lines = [
        "| Technology | Requires | Enables | Year | Wikipedia |",
        "|---|---|---|---|---|",
    ]

    def sort_key(t):
        # Techs with year first (sorted by year), then without (alphabetical)
        if t["year"]:
            return (0, int(t["year"]), t["name"])
        return (1, 0, t["name"])

    for t in sorted(techs, key=sort_key):
        reqs = [r for r in (t["req1"], t["req2"]) if r not in ("None", "Never")]
        reqs_str = ", ".join(reqs) if reqs else ""
        year_str = format_year(t["year"])
        wiki_str = f"[Link]({t['wiki_url']})" if t["wiki_url"] else ""

        # Build enables string
        enabled = enables_map.get(t["name"], {"units": [], "buildings": []})
        parts = []
        for name in enabled["units"]:
            parts.append(f"{name} (unit)")
        for name in enabled["buildings"]:
            parts.append(f"{name} (bldg)")
        enables_str = ", ".join(parts)

        lines.append(
            f"| {t['name']} | {reqs_str} | {enables_str} | {year_str} | {wiki_str} |"
        )

    return "\n".join(lines)


def generate_unit_table(units):
    """Generate a markdown table of all units with stats."""
    lines = [
        "| Unit | Class | Tech Req | Obsolete By | Atk | Def | HP | FP "
        "| Move | Cost | Year | Wikipedia | Notes |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    def sort_key(u):
        # Units with year first (sorted by year), then without (alphabetical)
        if u["year"]:
            return (0, int(u["year"]), u["class"], u["name"])
        return (1, 0, u["class"], u["name"])

    for u in sorted(units, key=sort_key):
        notes = []
        if u["first_strikes"]:
            notes.append(f"FS: {u['first_strikes']}")
        for b in u["bonuses"]:
            if b["type"] == "FirstStrikes":
                notes.append(f"FS vs {b['flag']}: {b['value']}")
            elif b["type"] == "DefenseDivider":
                notes.append(f"Atk vs {b['flag']}: /{b['value'] + 1} def")
            elif b["type"] == "DefenseDividerPct":
                notes.append(f"Atk vs {b['flag']}: +{b['value']}%")
            elif b["type"] == "DefenseMultiplier":
                notes.append(f"Def vs {b['flag']}: x{b['value'] + 1}")
            elif b["type"] == "DefenseMultiplierPct":
                notes.append(f"Def vs {b['flag']}: +{b['value']}%")
            elif b["type"] == "Firepower1":
                notes.append(f"FP1 vs {b['flag']}")
        if u["transport_cap"]:
            notes.append(f"transport: {u['transport_cap']}")
        if u["fuel"]:
            notes.append(f"fuel: {u['fuel']}")
        if u["pop_cost"]:
            notes.append(f"pop: {u['pop_cost']}")
        notes_str = ", ".join(notes)

        tech = u["tech_req"] if u["tech_req"] != "None" else ""
        obs = u["obsolete_by"] if u["obsolete_by"] != "None" else ""
        year_str = format_year(u["year"])
        wiki_str = f"[Link]({u['wiki_url']})" if u["wiki_url"] else ""

        lines.append(
            f"| {u['name']} | {u['class']} | {tech} | {obs} "
            f"| {u['attack']} | {u['defense']} | {u['hitpoints']} "
            f"| {u['firepower']} | {u['move_rate']} | {u['build_cost']} "
            f"| {year_str} | {wiki_str} | {notes_str} |"
        )

    return "\n".join(lines)


def generate_building_table(buildings):
    """Generate a markdown table of all buildings."""
    lines = [
        "| Building | Type | Tech Req | Build Cost | Upkeep |",
        "|---|---|---|---|---|",
    ]

    def sort_key(b):
        tech_str = ", ".join(b["tech_reqs"]) if b["tech_reqs"] else ""
        return (b["genus"], tech_str, b["name"])

    for b in sorted(buildings, key=sort_key):
        tech_str = ", ".join(b["tech_reqs"]) if b["tech_reqs"] else ""
        lines.append(
            f"| {b['name']} | {b['genus']} | {tech_str} "
            f"| {b['build_cost']} | {b['upkeep']} |"
        )

    return "\n".join(lines)


def main():
    script_dir = Path(__file__).resolve().parent
    data_dir = script_dir / ".." / "data" / "nationstates"
    output_path = script_dir / "techtree.md"

    techs = parse_techs(data_dir / "techs.ruleset")
    units = parse_units(data_dir / "units.ruleset")
    buildings = parse_buildings(data_dir / "buildings.ruleset")

    enables_map = build_enables_map(units, buildings)

    mermaid = generate_mermaid(techs)
    unit_upgrade_mermaid = generate_unit_upgrade_mermaid(units)
    tech_table = generate_table(techs, enables_map)
    unit_table = generate_unit_table(units)
    building_table = generate_building_table(buildings)

    output_path.write_text(
        f"# Nation States Tech Tree\n\n"
        f"```mermaid\n{mermaid}\n```\n\n"
        f"## Technology Reference\n\n{tech_table}\n\n"
        f"## Unit Upgrade Chains\n\n"
        f"```mermaid\n{unit_upgrade_mermaid}\n```\n\n"
        f"## Unit Reference\n\n{unit_table}\n\n"
        f"## Building Reference\n\n{building_table}\n"
    )
    print(f"Generated {output_path} with {len(techs)} techs, "
          f"{len(units)} units, {len(buildings)} buildings")


if __name__ == "__main__":
    main()
