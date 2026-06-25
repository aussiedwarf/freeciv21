# Nationstates

## Lore

The Nation States region is set in 1946. This means freeciv21 needs to be able to simulate technology for society between 1800 and the present, 2026.

## Tech Tree Visualization

To regenerate the tech tree diagram after editing `data/nationstates/techs.ruleset`:

```
python3 nationstates/gen_techtree.py
```

This parses the ruleset and outputs `nationstates/techtree.md`, which can be previewed in VS Code (Ctrl+Shift+V) using the "Markdown Preview Mermaid Support" extension.
