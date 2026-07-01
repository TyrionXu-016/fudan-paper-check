CREATE SCHEMA IF NOT EXISTS "fudan_pager";
SET search_path TO "fudan_pager";

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR NOT NULL,
    email VARCHAR NOT NULL,
    name VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL,
    PRIMARY KEY (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
ALTER TABLE "users" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_projects (
    id VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    initiator_role VARCHAR NOT NULL,
    advisor_id VARCHAR,
    advisor_email VARCHAR,
    student_id VARCHAR,
    student_email VARCHAR,
    rule_base_ids_json TEXT NOT NULL,
    status VARCHAR NOT NULL,
    current_round INTEGER NOT NULL,
    auto_notify_student BOOLEAN NOT NULL,
    created_at VARCHAR NOT NULL,
    updated_at VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(advisor_id) REFERENCES users (id),
    FOREIGN KEY(student_id) REFERENCES users (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_projects_advisor_id ON mse_projects (advisor_id);
CREATE INDEX IF NOT EXISTS ix_mse_projects_student_id ON mse_projects (student_id);
ALTER TABLE "mse_projects" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_activity (
    id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    user_id VARCHAR,
    event VARCHAR NOT NULL,
    summary TEXT NOT NULL,
    created_at VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES mse_projects (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_activity_created_at ON mse_activity (created_at);
CREATE INDEX IF NOT EXISTS ix_mse_activity_project_id ON mse_activity (project_id);
ALTER TABLE "mse_activity" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_invite_tokens (
    token VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    target_role VARCHAR NOT NULL,
    target_email VARCHAR NOT NULL,
    expires_at VARCHAR NOT NULL,
    used_at VARCHAR,
    PRIMARY KEY (token),
    FOREIGN KEY(project_id) REFERENCES mse_projects (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_invite_tokens_project_id ON mse_invite_tokens (project_id);
ALTER TABLE "mse_invite_tokens" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_issue_dismissals (
    id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    fingerprint VARCHAR NOT NULL,
    dismissed_by VARCHAR NOT NULL,
    reason TEXT NOT NULL,
    dismissed_at VARCHAR NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (project_id, fingerprint),
    FOREIGN KEY(project_id) REFERENCES mse_projects (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_issue_dismissals_project_id ON mse_issue_dismissals (project_id);
ALTER TABLE "mse_issue_dismissals" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_submission_rounds (
    id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    round_number INTEGER NOT NULL,
    job_id VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    issue_count INTEGER NOT NULL,
    error_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    gate_passed BOOLEAN,
    gate_reason TEXT NOT NULL,
    notify_target VARCHAR,
    diff_json TEXT,
    submitted_at VARCHAR NOT NULL,
    analyzed_at VARCHAR,
    released_at VARCHAR,
    PRIMARY KEY (id),
    UNIQUE (project_id, round_number),
    FOREIGN KEY(project_id) REFERENCES mse_projects (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_submission_rounds_job_id ON mse_submission_rounds (job_id);
CREATE INDEX IF NOT EXISTS ix_mse_submission_rounds_project_id ON mse_submission_rounds (project_id);
ALTER TABLE "mse_submission_rounds" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_innovation_reviews (
    id VARCHAR NOT NULL,
    project_id VARCHAR NOT NULL,
    round_id VARCHAR NOT NULL,
    llm_summary TEXT NOT NULL,
    novelty_score FLOAT,
    comparison_notes TEXT NOT NULL,
    strengths_json TEXT NOT NULL,
    weaknesses_json TEXT NOT NULL,
    suggested_questions_json TEXT NOT NULL,
    advisor_comment TEXT NOT NULL,
    advisor_decision VARCHAR,
    reviewed_at VARCHAR,
    created_at VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(project_id) REFERENCES mse_projects (id),
    FOREIGN KEY(round_id) REFERENCES mse_submission_rounds (id)
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mse_innovation_reviews_project_id ON mse_innovation_reviews (project_id);
CREATE INDEX IF NOT EXISTS ix_mse_innovation_reviews_round_id ON mse_innovation_reviews (round_id);
ALTER TABLE "mse_innovation_reviews" ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS mse_issues (
    id VARCHAR NOT NULL,
    round_id VARCHAR NOT NULL,
    job_id VARCHAR NOT NULL,
    fingerprint VARCHAR NOT NULL,
    code VARCHAR NOT NULL,
    severity VARCHAR NOT NULL,
    issue_type VARCHAR,
    category VARCHAR NOT NULL,
    page INTEGER,
    section VARCHAR,
    message TEXT NOT NULL,
    revision_hint TEXT NOT NULL,
    rule_ref VARCHAR,
    original_text TEXT NOT NULL,
    created_at VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(round_id) REFERENCES mse_submission_rounds (id)
);
CREATE INDEX IF NOT EXISTS ix_mse_issues_fingerprint ON mse_issues (fingerprint);
CREATE INDEX IF NOT EXISTS ix_mse_issues_job_id ON mse_issues (job_id);
CREATE INDEX IF NOT EXISTS ix_mse_issues_round_id ON mse_issues (round_id);
ALTER TABLE "mse_issues" ENABLE ROW LEVEL SECURITY;
