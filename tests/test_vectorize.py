import numpy as np

from font_length.vectorize import rdp, skeleton_to_polylines


def test_skeleton_to_polylines_line():
    skel = np.zeros((3, 5), dtype=bool)
    skel[1, :] = True
    polylines = skeleton_to_polylines(skel)
    assert len(polylines) == 1
    assert polylines[0][0] == (0.0, 1.0)
    assert polylines[0][-1] == (4.0, 1.0)


def test_skeleton_to_polylines_branch():
    skel = np.zeros((5, 5), dtype=bool)
    skel[2, 1:4] = True
    skel[1:4, 2] = True
    polylines = skeleton_to_polylines(skel)
    assert len(polylines) == 4  # four arms from the center


def test_rdp_reduces_points():
    points = [(0.0, 0.0), (1.0, 0.1), (2.0, 0.0)]
    simplified = rdp(points, 0.2)
    assert simplified == [(0.0, 0.0), (2.0, 0.0)]
