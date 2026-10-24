# The acceptance checks, run from a clean checkout

The record `P4.1` (#26) produces. It is what a reader re-runs to check that `P3`'s seven acceptance
criteria hold, and it says for each one what the check does **not** show.

Date: 2026-10-24
Issues: #26
Phase: P4
Fork: `UBC-FRESH/PyFVS` at `e95172b`, cloned fresh, FVS source submodule at `ef5fa847`, volume
submodule at `97d2070e`

## The two pins the record carries match the clean checkout

`src/fresh_fvsbc/provenance.py` pins `PYFVS_COMMIT = "e95172b"` and `FVS_SOURCE_COMMIT = "ef5fa847"`,
and the fresh clone reports exactly those. That is a check the project could not previously make,
because every build so far came from a working tree that already carried the patches.

## The build

```text
git clone --filter=blob:none https://github.com/UBC-FRESH/PyFVS.git  -> exit 0
git checkout e95172b                                                 -> fork at e95172b
git submodule update --init --recursive                              -> fvs at ef5fa847, volume at 97d2070e
git apply --check notes/reference/pyfvs-patchset.diff.gz             -> applies cleanly
git apply         notes/reference/pyfvs-patchset.diff.gz             -> applied
git apply --check notes/reference/fvsbc-patchset.diff.gz             -> applies cleanly
git apply         notes/reference/fvsbc-patchset.diff.gz             -> applied
SETUPTOOLS_SCM_PRETEND_VERSION=0.3.11 python -m pip install --no-build-isolation . \
    --config-settings=setup-args="-Dfvsvariants=bc"                  -> exit 0
python -c "import pyfvs; pyfvs.list_variants()"                      -> {'BC': {'lib': 'pyfvs.fvsbc', 'status': 'OK'}}
```

Both patch sets apply to a checkout that has never held them, and the import reports BC as `OK`.

### The toolchain differs from CI's, and it worked anyway

CI installs `gfortran meson ninja-build patchelf` from `apt`. Here `gfortran` 13.3.0 was present,
`meson` and `ninja` came from `pip` into a throwaway venv, and **`patchelf` was not installed at all**.

**The first attempt failed**, with:

```text
meson-python: error: meson executable "meson" not found
error: metadata-generation-failed
```

`pip install meson` puts the executable in the venv's `bin`, and `meson-python` looks for it on
`PATH`. With `PATH` set, the build succeeded.

**That message is worth recording for its own sake.** CI's first build failure in `P3`, run
`40040321924`, carried the same final line, `error: metadata-generation-failed`, from a completely
different cause: a patch set that had never been banked. The message names a phase of the build, not a
fault, and reading it as the diagnosis would have sent this check after the wrong thing.

**`patchelf` is not required by this path.** Whether a wheel built for distribution needs it is not
established here, and this note does not claim it either way.

## The suite, in that environment

```text
python -m pytest                -> exit 0
370 passed, 2 skipped in 29.08s
Required test coverage of 95% reached. Total coverage: 98.92%
```

**Both skips are the mirror image of the project's own environment.** They are
`tests/test_command.py` and `tests/test_run.py`'s tests that the extension is *absent*, and they skip
here precisely because it is present, with the reason "the extension is present here, so its absence
cannot be shown". In the project's environment those two pass and the end-to-end test skips instead.
Neither environment skips silently.

Coverage rises from 98.15 percent to 98.92 percent, and the reason is the same: the end-to-end test
runs here, so `run.py`'s drive body is executed. It reports **96 percent**, and the four uncovered
lines are the `ExtensionUnavailableError` paths, which cannot run when the extension is present. The
two environments cover each other's gaps, which is why the gate is met in both.

```text
src/fresh_fvsbc/cli.py             68      0     12      0   100%
src/fresh_fvsbc/run.py            117      4     22      2    96%
TOTAL                            1196     10    374      7    99%
```

## The command, in that environment

```text
python -m fresh_fvsbc population.json --directory run --species FD --tree-age 60 \
  --keyword "STDIDENT=SYNTHETIC   P4.1 acceptance" --keyword STDINFO=712,CHS131,0,200,35,16 \
  --keyword MANAGED=0,1 --keyword SITECODE=FD,100 --keyword INVYEAR=0 \
  --keyword DESIGN=0,1,999,1,0,1,1 --keyword NUMCYCLE=4 --keyword RANNSEED=1 \
  --keyword ECHOSUM --keyword PROCESS --keyword STOP
```

Exit `0`, and:

```text
case fc4195d3-460f-44a2-93bb-3d6ea5d287f3
ran bc in .../run
summary: 5 rows, 22 columns
warnings: 1
provenance: .../run/provenance.json
```

The directory holds `FVSOut.db`, `provenance.json`, `pyfvs.log`, `run.key`, `run.out`, `run.sum` and
`run.tre`. The one warning is the `FVS03` site-code warning the synthetic stand always produces.

## The dashboard, in that environment

```text
lint GREEN | format GREEN | types GREEN | tests GREEN | validator GREEN | docs GREEN
OVERALL: GREEN. Every gate passed.
```

## The seven criteria, with what each check does not show

| Criterion | Evidence | What it does not show |
| --- | --- | --- |
| The quality job runs on 3.11 and 3.12, and protection requires the four contexts | The protection read-back lists `Green dashboard summary`, `Pre-commit parity`, `Quality gates, Python 3.11`, `Quality gates, Python 3.12`, with `required_linear_history: true`. CI runs the quality job on both | That the contexts are *correct*, only that they are required. A required context that checked nothing would read the same |
| The pinned fork's BC variant builds from a clean checkout in CI | CI run `40073616342`, and this note's build on a second machine from a clone that never held the patches | That the build is reproducible **byte for byte**. Two toolchains, two binaries. It shows the recipe is not specific to CI's `apt` packages, and not specific to this repository's working tree |
| The standalone executable writes `FVS_Compute` and `FVS_Summary_Metric` | `CHANGE_LOG.md`'s `P3.2` entry, commit `fdbdc29`: the official case exits 0 and writes `FVS_Compute` (160 rows) and `FVS_Summary_Metric` (164 rows), with `FVS_Cases` at four rows and `FVS_Error` absent | That the standalone is adopted. It is not (ADR 0009), and this phase did not re-run it. The row counts are quoted from that entry, not re-derived here |
| The mutation harness reproduces a named mutation failing a named test | `python scripts/mutation_check.py` reports `23 of 23 mutations caught`, and the harness exits non-zero when an anchor does not match | That the mutation set is complete. It shows every mutation **in the set** is caught, and the set is the author's choice |
| One synthetic run through the public API returns outputs carrying provenance | The command above goes through `run_population` and `run_case`, and `tests/test_run.py`'s end-to-end test passes here: 370 passed, 2 skipped | That the outputs are **right**. Matching the oracle is `P2.3`'s comparison, which is not reproducible from the repository, and is `P4.2` |
| The command-line entry point runs a case end to end | The command above, exit `0`, and the seven files it left | That every exit code is exercised end to end. `1` and `2` are tested with a faked drive and in a subprocess, not by a real failing run |
| `python scripts/dashboard.py` exits zero on both Python versions | Green here on 3.12; in CI the script runs on 3.12 and the six gates it wraps run on both | **The script itself on 3.11.** This is the one criterion met in substance rather than in letter, and `P4.3` (#28) is where it closes |

## What this note does not establish

- **That the results are correct**, only that they reproduce. Correctness against BC's own output is
  `P2.3`'s comparison and `P4.2`'s test.
- **That CI's toolchain is the one used here.** It is not: `meson` and `ninja` came from `pip` and
  `patchelf` was absent. The build's dependence on those three is not measured.
- **Anything about a distribution wheel**, a tag, or a release. That is `P5`.

## The oracle comparison, and what it found

`P4.2` (#27) turned `P2.3`'s ad hoc comparison into `tests/test_oracle.py`. It runs the command the FVS
project's own `tests/FVSbc/makefile` runs, and it passes:

```text
8 passed
zero differing lines across 164 rows, four stands
FVS_Compute: 160 rows, with Year, SMVOL, MDVOL and LGVOL
```

**Wired into CI's build job beside the end-to-end test, it failed on 104 of 164 rows**, in three
columns:

| Column | Produced against the oracle |
| --- | --- |
| `Tpa` | 2416 against 2414, 2134 against 2132, 1887 against 1882 |
| `CCF` | 8 against 9 |
| `CU M` | 54 against 53, 36 against 35 |

**The cause is not the toolchain, and the first reading of this record said it was.** Three hypotheses
were tested and each is dead:

- **The compiler version.** CI's `gfortran` is 13.3.0-6ubuntu2~24.04.1, **the same as the machine that
  passes**, printed by the build job since this was asked.
- **The instruction set.** The build passes no `-march`, and disabling AVX-512 and AVX2 through
  `GLIBC_TUNABLES` on the passing machine changes nothing.
- **The inputs.** The case's key, oracle and input database are byte-identical to the pinned commit
  `ef5fa847`.

**What it is: FVS keeps its state in the process, not in the working directory.** Two runs on the same
machine, from the same build, in two fresh directories, disagree when the second follows another
projection. The test passed alone and failed with `tests/test_run.py` first, in the same pytest
process, on both machines. A diagnostic step on the runner that ran the case twice in one process
reported **zero** differing rows against the oracle for both, and the same step with the end-to-end
test ahead of it reports 104.

**The test therefore runs its case in a child process**, and it passes in either order: 34 passed, 1
skipped with both files in one process. It is now a gate in CI's build job, with `FVSBC_CASE_DIR` set
to the clone that job already makes. No tolerance was needed, and none was added.

**This is a property of the library, not only of the test.** `run_case` is not re-entrant in a process:
a second run inherits the first one's Fortran state. Two runs in one process are therefore not
independent, and the directory isolation `run.py` documents is not enough on its own. That is recorded
here and is a candidate for a task of its own.
