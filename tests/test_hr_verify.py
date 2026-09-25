#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import hr_verify


def test_company_csv_always_ok():
    assert hr_verify.verified_enough("careers@acme.com", "company_csv")


def test_jd_parse_prefix():
    assert hr_verify.verified_enough("careers@acme.com", "jd_parse")
    assert not hr_verify.verified_enough("random@acme.com", "jd_parse")


def test_extract_from_description():
    text = "Send CV to careers@example.co.in for more details"
    assert hr_verify.extract_from_description(text) == "careers@example.co.in"


if __name__ == "__main__":
    test_company_csv_always_ok()
    test_jd_parse_prefix()
    test_extract_from_description()
    print("ok")
