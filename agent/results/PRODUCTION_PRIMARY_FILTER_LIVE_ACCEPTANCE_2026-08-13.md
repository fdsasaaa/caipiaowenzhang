# Production Primary Filter Live Acceptance

**Date:** 2026-08-13  
**Status:** CONTENT ACCEPTED / ARTIFACT RECOVERY REQUIRED

## Scope

One strictly bounded provider call was used to verify the new machine-bound production filter contract before expanding the user-authorized 200-article campaign.

## Run

- workflow run: `31651296877`
- model: `gpt-5.4-mini`
- provider endpoint: configured OpenAI-compatible endpoint
- maximum provider calls: `1`
- actual attempted: `1`
- generated: `1`
- approved: `1`
- formal inventory staged in runner: `1`
- approval failed: `0`
- generation failed: `0`
- reader terminology failed: `0`
- quality average: `100.0`
- editorial average: `100.0`
- website sync: `false`
- scheduled: `false`
- published: `false`

## Accepted article

- article ID: `LCM-IDEA-40be5a222f5cccf7`
- primary keyword: `分分彩五星直选跨度技巧`
- subject: `分分彩` / `五星直选`
- site category: `tzjq`
- primary SEO cluster: `ffc_research`
- source ref: `BRBCW-002590`
- verified rule ref: `SSC-HIST-MECH-5STAR-DIRECT-V1`
- content hash: `fc4e7b340d1ac92f77e0e3532a5aef9a5368bda58b2b9bd24287249b677cf2bd`

Machine contract before generation:

- primary atom: `span_range`
- selector: `五星`
- candidate space: ordered five-digit
- frozen span: `2–6`
- starting space: `100000`
- after filter: `43620`
- excluded: `56380`
- parameters frozen before prose generation
- source recommendation claimed: false
- predictive advantage claimed: false

The model correctly reproduced the exact `100000 -> 43620` reduction and explicit stop condition. Approval therefore reached Quality 100 / Editorial 100.

## Final workflow failure was infrastructure-only

The workflow's validation step failed **after** the article had already passed Approval and formal staging because direct execution of:

`python scripts/audit_reader_terminology.py`

raised `ModuleNotFoundError: No module named 'engine'`.

That is the same repo-root `sys.path` entrypoint class previously fixed for the total-controller CLI. It is not an article/content failure.

The reader terminology CLI is now fixed permanently and has a direct-execution regression test.

## Recovery evidence

The accepted package was preserved in the run artifact rather than regenerated.

- artifact ID: `9162674884`
- artifact ZIP SHA256: `5ee0b62037e14817d7c96d74eff89fae87bd8476597bcd96bb40759155fc87aa`
- approved package file: `articles/approved/LCM-IDEA-40be5a222f5cccf7.json`
- approved package artifact SHA256: `418eb1289d0e147869c53a13e2a5d8e483719216ad9e3ff557428aeba8a4817e`

Manual artifact verification confirms:

- `status=approved`
- exact content hash matches content bytes
- `subject_lottery=分分彩`
- `site_category_key=tzjq`
- no reader-facing `时时彩` leakage
- no literal forbidden guarantee term

This approved package must be recovered into the canonical production branch without another model call.

## Campaign accounting

At this checkpoint:

- real model calls in the 200-article campaign: `5`
- accepted formal content generated: `1`
- canonical `main` formal Approved files: still `0` until artifact recovery is merged

No duplicate paid regeneration is authorized for this accepted article.
