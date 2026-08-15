# Daily Website-Ready Article Production

## Purpose

This repository can create a new quality-first article inventory every day without a daily human prompt. The automation produces immutable Approved parents and corresponding reviewed `website_public_release` revisions. Only articles that reach the public-r1 gate count toward the daily website-ready total.

The article repository never writes the website CMS, creates website schedules, changes Publisher/cron, or publishes pages. Website intake and publication remain owned by `fdsasaaa/xyptdq`.

## Daily volume contract

- Time zone: `Asia/Singapore`
- Scheduled start: 09:20 Singapore time (`01:20 UTC`)
- Target: 20 website-ready public-r1 articles
- Accepted quality-first range: 10-25
- Minimum: fewer than 10 accepted public-r1 articles makes the run fail closed and no generated inventory is committed
- Quality floor is never lowered to reach a number
- Candidate discovery can inspect up to 40 candidates per refill round while the existing production controller applies rule, keyword, lexical, structural, editorial, evidence and Approval gates
- Refill hard caps: 4 rounds, 80 staged Approved parents, and 120 model-generation attempts per day

The completion condition is the final website-ready `public-r1` count, not the number of Approved parents. If an Approved parent fails the public-r1 gate, the runner asks the existing Creator/Production Controller for new non-duplicate candidates and continues refilling until the target is reached or a hard capacity/cost cap is reached. A result between 10 and 19 is accepted as quality-first partial completion after the refill/cap path is exhausted. The 25 ceiling prevents uncontrolled overproduction.

## Provider configuration

Required repository Actions secret:

- `MODEL_PROVIDER_API_KEY`

The daily workflow defaults to the already verified OpenAI-compatible endpoint `https://api.synapai.top/v1`. The provider preflight passed Structured Outputs there with the existing secret and selected `gpt-5.4-mini` automatically.

Optional repository Actions variables:

- `MODEL_PROVIDER_BASE_URL` — overrides the verified default endpoint when intentionally changing provider.
- `MODEL_PROVIDER_MODEL` — explicit model ID. Empty means the runner asks `/models` and prefers model IDs containing `mini`, `flash`, `small`, then `lite` before falling back to the first returned model.

Do not store API keys in tracked files, issues, PR bodies, logs, or workflow inputs.

## Production path

Each accepted day uses batch identity `DAILY-YYYYMMDD`.

1. Read current `main` and existing formal inventory.
2. Discover candidates only from verified mechanics.
3. Apply exact keyword ownership, lexical and structural duplicate gates before model generation.
4. Generate through the existing Creator/Production Controller and normal Approval path.
5. Stage immutable Approved parents with the daily batch identity.
6. Rewrite each newly Approved parent into a non-operational public-r1 revision.
7. Reject public versions containing candidate lists, next-round selection, chase/doubling/funding instructions, monetary/multiple execution paths, prohibited HTML, insufficient content structure, or missing uncertainty boundaries.
8. Bind each public-r1 to the immutable parent's content hash and fingerprint and validate the normal public-release revision contract.
9. If final public-r1 count is below 20, discover fresh candidates and repeat without retrying already attempted identities; stop only at target or hard refill/cost/capacity boundaries.
10. Write a complete daily public-release manifest only when at least 10 public-r1 articles pass.
11. Run repository audit and tests, create a dated PR, dispatch the independent Python 3.10/3.13 `test.yml`, and attempt a normal squash merge only after that CI passes.

No admin bypass is used. If repository protection, required human review, token permissions, Actions policy, or another gate prevents merge, the PR remains open and the automation stops rather than bypassing the protection.

## Diagnostics and evidence retention

The runner writes `artifacts/daily_website_ready/YYYY-MM-DD.json` after every completed refill round and again at final disposition. The report records round-by-round candidate counts, generation/Approval results, public-r1 successes and failures, quality/editorial averages, distributions, stop reason and hard-cap consumption.

Successful reports are committed with the accepted daily inventory and therefore enter `main`. Failed production runs are never allowed to commit generated article inventory. Instead, the workflow first uploads the report as a GitHub Actions artifact and then resets all generated content, retaining only the diagnostic JSON on a permanent branch named `diagnostics/daily-website-ready-YYYY-MM-DD-run-RUNID`. This preserves failure evidence without contaminating formal inventory.

## Frozen CF50 tail

The following existing CF50 identities remain excluded from daily production until the website SEO Gate explicitly authorizes them:

- `LCM-CREATOR-cf50-20260813-020`
- `LCM-CREATOR-cf50-20260813-029`
- `LCM-CREATOR-cf50-20260813-038`
- `LCM-CREATOR-cf50-20260813-039`
- `LCM-CREATOR-cf50-20260813-040`

Daily production creates independent new long-tail inventory; it does not use automation to bypass that historical Gate.

## Fail-closed conditions

Normal no-touch operation still depends on more than API credit. A run stops safely when any of these is true:

- provider key is missing, invalid, rate-limited, out of quota, or the provider is unavailable;
- the provider cannot return compatible Structured Outputs;
- after refill/cost/capacity exhaustion, fewer than 10 website-ready articles pass;
- repository audit or pytest fails;
- a previous daily production PR remains unresolved;
- GitHub Actions is disabled or the workflow token cannot create/push a branch or PR;
- branch protection or repository policy prevents normal merge.

These failures do not lower quality, publish raw Approved bodies, or bypass website controls.
