-- PostgreSQL schema for class_dataset.csv
--
-- One student per survey row. tools and availability hold several
-- semicolon-separated values per row, so each is a lookup table plus
-- a bridge table (many-to-many). Skill ratings stay on students.
--
-- Create parents before bridges.

CREATE TABLE students (
    student_id            INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    netid                 TEXT NOT NULL UNIQUE,
    name                  TEXT NOT NULL,
    school_year           TEXT NOT NULL,
    intro_programming     TEXT NOT NULL,
    skill_programming     SMALLINT NOT NULL,
    skill_data_stats      SMALLINT NOT NULL,
    skill_frontend_design SMALLINT NOT NULL,
    skill_business_pitch  SMALLINT NOT NULL,
    working_style         TEXT NOT NULL,
    interests             TEXT NOT NULL,
    semester_goal         TEXT NOT NULL,
    submitted_at          TIMESTAMP WITH TIME ZONE NOT NULL,

    CONSTRAINT students_school_year_chk
        CHECK (school_year IN ('First-year', 'Sophomore', 'Junior', 'Senior')),

    CONSTRAINT students_intro_programming_chk
        CHECK (intro_programming IN ('took_it', 'equivalent', 'neither')),

    CONSTRAINT students_skill_programming_chk
        CHECK (skill_programming BETWEEN 1 AND 5),

    CONSTRAINT students_skill_data_stats_chk
        CHECK (skill_data_stats BETWEEN 1 AND 5),

    CONSTRAINT students_skill_frontend_design_chk
        CHECK (skill_frontend_design BETWEEN 1 AND 5),

    CONSTRAINT students_skill_business_pitch_chk
        CHECK (skill_business_pitch BETWEEN 1 AND 5)
);

CREATE TABLE tools (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE availability (
    id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE student_tools (
    student_id INTEGER NOT NULL REFERENCES students (student_id),
    tool_id    INTEGER NOT NULL REFERENCES tools (id),
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE student_availability (
    student_id      INTEGER NOT NULL REFERENCES students (student_id),
    availability_id INTEGER NOT NULL REFERENCES availability (id),
    PRIMARY KEY (student_id, availability_id)
);

COMMENT ON TABLE students IS
    'One row per class survey response. student_id is generated; name is not unique.';

COMMENT ON COLUMN students.skill_programming IS
    'Self-rated programming skill, 1 (low) to 5 (high).';

COMMENT ON COLUMN students.skill_data_stats IS
    'Self-rated data and statistics skill, 1 (low) to 5 (high).';

COMMENT ON COLUMN students.skill_frontend_design IS
    'Self-rated frontend design skill, 1 (low) to 5 (high).';

COMMENT ON COLUMN students.skill_business_pitch IS
    'Self-rated business pitch skill, 1 (low) to 5 (high).';

COMMENT ON COLUMN students.submitted_at IS
    'Survey submission time, stored as a timestamp with time zone.';

COMMENT ON TABLE tools IS
    'Distinct tools named in the survey, such as Python or SQL.';

COMMENT ON TABLE availability IS
    'Distinct time slots named in the survey, such as Weekday mornings.';

COMMENT ON TABLE student_tools IS
    'Which students use which tools. A student can use many tools, and a tool can be used by many students.';

COMMENT ON TABLE student_availability IS
    'Which students are free in which time slots. A student can have many slots, and a slot can include many students.';
