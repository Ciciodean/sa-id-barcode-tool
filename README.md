# ✨ VisualArc Editing — SA ID Barcode Studio (Code 39 + PDF417)

Generate **test/specimen** barcodes in the style of the back of the South African **Smart ID Card**:

| Barcode | Type | Content |
|---|---|---|
| Small strip (1D) | **Code 39** | The 13-digit ID number (`YYMMDD SSSS C A Z`) |
| Large block (2D) | **PDF417** | Surname, names, sex, nationality, ID number, birth date, country of birth, status, date of issue, 5-digit security number, 9-digit card number + `1234567890` filler |

Field list follows the public description on Wikipedia's [*South African identity card*](https://en.wikipedia.org/wiki/South_African_identity_card) article. The exact byte-level layout used by the Department of Home Affairs is proprietary, so structured mode uses a documented pipe-delimited **test layout**:

```
SURNAME|NAMES|SEX|NATIONALITY|ID|DOB|COUNTRY|STATUS|ISSUE|SECURITY|CARD|1234567890…
```

Use **raw mode** if your parser expects a different delimiter or order.

> ⚠️ **FOR SOFTWARE TESTING & EDUCATION ONLY.** Outputs are clearly marked TEST SPECIMEN and are not valid identity documents. Creating, altering or using a fake SA ID is a criminal offence. Do not print these onto anything imitating an official document. The driver's licence barcode is *encrypted* and is a different system — not covered here.

## Option A — Web app (easiest)

```bash
cd sa-id-barcode-tool
pip install -r requirements.txt
python3 web_app.py
```

Open http://localhost:5000 — fill in the form, generate, and download the PNGs. Everything runs offline on your machine.

The form can **generate a valid test ID number from any birth date + gender**, and downloads can use a **white or transparent background**.

## Option B — Python script (CLI)

```bash
cd sa-id-barcode-tool
pip install -r requirements.txt

# Interactive (prompts for each field):
python3 sa_id_barcode_tool.py

# One-shot:
python3 sa_id_barcode_tool.py --surname DUBE --names "THABO SIPHO" --sex M \
  --id-number 8001015000086 --dob 19800101 --issue 20190115 \
  --security 12345 --card 123456789 --out ./output

# Fully custom PDF417 content:
python3 sa_id_barcode_tool.py --id-number 8001015000086 --raw "HELLO|WORLD|123"

# Transparent-background PNGs (no white):
python3 sa_id_barcode_tool.py --id-number 8001015000086 --transparent --out ./output
```

Outputs: `code39_<ID>.png`, `pdf417_<ID>.png`, `payload_<ID>.txt`.

## The SA ID number (`YYMMDD SSSS C A Z`)

- `YYMMDD` — date of birth
- `SSSS` — sequence: `0000–4999` female, `5000–9999` male
- `C` — status: `0` citizen, `1` permanent resident, `2` refugee
- `A` — `8` or `9` (historically a racial marker, now effectively random)
- `Z` — Luhn check digit

Both the web app and CLI validate the check digit and auto-derive birth date/gender.

## Files

- `sa_id_barcode.py` — core library (validation + rendering)
- `sa_id_barcode_tool.py` — command-line tool
- `web_app.py` — Flask web app (single self-contained page, no internet needed)
- `requirements.txt`, `README.md`

## \U0001F4AC Help Desk

The app has a Help Desk section (contact buttons + quick-fix FAQ + GitHub issues link). To let users text/WhatsApp/email you, set `SUPPORT_WHATSAPP` / `SUPPORT_SMS` / `SUPPORT_EMAIL` at the top of `web_app.py`.

## Push to GitHub

```bash
cd sa-id-barcode-tool
git init
git add .
git commit -m "SA Smart ID barcode test tool"
# create an empty repo on github.com, then:
git remote add origin https://github.com/YOUR-USERNAME/sa-id-barcode-tool.git
git branch -M main
git push -u origin main
```

## Put it live on the internet (free)

GitHub Pages can't run Python apps, so use **Render.com** (free):

1. Push this project to GitHub (above).
2. Go to [render.com](https://render.com), sign up, **New → Web Service**.
3. Connect your GitHub repo — Render auto-detects `render.yaml`.
4. Deploy — you get a public link like `https://sa-id-barcode-tool.onrender.com`.
