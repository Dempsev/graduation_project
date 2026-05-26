# GitHub Publish Checklist

Use this checklist before pushing the final public refactor.

## Must Pass

```powershell
python scripts\check_project\check_public_layout.py
python -m unittest tests.test_thesis_mainline_smoke
git diff --check
```

## Must Not Commit

These roots are local generated payloads and should stay ignored:

- `data/`
- `output/`
- `tmp/`
- `tmp_ppt_rebuild/`
- `tmp_ppt_render/`
- `.worktrees/`
- generated `research_validation/` payloads:
  - `*.csv`
  - `*.png`
  - `*.svg`
  - `*.pdf`
  - `*.txt`
  - `*.json`

Office/PDF exports are ignored globally:

- `*.doc`
- `*.docx`
- `*.pdf`
- `*.ppt`
- `*.pptx`

## Research Validation Tracking Policy

The `research_validation/` tree contains a mix of:

- reusable scripts (`.py`, `.m`)
- lightweight Markdown reports (`.md`)
- summary tables (`.csv`)
- generated figure assets (`.png`, `.svg`, `.pdf`)
- generated local checklists (`.json`, `.txt`)

For the public refactor, track scripts and Markdown reports, and regenerate
tables, figures, and local checklists from the tracked scripts. This keeps the
repository small while preserving the chapter evidence workflow.

## License And Citation

No public license file has been added yet. Before opening the repository to
others, choose a license intentionally.

Recommended additional files before public release:

- `LICENSE`
- `CITATION.cff` or a short citation section in `README.md`

## Final Git Review

Before committing, run:

```powershell
git status --short
git diff --stat
git diff -- .gitignore README.md README_CN.md docs scripts src tests
```

Check that archived paths are intentional moves rather than accidental deletes.
