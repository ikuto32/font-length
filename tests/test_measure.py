import math

from font_length.measure import polylines_bounds, polyline_total_length, total_length


def test_polyline_total_length():
    polyline = [(0.0, 0.0), (3.0, 4.0)]
    assert math.isclose(polyline_total_length(polyline), 5.0)


def test_total_length_multiple():
    polylines = [[(0.0, 0.0), (0.0, 3.0)], [(0.0, 0.0), (4.0, 0.0)]]
    assert math.isclose(total_length(polylines), 7.0)


def test_polylines_bounds():
    polylines = [[(1.0, 1.0), (2.0, 1.0)], [(0.0, 0.0), (0.0, 5.0)]]
    bounds = polylines_bounds(polylines)
    assert bounds == (0.0, 0.0, 2.0, 5.0)
