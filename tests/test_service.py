import unittest

from app.web_service import StatsRequest, compute_average


class ServiceTest(unittest.TestCase):
    def test_compute_average_normal(self):
        self.assertEqual(compute_average(StatsRequest(total=10, count=2)), 5)

    def test_compute_average_zero(self):
        self.assertEqual(compute_average(StatsRequest(total=10, count=0)), 0.0)


if __name__ == "__main__":
    unittest.main()