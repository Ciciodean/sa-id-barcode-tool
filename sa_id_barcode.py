"""
SA Smart ID Barcode Tool — Core Library
=======================================
Generates TEST/SPECIMEN barcodes in the style of the South African
Smart ID Card reverse side:

  * Code 39 (1D)  — encodes the 13-digit ID number
  * PDF417  (2D)  — encodes personal details (surname, names, sex,
    nationality, ID number, birth date, country of birth, status,
    date of issue, security number, card number) plus filler.

This layout follows the field list published on Wikipedia's
"South African identity card" article. The exact byte-level layout used
by the Department of Home Affairs is proprietary, so this tool produces
a documented TEST-COMPATIBLE layout for scanner/parser development —
NOT a byte-identical government replica.

FOR SOFTWARE TESTING & EDUCATION ONLY. Do not use to make fake IDs.
Creating or using a counterfeit identity document is a crime in
South Africa (Identity Act, 1997 and related laws).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from io import BytesIO

# ---------------------------------------------------------------------------
# SA ID number helpers (format YYMMDD SSSS C A Z)
# ---------------------------------------------------------------------------

def luhn_check_digit(first12: str) -> str:
    """Calculate the SA ID Luhn check digit for the first 12 digits."""
    if len(first12) != 12 or not first12.isdigit():
        raise ValueError("Need exactly 12 digits to compute check digit")
    # Sum of digits in odd positions (1st, 3rd, 5th...), excluding check digit
    odd_sum = sum(int(first12[i]) for i in range(0, 12, 2))
    # Concatenate even-position digits, x2, sum the digits of the result
    even_number = int("".join(first12[i] for i in range(1, 12, 2))) * 2
    even_sum = sum(int(d) for d in str(even_number))
    total = odd_sum + even_sum
    return str((10 - (total % 10)) % 10)


def validate_id_number(id_number: str) -> tuple[bool, str]:
    """Validate a 13-digit SA ID number. Returns (ok, message)."""
    id_number = (id_number or "").strip()
    if len(id_number) != 13 or not id_number.isdigit():
        return False, "ID number must be exactly 13 digits."
    # Date part must be a real calendar date
    try:
        _dt.datetime.strptime(id_number[:6], "%y%m%d")
    except ValueError:
        return False, "First 6 digits (YYMMDD) are not a valid date."
    if luhn_check_digit(id_number[:12]) != id_number[12]:
        return False, "Check digit invalid (fails Luhn check). Typo in ID number?"
    return True, "Valid SA ID number."


def info_from_id_number(id_number: str) -> dict:
    """Derive birth date, gender and citizenship from an ID number."""
    yy, mm, dd = int(id_number[0:2]), int(id_number[2:4]), int(id_number[4:6])
    # Pivot: assume 1900s/2000s sensibly (IDs issued to people 16+)
    current_yy = _dt.date.today().year % 100
    century = 2000 if yy <= current_yy else 1900
    dob = f"{century + yy:04d}-{mm:02d}-{dd:02d}"
    gender_num = int(id_number[6:10])
    gender = "Female" if gender_num < 5000 else "Male"
    citizen_map = {"0": "SA Citizen", "1": "Permanent Resident", "2": "Refugee"}
    citizenship = citizen_map.get(id_number[10], "Unknown")
    return {"dob": dob, "gender": gender, "citizenship": citizenship}


# ---------------------------------------------------------------------------
# Data model for the PDF417 payload
# ---------------------------------------------------------------------------

FILLER_UNIT = "1234567890"  # same filler pattern as the real card

PDF417_FIELD_ORDER = [
    "surname", "names", "sex", "nationality", "id_number",
    "date_of_birth", "country_of_birth", "status", "date_of_issue",
    "security_number", "card_number",
]


@dataclass
class SmartIDData:
    surname: str = ""
    names: str = ""
    sex: str = "M"                      # M or F
    nationality: str = "RSA"
    id_number: str = ""
    date_of_birth: str = ""             # YYYYMMDD
    country_of_birth: str = "RSA"
    status: str = "CITIZEN"             # CITIZEN / PERMANENT RESIDENT
    date_of_issue: str = ""             # YYYYMMDD
    security_number: str = ""           # 5 digits (RSA hologram number)
    card_number: str = ""               # 9 digits (back of card)
    filler_chars: int = 600             # amount of 1234567890 filler
    delimiter: str = "|"                # field separator in test layout

    def clean(self) -> "SmartIDData":
        self.surname = self.surname.strip().upper()
        self.names = self.names.strip().upper()
        self.sex = self.sex.strip().upper()[:1] or "M"
        self.nationality = self.nationality.strip().upper() or "RSA"
        self.id_number = self.id_number.strip()
        self.date_of_birth = self.date_of_birth.strip()
        self.country_of_birth = self.country_of_birth.strip().upper() or "RSA"
        self.status = self.status.strip().upper() or "CITIZEN"
        self.date_of_issue = self.date_of_issue.strip()
        self.security_number = self.security_number.strip()
        self.card_number = self.card_number.strip()
        return self

    def validate(self) -> list[str]:
        """Return a list of problems (empty = OK)."""
        errors: list[str] = []
        if not self.surname:
            errors.append("Surname is required.")
        if not self.names:
            errors.append("Names are required.")
        if self.sex not in ("M", "F"):
            errors.append("Sex must be M or F.")
        ok, msg = validate_id_number(self.id_number)
        if not ok:
            errors.append(f"ID number: {msg}")
        for label, value in (("Date of birth", self.date_of_birth),
                             ("Date of issue", self.date_of_issue)):
            if len(value) != 8 or not value.isdigit():
                errors.append(f"{label} must be YYYYMMDD (8 digits).")
        if len(self.security_number) != 5 or not self.security_number.isdigit():
            errors.append("Security number must be 5 digits.")
        if len(self.card_number) != 9 or not self.card_number.isdigit():
            errors.append("Card number must be 9 digits.")
        return errors

    def pdf417_payload(self) -> str:
        """Build the delimited test-layout payload string."""
        self.clean()
        fields = [getattr(self, f) for f in PDF417_FIELD_ORDER]
        filler = (FILLER_UNIT * ((self.filler_chars // 10) + 1))[: self.filler_chars]
        return self.delimiter.join(fields) + self.delimiter + filler


# ---------------------------------------------------------------------------
# Barcode rendering (Pillow images)
# ---------------------------------------------------------------------------

def render_code39(id_number: str, add_test_banner: bool = True):
    """Render the Code 39 barcode image for the ID number."""
    from barcode import Code39
    from barcode.writer import ImageWriter

    writer = ImageWriter()
    writer.set_options({
        "module_width": 0.35,
        "module_height": 18.0,
        "font_size": 22,
        "text_distance": 6.0,
        "quiet_zone": 8.0,
        "dpi": 300,
    })
    code = Code39(id_number.strip(), writer=writer, add_checksum=False)
    img = code.render()
    if add_test_banner:
        img = _add_banner(img, "TEST SPECIMEN — NOT AN OFFICIAL DOCUMENT")
    return img


def render_pdf417(payload: str, columns: int = 8, security_level: int = 3,
                  scale: int = 3, add_test_banner: bool = True):
    """Render the PDF417 barcode image for the given payload string."""
    from pdf417gen import encode, render_image

    columns = min(max(int(columns), 3), 20)
    security_level = min(max(int(security_level), 0), 5)
    codes = encode(payload, columns=columns, security_level=security_level)
    img = render_image(codes, scale=scale, ratio=3, padding=12)
    img = img.convert("RGB")
    if add_test_banner:
        img = _add_banner(img, "TEST SPECIMEN — NOT AN OFFICIAL DOCUMENT")
    return img


def _add_banner(img, text: str):
    """Add a small caption strip under the barcode image."""
    from PIL import Image, ImageDraw, ImageFont

    # Scale font to image width so the banner stays readable
    size = max(16, min(28, img.width // 28))
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except Exception:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except Exception:
            font = ImageFont.load_default()
    strip_h = size + 22
    new = Image.new("RGB", (img.width, img.height + strip_h), "white")
    new.paste(img, (0, 0))
    draw = ImageDraw.Draw(new)
    draw.rectangle([0, img.height, img.width, img.height + strip_h], fill=(178, 34, 34))
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((img.width - tw) / 2, img.height + 8), text, fill="white", font=font)
    return new


def image_to_png_bytes(img) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# One-shot helper used by CLI + web app
# ---------------------------------------------------------------------------

def generate_pair(data: SmartIDData, raw_payload: str | None = None,
                  pdf_columns: int = 8, pdf_security: int = 3,
                  pdf_scale: int = 3, add_test_banner: bool = True) -> dict:
    """Generate both barcodes. Returns dict with PIL images + payload text."""
    data.clean()
    payload = raw_payload if raw_payload else data.pdf417_payload()
    code39_img = render_code39(data.id_number, add_test_banner)
    pdf417_img = render_pdf417(payload, pdf_columns, pdf_security,
                               pdf_scale, add_test_banner)
    return {"code39": code39_img, "pdf417": pdf417_img, "payload": payload}
