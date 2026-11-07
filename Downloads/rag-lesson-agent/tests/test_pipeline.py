import os
from pathlib import Path
import pytest
from lesson_agent.cli import main
from lesson_agent.rubric import run_det

os.environ["LLM_PROVIDER"] = "mock"


@pytest.fixture(autouse=True)
def mem(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "m.json"))
    monkeypatch.chdir(tmp_path)


def test_clean_run_passes_first_try():
    st = main(["run", "--out", "o"])
    assert st["status"] == "PASSED" and st["attempt"] == 1 and st["rejections"] == []


def test_injected_error_is_caught_then_fixed():
    st = main(["run", "--inject-error", "--out", "o"])
    ids = {f["id"] for f in st["rejections"][0]["failed"]}
    assert {"J1", "D5"} <= ids                       # false claim + jargon both caught
    assert st["status"] == "PASSED" and st["attempt"] == 2
    assert Path("o/lesson.md").exists() and Path("o/rejection_log.md").exists()


def test_loop_terminates_and_never_ships_unverified():
    st = main(["run", "--inject-error", "--max-retries", "0", "--out", "o"])
    assert st["status"] == "NEEDS_HUMAN_REVIEW"
    assert not Path("o/lesson.md").exists() and Path("o/lesson.NEEDS_REVIEW.md").exists()


def test_memory_learns_and_persists():
    main(["run", "--inject-error", "--out", "o"])
    import json
    m = json.load(open(os.environ["MEMORY_PATH"]))
    assert m["learned_rules"] and m["check_stats"]["J1"]["fails"] == 1


def test_reference_lesson_passes_deterministic_checks():
    md = (Path(__file__).parents[1] / "docs/final_lesson_REFERENCE.md").read_text()
    bad = [r for r in run_det(md) if not r["passed"]]
    assert not bad, bad
