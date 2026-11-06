-- QS World University Rankings 2024: normalised relational schema (SQLite).
-- One row per university in University; each indicator family lives in its own
-- one-to-one table keyed by university_id, mirroring the original ER design.

PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS FacultyStudents;
DROP TABLE IF EXISTS Sustainability;
DROP TABLE IF EXISTS EmploymentOutcomes;
DROP TABLE IF EXISTS Reputation;
DROP TABLE IF EXISTS Research;
DROP TABLE IF EXISTS Rankings;
DROP TABLE IF EXISTS University;
DROP TABLE IF EXISTS Country;

CREATE TABLE Country (
    country_code  TEXT PRIMARY KEY CHECK (length(country_code) = 2),
    country_name  TEXT NOT NULL
);

CREATE TABLE University (
    university_id    INTEGER PRIMARY KEY,
    institution_name TEXT NOT NULL UNIQUE,
    country_code     TEXT NOT NULL REFERENCES Country(country_code),
    size             TEXT CHECK (size IN ('S', 'M', 'L', 'XL')),
    focus            TEXT CHECK (focus IN ('CO', 'FC', 'FO', 'SP')),
    research_level   TEXT CHECK (research_level IN ('LO', 'MD', 'HI', 'VH')),
    age_band         INTEGER CHECK (age_band BETWEEN 1 AND 5),
    status           TEXT CHECK (status IN ('A', 'B', 'C'))
);

-- Ranks are published as exact positions ("17"), ties ("=17") or bands ("601-610", "1401+").
-- rank_label keeps the published text; rank_min / rank_max make it sortable and comparable.
CREATE TABLE Rankings (
    university_id   INTEGER PRIMARY KEY REFERENCES University(university_id),
    rank_2024_label TEXT,
    rank_2024_min   INTEGER,
    rank_2024_max   INTEGER,
    rank_2023_label TEXT,
    rank_2023_min   INTEGER,
    overall_score   REAL CHECK (overall_score BETWEEN 0 AND 100)  -- published only for the top ~600
);

CREATE TABLE Research (
    university_id                 INTEGER PRIMARY KEY REFERENCES University(university_id),
    citations_per_faculty_score   REAL,
    citations_per_faculty_rank    INTEGER,
    intl_research_network_score   REAL,
    intl_research_network_rank    INTEGER
);

CREATE TABLE Reputation (
    university_id              INTEGER PRIMARY KEY REFERENCES University(university_id),
    academic_reputation_score  REAL,
    academic_reputation_rank   INTEGER,
    employer_reputation_score  REAL,
    employer_reputation_rank   INTEGER
);

CREATE TABLE EmploymentOutcomes (
    university_id              INTEGER PRIMARY KEY REFERENCES University(university_id),
    employment_outcomes_score  REAL,
    employment_outcomes_rank   INTEGER
);

CREATE TABLE Sustainability (
    university_id         INTEGER PRIMARY KEY REFERENCES University(university_id),
    sustainability_score  REAL,
    sustainability_rank   INTEGER
);

CREATE TABLE FacultyStudents (
    university_id               INTEGER PRIMARY KEY REFERENCES University(university_id),
    faculty_student_score       REAL,
    faculty_student_rank        INTEGER,
    intl_faculty_score          REAL,
    intl_faculty_rank           INTEGER,
    intl_student_score          REAL,
    intl_student_rank           INTEGER
);

CREATE INDEX idx_university_country ON University(country_code);
