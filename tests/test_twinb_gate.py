import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("gate", Path(__file__).parents[1] / "scripts/twinb_baseline_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class GateTests(unittest.TestCase):
    def test_success_summary_does_not_hide_severe(self):
        text = "** Severe ** bad floor\nEnergyPlus Completed Successfully-- 1 Severe Errors"
        self.assertEqual(gate.error_counts(text), {"Warning": 0, "Severe": 1, "Fatal": 0})

    def test_counts_records_not_summary(self):
        self.assertEqual(gate.error_counts("** Warning ** x\n** Fatal ** y\n3 Severe Errors"),
                         {"Warning": 1, "Severe": 0, "Fatal": 1})
