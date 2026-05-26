# P5 Publish Readiness Report

## Scope

P5 prepares the refactored thesis repository for a lean GitHub publish pass.
It focuses on generated-artifact policy, supplemental chapter-evidence
tracking, and repeatable lightweight verification.

## Changes

- Added a `research_validation/README.md` index so the chapter-specific
  evidence workspace is documented at the directory root.
- Updated `.gitignore` so generated `research_validation/` payloads stay local:
  CSV tables, rendered PNG/SVG/PDF figures, JSON checklists, and TXT exports.
- Kept reusable `research_validation/` Python scripts, MATLAB scripts, and
  Markdown reports visible as commit candidates.
- Updated the GitHub checklist, project structure, and dataset manifest to
  describe the new tracking policy.
- Added `research_validation/README.md` to the public layout checker.

## Current Research-Validation Policy

Track:

- `*.py`
- `*.m`
- `*.md`

Ignore under `research_validation/`:

- `*.csv`
- `*.png`
- `*.svg`
- `*.pdf`
- `*.txt`
- `*.json`

The ignored files remain reproducible local outputs and are still referenced by
the result indexes where appropriate.

## Verification

Passing checks:

```powershell
D:\python312\python.exe scripts\check_project\check_public_layout.py
D:\python312\python.exe -m compileall -q research_validation scripts
D:\python312\python.exe -m unittest tests.test_thesis_mainline_smoke
git diff --check
```

Observed state after the ignore update:

- 63 untracked `research_validation/` source/report candidates remain visible.
- 310 generated or bytecode artifacts under `research_validation/` are ignored.

## Remaining Before Public Push

- Choose a license intentionally and add `LICENSE`.
- Decide whether to add `CITATION.cff` or keep citation text only in the
  README.
- Review staged changes as one public-refactor commit, with special attention
  to moved archive paths and retained MATLAB/COMSOL runners.
- Optionally normalize hardcoded local paths inside generated Markdown reports
  if those reports are meant to be polished public documentation rather than
  local thesis evidence logs.
