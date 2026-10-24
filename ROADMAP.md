# FVS-BC Roadmap

This roadmap is the plan of record and the issue tracker map for FVS-BC. Keep it in step with the GitHub issues, `CHANGE_LOG.md`, and `notes/`. `scripts/check_workflow.py` parses the phase headers, status lines, and checkboxes below, so keep their format.

Every phase starts as `planned` with `Parent issue: TBD`. Activate a phase only after its parent issue exists and the maintainer approves it.

## Issue Tracker Map

| Phase | Parent issue | Branch | Status |
| --- | --- | --- | --- |
| P0 Bootstrap | #1 | `feature/p0-bootstrap` | complete |
| P1 Scope and design | #5 | `feature/p1-scope-design` | complete |
| P2 Contracts and prototype | #10 | `feature/p2-contracts-prototype` | complete |
| P3 Build | #17 | `feature/p3-build` | complete |
| P4 Verify | #25 | `feature/p4-verify` | active |
| P5 Release and deploy | TBD | `feature/p5-release` | planned |
| P6 Operate and maintain | TBD | `feature/p6-operate` | planned |

## Lifecycle Map

| Stage | Phases | Exit criteria |
| --- | --- | --- |
| Scope and design | P0, P1 | Goal, scope, and out-of-scope items recorded; decisions in ADRs, each accepted or deferred |
| Build | P2, P3 | Each task committed with its task ID; each commit leaves the dashboard green; docs updated in the same change set |
| Verify | P4 | The dashboard and CI pass on the head commit; each acceptance criterion has evidence in the close-out report |
| Release and deploy | P5 | Tag, release notes, and Pages live; a clean checkout verifies them; each release action approved on its own |
| Operate and maintain | P6 | Review cadence held; incoming ideas triaged; retirement decided and recorded as an ADR |
| Retire | P6 (procedure) | Archive notice, final changelog entry, and issues closed |

## Conventions

- A phase is `P<n>`. A task is `P<n>.<m>`. A subtask is a checklist item inside the task's issue body. Three levels at most.
- Status values are `planned`, `active`, `pr-open`, `complete`, and `deferred`.
- A phase becomes `complete` only after its pull request merges to `main` and its parent issue closes.

## Phase 0: Bootstrap

Parent issue: #1
Branch: `feature/p0-bootstrap`
Status: complete

Goal: adapt the contract to this project, and make the first pull request reviewable.

- [x] P0.1 Adapt `AGENTS.md` and `README.md` to this project (#2)
- [x] P0.2 Confirm the validator and the docs build pass (#3)

Acceptance criteria:

- `AGENTS.md` states the project-specific rules, and links the shared workflow rules instead of copying them.
- `README.md` describes `fresh-fvsbc`, its place in the pipeline, and its status, and claims nothing the roadmap has not recorded.
- `python scripts/dashboard.py` exits zero on the head commit of the phase branch.

## Phase 1: Scope and design

Parent issue: #5
Branch: `feature/p1-scope-design`
Status: complete

Goal: settle the repository's public footing, then state the question, the users, the scope, and the out-of-scope items, and record the first decisions as ADRs.

- [x] P1.1 Add the MIT licence and align the package metadata (#6)
- [x] P1.2 Write the problem statement and scope in `notes/` (#7)
- [x] P1.3 Record the first design decisions as ADRs in `notes/adr/` (#8)

Acceptance criteria:

- `LICENSE` is MIT, and the package metadata agrees with it.
- `notes/` states the problem, the users, the scope, and the out-of-scope items.
- Every ADR is accepted or superseded, and any new decision is recorded.
- `python scripts/dashboard.py` exits zero on the head commit of the phase branch.

## Phase 2: Contracts and prototype

Parent issue: #10
Branch: `feature/p2-contracts-prototype`
Status: complete

Goal: define the interfaces and the data contracts, then build the smallest prototype that exercises them.

The detail for this phase is the focused plan `notes/p2-contracts-and-prototype.md`, which carries each
task's sections, the phase criteria and their evidence, the deviations, and the open proposals.

- [x] P2.1 Define the interface and data contracts in `docs/` (#11)
  - [x] Read `canada/bc/BC.trf`, and establish that it is an SVS asset rather than a tree-list format.
  - [x] Read `canada/bc/bcspp.f`, and establish that the BC build does not compile it and never calls it.
  - [x] Read `canada/bc/blkdat.f`, and record its `TREFMT` tree-record format and its `JSP` species list.
  - [x] Read `base/keywds.f` and `canada/bc/initre.f`, and record the keyword vocabulary and the BC site input.
  - [x] Read `dbsqlite/` and `canada/bc/BCPLOT.F77`, and record the output tables and the BEC structure.
  - [x] Record the format conflict between the BC variant default and PyFVS's injected `TREEFMT`, and hand the resolution to `P2.2`.
  - [x] Write the tree-list input contract.
  - [x] Write the keyword-set contract.
  - [x] Write the output contract and the provenance record.
  - [x] Write the `nemora` ingestion contract.
  - [x] Add `CODE_OF_CONDUCT.md` and `CITATION.cff`.
- [x] P2.2 Build a prototype that exercises the contracts on synthetic data (#12) — its one open subtask was **transferred to `P3.2` (#19)** and **discharged there** (ADR 0009): reading `FVS_Compute` and `FVS_Summary_Metric`, which PyFVS makes unreachable
  - [x] Run the build spike, and record the command, its output, and its exit status.
  - [x] Record the build outcome, and write the build-recipe ADR if the spike is conclusive.
  - [x] Write a synthetic stem population shaped like `nemora` output, as a fixture built at runtime in `tests/`.
  - [x] Write the tree-list writer, with a test that asserts the exact column positions and tests that reject an unresolvable species code.
  - [x] Write the keyword-set validator: reject an unknown keyword by name, warn on `xSALVAGE`, and carry a hash.
  - [x] Answer the `TREEFMT` hazard: whether PyFVS injects its own format for a BC run, and whether it misaligns a list.
  - [x] Run the synthetic stand through the `DATABASE` path.
  - [x] Write the output reader for `FVS_Cases` and `FVS_Error`, and fail a run that holds a row of severity `ERROR`.
  - [x] Read `FVS_Compute` and `FVS_Summary_Metric`. **Transferred to `P3.2` (#19)**, which builds the standalone executable that reaches them; PyFVS makes them unreachable by occupying the `DATABASE` output block.
  - [x] Write the `nemora` adapter: require `species` and `tree_age`, and reject a crown ratio the one-digit field cannot represent.
  - [x] Record provenance for the run, including the case id and run datetime from `FVS_Cases`.
  - [x] Create the package skeleton and extend the gates to cover it.
- [x] P2.3 Record the FVS source patch set and its oracle comparison (#13)
  - [x] Bank the patch set and record the recipe in ADR 0004.
  - [x] Compare the build against the official BC test data and record the results with their limits.
  - [x] Disclose the mislabelled commits in the changelog and on this issue.
- [x] P2.4 Rename the project to `fresh-fvsbc` (#14)
  - [x] Rename the GitHub repository. Public; approved and run on 2026-10-23.
  - [x] Update the published URLs in `pyproject.toml` and `CITATION.cff`.
  - [x] Rename the package directory, the distribution name, and the gate configuration.
  - [x] Rename the living documents, and add the variant-versus-package wording rule.
  - [x] Add the `Renamed by ADR 0005` line to ADRs 0001 to 0004.
  - [x] Rename the local directory.
- [x] P2.5 Repair the plan of record after the workflow audit (#15)
  - [x] Add the indented subtask level to this roadmap for `P2.1` to `P2.4`, and link the plan from each task line.
  - [x] Reconcile parent issue `#10`: its child checklist and its scope, with a scope-change comment.
  - [x] Correct `README.md`'s status paragraph, which claims that no variant has been built.
  - [x] Correct the closed task issues' `Status:` and `Completion metadata:`.
  - [x] Move the multi-paragraph roadmap notes into the focused plan.
  - [x] Pin the workflow revision in `AGENTS.md`, and file the missing agent pages upstream.
  - [x] Record the `P2.3` incident, thirteen commits with no child issue, in the close-out report.
  - [x] Record this project's roles and open the model log at `docs/agents/roles-and-models.rst`.
  - [x] Have a separate Verifier session check every claim in the close-out report against its evidence.

Acceptance criteria:

- `docs/` states the interfaces and the data contracts: the tree-list input, the keyword set, the parsed outputs, and the provenance record.
- A prototype runs on synthetic data and exercises each contract, with checks that can fail.
- The build question in ADR 0001 is answered with evidence: either `bc` builds from the variant matrix, or the patch the FVS source submodule needs is recorded.
- `python scripts/dashboard.py` exits zero on the head commit of the phase branch.

## Phase 3: Build

Parent issue: #17
Branch: `feature/p3-build`
Status: complete

Goal: implement the agreed scope of the BC layer on top of the validated prototype: make the build
reproducible in CI, reach the two output tables PyFVS cannot, make the falsifiability evidence
reproducible, and give the package a public API, a run orchestration, and a command-line entry point.

The detail for this phase is the focused plan `notes/p3-build.md`, written before the work began.

- [x] P3.1 The CI quality matrix, and a CI build of the variant (#18)
  - [x] Set the `quality` job's `name:` to `Quality gates, Python ${{ matrix.python-version }}` and its `setup-python` input to the matrix variable, and add a `[3.11, 3.12]` matrix.
  - [x] Add a job that applies ADR 0004's patch to the pinned fork, builds the BC variant, and imports `pyfvs.fvsbc`.
  - [x] After the matrix has run, set branch protection with the specification's four-context `PUT`, including `required_linear_history`, and read the rule back.
  - [x] Record the gate change in the changelog with its reason.
- [x] P3.2 Build the standalone `FVSbc` executable (#19) — **proven and not adopted**; `FVS_Compute` holds `COMPUTE` expressions and the summary was already available in memory (ADR 0009)
  - [x] Build `bin/FVSbc` from the patched fork, and record the command and its output.
  - [x] Run one case through it with a `DATABASE` output block, and confirm `FVS_Compute` and `FVS_Summary_Metric` are written.
  - [x] Record the recipe as a new ADR.
- [x] P3.3 Commit the mutation harness (#20)
  - [x] Write the harness so that a mutation which does not apply is an error rather than a pass.
  - [x] Register the mutations already recorded for the five prototype modules.
  - [x] Run it in CI, or record why not.
- [x] P3.4 The public API over the five contracts, and three open decisions (#21)
  - [x] Export the five modules' public names, with `__all__` and numpydoc docstrings.
  - [x] Resolve the record-versus-dataframe question in `outputs.rst`.
  - [x] Resolve the species-assignment question in `nemora-ingest.rst`.
  - [x] Resolve the `BECINFO` question in `keywords.rst`.
  - [x] Add the API pages, and extend `tests/test_api_docstrings.py` to cover the package.
- [x] P3.5 Run orchestration (#22)
  - [x] Write the orchestration over the five prototype modules.
  - [x] Return the outputs with the provenance record, and fail a run that holds an error.
  - [x] Test it end to end, skipping when the built extension is absent and recording the skip.
- [x] P3.6 The command-line entry point (#23)
  - [x] Write the command over the orchestration.
  - [x] Test its exit codes for success, a failed run, and bad input.
  - [x] Document it in the README and in `docs/`.

Acceptance criteria:

- The quality job runs on Python 3.11 and 3.12, and protection requires all four contexts the workflow spec names.
- The pinned fork's BC variant builds from a clean checkout in CI.
- The standalone executable writes `FVS_Compute` and `FVS_Summary_Metric`.
- The mutation harness reproduces a named mutation failing a named test.
- One synthetic run through the public API returns outputs carrying provenance.
- The command-line entry point runs a case end to end.
- `python scripts/dashboard.py` exits zero on both Python versions.

## Phase 4: Verify

Parent issue: #25
Branch: `feature/p4-verify`
Status: active

Goal: show that the build meets its acceptance criteria, and record the evidence in the changelog.

The detail for this phase is the focused plan `notes/p4-verify.md`, which carries each task's sections,
the phase criteria, the order and its reason, and the open proposals.

- [x] P4.1 The acceptance checks, from a clean checkout (#26)
  - [x] Build the variant from the pin in a clean checkout, and record the command, the exit status, and the import.
  - [x] Run the full suite there, and record the count and the skips with their reasons.
  - [x] Run the command on the synthetic population, and record the exit status and the outputs.
  - [x] Record each of `P3`'s seven criteria with the evidence that produces it.
- [x] P4.2 Promote the oracle comparison into a repository test (#27)
  - [x] Establish where the official case data comes from, and whether it may be committed, with its licence.
  - [x] Write the comparison as a repository test, skipping with a recorded reason when the data or the build is absent.
  - [x] Record the result, including the stands and rows it covers and the columns it does not.
- [x] P4.3 Make the dashboard's 3.11 evidence literal (#28) — both interpreters in the existing job, chosen by the maintainer, so no protection change
  - [x] Choose between running the script under both interpreters in the existing job and renaming the context with protection changed in the same approved move.
  - [x] Write the change and the protection change, with its exact command, as a proposal.
  - [x] After approval, run it and read the protection back.
- [x] P4.4 Close the `__all__` gap (#29) — **its premise was false**: the assertion exists since `6e99a41`, so the task became proving it can fail
  - [x] Add a mutation the harness catches, so the existing assertion's falsifiability is reproducible.
  - [x] Assert that `__all__` holds no duplicate, which nothing else checks.

Acceptance criteria:

- Each of `P3`'s seven acceptance criteria has evidence recorded in the changelog, with the command or run id that produces it.
- The oracle comparison runs from the repository against the committed or fetched case data, and its result is recorded.
- `python scripts/dashboard.py` exits zero on 3.11 and 3.12 in CI, with the protection contexts still matching the four the workflow spec names.
- Every name in the package's `__all__` resolves, asserted by a test.
- `python scripts/dashboard.py` exits zero on the head commit of the phase branch.

## Phase 5: Release and deploy

Parent issue: TBD
Branch: `feature/p5-release`
Status: planned

Goal: tag a release, publish the docs, and verify the published artifacts from a clean checkout.

- [ ] P5.1 Write the release notes and the known-gaps list
- [ ] P5.2 Tag, publish, and verify from a clean checkout (maintainer approval required)

Acceptance criteria:

- <State the criterion that shows this phase met its goal.>

## Phase 6: Operate and maintain

Parent issue: TBD
Branch: `feature/p6-operate`
Status: planned

Goal: keep the project current: triage incoming ideas, review on a cadence, and close out cleanly.

- [ ] P6.1 Set a review cadence and record the first review

Acceptance criteria:

- <State the criterion that shows this phase met its goal.>

## Detailed Next Steps Notes

The substance of these notes now lives in the focused plans under `notes/`, which is where the workflow
model puts detail too long for this roadmap. What stays here is the ordering and the open decisions.

1. The prototype's plan, and the phase's detail, are in `notes/p2-contracts-and-prototype.md`. It
   carries each task's sections, the phase criteria with their evidence, the deviations, and four
   proposals for the maintainer.
2. **Open, and the maintainer's: the CI quality matrix.** `.github/workflows/ci.yml` runs one `quality`
   job on Python 3.12, where `docs/reference/quality-gates.rst` in the workflow spec requires 3.11 and
   3.12 and names the contexts `Quality gates, Python 3.11` and `Quality gates, Python 3.12`. Changing
   CI or branch protection is a settings change. Recommendation in the plan, proposal 2.
3. **Open, and the maintainer's: `ADR 0004` is still `Status: proposed`**, although its task is closed
   and the phase's third acceptance criterion rests on it. It also contradicts itself and names the
   wrong task issue. Recommendation in the plan, proposal 3.
4. **Open: `FVS_Compute` and `FVS_Summary_Metric` are unreachable through PyFVS**, which occupies the
   `DATABASE` output block. Recommendation in the plan, proposal 1.
5. **Proposed adjacent work, not started: promote the oracle comparison into a repository test that can
   fail.** Every comparison so far was an ad hoc script outside the repository, and three of them were
   buggy in ways that produced false findings. A test that runs the first official case and asserts zero
   differing lines would have caught them, and it needs a task of its own.
6. **Proposed: pin the workflow revision in `AGENTS.md`.** It names the workflow spec with no path, URL,
   or revision, and the project carries no local copy of the pages that govern it. Recommendation in the
   plan, and the upstream gap is to be filed under `P2.5`.
