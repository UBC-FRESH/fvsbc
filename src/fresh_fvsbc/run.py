"""The run orchestration.

This is where the five contracts meet. A run writes a keyword file, writes the tree list beside
it, drives BC through PyFVS's step API, reads the outputs back, and records its provenance. The
reference pages govern each part: :doc:`/reference/tree-list` the records,
:doc:`/reference/keywords` the set, :doc:`/reference/outputs` the read-back,
:doc:`/reference/provenance` the record, and :doc:`/reference/nemora-ingest` the adapter that feeds
it.

Three facts about the run are not choices, and each of them is a way to get a run quietly wrong

- **The tree-data file is named after the keyword file, in lowercase.** PyFVS computes its treelist
  path as ``keywords_path.with_suffix('.tre')`` and refuses to start when that file is absent, so a
  list written as ``.TRE`` passes FVS and fails PyFVS.
- **The output database has a fixed name.** ``dbsqlite/dbsblkd.f`` has ``DATA DSNOUT/"FVSOut.db"``,
  so the database lands in the working directory under that name whatever the keyword file is
  called. Two runs in one directory overwrite each other's database.
- **The tree-record format must be the variant's.** PyFVS injects its own ``TREEFMT`` when it is
  given a keyword *set*, using a default format rather than BC's. A run here passes a keyword
  *file*, so nothing is injected and BC's format is the only one a run can get.

Because the database's name is fixed, :func:`run_case` owns its working directory for the duration
of the drive and restores it afterwards. That is process-global state: another thread that changes
directory at the same moment will interfere, and a run is therefore not thread-safe. The alternative
is a subprocess per run, which loses ``FVS.summary``, the summary the output contract names as the
route to that table.

What the orchestration writes, and what it refuses
--------------------------------------------------

The caller writes the stand: ``STDIDENT``, ``STDINFO``, ``DESIGN``, ``NUMCYCLE``, ``SITECODE``, and
whatever else the case needs. The orchestration writes the tree handoff, which is ``TREEFMT`` with
BC's format and ``TREEDATA`` with a blank parameter, placed before the first ``PROCESS`` or ``STOP``
so that FVS reads the trees before it starts the projection. A set that already carries either
keyword is refused rather than quietly overridden, so nothing the caller wrote is replaced.

That insertion is a reading of the keyword contract's rule 4, which allows one exception, "the
tree-record format, which it must control". Without ``TREEDATA`` FVS never opens the tree file, so
the format and the instruction to use it are one handoff. The reading is recorded on
:doc:`/reference/keywords` rather than left to be inferred from this module.

The keyword hash covers what FVS read
-------------------------------------

Provenance is taken after the handoff is inserted, because a hash of the set the caller wrote would
identify a set no run ever saw.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from fresh_fvsbc.keywords import Keyword, KeywordSet
from fresh_fvsbc.nemora import PlotFields, to_tree_list
from fresh_fvsbc.outputs import check_run, read_cases
from fresh_fvsbc.provenance import Provenance, built_variants, from_cases, treelist_hash
from fresh_fvsbc.treelist import BC_TREFMT, TreeListFields, write_tree_file

__all__ = [
    "DATABASE_NAME",
    "KEYWORD_FILE_NAME",
    "PROVENANCE_FILE_NAME",
    "TREEFMT_LINES",
    "ExtensionUnavailableError",
    "KeywordConflictError",
    "RunError",
    "RunResult",
    "database_path",
    "run_case",
    "run_population",
    "tree_file_name",
    "treelist_format_lines",
    "with_tree_handoff",
]

#: The keyword file's name inside a run's directory. FVS and PyFVS both derive other names from it.
KEYWORD_FILE_NAME: str = "run.key"

#: The database's name, which ``dbsblkd.f`` fixes and no caller can change.
DATABASE_NAME: str = "FVSOut.db"

#: The provenance record's name, which the provenance contract puts beside the outputs.
PROVENANCE_FILE_NAME: str = "provenance.json"

#: The two keywords the orchestration writes, in the order FVS needs them.
TREE_FORMAT_KEYWORD: str = "TREEFMT"
TREE_DATA_KEYWORD: str = "TREEDATA"
_TREE_HANDOFF: tuple[str, ...] = (TREE_FORMAT_KEYWORD, TREE_DATA_KEYWORD)

#: The keywords that start and end a projection. The handoff goes before the first of them.
_PROJECTION_KEYWORDS: tuple[str, ...] = ("PROCESS", "STOP")

#: The point in BC's format where the format is split across the two lines FVS reads it from. It is
#: the split the variant's own keyword files use, and a split inside a group is safe because FVS
#: joins the two lines without padding.
_SPLIT_AFTER: str = "2I3,"


class RunError(Exception):
    """A run that could not be set up, driven, or read."""


class ExtensionUnavailableError(RunError):
    """PyFVS is not importable, or the variant it was asked for did not load."""


class KeywordConflictError(RunError):
    """A keyword set that carries a keyword the orchestration writes itself."""


def treelist_format_lines(format_string: str = BC_TREFMT) -> tuple[str, str]:
    """Split a tree-record format into the two lines FVS reads it from.

    ``TREEFMT`` takes its format from the two lines that follow it, and ``intree.f`` joins them
    without padding, so the split may fall inside a FORTRAN group. It falls where the variant's own
    keyword files put it.

    Parameters
    ----------
    format_string : str, optional
        The format to split. Defaults to BC's.

    Returns
    -------
    tuple of str
        The first and second line.

    Raises
    ------
    RunError
        If the format does not carry the split point. A format that cannot be split cannot be handed
        over, and guessing a split would produce a format FVS misreads.
    """
    cut = format_string.find(_SPLIT_AFTER)
    if cut < 0:
        raise RunError(f"the format has no {_SPLIT_AFTER!r} to split at: {format_string!r}")
    cut += len(_SPLIT_AFTER)
    return format_string[:cut], format_string[cut:]


#: BC's format, split into the two lines a ``TREEFMT`` keyword carries.
TREEFMT_LINES: tuple[str, str] = treelist_format_lines()


def database_path(directory: str | Path) -> Path:
    """Return the path of the database a run in ``directory`` writes.

    Parameters
    ----------
    directory : str or Path
        The run's directory.

    Returns
    -------
    Path
        ``directory/FVSOut.db``, the **default** ``DSNOUT`` that ``dbsblkd.f`` initialises. A
        keyword set carrying a ``DATABASE`` block with a ``DSNOUT`` option names another, and this
        function does not read it; the route this module runs carries no such block.
    """
    return Path(directory) / DATABASE_NAME


def tree_file_name(key_path: str | Path) -> Path:
    """Return the tree-data path PyFVS expects beside a keyword file.

    Parameters
    ----------
    key_path : str or Path
        The keyword file's path.

    Returns
    -------
    Path
        The same path with a lowercase ``.tre`` suffix. FVS would also accept ``.TRE``, but PyFVS
        checks for ``.tre`` and refuses to start without it, so the lowercase name is the only one
        that works through this route.
    """
    return Path(key_path).with_suffix(".tre")


def with_tree_handoff(keywords: Sequence[Keyword]) -> tuple[Keyword, ...]:
    """Return a keyword set with the tree handoff inserted, in the caller's order.

    The handoff goes before the first ``PROCESS`` or ``STOP``, because FVS reads the trees when it
    reaches ``TREEDATA`` and starts the projection at ``PROCESS``. A set that carries neither ends
    with the handoff.

    Parameters
    ----------
    keywords : Sequence of Keyword
        The caller's set, which describes the stand and the run.

    Returns
    -------
    tuple of Keyword
        The caller's keywords in order, with ``TREEFMT`` and ``TREEDATA`` inserted.

    Raises
    ------
    KeywordConflictError
        If the set already carries either keyword. Overriding it would replace something the caller
        wrote, which the keyword contract forbids.
    """
    given = tuple(keywords)
    carried = [keyword.name for keyword in given if keyword.name in _TREE_HANDOFF]
    if carried:
        raise KeywordConflictError(
            f"the keyword set carries {', '.join(carried)}, which the run writes itself"
        )
    handoff = (Keyword(TREE_FORMAT_KEYWORD, TREEFMT_LINES), Keyword(TREE_DATA_KEYWORD))
    for index, keyword in enumerate(given):
        if keyword.name in _PROJECTION_KEYWORDS:
            return (*given[:index], *handoff, *given[index:])
    return (*given, *handoff)


def _seed_of(keywords: Sequence[Keyword]) -> int | None:
    """Return the seed the set carries, or ``None`` when it carries none."""
    for keyword in keywords:
        if keyword.name != "RANNSEED":
            continue
        if len(keyword.parameters) != 1:
            raise RunError(f"RANNSEED takes one parameter, not {len(keyword.parameters)}")
        try:
            return int(keyword.parameters[0])
        except ValueError as error:
            raise RunError(f"RANNSEED is not a whole number: {keyword.parameters[0]!r}") from error
    return None


@contextmanager
def _working_directory(directory: Path) -> Iterator[Path]:
    """Change into ``directory`` for the duration of the block, and always restore."""
    previous = Path.cwd()
    os.chdir(directory)
    try:
        yield Path.cwd()
    finally:
        os.chdir(previous)


@dataclass(frozen=True, slots=True)
class _Drive:
    """What driving a projection yields: the in-memory summary, and the build's variant list."""

    summary: pd.DataFrame
    variants: tuple[str, ...]


def _drive(key_name: str, *, variant: str) -> _Drive:
    """Drive one projection through PyFVS's step API, from inside the run's directory.

    Parameters
    ----------
    key_name : str
        The keyword file's name, relative to the working directory.
    variant : str
        The variant to run, which for this project is ``bc``.

    Returns
    -------
    _Drive
        The summary the run produced in memory, and the build's variant list.

    Raises
    ------
    ExtensionUnavailableError
        If PyFVS is not importable, or the variant did not load.
    RunError
        If the projection ends with a non-zero return code.
    """
    if importlib.util.find_spec("pyfvs") is None:
        raise ExtensionUnavailableError(
            "pyfvs is not importable, so no variant can run; the build recipe is in ADR 0004 and a "
            "worked run is in notes/reference/fvsbc-smoke-run.md"
        )
    import pyfvs
    from pyfvs import fvs

    try:
        simulator = fvs.FVS(variant)
    except Exception as error:  # PyFVS raises its own types when a variant is absent
        raise ExtensionUnavailableError(f"the {variant} variant did not load: {error}") from error
    simulator.init_projection(key_name)
    for _ in range(int(simulator.globals.ncyc)):
        simulator.grow()
    code = int(simulator.end_projection())
    if code != 0:
        raise RunError(f"the projection ended with return code {code}")
    return _Drive(summary=simulator.summary, variants=built_variants(pyfvs.list_variants()))


def _first_case(cases: pd.DataFrame) -> dict[str, object]:
    """Return the first ``FVS_Cases`` row as a mapping, refusing an empty table."""
    if cases.empty:
        raise RunError("the run wrote no FVS_Cases row, so it cannot record its provenance")
    return {str(name): value for name, value in cases.iloc[0].items()}


@dataclass(frozen=True, slots=True)
class RunResult:
    """What a run returns: its tables, its provenance, and where it left them.

    Parameters
    ----------
    provenance : Provenance
        The record, as the provenance contract defines it.
    cases : pandas.DataFrame
        ``FVS_Cases``, which identifies the run.
    warnings : pandas.DataFrame
        The rows of ``FVS_Error`` whose severity is ``WARNING``. A row of severity ``ERROR`` raises
        instead, so a result never carries one.
    summary : pandas.DataFrame
        The summary the run produced in memory, which the output contract names as the route to
        that table through this API.
    directory : Path
        The run's directory, which holds the keyword file, the tree list, the database, the
        reports, and the provenance record.
    keyword_file : Path
        The keyword file written.
    database : Path
        The database read.
    """

    provenance: Provenance
    cases: pd.DataFrame
    warnings: pd.DataFrame
    summary: pd.DataFrame
    directory: Path
    keyword_file: Path
    database: Path


def run_case(
    records: Sequence[TreeListFields],
    keywords: Sequence[Keyword],
    *,
    directory: str | Path,
    variant: str = "bc",
    key_name: str = KEYWORD_FILE_NAME,
) -> RunResult:
    """Run one case: write the inputs, drive BC, read the outputs, and record the provenance.

    The caller describes the stand and the run in ``keywords`` and supplies the trees in
    ``records``. The orchestration writes the tree handoff, the keyword file, and the tree list,
    drives one projection in ``directory``, and reads the database back. A run that reports an error
    row raises rather than returning a result that holds one.

    Parameters
    ----------
    records : Sequence of TreeListFields
        The trees, in the order to write them. :func:`fresh_fvsbc.nemora.to_tree_list` builds these
        from a synthetic population.
    keywords : Sequence of Keyword
        The keyword set, in the order FVS will read it. It must not carry ``TREEFMT`` or
        ``TREEDATA``.
    directory : str or Path
        Where the run writes. It is created if it does not exist, and the run owns it: the
        database's name is fixed, so two runs in one directory would overwrite each other.
    variant : str, optional
        The variant to run. Defaults to ``bc``, which is the only variant this project wraps.
    key_name : str, optional
        The keyword file's name inside ``directory``. The tree file takes the same base name.

    Returns
    -------
    RunResult
        The tables, the provenance, and the paths.

    Raises
    ------
    KeywordConflictError
        If the keyword set carries a keyword the orchestration writes.
    UnknownKeywordError
        If the set carries a keyword FVS's table does not hold.
    ExtensionUnavailableError
        If PyFVS is not importable, or the variant did not load.
    RunFailedError
        If the run holds a row of severity ``ERROR``.
    MissingOutputError
        If the run wrote no database.
    RunError
        If the projection ends badly, or the run recorded no case.
    """
    handoff = with_tree_handoff(keywords)
    keyword_set = KeywordSet(handoff)
    target = Path(directory).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    keyword_file = target / key_name
    keyword_file.write_text(keyword_set.render())
    tree_file_name(keyword_file).write_text(write_tree_file(records))

    with _working_directory(target):
        driven = _drive(keyword_file.name, variant=variant)

    database = database_path(target)
    cases = read_cases(database)
    warnings = check_run(database)
    case_id, run_datetime = from_cases(_first_case(cases))
    provenance = Provenance(
        variant=variant,
        keyword_set_hash=keyword_set.digest,
        treelist_hash=treelist_hash(records),
        case_id=case_id,
        run_datetime=run_datetime,
        variant_list=driven.variants,
        random_seed=_seed_of(handoff),
    )
    provenance.write(target / PROVENANCE_FILE_NAME)
    return RunResult(
        provenance=provenance,
        cases=cases,
        warnings=warnings,
        summary=driven.summary,
        directory=target,
        keyword_file=keyword_file,
        database=database,
    )


def run_population(
    population: Sequence[Mapping[str, object]],
    *,
    directory: str | Path,
    species: str | None = None,
    tree_age: float | None = None,
    keywords: Sequence[Keyword] = (),
    variant: str = "bc",
    plot_fields: PlotFields | None = None,
    key_name: str = KEYWORD_FILE_NAME,
) -> RunResult:
    """Run one case built from a synthetic stem population.

    This is :func:`fresh_fvsbc.nemora.to_tree_list` followed by :func:`run_case`, and it exists
    because that pair is the project's own path from a population to a run. It adds no behaviour of
    its own, and the adapter's refusals are its refusals.

    Parameters
    ----------
    population : Sequence of Mapping
        The stems, shaped like `nemora`'s output.
    directory : str or Path
        Where the run writes.
    species : str, optional
        The species code. Required, because `nemora` emits none.
    tree_age : float, optional
        The age at breast height, in years. Required, for the same reason.
    keywords : Sequence of Keyword, optional
        The keyword set. The orchestration writes the tree handoff.
    variant : str, optional
        The variant to run. Defaults to ``bc``.
    plot_fields : PlotFields, optional
        The plot-level fields, which belong to a run.
    key_name : str, optional
        The keyword file's name inside ``directory``.

    Returns
    -------
    RunResult
        The tables, the provenance, and the paths.

    Raises
    ------
    MissingAssignmentError
        If ``species`` or ``tree_age`` is not supplied.
    PopulationError
        If a record is missing a field the adapter reads, or carries a non-numeric one.
    CrownRatioError
        If a crown ratio cannot be represented by the tree-list field.
    SpeciesError
        If the species code resolves to no BC species, or to more than one.
    RunError
        If the run cannot be set up, driven, or read.
    """
    records = to_tree_list(population, species=species, tree_age=tree_age, plot_fields=plot_fields)
    return run_case(records, keywords, directory=directory, variant=variant, key_name=key_name)
