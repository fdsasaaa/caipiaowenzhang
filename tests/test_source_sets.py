from engine.source_sets import brbcw_selected_ids


def test_brbcw_selected_source_set_has_2406_unique_ids():
    ids = brbcw_selected_ids()
    assert len(ids) == 2406
    assert len(set(ids)) == 2406
