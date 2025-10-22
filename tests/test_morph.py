import numpy as np

from font_length.morph import _prune_spurs, skeletonize_clean


def test_skeletonize_clean_removes_small_objects():
    bw = np.zeros((10, 10), dtype=bool)
    bw[1:9, 5] = True
    bw[0, 0] = True
    skel = skeletonize_clean(bw, min_obj_area=2, spur_prune_len=0)
    assert skel[0, 0] is False
    assert skel[:, 5].any()


def test_prune_spurs_removes_short_branch():
    skel = np.zeros((5, 5), dtype=bool)
    skel[2, 1:4] = True
    skel[1, 3] = True  # short spur on the right arm
    pruned = _prune_spurs(skel, max_len=1)
    assert pruned[1, 3] is False
    assert pruned[2, 2] is True
