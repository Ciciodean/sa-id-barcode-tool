#!/usr/bin/env python3
"""
SA Smart ID Barcode Tool — Command-line interface
=================================================
Generate TEST/SPECIMEN Code 39 + PDF417 barcodes in the style of the
South African Smart ID Card (for scanner/software testing only).

Examples
--------
  # Interactive mode (asks you each field):
  python3 sa_id_barcode_tool.py

  # One-shot with arguments:
  python3 sa_id_barcode_tool.py --surname DUBE --names "THABO SIPHO" --sex M \\
      --id-number 8001015000086 --dob 19800101 --issue 20190115 \\
      --security 12345 --card 123456789 --out ./output

  # Encode a fully custom raw string into the PDF417 instead:
  python3 sa_id_barcode_tool.py --id-number 8001015000086 --raw "HELLO|WORLD|123"

Legal: FOR TESTING & EDUCATION ONLY. Making or using a fake SA ID is a crime.
"""

from __future__ import annotations

import argparse
import os
import sys

from sa_id_barcode import (
    SmartIDData,
    generate_pair,
    info_from_id_number,
    validate_id_number,
)


def prompt(text: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    val = input(f"{text}{hint}: ").strip()
    return val if val else default


def interactive() -> SmartIDData:
    print("\n=== SA Smart ID Barcode Tool (TEST specimens) ===\n")
    print("Tip: press Enter to accept the [default] shown.\n")
    while True:
        id_number = prompt("ID number (13 digits)", "8001015000086")
        ok, msg = validate_id_number(id_number)
        if ok:
            info = info_from_id_number(id_number)
            print(f"  -> {msg}  DOB: {info['dob']}  Gender: {info['gender']}  {info['citizenship']}")
            break
        print(f"  !! {msg} Try again.")
    info = info_from_id_number(id_number)
    dob_default = info["dob"].replace("-", "")
    sex_default = "F" if info["gender"] == "Female" else "M"
    data = SmartIDData(
        surname=prompt("Surname", "DUBE"),
        names=prompt("Full names", "THABO SIPHO"),
        sex=prompt("Sex (M/F)", sex_default),
        nationality=prompt("Nationality", "RSA"),
        id_number=id_number,
        date_of_birth=prompt("Date of birth YYYYMMDD", dob_default),
        country_of_birth=prompt("Country of birth", "RSA"),
        status=prompt("Status", "CITIZEN"),
        date_of_issue=prompt("Date of issue YYYYMMDD", "20190115"),
        security_number=prompt("Security number (5 digits)", "12345"),
        card_number=prompt("Card number (9 digits)", "123456789"),
    )
    return data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate SA Smart ID style TEST barcodes (Code39 + PDF417).")
    p.add_argument("--surname", default=None)
    p.add_argument("--names", default=None)
    p.add_argument("--sex", default=None)
    p.add_argument("--nationality", default="RSA")
    p.add_argument("--id-number", default=None)
    p.add_argument("--dob", default=None, help="Date of birth YYYYMMDD")
    p.add_argument("--country-of-birth", default="RSA")
    p.add_argument("--status", default="CITIZEN")
    p.add_argument("--issue", default=None, help="Date of issue YYYYMMDD")
    p.add_argument("--security", default=None, help="5-digit security number")
    p.add_argument("--card", default=None, help="9-digit card number")
    p.add_argument("--raw", default=None, help="Custom raw string for PDF417 (skips structured fields)")
    p.add_argument("--pdf-columns", type=int, default=8)
    p.add_argument("--pdf-security", type=int, default=3)
    p.add_argument("--pdf-scale", type=int, default=3)
    p.add_argument("--no-banner", action="store_true", help="Omit the TEST SPECIMEN banner")
    p.add_argument("--transparent", action="store_true", help="Transparent background (no white) in PNGs")
    p.add_argument("--out", default="./output", help="Output folder for PNG files")
    return p


def main() -> int:
    args = build_parser().parse_args()

    if args.id_number is None and args.raw is None and sys.stdin.isatty():
        data = interactive()
        raw = None
    elif args.id_number is None:
        print("Error: --id-number is required (or run interactively).", file=sys.stderr)
        return 2
    else:
        info = {}
        ok, msg = validate_id_number(args.id_number)
        if not ok:
            print(f"Error: invalid ID number: {msg}", file=sys.stderr)
            return 2
        info = info_from_id_number(args.id_number)
        data = SmartIDData(
            surname=args.surname or "DUBE",
            names=args.names or "THABO SIPHO",
            sex=(args.sex or ("F" if info["gender"] == "Female" else "M")),
            nationality=args.nationality,
            id_number=args.id_number,
            date_of_birth=args.dob or info["dob"].replace("-", ""),
            country_of_birth=args.country_of_birth,
            status=args.status,
            date_of_issue=args.issue or "20190115",
            security_number=args.security or "12345",
            card_number=args.card or "123456789",
        )
        raw = args.raw

    problems = [] if raw else data.validate()
    if problems:
        print("Please fix the following:", file=sys.stderr)
        for pr in problems:
            print(f"  - {pr}", file=sys.stderr)
        return 2

    result = generate_pair(
        data, raw_payload=raw,
        pdf_columns=args.pdf_columns, pdf_security=args.pdf_security,
        pdf_scale=args.pdf_scale, add_test_banner=not args.no_banner,
        transparent=args.transparent,
    )

    os.makedirs(args.out, exist_ok=True)
    c39_path = os.path.join(args.out, f"code39_{data.id_number}.png")
    pdf_path = os.path.join(args.out, f"pdf417_{data.id_number}.png")
    txt_path = os.path.join(args.out, f"payload_{data.id_number}.txt")
    result["code39"].save(c39_path)
    result["pdf417"].save(pdf_path)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result["payload"])

    print("\nDone! TEST specimens saved to", os.path.abspath(args.out))
    print("  Code 39 :", c39_path)
    print("  PDF417  :", pdf_path)
    print("  Payload :", txt_path, f"({len(result['payload'])} chars)")
    print("\nRemember: TEST ONLY — not valid ID documents. Misuse is illegal.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
