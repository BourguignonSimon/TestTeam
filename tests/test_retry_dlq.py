from scripts.demo_failure_retry_dlq import run_failure_demo


def test_failure_moves_to_dlq():
    transcript = run_failure_demo()
    assert any("dlq size: 1" in step for step in transcript)
