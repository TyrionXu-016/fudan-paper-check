from schema.models import JobRecord, JobStatus
from storage.jobs import JobStore


def test_job_store_reloads_external_updates(tmp_path, monkeypatch):
    monkeypatch.setattr("storage.jobs.STORAGE", tmp_path)
    store = JobStore()
    queued = JobRecord(job_id="job-1", status=JobStatus.QUEUED)
    done = JobRecord(job_id="job-1", status=JobStatus.DONE)

    store.save(queued)
    (tmp_path / "job-1.json").write_text(
        done.model_dump_json(indent=2),
        encoding="utf-8",
    )

    assert store.get("job-1").status == JobStatus.DONE
