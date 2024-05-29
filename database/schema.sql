CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    status VARCHAR(10) CHECK (status IN ('queued', 'ongoing', 'complete', 'error'))
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    job_id INTEGER REFERENCES jobs(id),
    number INTEGER
);