"""The mutation harness.

A test that cannot fail is not evidence, and neither is a mutation that was never applied. Both
happened in `P2`: a severity rule that was unobservable, and a mutation whose anchor `ruff format`
had moved, which reported a pass because nothing was mutated at all. This harness exists so that
neither can happen silently.

How it works
------------

Each mutation names a source file, the exact text to replace, the replacement, and one test. The
harness applies the mutation, runs that test, and requires it to **fail**. Then it restores the file
and checks the restore byte for byte. If the anchor does not match exactly once, that is an error
rather than a pass, because a mutation that did not apply proves nothing.

Usage
-----

```bash
python scripts/mutation_check.py --list     # what is registered
python scripts/mutation_check.py --control  # the suite passes with nothing mutated
python scripts/mutation_check.py            # every mutation must fail its test
python scripts/mutation_check.py --only keywords
```
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]

__all__ = [
    "MUTATIONS",
    "Mutation",
    "MutationError",
    "check",
    "control",
    "main",
]


class MutationError(Exception):
    """A mutation that cannot be applied, or a file that cannot be restored."""


@dataclass(frozen=True, slots=True)
class Mutation:
    """One mutation, and the test that must catch it.

    Attributes
    ----------
    identifier : str
        A short name, used on the command line and in the report.
    module : str
        The source file, relative to the repository root.
    find : str
        The exact text to replace. It must occur exactly once.
    replace : str
        What to replace it with.
    test : str
        The pytest node that must fail while the mutation is applied.
    """

    identifier: str
    module: str
    find: str
    replace: str
    test: str


#: Every registered mutation. Two per prototype module, chosen for the behaviour each one protects.
MUTATIONS: tuple[Mutation, ...] = (
    Mutation(
        identifier="treelist-ignores-the-tab",
        module="src/fresh_fvsbc/treelist.py",
        find="        if field is None:\n            cursor = int(edit[1:])\n            continue",
        replace="        if field is None:\n            continue",
        test="tests/test_treelist.py::test_t1_puts_the_tree_number_back_at_column_one",
    ),
    Mutation(
        identifier="treelist-overwrites-the-plot-id",
        module="src/fresh_fvsbc/treelist.py",
        find="        placed[field] = (max(first, cursor), last)",
        replace="        placed[field] = (first, last)",
        test="tests/test_treelist.py::test_the_written_spans_tile_the_record_with_no_gap_or_overlap",
    ),
    Mutation(
        identifier="keywords-drops-the-misspelling-warning",
        module="src/fresh_fvsbc/keywords.py",
        find="    if keyword.name == MISSPELLED_KEYWORD:",
        replace="    if False:",
        test="tests/test_keywords.py::test_the_misspelled_keyword_warns_rather_than_failing",
    ),
    Mutation(
        identifier="keywords-ignores-the-order-in-the-hash",
        module="src/fresh_fvsbc/keywords.py",
        find="    text = render_keywords(keywords)",
        replace="    text = render_keywords(sorted(keywords, key=lambda k: k.name))",
        test="tests/test_keywords.py::test_the_hash_changes_when_the_order_changes",
    ),
    Mutation(
        identifier="nemora-copies-the-crown-ratio",
        module="src/fresh_fvsbc/nemora.py",
        find='            "crown_ratio": crown_class(_number(stem, "crown_ratio")),',
        replace='            "crown_ratio": int(_number(stem, "crown_ratio")),',
        test="tests/test_nemora_adapter.py::test_the_crown_ratio_becomes_a_class_the_field_can_hold",
    ),
    Mutation(
        identifier="nemora-skips-the-species-resolution",
        module="src/fresh_fvsbc/nemora.py",
        find="    resolved = resolve_species(species)",
        replace="    resolved = species",
        test="tests/test_nemora_adapter.py::test_the_supplied_species_is_resolved_before_it_is_written",
    ),
    Mutation(
        identifier="outputs-renames-the-columns",
        module="src/fresh_fvsbc/outputs.py",
        find="        return pd.DataFrame.from_records([dict(row) for row in cursor])",
        replace=(
            "        return pd.DataFrame.from_records("
            "[{k.lower(): v for k, v in dict(row).items()} for row in cursor])"
        ),
        test="tests/test_outputs.py::test_the_columns_are_the_databases_own_names",
    ),
    Mutation(
        identifier="outputs-exposes-every-table",
        module="src/fresh_fvsbc/outputs.py",
        find="    if table not in EXPOSED_TABLES:",
        replace="    if False:",
        test="tests/test_outputs.py::test_an_unexposed_table_is_refused_even_though_the_database_holds_it",
    ),
    Mutation(
        identifier="provenance-hashes-in-key-order",
        module="src/fresh_fvsbc/provenance.py",
        find='sort_keys=True, separators=(",", ":")',
        replace='sort_keys=False, separators=(",", ":")',
        test="tests/test_provenance.py::test_the_treelist_hash_does_not_depend_on_how_a_record_was_built",
    ),
    Mutation(
        identifier="provenance-accepts-a-failed-variant",
        module="src/fresh_fvsbc/provenance.py",
        find="    if failed:",
        replace="    if False:",
        test="tests/test_provenance.py::test_built_variants_refuses_a_variant_that_did_not_import",
    ),
    Mutation(
        identifier="keywords-drops-the-near-miss-hint",
        module="src/fresh_fvsbc/keywords.py",
        find='    for candidate in (name.upper(), f"x{name}", f"x{name.upper()}"):',
        replace="    for candidate in ():",
        test="tests/test_keywords.py::test_the_intended_spelling_is_refused_and_points_at_the_table",
    ),
    Mutation(
        identifier="package-exports-a-name-it-does-not-define",
        module="src/fresh_fvsbc/__init__.py",
        find='    "write_tree_record",',
        replace='    "write_tree_records",',
        test="tests/test_fresh_fvsbc_package.py::test_package_exports_only_names_it_defines",
    ),
    Mutation(
        identifier="command-reports-a-failed-run-as-bad-input",
        module="src/fresh_fvsbc/cli.py",
        find="        return EXIT_FAILED_RUN",
        replace="        return EXIT_BAD_INPUT",
        test="tests/test_command.py::test_a_run_that_holds_an_error_exits_one",
    ),
    Mutation(
        identifier="command-drops-a-blank-field",
        module="src/fresh_fvsbc/cli.py",
        find='    return Keyword(name, tuple(fields.split(",")))',
        replace='    return Keyword(name, tuple(field for field in fields.split(",") if field))',
        test="tests/test_command.py::test_a_keyword_keeps_its_blank_fields",
    ),
    Mutation(
        identifier="run-puts-the-handoff-after-the-projection",
        module="src/fresh_fvsbc/run.py",
        find="            return (*given[:index], *handoff, *given[index:])",
        replace="            return (*given, *handoff)",
        test="tests/test_run.py::test_the_handoff_goes_before_the_first_projection_keyword",
    ),
    Mutation(
        identifier="run-writes-an-uppercase-tree-file",
        module="src/fresh_fvsbc/run.py",
        find='    return Path(key_path).with_suffix(".tre")',
        replace='    return Path(key_path).with_suffix(".TRE")',
        test="tests/test_run.py::test_the_tree_file_is_lowercase_and_shares_the_keyword_files_base",
    ),
    Mutation(
        identifier="run-hashes-the-set-the-caller-wrote",
        module="src/fresh_fvsbc/run.py",
        find="        keyword_set_hash=keyword_set.digest,",
        replace="        keyword_set_hash=KeywordSet(keywords).digest,",
        test="tests/test_run.py::test_the_run_writes_the_inputs_the_record_and_the_result",
    ),
    Mutation(
        identifier="keywords-accepts-any-name",
        module="src/fresh_fvsbc/keywords.py",
        find="    if keyword.name not in KEYWORDS and keyword.name not in SPECIAL_KEYWORDS:",
        replace="    if False:",
        test="tests/test_keywords.py::test_an_unknown_keyword_is_rejected_and_named",
    ),
    Mutation(
        identifier="nemora-accepts-a-class-the-field-cannot-hold",
        module="src/fresh_fvsbc/nemora.py",
        find="    if not CROWN_CLASS_MIN <= nearest <= CROWN_CLASS_MAX:",
        replace="    if False:",
        test="tests/test_nemora_adapter.py::test_a_crown_ratio_the_field_cannot_hold_is_refused",
    ),
    Mutation(
        identifier="nemora-numbers-the-plots-wrongly",
        module="src/fresh_fvsbc/nemora.py",
        find="        plot_id = plots.setdefault(stand, len(plots) + 1)",
        replace="        plot_id = plots.setdefault(stand, len(records) + 1)",
        test="tests/test_nemora_adapter.py::test_plots_are_assigned_in_order_of_first_appearance",
    ),
    Mutation(
        identifier="outputs-treats-every-row-as-an-error",
        module="src/fresh_fvsbc/outputs.py",
        find='    return _rows_of_severity(table, "ERROR")',
        replace="    return table",
        test="tests/test_outputs.py::test_a_run_with_only_warnings_is_not_failed",
    ),
    Mutation(
        identifier="outputs-lets-the-last-severity-win",
        module="src/fresh_fvsbc/outputs.py",
        find=(
            "    for token in message.split():\n"
            "        if token in _SEVERITIES:\n"
            "            return _SEVERITIES[token]\n"
            '    return "UNKNOWN"'
        ),
        replace=(
            '    found = "UNKNOWN"\n'
            "    for token in message.split():\n"
            "        if token in _SEVERITIES:\n"
            "            found = _SEVERITIES[token]\n"
            "    return found"
        ),
        test="tests/test_outputs.py::test_the_first_severity_in_a_message_is_the_one_that_counts",
    ),
    Mutation(
        identifier="provenance-skips-the-cases-check",
        module="src/fresh_fvsbc/provenance.py",
        find="    if missing:",
        replace="    if False:",
        test="tests/test_provenance.py::test_from_cases_refuses_a_row_without_them",
    ),
    Mutation(
        identifier="provenance-hashes-in-sorted-order",
        module="src/fresh_fvsbc/provenance.py",
        find='        [dict(record) for record in records], sort_keys=True, separators=(",", ":")',
        replace=(
            '        [dict(record) for record in sorted(records, key=lambda r: r["tree_num"])], '
            "sort_keys=True"
        ),
        test="tests/test_provenance.py::test_the_treelist_hash_moves_with_the_order",
    ),
)


def apply(mutation: Mutation) -> str:
    """Apply a mutation, and return the file's original text.

    Parameters
    ----------
    mutation : Mutation
        The mutation to apply.

    Returns
    -------
    str
        The original text, so that :func:`restore` can put it back.

    Raises
    ------
    MutationError
        If the anchor does not occur exactly once, which means the mutation would not be applied and
        its test's failure would prove nothing.
    """
    path = ROOT / mutation.module
    original = path.read_text()
    occurrences = original.count(mutation.find)
    if occurrences != 1:
        raise MutationError(
            f"{mutation.identifier}: the anchor occurs {occurrences} times in {mutation.module}, "
            "and a mutation that does not apply proves nothing"
        )
    path.write_text(original.replace(mutation.find, mutation.replace))
    return original


def restore(mutation: Mutation, original: str) -> None:
    """Put a file back, and check that it is byte for byte what it was.

    Parameters
    ----------
    mutation : Mutation
        The mutation whose file is restored.
    original : str
        The text :func:`apply` returned.

    Raises
    ------
    MutationError
        If the restored file differs from the original.
    """
    path = ROOT / mutation.module
    path.write_text(original)
    if path.read_text() != original:
        raise MutationError(f"{mutation.identifier}: {mutation.module} was not restored")


def _pytest(node: str) -> bool:
    """Run one test node, and return whether it passed."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", node, "-q", "--no-cov", "-p", "no:cacheprovider"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def check(mutation: Mutation) -> bool:
    """Apply a mutation, require its test to fail, and restore the file.

    Parameters
    ----------
    mutation : Mutation
        The mutation to check.

    Returns
    -------
    bool
        ``True`` when the test failed under the mutation, which is what the harness requires.

    Raises
    ------
    MutationError
        If the mutation cannot be applied, or the file cannot be restored.
    """
    original = apply(mutation)
    try:
        caught = not _pytest(mutation.test)
    finally:
        restore(mutation, original)
    return caught


def control() -> bool:
    """Return whether the whole suite passes with nothing mutated.

    Returns
    -------
    bool
        ``True`` when the suite passes, which is the state a mutation run starts from.
    """
    return _pytest("tests")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the harness.

    Parameters
    ----------
    argv : Sequence of str, optional
        The command line, without the program name.

    Returns
    -------
    int
        Zero when every registered mutation was caught and every file was restored; one otherwise.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="list the registered mutations")
    parser.add_argument(
        "--control", action="store_true", help="require the suite to pass unmutated"
    )
    parser.add_argument(
        "--only", default=None, help="run only mutations whose identifier contains this"
    )
    arguments = parser.parse_args(argv)

    if arguments.list:
        for mutation in MUTATIONS:
            print(f"{mutation.identifier}\t{mutation.module}\t{mutation.test}")
        return 0

    if arguments.control:
        passed = control()
        print(f"control: the suite {'passes' if passed else 'fails'} with nothing mutated")
        return 0 if passed else 1

    selected = [
        mutation
        for mutation in MUTATIONS
        if arguments.only is None or arguments.only in mutation.identifier
    ]
    if not selected:
        print(f"no mutation matches {arguments.only!r}", file=sys.stderr)
        return 1

    failures = 0
    for mutation in selected:
        try:
            caught = check(mutation)
        except MutationError as error:
            print(f"ERROR  {error}", file=sys.stderr)
            failures += 1
            continue
        print(f"{'caught' if caught else 'MISSED'}  {mutation.identifier}")
        if not caught:
            failures += 1
    print(f"\n{len(selected) - failures} of {len(selected)} mutations caught")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
