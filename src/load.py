"""Clean the QS 2024 CSV and load it into a normalised SQLite database.

Usage:  python -m src.load            (creates qs_rankings.db next to the repo root)
"""

import re
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "qs_world_rankings_2024.csv"
SCHEMA = ROOT / "sql" / "schema.sql"
DB = ROOT / "qs_rankings.db"


def parse_rank(label) -> Tuple[Optional[str], Optional[int], Optional[int]]:
    """'17' -> (17, 17); '=17' or '17=' -> tie at 17; '601-610' -> band; '1401+' -> open band."""
    if label is None or (isinstance(label, float) and pd.isna(label)):
        return None, None, None
    text = str(label).strip()
    if not text or text == "-":
        return None, None, None
    if m := re.fullmatch(r"=?(\d+)=?", text):
        n = int(m.group(1))
        return text, n, n
    if m := re.fullmatch(r"(\d+)\s*-\s*(\d+)", text):
        return text, int(m.group(1)), int(m.group(2))
    if m := re.fullmatch(r"(\d+)\+", text):
        return text, int(m.group(1)), None
    raise ValueError(f"Unrecognised rank format: {text!r}")


def to_number(series: pd.Series) -> pd.Series:
    """Strip tie markers and turn '-' or blanks into NULL. Missing is never replaced by 0."""
    return pd.to_numeric(series.astype(str).str.replace("=", "", regex=False).str.strip(), errors="coerce")


def read_clean(path: Path = CSV) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=[1])  # row 1 repeats the column codes
    numeric = [c for c in df.columns if c.endswith("Score") or c.endswith("Rank") and "RANK" not in c] + ["Overall SCORE", "AGE"]
    for c in numeric:
        df[c] = to_number(df[c])
    df = df.dropna(subset=["Institution Name"]).drop_duplicates(subset=["Institution Name"]).reset_index(drop=True)
    df.insert(0, "university_id", range(1, len(df) + 1))
    return df


def _none(v):
    return None if pd.isna(v) else (int(v) if isinstance(v, float) and v.is_integer() else v)


def build(db_path: Path = DB, csv_path: Path = CSV) -> sqlite3.Connection:
    df = read_clean(csv_path)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA.read_text())

    countries = df[["Country Code", "Country"]].drop_duplicates("Country Code")
    con.executemany("INSERT INTO Country VALUES (?, ?)", countries.itertuples(index=False, name=None))

    def rows(cols):
        return [tuple(_none(v) for v in r) for r in df[["university_id"] + cols].itertuples(index=False, name=None)]

    con.executemany("INSERT INTO University VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    rows(["Institution Name", "Country Code", "SIZE", "FOCUS", "RES.", "AGE", "STATUS"]))
    ranks = []
    for uid, r24, r23, score in df[["university_id", "2024 RANK", "2023 RANK", "Overall SCORE"]].itertuples(index=False, name=None):
        l24, min24, max24 = parse_rank(r24)
        l23, min23, _ = parse_rank(r23)
        ranks.append((uid, l24, min24, max24, l23, min23, _none(score)))
    con.executemany("INSERT INTO Rankings VALUES (?, ?, ?, ?, ?, ?, ?)", ranks)
    con.executemany("INSERT INTO Research VALUES (?, ?, ?, ?, ?)",
                    rows(["Citations per Faculty Score", "Citations per Faculty Rank",
                          "International Research Network Score", "International Research Network Rank"]))
    con.executemany("INSERT INTO Reputation VALUES (?, ?, ?, ?, ?)",
                    rows(["Academic Reputation Score", "Academic Reputation Rank",
                          "Employer Reputation Score", "Employer Reputation Rank"]))
    con.executemany("INSERT INTO EmploymentOutcomes VALUES (?, ?, ?)",
                    rows(["Employment Outcomes Score", "Employment Outcomes Rank"]))
    con.executemany("INSERT INTO Sustainability VALUES (?, ?, ?)",
                    rows(["Sustainability Score", "Sustainability Rank"]))
    con.executemany("INSERT INTO FacultyStudents VALUES (?, ?, ?, ?, ?, ?, ?)",
                    rows(["Faculty Student Score", "Faculty Student Rank", "International Faculty Score",
                          "International Faculty Rank", "International Students Score", "International Students Rank"]))
    con.commit()
    return con


def run_named_queries(con: sqlite3.Connection, path: Path = ROOT / "sql" / "queries.sql") -> dict:
    """Split queries.sql on '-- name: <id>' markers and return {id: DataFrame}."""
    blocks = re.split(r"^-- name: (\S+)\s*$", path.read_text(), flags=re.M)[1:]
    return {name: pd.read_sql_query(sql, con) for name, sql in zip(blocks[::2], blocks[1::2])}


if __name__ == "__main__":
    con = build()
    n = con.execute("SELECT COUNT(*) FROM University").fetchone()[0]
    print(f"Loaded {n} universities into {DB.name}")
