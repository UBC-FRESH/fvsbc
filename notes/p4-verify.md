# Phase 4 plan: Verify

Phase: P4 Verify
Parent issue: the issue this plan is committed with
Branch: `feature/p4-verify`
Roadmap: `ROADMAP.md`, section "Phase 4: Verify"
Predecessor: `P3` closed as `89db30e`, report in `notes/reports/p3-closeout.md`

## Goal

Show that the build meets its acceptance criteria, and record the evidence in the changelog. `P3`
closed with six of seven criteria met and one met in substance rather than in letter; this phase turns
every one of them into evidence a reader can reproduce, and closes the two verification gaps `P3`
named.

## What this phase is not

No new capability, no modelling, no contract change. If a check here fails, the remedy is a finding
and a proposed task, not a fix inside this phase.

## Scope, as approved

`notes/reports/p3-closeout.md`, section 6, approved with the phase on 2026-10-24:

1. **`P4.1` The acceptance checks, from a clean checkout.** Build the variant from the pin, run the
   suite, run the command, and record the run ids and the outputs. This is the phase's substance and
   it needs no new code.
2. **`P4.2` Promote the oracle comparison into a repository test.** `P2.3` compared the build against
   the official BC test data and recorded the result in `notes/reference/fvsbc-validation.md`; the
   comparison is not reproducible from the repository. It is the oldest open proposal in the project.
3. **`P4.3` Make the dashboard's 3.11 evidence literal.** The dashboard script runs on 3.12 in CI while
   the six gates it wraps run on both. **This touches a required context**, so it stops at its approval
   gate and does not proceed on its own.
4. **`P4.4` Close the `__all__` gap.** Nothing asserts that every name in the package's `__all__`
   resolves; it was checked by hand once.

   **Corrected when the task started: the premise was false.**
   `tests/test_fresh_fvsbc_package.py::test_package_exports_only_names_it_defines` asserts exactly
   that, and it has existed since `6e99a41`, the `P2` merge, before `P3.4` recorded otherwise. The
   task became making that assertion's falsifiability reproducible through the harness, which it now
   is, plus a uniqueness assertion nothing else checks.

## The order, and why

`P4.1` first: it produces the evidence the other three are judged against, and it is the only task that
can show a criterion failing. `P4.2` second, because a repository test for the oracle comparison is the
one thing that would have caught the three wrong claims `P2.3` published. `P4.4` third, because it is
small and independent. `P4.3` last, because it is the only task that needs a maintainer decision and it
must not block the others.

## Out of scope

- Block keywords (`COMMENT`, `COMPUTE`, `IF`, `DATABASE`), which remain refused rather than written. A
  run that needs `COMPUTE` cannot be expressed; that is a capability with a research burden.
- Any tag, release, or publication, which is `P5`.
- Real inventory data. The fixtures stay synthetic.
- The seed's own defects, `ubc-fresh-dev-workflow` #44, #45 and #46, which are upstream.

## Risks

- **`P4.1` needs the build**, and the build is the thing `P3` proved in CI rather than on every
  machine. If the local environment cannot build it, the check runs in CI and the report says so
  rather than skipping silently.
- **`P4.2` needs the official case data**, which is FVS's own and is not this repository's. The test
  must say where the data comes from and skip, with a recorded reason, when it is absent.
- **`P4.3` changes a required context.** The `P2` report records the failure mode: a protection change
  that dropped two contexts. It runs only with its own approval, and the read-back is quoted.
- **Verification can become self-congratulation.** The Verifier role exists for that, and its findings
  are the evidence that the checks are checks.

## Artifacts

The changelog entries with the recorded evidence, the repository test for the oracle comparison, the
dashboard job's change if approved, and the `__all__` test.

## Open proposals, not tasks

- **`scripts/check_workflow.py` does not catch a POSIX temporary path** in a tracked file, although it
  catches a Linux home-directory path. Four such paths were in `notes/reference/synthetic-run.md`
  until `P3`'s close-out removed them. A pattern could false-positive on legitimate prose, so it needs
  its own evidence and its own approval rather than a line in this phase.
- **`run.py`'s drive body is covered only where the extension is built**, so the quality job reports
  that file at 87 percent while the gate is met at 98 percent overall. Closing it properly needs the
  extension in the coverage job, which is a CI decision.
