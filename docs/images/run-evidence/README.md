# Screenshots of archived run evidence

Forty PNGs were captured with a real Chromium browser on 2026-09-26 from the
[generated evidence pages](../../tutorial-evidence/README.md). These are screenshots
of a local **archived-results viewer**, not a live LANTA terminal and not a fresh
rerun. They are not AI-generated expected-result images. Seven setup/reading
pages have no matching archived job and therefore no invented result screenshot.

Each viewer joins the archived job ID to `workflow-status.json`, allocation rows
in `accounting.psv`, and job-ID-associated stdout in `artifacts.tar.gz`. For arrays,
the viewer shows every allocation row and one explicitly named output element.
Long logs are excerpted; the full archive and per-excerpt SHA-256 remain linked.
The Markdown excerpts trim trailing whitespace; raw source bytes are unchanged.

See [capture hashes](capture-manifest.json) and [job/excerpt mappings](../../tutorial-evidence/manifest.json).
The capture manifest covers the HTML source and screenshots so stale images can
be detected after edits. Images of newer EnergyPlus benchmark traces are separate
plots made from scientific output, not replacements for these historical records.

## Recapture

1. Run `python3 scripts/build_tutorial_evidence.py` from the repository root.
2. Serve that root locally, bound to loopback, and open the evidence HTML in a
   browser through Playwright CLI. Use a local Chromium executable if Chrome is
   unavailable; do not assume a workstation-specific browser path exists elsewhere.
3. Set the viewport to 1280×1000. For each entry with a `screenshot` value in the
   tutorial evidence manifest, navigate to its HTML and capture a full-page PNG
   under `output/playwright/tutorial-evidence/`.
4. Inspect representative single-job, array, GPU and failed-job pages, then copy
   approved PNGs here and update capture hashes. Preserve the visible archive/date
   label. Run the documentation/evidence tests before publishing.

For shell syntax see the [Bash reference](../../BASH_COMMAND_REFERENCE_TH.md).
