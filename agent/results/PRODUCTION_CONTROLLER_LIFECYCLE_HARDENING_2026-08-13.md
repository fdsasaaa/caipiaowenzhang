# Production Controller Lifecycle Hardening

**Date:** 2026-08-13  
**Status:** ACCEPTED PRE-MERGE EVIDENCE

## Trigger

The first correctly connected total-controller provider acceptance run (`31649189253`) made 3 real model requests. All 3 returned structured articles, but all 3 were rejected and no formal Approved Package was staged.

The failure exposed two controller-level problems rather than a provider transport problem:

1. the highest-ranked candidates were `position_filter`-only blueprints, which are context descriptions and cannot satisfy the V2.1 requirement that a formal filtering technique demonstrate a real candidate-space reduction;
2. a `rejected_for_revision` lifecycle record was incorrectly allowed to own duplicate/structural space, so one failed attempt could block later candidates.

## Permanent changes

- `position_filter` remains valid context, but a blueprint with no non-context technique atom is blocked with `no_executable_technique_atom` before any model request.
- lexical duplicate ownership ignores rejected/revision-only lifecycle records.
- structural duplicate ownership ignores rejected/revision-only lifecycle records.
- active states such as idea/draft/approved/queued/scheduled/published continue to own duplicate space.
- no quality threshold, evidence requirement, terminology gate, guarantee-language gate, or Approval rule was relaxed.

## Post-fix target-200 capacity

Zero-provider acceptance run: `31649868346`

- repository audit: PASS
- keyword conflicts: 0
- target: 200
- initial shallow capacity: 81, non-exhaustive
- automatic deep probe: yes
- final candidate capacity: **230**
- capacity exhaustive: **true**
- target feasible: **true**
- attempt budget: 230
- formal inventory before: 0
- provider calls in this acceptance: 0
- website sync: false
- scheduling: false
- publication: false

Artifact:
- ID: `9162153656`
- SHA256: `5461010fb184db0fc809b9b1f2d1fc76c4712f5b571b99950708892adb838e3a`

The target therefore remains feasible after removing the invalid context-only article space.
