from scripts.demo_happy_path import run_demo


def test_happy_path_demo_runs():
    transcript = run_demo()
    assert any("orchestrator" in step for step in transcript)
    assert any("snapshot" in step for step in transcript[-1:])
