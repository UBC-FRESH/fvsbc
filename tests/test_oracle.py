"""The oracle comparison, as a test.

`P2.3` compared this build against FVS's own official case and recorded the result in
``notes/reference/fvsbc-validation.md``. The comparison was ad hoc scripts, so a reader could not
re-run it, and three of the claims it published were wrong for that reason.

This module is that comparison. It runs the command the FVS project's own ``tests/FVSbc/makefile``
runs:

.. code-block:: bash

   grep -v -- "-999" StandStructure.sum      > StandStructure.tmp
   grep -v -- "-999" StandStructure.sum.save > StandStructure.tmp.save
   diff -w StandStructure.tmp StandStructure.tmp.save

The case data is FVS's own and is **not** committed here, because its licence is not established and
``AGENTS.md`` says to treat BC inventory data as restricted until it is. The test finds it through
``FVSBC_CASE_DIR`` and skips with a reason that says how to set it.

**The comparison is exact, and it runs in its own process for a reason.** It first ran in CI beside
``tests/test_run.py`` and failed on 104 of 164 rows, in ``Tpa``, ``CCF`` and ``CU M``. The cause was
not the toolchain: **FVS keeps its state in the process**, so a case run after another projection
produces different numbers even in a different directory. Running the case in a child process makes
the comparison pass in either order, and it is now a gate in CI's build job. See
``notes/reference/p4-acceptance.md``.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from fresh_fvsbc.outputs import errors_in, read_errors

#: This file's directory, which the child process needs on its path.
TESTS: Path = Path(__file__).resolve().parent

#: The environment variable that names a PyFVS clone's ``fvs/tests/FVSbc``.
CASE_DIR_ENV: str = "FVSBC_CASE_DIR"

#: The case the comparison covers.
CASE: str = "StandStructure"

#: The oracle's rows once the four ``-999`` stand headers are dropped.
ORACLE_ROWS: int = 164

#: The rows ``FVS_Compute`` holds for the four stands: one per stand-period.
COMPUTE_ROWS: int = 160


def kept_lines(text: str) -> list[str]:
    """Return the lines ``grep -v -- "-999"`` would keep.

    Parameters
    ----------
    text : str
        The file's text.

    Returns
    -------
    list of str
        The lines that do not contain ``-999``, which are the stand headers in a summary.
    """
    return [line for line in text.splitlines() if "-999" not in line]


def differing_lines(produced: str, expected: str) -> list[tuple[int, str, str]]:
    """Return the line pairs that differ under ``diff -w`` semantics.

    ``diff -w`` compares lines and ignores whitespace within them, so two lines that hold the same
    tokens in the same order are equal however they are spaced. A line inserted or removed shifts
    every line after it and is therefore reported as a difference; ``diff`` would describe that as
    an insertion, and this function describes it as the lines that moved.

    Parameters
    ----------
    produced : str
        The summary the run wrote.
    expected : str
        The oracle.

    Returns
    -------
    list of tuple
        One ``(line number, produced line, expected line)`` per difference, in order. Empty when the
        run agrees with the oracle.
    """
    left = kept_lines(produced)
    right = kept_lines(expected)
    differences: list[tuple[int, str, str]] = []
    for index in range(max(len(left), len(right))):
        mine = left[index] if index < len(left) else ""
        theirs = right[index] if index < len(right) else ""
        if mine.split() != theirs.split():
            differences.append((index + 1, mine, theirs))
    return differences


def case_directory() -> Path:
    """Return the case directory named by ``FVSBC_CASE_DIR``.

    Returns
    -------
    Path
        The directory holding ``StandStructure.key`` and its oracle.

    Raises
    ------
    pytest.skip.Exception
        If the variable is unset, or the directory holds no case. The message says how to set it,
        because a skip that does not say what to do is indistinguishable from a test that never ran.
    """
    raw = os.environ.get(CASE_DIR_ENV)
    if not raw:
        pytest.skip(
            f"set {CASE_DIR_ENV} to a PyFVS clone's fvs/tests/FVSbc to run the oracle comparison"
        )
    directory = Path(raw)
    if not (directory / f"{CASE}.key").is_file():
        pytest.skip(f"{CASE_DIR_ENV}={directory} holds no {CASE}.key")
    return directory


def run_case(case: Path, workdir: Path) -> list[Path]:
    """Run the official case in ``workdir``.

    The step API is single-stand by design, and this case has four stands, so the run drives the
    native routine directly, which is the route ``P2.3`` established and the one the FVS project's
    own command takes.

    Parameters
    ----------
    case : Path
        The case directory.
    workdir : Path
        Where to run, which must be empty. FVS writes its summary and its database into the working
        directory, so the caller gives it one of its own.

    Returns
    -------
    list of Path
        The databases the run wrote, which are the ``.db`` files in ``workdir`` that were not copied
        in. **The output database's name is not assumed**: the case's keyword set names it with
        ``DSNOut``, so the name is a property of the key rather than of FVS.
    """
    from pyfvs import fvs

    shutil.copy(case / f"{CASE}.key", workdir)
    supplied = {database.name for database in case.glob("*.db")}
    for database in case.glob("*.db"):
        shutil.copy(database, workdir)
    previous = Path.cwd()
    os.chdir(workdir)
    try:
        simulator = fvs.FVS("bc")
        command = f"--keywordfile={CASE}.key"
        simulator.fvslib.fvssetcmdline(command, len(command))
        while int(simulator.fvslib.fvs()) == 0:
            pass
    finally:
        os.chdir(previous)
    return sorted(path for path in workdir.glob("*.db") if path.name not in supplied)


def run_case_in_child(case: Path, workdir: Path) -> list[Path]:
    """Run the official case in a child process, and return the databases it wrote.

    **FVS keeps its state in the process, not in the working directory.** A case run after another
    projection in the same process produces different numbers: this comparison passes alone and
    fails with 104 differing rows when ``tests/test_run.py`` runs first, which is how CI first ran
    it. So each case gets its own process, and that is a property of FVS rather than of this test.

    Parameters
    ----------
    case : Path
        The case directory.
    workdir : Path
        Where to run, which must be empty.

    Returns
    -------
    list of Path
        The databases the child wrote.

    Raises
    ------
    AssertionError
        If the child fails, with its standard error attached.
    """
    script = (
        "import sys; "
        "sys.path.insert(0, 'tests'); "
        "from pathlib import Path; "
        "from test_oracle import run_case; "
        f"run_case(Path({str(case)!r}), Path({str(workdir)!r}))"
    )
    finished = subprocess.run(
        [sys.executable, "-c", script],
        cwd=TESTS.parent,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(TESTS.parent / "src")},
    )
    if finished.returncode != 0:
        raise AssertionError(f"the child run failed: {finished.stderr[-2000:]}")
    supplied = {database.name for database in case.glob("*.db")}
    return sorted(path for path in workdir.glob("*.db") if path.name not in supplied)


def test_identical_text_has_no_differences() -> None:
    """The comparator's baseline: the same text twice agrees."""
    text = "2020  21  3140\n2024  25  3081\n"
    assert differing_lines(text, text) == []


def test_a_changed_digit_is_a_difference() -> None:
    """The comparison can fail, which is the whole point of having it."""
    produced = "2020  21  3140\n2024  25  3081\n"
    expected = "2020  21  3140\n2024  25  3082\n"
    assert differing_lines(produced, expected) == [(2, "2024  25  3081", "2024  25  3082")]


def test_a_spacing_difference_is_not_a_difference() -> None:
    """``diff -w`` compares tokens, so a wider column is not a disagreement."""
    assert differing_lines("2020 21 3140\n", "2020   21    3140\n") == []


def test_the_stand_headers_are_dropped_before_comparing() -> None:
    """The ``-999`` lines carry a timestamp, so comparing them would compare run times."""
    produced = "-999   41 101   NONE  2022 06-28-2022\n2020  21  3140\n"
    expected = "-999   41 101   NONE  2022 06-28-2022\n2020  21  3140\n"
    assert differing_lines(produced, expected) == []


def test_a_missing_line_is_a_difference() -> None:
    """A run that writes fewer rows disagrees, even if every row it wrote is right."""
    assert differing_lines("2020  21\n", "2020  21\n2024  25\n") == [(2, "", "2024  25")]


def test_an_unset_variable_skips_and_says_how_to_set_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A skip that does not say what to do is indistinguishable from a test that never ran."""
    monkeypatch.delenv(CASE_DIR_ENV, raising=False)
    with pytest.raises(pytest.skip.Exception, match=CASE_DIR_ENV):
        case_directory()


def test_a_directory_without_the_case_skips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The variable being set is not the same as the data being there."""
    monkeypatch.setenv(CASE_DIR_ENV, str(tmp_path))
    with pytest.raises(pytest.skip.Exception, match="holds no"):
        case_directory()


def test_the_official_case_matches_its_oracle(tmp_path: Path) -> None:
    """The comparison `P2.3` ran by hand, run as a test.

    It covers the database read, the tree decode, the metric units, the column order, the summary
    stride, and the establishment initialisation at once, because every one of them shows in the
    summary. It does **not** cover the second official case, `YSM-SkyRanch`, whose three stands
    still differ; see `notes/reference/fvsbc-validation.md`.
    """
    pytest.importorskip(
        "pyfvs", reason="the BC extension is not built in this environment; ADR 0004 is the recipe"
    )
    case = case_directory()
    workdir = tmp_path / "case"
    workdir.mkdir()
    written = run_case_in_child(case, workdir)
    assert len(written) == 1, f"the run wrote {len(written)} databases: {written}"

    produced = (workdir / f"{CASE}.sum").read_text(encoding="latin-1")
    expected = (case / f"{CASE}.sum.save").read_text(encoding="latin-1")
    differences = differing_lines(produced, expected)
    assert differences == []
    assert len(kept_lines(produced)) == ORACLE_ROWS

    database = written[0]

    # Read directly rather than through the reader: the output contract exposes only the tables it
    # has tested, and this checks the database rather than the reader's surface.
    connection = sqlite3.connect(database)
    try:
        tables = {
            row[0]
            for row in connection.execute("select name from sqlite_master where type='table'")
        }
        columns = [row[1] for row in connection.execute("pragma table_info('FVS_Compute')")]
        rows = connection.execute("select count(*) from FVS_Compute").fetchone()[0]
    finally:
        connection.close()

    assert rows == COMPUTE_ROWS
    assert {"Year", "SMVOL", "MDVOL", "LGVOL"} <= set(columns)

    # The case's `DATABASE` block does not ask for `FVS_Error`, so the table is **absent** rather
    # than empty, and "the run writes no error rows" is true vacuously. Both readings mean no error
    # row, and only one is reachable through the reader, so the test says which one it found.
    if "FVS_Error" in tables:
        assert errors_in(read_errors(database)).empty
