import numpy as np
import pandas as pd
import pytest

from deepface_pad.round7 import choose_cases, pair_videos, subgroup_table


def fixture():
    meta = pd.DataFrame({"video_id": ["a", "b", "c", "d"], "subject_id": ["1"]*4,
                         "label": [0, 0, 1, 1], "attack_type": ["replay"]*2+["live"]*2,
                         "quality": ["low"]*4})
    e1 = meta[["video_id", "label"]].assign(score=[.6, .1, .1, .9])
    e3 = meta[["video_id", "label"]].assign(score=[.1, .6, .1, .9])
    return e1, e3, meta


def test_outcomes_boundary_denominators_and_missing_groups():
    a, b, meta = fixture()
    p = pair_videos(a, b, .5, .6, meta).assign(seed=44)
    assert p.role.tolist() == ["corrected", "new_errors", "both_wrong", "both_correct"]
    assert p.E3_error_type.tolist() == ["correct", "false_live", "false_spoof", "correct"]
    sub = subgroup_table(p)
    replay = sub[(sub.model == "E3") & (sub.stratum == "replay")]
    assert replay.denominator.tolist() == [2, 0]
    assert replay.errors.tolist() == [1, 0]
    assert np.isnan(replay.rate.iloc[1])


@pytest.mark.parametrize("change", ["missing", "label", "duplicate", "nan", "metadata"])
def test_pairing_fails_closed(change):
    a, b, meta = fixture()
    if change == "missing": b = b.iloc[:-1]
    if change == "label": b.loc[0, "label"] = 1
    if change == "duplicate": b = pd.concat([b, b.iloc[:1]])
    if change == "nan": b.loc[0, "score"] = np.nan
    if change == "metadata": meta = meta.iloc[:-1]
    with pytest.raises(ValueError): pair_videos(a, b, .5, .5, meta)


def test_selection_is_order_independent_and_middle_frame():
    a, b, meta = fixture()
    p = pair_videos(a, b, .5, .5, meta).assign(seed=43)
    frames = pd.concat([meta.assign(frame_index=i, sample_id=meta.video_id+str(i)) for i in range(20)])
    cases = choose_cases(p.sample(frac=1, random_state=9), frames.sample(frac=1, random_state=3))
    assert set(cases.frame_index) == {10}
    assert set(cases.role) == {"corrected", "new_errors", "both_wrong", "both_correct"}
