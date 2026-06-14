-- Initial schema for the Cloud AI Study Agent MVP.
-- SQLite is the default local database. PostgreSQL can use the same logical model.

CREATE TABLE IF NOT EXISTS courses (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    description VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS study_tasks (
    id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    course_id VARCHAR(36),
    prompt TEXT NOT NULL DEFAULT '',
    source_type VARCHAR(30) NOT NULL,
    source_name VARCHAR(255),
    material_text TEXT NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    result JSON,
    error TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE INDEX IF NOT EXISTS ix_courses_created_at ON courses(created_at);
CREATE INDEX IF NOT EXISTS ix_study_tasks_course_id ON study_tasks(course_id);
CREATE INDEX IF NOT EXISTS ix_study_tasks_status ON study_tasks(status);
CREATE INDEX IF NOT EXISTS ix_study_tasks_created_at ON study_tasks(created_at);
