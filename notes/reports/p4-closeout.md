# Phase close-out report: P4 Verify

Phase: P4 Verify
Parent issue: #25
Pull request: #30, `feature/p4-verify` into `main`, opened as a draft when the phase was activated
Evidence head: `b7656bf`, the head that the gates in section 3 cover. **The branch carried 15 commits
and 15 CI runs at that head.** It carries this report's own commits and their runs on top of it, so
those counts move with each revision and are never quoted for the branch's head.
Report commit: the commit that adds this revision of the report. Its CI run is posted on the pull request.
Date: 2026-10-24
Status: queued for approval. Not merged.

## Recommendation

Approve these actions. The agent carries them out in this order, and reads back each result.

Pull request #30 is **queued ready for review** when this report is committed, so the first action is
the maintainer's decision rather than the agent's.

1. Squash-merge pull request #30, and delete the branch `feature/p4-verify`:
   `gh pr merge 30 --squash --delete-branch`.
2. Close parent issue #25 with a closeout comment that cites the merge commit.
3. Launch `P5`, after approving its scope in section 6: create its parent issue, its branch
   `feature/p5-release`, its child issues as sub-issues, and its roadmap subtask lines.

**Settings changes: none.** This phase changed no branch protection, tag, release, external account, or
repository setting. The one settings change the project has made was branch protection in `P3.1`, and
`P4.3` deliberately avoided touching it. Read back on 2026-10-24:

```json
{"contexts":["Green dashboard summary","Pre-commit parity","Quality gates, Python 3.11","Quality gates, Python 3.12"],"linear":true}
```

## 1. Objectives and acceptance

| Criterion | Evidence | Status |
| --- | --- | --- |
| Each of `P3`'s seven acceptance criteria has evidence recorded in the changelog, with the command or run id that produces it | `notes/reference/p4-acceptance.md`, added by `P4.1` (#26) in `cf64bec`, carries the seven criteria with their evidence **and a column saying what each check does not show**; the changelog entry for `P4.1` summarises it and points at the note | met |
| The oracle comparison runs from the repository against the committed or fetched case data, and its result is recorded | `tests/test_oracle.py`, `P4.2` (#27), commit `06b8d20`: zero differing lines across 164 rows and four stands, `FVS_Compute` at 160 rows. **The case data is neither committed nor fetched at run time**: it is FVS's own, its licence is not established, and the test takes its location from `FVSBC_CASE_DIR`, which CI's build job sets to the pinned clone it already checks out. That is the substance of the criterion with a different mechanism, and the report says so rather than letting "fetched" cover it | met, with the mechanism stated |
| `python scripts/dashboard.py` exits zero on 3.11 and 3.12 in CI, with the protection contexts still matching the four the workflow spec names | `P4.3` (#28), `86642cf`: run `40131167200`'s artifact holds `dashboard-3.11.json` and `dashboard-3.12.json`, each `green` with six gates, and the protection read-back above lists the four contexts with linear history | met |
| Every name in the package's `__all__` resolves, asserted by a test | `tests/test_fresh_fvsbc_package.py::test_package_exports_only_names_it_defines`, **which has existed since `6e99a41`**, plus a mutation (`package-exports-a-name-it-does-not-define`) added in `eb06a8f` so its falsifiability is reproducible. Registry: 24 of 24 | **met before the phase began.** `P3.4`'s claim that no such test existed was false, and section 5 records it |
| `python scripts/dashboard.py` exits zero on the head commit of the phase branch | Green on `b7656bf`, locally, and CI run `40131457849` succeeds on that exact head | met |

**Four of five met, and the fifth was already met when the phase started.** Nothing in this phase
failed to meet its criterion; one criterion turned out to describe work that had already been done, and
one was met by a different mechanism than the words suggest.

## 2. Workflow compliance

- **Parent issue before the branch.** `#25` was created before `feature/p4-verify` was cut from
  `89db30e`, and the plan `notes/p4-verify.md` was committed in `83545d2`, the activation commit,
  before any task's code.
- **A plan before each task.** `#26`, `#27`, `#28` and `#29` each carry a plan comment posted before
  that task's first code commit. `P4.4`'s plan says its own premise had already failed.
- **Branch from `main`.** `89db30e`, the squash-merge of `P3`.
- **Commit messages that start with a task ID.** 14 of the 15 commits at the evidence head. The one
  that does not is `83545d2`, the activation commit, which starts with the phase ID. `8d7b879` and
  `1abb5a8`, a CI diagnostic and its repair, both start with `P4.2`.
- **Gates for each commit.** Section 3.
- **Roadmap and changelog in step.** Each task's change set carries its roadmap tick and its changelog
  entry. **No mechanical test exists for "same change set"**, so this is a claim about the record.
- **Child issues closed with closeout evidence.** `#26` through `#29` each carry a closeout comment
  naming the commits, the CI run, and the verification.
- **Approval gates.** Two decisions were put to the maintainer, and both were presented with the
  options, their costs and a recommendation before being asked: the oracle comparison's treatment
  (`P4.2`) and the dashboard's 3.11 evidence (`P4.3`). **The first attempt at the first one was not
  presented that way** — the agent wrote that the choice "is the maintainer's" and did not present it,
  and the maintainer said so. Section 5 records it.

## 3. Gate evidence

- **On the evidence head `b7656bf`:** all six dashboard gates green, run locally, and CI run
  `40131457849` succeeds on that exact head.
- **Per commit:** every commit that changes code or a contract carries a changelog entry for its
  change set. **The four roadmap-only commits** (`d14ca8a`, `f5117f6`, `6170793`, `b7656bf`) carry none
  of their own, and their dashboard result is the one their parent task's entry records. **Those
  records are the implementer's claims, not independent evidence.**
- **The mutation harness** runs inside the quality job. The registry grew from 23 to 24 in this phase.
- **The oracle comparison and the end-to-end test** run in the build job, the only job with the
  extension and FVS's case data: `34 passed, 1 skipped` on `cab1df7` and later.

## 4. CI evidence

**At the evidence head: fifteen runs, fourteen success, one failure.** Every run is a `pull_request`
run. The branch carries one run per commit, so the counts move with each revision.

The failure is the most useful row, and it is the one that produced this phase's largest finding:

- `40123488223` on `06b8d20`, **failure** in `Build the BC variant`, because `tests/test_oracle.py`
  was wired in beside `tests/test_run.py` and the comparison failed on 104 of 164 rows.

| Run ID | Head commit | Conclusion | Task |
| --- | --- | --- | --- |
| `40131457849` | `b7656bf` | success | the evidence head |
| `40131418899` | `2886411` | success | `P4.3` correction |
| `40131167200` | `86642cf` | success | `P4.3`, the dashboard on both versions |
| `40130988365` | `6170793` | success | `P4.4` roadmap |
| `40130780534` | `eb06a8f` | success | `P4.4` |
| `40130203623` | `cab1df7` | success | `P4.2`, the oracle test as a gate |
| `40129822165` | `8d7b879` | success | `P4.2` diagnostic repair |
| `40129623307` | `1abb5a8` | success | `P4.2` diagnostic |
| `40129295794` | `611e776` | success | `P4.2` compiler version |
| `40124078681` | `f5117f6` | success | `P4.2` roadmap |
| `40123875251` | `df90775` | success | `P4.2`, the step removed |
| `40123488223` | `06b8d20` | **failure** | `P4.2`, the oracle test wired in and failing |
| `40122706142` | `d14ca8a` | success | `P4.1` roadmap |
| `40122444974` | `cf64bec` | success | `P4.1` |
| `40120498910` | `83545d2` | success | the activation commit |

## 5. Deviations

| Deviation | Cause | Remedy |
| --- | --- | --- |
| **`P4.4`'s premise was false.** `P3.4` recorded, and `P3`'s approved close-out report repeated, that nothing asserts every name in `__all__` resolves. `tests/test_fresh_fvsbc_package.py` has asserted it since `6e99a41`, before the claim was made | The claim was asserted rather than checked, and the file it was about was never opened | The task became proving the assertion can fail: a mutation was added and the registry is 24 of 24, plus a uniqueness assertion nothing else checks. `notes/p4-verify.md` and the roadmap line carry the correction. **`notes/reports/p3-closeout.md` is approved and is not edited**; the false claim stays in it and this report carries the correction |
| **The agent's first explanation of the oracle failure was wrong.** It recorded that the runner's toolchain produced different numbers, and named the compiler version as a candidate | The explanation was plausible and asserted before it was tested, which is the failure this project's record has now made three times | Three hypotheses were tested and each died: the compiler (**13.3.0 on the runner, the same as the passing machine**), the instruction set (no `-march`, and `GLIBC_TUNABLES` changes nothing), and the inputs (byte-identical to the pin). The cause is **FVS keeps its state in the process**, and the test now runs its case in a child process. The wrong entries stay in the changelog with corrections beside them |
| **A CI diagnostic was added, broken, repaired, and removed.** Its step in `1abb5a8` failed because `PYTHONPATH=tests` dropped `src`; the run is green because the step was `continue-on-error` | The same mistake as an earlier subprocess in `P3.5`, made again | Fixed in `8d7b879`, and the step was removed in `cab1df7` once it had answered the question. **It is the second occurrence of that exact mistake**, and the record says so rather than counting it once |
| **`run_case` is not re-entrant in a process.** A second run inherits the first one's Fortran state, so two runs in one process are not independent and the directory isolation `run.py` documents is not enough | Found by the oracle test, not by design; the library's docstring says a run owns its directory and does not say the process is shared | **Not fixed, and out of scope for a verification phase.** Recorded in `notes/reference/p4-acceptance.md` and named in section 6 as the largest open item |
| **The `P4.3` cost estimate was pessimistic.** The plan said the job would roughly double to about two and a half minutes | Estimated rather than measured | Measured at **one minute forty-seven**, against one minute ten and one minute fourteen on two earlier runs. The correction is in the changelog |
| **`-O0` is not a usable configuration.** An experiment to test whether the optimiser affected the numbers produced a build that wrote no database at all | The variant is fragile at `-O0`, which ADR 0008 already recorded for the standalone | Recorded, not pursued: it is consistent with the existing ADR and it was not the cause being sought |

## 6. Next phase

`P5` is the roadmap's release phase, and its content is a maintainer decision rather than an inference
from this phase. What this report can say is what `P5` inherits, in order of weight:

1. **`run_case` is not re-entrant in a process.** Two runs in one process are not independent. A guard,
   a subprocess per run, or a documented restriction are the three routes, and the choice changes the
   public API's contract. **This is the largest open item in the project.**
2. **Block keywords are refused, not written** (`COMMENT`, `COMPUTE`, `IF`, `DATABASE`). A run that
   needs `COMPUTE` cannot be expressed, and `P3.2` showed `FVS_Compute` is exactly that table.
3. **The second official case, `YSM-SkyRanch`, still differs**: 328 of 375 rows identical, three stands
   differing by small amounts, unexplained since `P2.3`. The oracle test covers the case that passes
   and says so.
4. **`scripts/check_workflow.py` does not catch a POSIX temporary path** in a tracked file, though it
   catches a home-directory path. Four such paths were in a tracked note until `P3`'s close-out.
5. **`run.py`'s drive body** is covered only where the extension is built, so the quality job reports
   that file at **87 percent** and the build environment at 96, while the gate is met at 98 percent
   overall.

## 7. Decision

Approve recommendations 1 to 3, or amend them. The phase's four tasks are complete and its branch is
green; four of its five acceptance criteria are met and the fifth was already met when the phase began,
and both are stated above rather than left to be found.

## Verification before approval

- `python scripts/dashboard.py` on `b7656bf`: six gates green.
- CI run `40131457849` on `b7656bf`: five jobs successful, including the build job's oracle comparison.
- `gh api repos/UBC-FRESH/fresh-fvsbc/branches/main/protection --jq '{contexts: .required_status_checks.contexts, linear: .required_linear_history.enabled}'`:
  the four contexts quoted in the header.
- `python scripts/mutation_check.py`: `24 of 24 mutations caught`.
- `gh issue list --state open`: `#25` alone, before this report was written.
