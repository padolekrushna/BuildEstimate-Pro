def test_floor_area_calculation():
    class R:
        def __init__(self, length, width, height):
            self.length = length
            self.width = width
            self.height = height

        @property
        def area(self):
            return (self.length or 0.0) * (self.width or 0.0)

    r = R(5.0, 4.0, 3.0)
    assert round(r.area, 4) == 20.0


def test_plaster_area_with_openings():
    class R:
        def __init__(self, length, width, height, openings=None):
            self.length = length
            self.width = width
            self.height = height
            self.openings = openings or []

    class O:
        def __init__(self, width, height, count=1):
            self.width = width
            self.height = height
            self.count = count

        @property
        def area(self):
            return self.width * self.height * self.count

    r = R(5.0, 3.0, 3.0, openings=[O(0.9, 2.1, 1), O(1.5, 1.2, 1)])
    openings_area = sum([o.area for o in r.openings])
    expected = round(max(2 * (r.length + r.width) * r.height - openings_area, 0.0), 4)
    assert expected == round(2 * (5.0 + 3.0) * 3.0 - openings_area, 4)
