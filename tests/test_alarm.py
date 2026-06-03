from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = PROJECT_ROOT / "custom_components" / "iminilide"

alarm = _load_module("iminilide_alarm", PACKAGE_ROOT / "alarm.py")
is_alarm_triggered = alarm.is_alarm_triggered


class AlarmTests(unittest.TestCase):
    def test_alarm_is_off_within_bounded_range(self) -> None:
        self.assertFalse(is_alarm_triggered(-20.0, -25.0, -14.0))

    def test_alarm_is_on_below_lower_threshold(self) -> None:
        self.assertTrue(is_alarm_triggered(-30.0, -25.0, -14.0))

    def test_alarm_is_on_above_upper_threshold(self) -> None:
        self.assertTrue(is_alarm_triggered(-10.0, -25.0, -14.0))

    def test_alarm_with_only_lower_threshold(self) -> None:
        self.assertTrue(is_alarm_triggered(2.0, 3.0, None))
        self.assertFalse(is_alarm_triggered(4.0, 3.0, None))

    def test_alarm_with_only_upper_threshold(self) -> None:
        self.assertTrue(is_alarm_triggered(8.0, None, 7.0))
        self.assertFalse(is_alarm_triggered(6.0, None, 7.0))

    def test_alarm_without_thresholds(self) -> None:
        self.assertFalse(is_alarm_triggered(5.0, None, None))


if __name__ == "__main__":
    unittest.main()
