from pathlib import Path


def test_compose_defines_required_services():
    compose = Path("compose.yaml").read_text()

    for service in ("web:", "db:", "redis:", "worker:", "scheduler:"):
        assert service in compose


def test_production_image_runs_as_non_root():
    dockerfile = Path("Dockerfile").read_text()

    assert "USER elora" in dockerfile
    assert "HEALTHCHECK" in dockerfile
