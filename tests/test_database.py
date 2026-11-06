import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.load import build, parse_rank, run_named_queries  # noqa: E402


@pytest.mark.parametrize("label, expected", [
    ("17", ("17", 17, 17)), ("=17", ("=17", 17, 17)), ("6=", ("6=", 6, 6)),
    ("601-610", ("601-610", 601, 610)), ("1401+", ("1401+", 1401, None)),
    ("-", (None, None, None)), (None, (None, None, None)),
])
def test_parse_rank(label, expected):
    assert parse_rank(label) == expected


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    return build(db_path=tmp_path_factory.mktemp("db") / "test.db")


def test_one_row_per_university_in_every_table(con):
    n = con.execute("SELECT COUNT(*) FROM University").fetchone()[0]
    assert n == 1497
    for table in ("Rankings", "Research", "Reputation", "EmploymentOutcomes", "Sustainability", "FacultyStudents"):
        assert con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == n


def test_foreign_keys_hold(con):
    assert con.execute("PRAGMA foreign_key_check").fetchall() == []


def test_missing_scores_stay_null_not_zero(con):
    zeros = con.execute("SELECT COUNT(*) FROM Rankings WHERE overall_score = 0").fetchone()[0]
    nulls = con.execute("SELECT COUNT(*) FROM Rankings WHERE overall_score IS NULL").fetchone()[0]
    assert zeros == 0 and nulls == 895


def test_rank_bands_are_parsed(con):
    assert con.execute("SELECT COUNT(*) FROM Rankings WHERE rank_2024_min IS NULL").fetchone()[0] == 0


def test_named_queries_run(con):
    results = run_named_queries(con)
    assert {"coverage", "indicator_correlation", "employability_gap"} <= set(results)
    assert all(len(df) > 0 for df in results.values())
