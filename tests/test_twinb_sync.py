import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from twinb_sync_adapter import StepClock, cooling_request, safe_setpoint, respect_deadband
from qualify_twinb_benchmark import equivalent


class SyncTests(unittest.TestCase):
    def test_deadband(self):
        self.assertEqual(respect_deadband(22.1, 22.7), 22.7)
        self.assertEqual(respect_deadband(26, 22.7), 26)
        self.assertIsNone(respect_deadband(None, 22.7))

    def test_finite_and_safe(self):
        for bad in (float("inf"), float("nan"), 17, 31):
            with self.assertRaises(ValueError):
                safe_setpoint(bad)
        self.assertIsNone(safe_setpoint(None))
        self.assertEqual(safe_setpoint(26), 26)

    def test_cooling_only_occupied(self):
        self.assertIsNone(cooling_request(20, 25, 1, True))
        self.assertIsNone(cooling_request(30, 25, 1, False))
        self.assertEqual(cooling_request(30, 25, 1, True), 25)

    def test_clock(self):
        clock = StepClock()
        self.assertTrue(clock.accept((1, 195, 0, 1)))
        self.assertFalse(clock.accept((1, 195, 0, 1)))
        self.assertTrue(clock.accept((1, 195, 0, 2)))
        with self.assertRaises(ValueError):
            clock.accept((1, 194, 0, 1))

    def test_output_comparison(self):
        self.assertTrue(equivalent([["a"], ["1.0"]], [["a"], ["1.000000001"]]))
        self.assertFalse(equivalent([["a"], ["1.0"]], [["a"], ["2"]]))
        self.assertFalse(equivalent([["a"]], [["b"]]))
