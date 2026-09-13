#!/usr/bin/env python3
"""
SA Smart ID Barcode Tool — Web App
==================================
Run:  python3 web_app.py
Then open: http://localhost:5000

FOR SOFTWARE TESTING & EDUCATION ONLY.
"""

from __future__ import annotations

import base64
import io
import os

from flask import Flask, jsonify, request, render_template_string

from sa_id_barcode import (
    SmartIDData,
    generate_pair,
    info_from_id_number,
    validate_id_number,
)

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Help desk contact details — fill these in to activate the contact buttons.
# Use international format WITHOUT "+" for WhatsApp, e.g. "254712345678".
# Leave a value as "" to hide that button.
# ---------------------------------------------------------------------------
SUPPORT_WHATSAPP = ""   # e.g. "254712345678"
SUPPORT_TELEGRAM = "https://t.me/visualarcediting"  # Telegram channel/group link
SUPPORT_SMS = ""        # e.g. "+254712345678"
SUPPORT_EMAIL = ""      # e.g. "help@visualarc.example"
GITHUB_ISSUES_URL = "https://github.com/Ciciodean/sa-id-barcode-tool/issues"

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VisualArc Editing — SA ID Barcode Studio (Code 39 + PDF417)</title>
<style>
  :root, [data-theme="heritage"] {
    --bg:#f4f6f5; --card:#fff; --ink:#222; --muted:#666;
    --accent:#007749; --accent-dark:#005a38; --accent-soft:#e7f4ec;
    --gold:#FCB514; --red:#DE3831; --ok:#007749;
    --head-grad:linear-gradient(135deg,#007749 0%,#005a38 60%,#111 100%);
    --input-bg:#fff; --input-border:#c9d2cd;
    --ghost-bg:#eef2f0; --ghost-ink:#222;
    --detail-bg:#f8faf9; --warn-bg:#fff8e1;
    --dl-bg:#111; --dl-ink:#fff;
  }
  [data-theme="light"] {
    --bg:#f2f6ff; --card:#ffffff; --ink:#1c2b4a; --muted:#5b6b8c;
    --accent:#0b5fff; --accent-dark:#0849c4; --accent-soft:#e3edff;
    --gold:#ffb020; --red:#d92d20; --ok:#067647;
    --head-grad:linear-gradient(135deg,#0b5fff,#062a78);
    --input-bg:#fff; --input-border:#c3d0e8;
    --ghost-bg:#e9eefb; --ghost-ink:#1c2b4a;
    --detail-bg:#f5f8ff; --warn-bg:#fffaeb;
    --dl-bg:#101828; --dl-ink:#fff;
  }
  [data-theme="dark"] {
    --bg:#101413; --card:#1a201e; --ink:#e9f0eb; --muted:#9aa8a1;
    --accent:#2fbf71; --accent-dark:#7fe0a8; --accent-soft:#14352a;
    --gold:#FCB514; --red:#ff6b61; --ok:#4ade80;
    --head-grad:linear-gradient(135deg,#0b3b26,#0d1512);
    --input-bg:#121715; --input-border:#39443f;
    --ghost-bg:#242c29; --ghost-ink:#e9f0eb;
    --detail-bg:#161c1a; --warn-bg:#2a2410;
    --dl-bg:#e9f0eb; --dl-ink:#101413;
  }
  [data-theme="ocean"] {
    --bg:#eef7f7; --card:#ffffff; --ink:#123338; --muted:#4f6b70;
    --accent:#0e7c86; --accent-dark:#0a5c64; --accent-soft:#dcf0f2;
    --gold:#f5a623; --red:#d92d20; --ok:#0e7c86;
    --head-grad:linear-gradient(135deg,#0e7c86,#083f46);
    --input-bg:#fff; --input-border:#bcd6d9;
    --ghost-bg:#e2eff0; --ghost-ink:#123338;
    --detail-bg:#f2f9fa; --warn-bg:#fffaeb;
    --dl-bg:#083f46; --dl-ink:#fff;
  }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; background:var(--bg); color:var(--ink); }
  header { background:var(--head-grad); color:#fff; padding:22px 16px; }
  header .wrap, main.wrap { max-width:1080px; margin:0 auto; }
  header h1 { margin:0 0 6px; font-size:22px; }
  header p { margin:0; opacity:.92; font-size:14px; max-width:70ch; }
  .themes { display:flex; gap:8px; margin-top:12px; flex-wrap:wrap; align-items:center; }
  .themes button { background:rgba(255,255,255,.14); color:#fff; border:1px solid rgba(255,255,255,.45); padding:7px 13px; font-size:12.5px; border-radius:20px; font-weight:700; cursor:pointer; }
  .themes button.active { background:#fff; color:#111; border-color:#fff; }
  .flagbar { height:6px; background:linear-gradient(90deg,#DE3831 0 20%,#fff 20% 24%,#002395 24% 44%,#fff 44% 48%,#007749 48% 68%,#FCB514 68% 72%,#111 72% 100%); }
  .warn { background:var(--warn-bg); border:2px solid var(--gold); border-radius:10px; padding:10px 14px; margin:14px 0; font-size:13.5px; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:900px){ .grid{grid-template-columns:1fr;} }
  .card { background:var(--card); border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.07); padding:18px; }
  .card h2 { margin:0 0 12px; font-size:17px; color:var(--accent-dark); }
  label { display:block; font-size:12.5px; font-weight:600; margin:10px 0 4px; color:var(--ink); }
  input, select, textarea { width:100%; padding:9px 10px; border:1px solid var(--input-border); background:var(--input-bg); color:var(--ink); border-radius:8px; font-size:14px; }
  input:focus, select:focus, textarea:focus { outline:2px solid var(--accent-soft); border-color:var(--accent); }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .id-ok { color:var(--ok); font-size:12.5px; margin-top:4px; }
  .id-bad { color:var(--red); font-size:12.5px; margin-top:4px; }
  .btns { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }
  button { cursor:pointer; border:0; border-radius:9px; padding:11px 16px; font-size:14px; font-weight:700; }
  .primary { background:var(--accent); color:#fff; }
  .primary:hover { filter:brightness(.9); }
  .ghost { background:var(--ghost-bg); color:var(--ghost-ink); }
  .toggle { display:flex; align-items:center; gap:8px; margin-top:12px; font-size:13.5px; }
  .toggle input { width:auto; }
  #rawBox { display:none; }
  .out img { max-width:100%; background:#fff; border:1px solid var(--input-border); border-radius:8px; }
  .dl { display:inline-block; margin:6px 8px 12px 0; background:var(--dl-bg); color:var(--dl-ink); text-decoration:none; padding:8px 14px; border-radius:8px; font-size:13px; font-weight:700; }
  pre.payload { background:#0e1a14; color:#d7ffe4; padding:12px; border-radius:8px; font-size:11.5px; max-height:180px; overflow:auto; word-break:break-all; white-space:pre-wrap; }
  footer { text-align:center; font-size:12px; color:var(--muted); padding:18px; }
  .pill { display:inline-block; background:var(--accent-soft); color:var(--accent-dark); border-radius:20px; padding:2px 10px; font-size:12px; font-weight:700; }
  details { font-size:13px; background:var(--detail-bg); border:1px solid var(--input-border); border-radius:8px; padding:10px 12px; margin-top:12px; }
  summary { cursor:pointer; font-weight:700; color:var(--accent-dark); }
  code { background:var(--ghost-bg); color:var(--ink); padding:1px 5px; border-radius:4px; }
  .idgen { display:flex; gap:8px; flex-wrap:wrap; align-items:center; background:var(--detail-bg); border:1px dashed var(--input-border); border-radius:8px; padding:8px 10px; margin-top:8px; font-size:12.5px; }
  .idgen input, .idgen select { width:auto; flex:1; min-width:110px; padding:7px 8px; font-size:13px; }
  .idgen button { padding:8px 12px; font-size:13px; }
  .out img.trans { background:repeating-conic-gradient(#c9c9c9 0 25%, #ffffff 0 50%) 0 0/18px 18px; }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>✨ VisualArc Editing <span class="pill">BARCODE STUDIO</span></h1>
    <p>Generate <b>Code&nbsp;39</b> (ID number) + <b>PDF417</b> (personal details) barcodes in the style of the back of the South African Smart ID Card — for testing scanners &amp; software. Field list follows the public Wikipedia description. 100% offline: nothing leaves your computer.</p>
    <div class="themes">
      <span style="font-size:12.5px;opacity:.9">🎨 Theme:</span>
      <button type="button" data-t="heritage" onclick="setTheme('heritage')">🇿🇦 Heritage</button>
      <button type="button" data-t="light" onclick="setTheme('light')">🌞 Light</button>
      <button type="button" data-t="dark" onclick="setTheme('dark')">🌙 Dark</button>
      <button type="button" data-t="ocean" onclick="setTheme('ocean')">🌊 Ocean</button>
      <a href="#help" style="color:#fff;font-size:12.5px;font-weight:700;margin-left:4px">💬 Help</a>
    </div>
  </div>
</header>
<div class="flagbar"></div>
<main class="wrap" style="padding:16px;">
  <div class="warn">⚠️ <b>Testing &amp; education only.</b> These are clearly-marked <b>TEST specimens</b>, not valid identity documents. Creating, altering or using a fake South African ID is a criminal offence. Do not print these onto any card that imitates an official document.</div>
  <div class="grid">
    <section class="card">
      <h2>1️⃣ Enter details</h2>
      <div class="btns" style="margin-top:0">
        <button class="ghost" type="button" onclick="fillSample()">Fill sample data</button>
        <button class="ghost" type="button" onclick="clearAll()">Clear</button>
      </div>
      <label for="id_number">ID number (13 digits) *</label>
      <div style="display:flex;gap:8px">
        <input id="id_number" maxlength="13" inputmode="numeric" placeholder="e.g. 8001015000086" value="8001015000086" style="flex:1">
        <button class="ghost" type="button" onclick="makeTestId()" title="Create a random valid test ID number" style="white-space:nowrap">🎲 Random valid ID</button>
      </div>
      <div id="idMsg" class="id-ok"></div>
      <div class="idgen">
        <span>🎂 Don’t have an ID number? Generate one from a birth date:</span>
        <input type="date" id="genDob" value="2004-02-25" min="1900-01-01" max="2026-12-31">
        <select id="genGender"><option value="F">Female</option><option value="M" selected>Male</option></select>
        <button class="ghost" type="button" onclick="makeIdFromDob()">Generate ID</button>
      </div>
      <div class="row">
        <div><label for="surname">Surname *</label><input id="surname" value="DUBE"></div>
        <div><label for="names">Full names *</label><input id="names" value="THABO SIPHO"></div>
      </div>
      <div class="row">
        <div><label for="sex">Sex</label><select id="sex"><option>M</option><option>F</option></select></div>
        <div><label for="nationality">Nationality</label><input id="nationality" value="RSA"></div>
      </div>
      <div class="row">
        <div><label for="dob">Date of birth (YYYYMMDD) *</label><input id="dob" maxlength="8" value="19800101"></div>
        <div><label for="cob">Country of birth</label><input id="cob" value="RSA"></div>
      </div>
      <div class="row">
        <div><label for="status">Status</label><select id="status"><option>CITIZEN</option><option>PERMANENT RESIDENT</option></select></div>
        <div><label for="issue">Date of issue (YYYYMMDD) *</label><input id="issue" maxlength="8" value="20190115"></div>
      </div>
      <div class="row">
        <div><label for="security">Security number (5 digits) *</label><input id="security" maxlength="5" value="12345"></div>
        <div><label for="card">Card number (9 digits) *</label><input id="card" maxlength="9" value="123456789"></div>
      </div>
      <label class="toggle"><input type="checkbox" id="rawMode" onchange="toggleRaw()"> <b>Raw mode</b> — type my own exact PDF417 text instead of structured fields</label>
      <div id="rawBox">
        <label for="raw">Raw PDF417 text</label>
        <textarea id="raw" rows="3" placeholder="Anything you want encoded..."></textarea>
      </div>
      <h2 style="margin-top:16px">2️⃣ PDF417 options</h2>
      <div class="row">
        <div><label for="cols">Columns (3–20)</label><input id="cols" type="number" min="3" max="20" value="8"></div>
        <div><label for="sec">Error correction (0–5)</label><input id="sec" type="number" min="0" max="5" value="3"></div>
      </div>
      <div class="row">
        <div><label for="scale">Image scale (1–6)</label><input id="scale" type="number" min="1" max="6" value="3"></div>
        <div><label for="filler">Filler chars (0–1200)</label><input id="filler" type="number" min="0" max="1200" value="600"></div>
      </div>
      <label for="bg">Image background (applies to downloads)</label>
      <select id="bg"><option value="white">⬜ White</option><option value="transparent">🔲 Transparent — no background</option></select>
      <label class="toggle"><input type="checkbox" id="banner" checked> Add red <b>TEST SPECIMEN</b> banner under barcodes (recommended)</label>
      <div class="btns">
        <button class="primary" onclick="generate()">⚙️ Generate barcodes</button>
      </div>
      <details>
        <summary>What exactly gets encoded? (test layout)</summary>
        <p>Structured mode joins the fields with <code>|</code> in the order on the real card, then appends the <code>1234567890</code> filler like the genuine barcode:</p>
        <p><code>SURNAME|NAMES|SEX|NATIONALITY|ID|DOB|COUNTRY|STATUS|ISSUE|SECURITY|CARD|1234567890…</code></p>
        <p>Home Affairs' exact byte layout is proprietary, so use <b>Raw mode</b> if your parser expects a different delimiter or order.</p>
      </details>
    </section>
    <section class="card out">
      <h2>3️⃣ Result</h2>
      <div id="err" class="id-bad"></div>
      <h3 style="font-size:14px;margin:8px 0 6px">Code 39 — ID number (1D)</h3>
      <img id="img39" alt="Code 39 preview">
      <div><a id="dl39" class="dl" download="code39.png">⬇ Download Code 39 PNG</a></div>
      <h3 style="font-size:14px;margin:8px 0 6px">PDF417 — personal details (2D)</h3>
      <img id="img417" alt="PDF417 preview">
      <div><a id="dl417" class="dl" download="pdf417.png">⬇ Download PDF417 PNG</a></div>
      <h3 style="font-size:14px;margin:8px 0 6px">Encoded PDF417 text (<span id="plen">0</span> chars)</h3>
      <pre class="payload" id="payloadText">Press “Generate barcodes”…</pre>
      <div><button class="ghost" onclick="copyPayload()">📋 Copy text</button></div>
    </section>
  </div>
  <!--HELP_DESK-->
  <div class="card" style="margin-top:16px">
    <h2>ℹ️ About these barcodes</h2>
    <p style="font-size:13.5px;line-height:1.6;margin:0">
      The back of the SA Smart ID Card carries <b>two</b> barcodes: a small <b>Code&nbsp;39</b> strip holding just the 13-digit ID number (<code>YYMMDD&nbsp;SSSS&nbsp;C&nbsp;A&nbsp;Z</code>, validated with the Luhn check digit),
      and a large <b>PDF417</b> block holding the holder's details plus filler. The old green ID book used a single barcode; the driver's licence uses an <b>encrypted</b> PDF417 (different system — not covered here).
      Sources: Wikipedia “South African identity card” [1](https://en.wikipedia.org/wiki/South_African_identity_card), Regula Forensics on SA IDs [2](https://regulaforensics.com/blog/south-african-ids-verification/).
      This tool generates clearly-marked test specimens so developers can test scanning and parsing without touching real personal data.
    </p>
  </div>
</main>
<footer>VisualArc Editing • Barcode Studio • For testing &amp; education only • Runs fully offline on your machine</footer>
<script>
function luhnOk(idn){
  if(!/^\d{13}$/.test(idn)) return false;
  let odd=0; for(let i=0;i<12;i+=2) odd+=+idn[i];
  let evenStr=""; for(let i=1;i<12;i+=2) evenStr+=idn[i];
  let evenSum=String(+evenStr*2).split("").reduce((a,c)=>a+ +c,0);
  return String((10-((odd+evenSum)%10))%10)===idn[12];
}
function checkId(auto){
  const v=document.getElementById("id_number").value.trim();
  const m=document.getElementById("idMsg");
  if(/^\d{13}$/.test(v)&&luhnOk(v)){
    // derive dob + gender
    const yy=+v.slice(0,2),mm=v.slice(2,4),dd=v.slice(4,6);
    const curYY=new Date().getFullYear()%100;
    const yyyy=(yy<=curYY?2000:1900)+yy;
    const g=+v.slice(6,10)<5000?"F":"M";
    m.className="id-ok"; m.textContent="✓ Valid • DOB "+yyyy+"-"+mm+"-"+dd+" • "+(g==="F"?"Female":"Male");
    if(auto){ document.getElementById("dob").value=""+yyyy+mm+dd; document.getElementById("sex").value=g; }
  } else if(v===""){ m.className="id-bad"; m.textContent=""; }
  else { m.className="id-bad"; m.textContent="✗ Invalid ID number (must be 13 digits with valid date + Luhn check digit)."; }
}
document.getElementById("id_number").addEventListener("input",()=>checkId(true));
function toggleRaw(){ document.getElementById("rawBox").style.display=document.getElementById("rawMode").checked?"block":"none"; }
function fillSample(){
  document.getElementById("id_number").value="8001015000086";
  document.getElementById("surname").value="DUBE";
  document.getElementById("names").value="THABO SIPHO";
  document.getElementById("sex").value="M";
  document.getElementById("nationality").value="RSA";
  document.getElementById("dob").value="19800101";
  document.getElementById("cob").value="RSA";
  document.getElementById("status").value="CITIZEN";
  document.getElementById("issue").value="20190115";
  document.getElementById("security").value="12345";
  document.getElementById("card").value="123456789";
  checkId(false);
}
function clearAll(){ ["surname","names","dob","issue","security","card"].forEach(id=>document.getElementById(id).value=""); document.getElementById("id_number").value=""; checkId(false); }
function luhnCheck(partial){
  let odd=0; for(let i=0;i<12;i+=2) odd+=+partial[i];
  let evenStr=""; for(let i=1;i<12;i+=2) evenStr+=partial[i];
  let evenSum=String(+evenStr*2).split("").reduce((a,c)=>a+ +c,0);
  return String((10-((odd+evenSum)%10))%10);
}
function buildId(yy,mm,dd,female){
  const seq=female?Math.floor(Math.random()*5000):5000+Math.floor(Math.random()*5000);
  const partial=yy+mm+dd+String(seq).padStart(4,"0")+"08";
  return partial+luhnCheck(partial);
}
function makeTestId(){
  const y=1960+Math.floor(Math.random()*46), m=1+Math.floor(Math.random()*12), d=1+Math.floor(Math.random()*28);
  document.getElementById("id_number").value=buildId(String(y).slice(2),String(m).padStart(2,"0"),String(d).padStart(2,"0"),Math.random()<0.5);
  checkId(true);
}
function makeIdFromDob(){
  const v=document.getElementById("genDob").value;
  const m=document.getElementById("idMsg");
  if(!v||!/^\d{4}-\d{2}-\d{2}$/.test(v)){ m.className="id-bad"; m.textContent="Pick a birth date first (click the calendar)."; return; }
  const p=v.split("-");
  const female=document.getElementById("genGender").value==="F";
  document.getElementById("id_number").value=buildId(p[0].slice(2),p[1],p[2],female);
  checkId(true);
}
async function generate(){
  const err=document.getElementById("err"); err.textContent="";
  const body={
    surname:document.getElementById("surname").value, names:document.getElementById("names").value,
    sex:document.getElementById("sex").value, nationality:document.getElementById("nationality").value,
    id_number:document.getElementById("id_number").value.trim(), date_of_birth:document.getElementById("dob").value.trim(),
    country_of_birth:document.getElementById("cob").value, status:document.getElementById("status").value,
    date_of_issue:document.getElementById("issue").value.trim(), security_number:document.getElementById("security").value.trim(),
    card_number:document.getElementById("card").value.trim(),
    raw_mode:document.getElementById("rawMode").checked, raw:document.getElementById("raw").value,
    pdf_columns:+document.getElementById("cols").value, pdf_security:+document.getElementById("sec").value,
    pdf_scale:+document.getElementById("scale").value, filler:+document.getElementById("filler").value,
    banner:document.getElementById("banner").checked,
    transparent:document.getElementById("bg").value==="transparent"
  };
  try{
    const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const j=await r.json();
    if(!j.ok){ err.textContent="⚠ "+j.errors.join(" "); return; }
    document.getElementById("img39").src="data:image/png;base64,"+j.code39;
    document.getElementById("img417").src="data:image/png;base64,"+j.pdf417;
    const tr=document.getElementById("bg").value==="transparent";
    document.getElementById("img39").classList.toggle("trans",tr);
    document.getElementById("img417").classList.toggle("trans",tr);
    document.getElementById("dl39").href="data:image/png;base64,"+j.code39;
    document.getElementById("dl39").download="code39_"+body.id_number+".png";
    document.getElementById("dl417").href="data:image/png;base64,"+j.pdf417;
    document.getElementById("dl417").download="pdf417_"+body.id_number+".png";
    document.getElementById("payloadText").textContent=j.payload;
    document.getElementById("plen").textContent=j.payload.length;
  }catch(e){ err.textContent="⚠ Server error: "+e; }
}
function copyPayload(){ navigator.clipboard.writeText(document.getElementById("payloadText").textContent); }
function setTheme(t){ document.documentElement.setAttribute("data-theme",t); try{ localStorage.setItem("va-theme",t); }catch(e){} document.querySelectorAll(".themes button").forEach(b=>b.classList.toggle("active",b.dataset.t===t)); }
(function(){ let t="heritage"; try{ t=localStorage.getItem("va-theme")||"heritage"; }catch(e){} setTheme(t); })();
checkId(false);
</script>
</body>
</html>
"""


def _help_desk_html() -> str:
    """Build the Help Desk card (only shows buttons for configured channels)."""
    prefill = "Hi%20VisualArc%20Editing!%20I%20need%20help%20with%20the%20barcode%20tool."
    buttons = []
    if SUPPORT_WHATSAPP:
        buttons.append(
            '<a class="dl" style="background:#25D366" target="_blank" rel="noopener" '
            f'href="https://wa.me/{SUPPORT_WHATSAPP}?text={prefill}">'
            "\U0001F4AC WhatsApp us</a>"
        )
    if SUPPORT_TELEGRAM:
        buttons.append(
            '<a class="dl" style="background:#229ED9" target="_blank" rel="noopener" '
            f'href="{SUPPORT_TELEGRAM}">'
            "\u2708\ufe0f Telegram us</a>"
        )
    if SUPPORT_SMS:
        buttons.append(
            '<a class="dl" style="background:#0b5fff" '
            f'href="sms:{SUPPORT_SMS}?body={prefill}">'
            "\U0001F4F1 Text us (SMS)</a>"
        )
    if SUPPORT_EMAIL:
        buttons.append(
            '<a class="dl" '
            f'href="mailto:{SUPPORT_EMAIL}?subject=VisualArc%20Editing%20help%20needed&body={prefill}">'
            "\U0001F4E7 Email us</a>"
        )
    buttons.append(
        '<a class="dl" style="background:#6e5494" target="_blank" rel="noopener" '
        f'href="{GITHUB_ISSUES_URL}">\U0001F41E Report an issue on GitHub</a>'
    )
    return (
        '<div class="card" id="help" style="margin-top:16px">'
        "<h2>\U0001F4AC Help Desk \u2014 having issues?</h2>"
        '<p style="font-size:13.5px;line-height:1.6;margin:0 0 6px">'
        "Found a bug, a barcode won\u2019t scan, or something looks wrong? Reach out and we\u2019ll help you out. "
        "Please include <b>what you clicked</b>, <b>what you expected</b>, and a <b>screenshot</b> if you can.</p>"
        "<div>" + "".join(buttons) + "</div>"
        "<details><summary>Quick fixes before you message us</summary>"
        "<p><b>\u2717 Invalid ID number?</b> The last digit is a calculated check digit \u2014 don\u2019t invent numbers. "
        "Use the \U0001F382 birth-date generator or \U0001F3B2 Random valid ID button instead.</p>"
        "<p><b>Barcode won\u2019t scan?</b> Download the PNG and scan at 100% size. Turn the TEST banner off "
        "for a clean symbol, and raise PDF417 error correction to 4\u20135 for rough prints.</p>"
        "<p><b>First load is slow?</b> The free hosting sleeps after 15 idle minutes \u2014 the first visit takes "
        "30\u201360 seconds to wake up. Just wait and refresh.</p>"
        "<p><b>Need no white background?</b> Set Image background to \U0001F532 Transparent before generating.</p>"
        "</details></div>"
    )


@app.get("/")
def index():
    return render_template_string(PAGE.replace("<!--HELP_DESK-->", _help_desk_html()))


@app.post("/api/generate")
def api_generate():
    try:
        b = request.get_json(force=True) or {}
        raw_mode = bool(b.get("raw_mode"))
        raw = (b.get("raw") or "").strip()
        data = SmartIDData(
            surname=b.get("surname", ""),
            names=b.get("names", ""),
            sex=b.get("sex", "M"),
            nationality=b.get("nationality", "RSA"),
            id_number=(b.get("id_number") or "").strip(),
            date_of_birth=(b.get("date_of_birth") or "").strip(),
            country_of_birth=b.get("country_of_birth", "RSA"),
            status=b.get("status", "CITIZEN"),
            date_of_issue=(b.get("date_of_issue") or "").strip(),
            security_number=(b.get("security_number") or "").strip(),
            card_number=(b.get("card_number") or "").strip(),
            filler_chars=int(b.get("filler", 600) or 0),
        )
        errors: list[str] = []
        ok, msg = validate_id_number(data.id_number)
        if not ok:
            errors.append(f"ID number: {msg}")
        if raw_mode:
            if not raw:
                errors.append("Raw mode is on but the raw text is empty.")
        else:
            errors += [e for e in data.validate() if not e.startswith("ID number")]
        if errors:
            return jsonify({"ok": False, "errors": errors})

        result = generate_pair(
            data,
            raw_payload=raw if raw_mode else None,
            pdf_columns=int(b.get("pdf_columns", 8) or 8),
            pdf_security=int(b.get("pdf_security", 3) or 0),
            pdf_scale=int(b.get("pdf_scale", 3) or 3),
            add_test_banner=bool(b.get("banner", True)),
            transparent=bool(b.get("transparent", False)),
        )
        def b64(img) -> str:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return base64.b64encode(buf.getvalue()).decode()
        return jsonify({
            "ok": True,
            "code39": b64(result["code39"]),
            "pdf417": b64(result["pdf417"]),
            "payload": result["payload"],
            "info": info_from_id_number(data.id_number),
        })
    except Exception as e:  # never leak a stack trace to the UI
        return jsonify({"ok": False, "errors": [f"Server error: {e}"]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  VisualArc Editing running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
