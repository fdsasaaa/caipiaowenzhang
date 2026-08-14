from engine.creator_quality_cli import main


def test_quality_entrypoint_is_callable():
    assert callable(main)
