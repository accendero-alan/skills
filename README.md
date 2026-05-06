# Skills

Claude skills for use with the Claude desktop app.

## Structure

Each skill lives in its own directory:

```
skill-name/
├── SKILL.md        # Skill definition and instructions (required)
└── evals/
    └── evals.json  # Test cases and assertions
```

Packaging a skill produces a `skill-name.skill` file (excluded from git) that can be installed in the Claude app.

## Skills

| Skill | Description |
|---|---|
| [critique-writing](critique-writing/SKILL.md) | Deep literary critique of creative writing — fiction, flash, novels, screenplays |

## Packaging

Requires the skill-creator scripts from the Claude app and PyYAML:

```bash
pip install pyyaml
python -X utf8 -m scripts.package_skill <path/to/skill> <output-dir>
```

Run from the `skill-creator` directory so the `scripts` module resolves correctly.
