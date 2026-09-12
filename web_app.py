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

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SA Smart ID Barcode Tool — Test Specimens (Code 39 + PDF417)</title>
<style>
  :root { --green:#007749; --gold:#FCB514; --red:#DE3831; --black:#111; --bg:#f4f6f5; --card:#fff; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif; background:var(--bg); color:#222; }
  header { background:linear-gradient(135deg,#007749 0%,#005a38 60%,#111 100%); color:#fff; padding:22px 16px; }
  header .wrap, main.wrap { max-width:1080px; margin:0 auto; }
  header h1 { margin:0 0 6px; font-size:22px; }
  header p { margin:0; opacity:.92; font-size:14px; max-width:70ch; }
  .flagbar { height:6px; background:linear-gradient(90deg,#DE3831 0 20%,#fff 20% 24%,#002395 24% 44%,#fff 44% 48%,#007749 48% 68%,#FCB514 68% 72%,#111 72% 100%); }
  .warn { background:#fff8e1; border:2px solid var(--gold); border-radius:10px; padding:10px 14px; margin:14px 0; font-size:13.5px; }
  .grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
  @media (max-width:900px){ .grid{grid-template-columns:1fr;} }
  .card { background:var(--card); border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.07); padding:18px; }
  .card h2 { margin:0 0 12px; font-size:17px; color:#005a38; }
  label { display:block; font-size:12.5px; font-weight:600; margin:10px 0 4px; color:#333; }
  input, select, textarea { width:100%; padding:9px 10px; border:1px solid #c9d2cd; border-radius:8px; font-size:14px; }
  input:focus, select:focus, textarea:focus { outline:2px solid #00774955; border-color:#007749; }
  .row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  .id-ok { color:#007749; font-size:12.5px; margin-top:4px; }
  .id-bad { color:var(--red); font-size:12.5px; margin-top:4px; }
  .btns { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }
  button { cursor:pointer; border:0; border-radius:9px; padding:11px 16px; font-size:14px; font-weight:700; }
  .primary { background:var(--green); color:#fff; }
  .primary:hover { background:#005a38; }
  .ghost { background:#eef2f0; color:#222; }
  .toggle { display:flex; align-items:center; gap:8px; margin-top:12px; font-size:13.5px; }
  .toggle input { width:auto; }
  #rawBox { display:none; }
  .out img { max-width:100%; background:#fff; border:1px solid #ddd; border-radius:8px; }
  .dl { display:inline-block; margin:6px 8px 12px 0; background:#111; color:#fff; text-decoration:none; padding:8px 14px; border-radius:8px; font-size:13px; font-weight:700; }
  pre.payload { background:#0e1a14; color:#d7ffe4; padding:12px; border-radius:8px; font-size:11.5px; max-height:180px; overflow:auto; word-break:break-all; white-space:pre-wrap; }
  footer { text-align:center; font-size:12px; color:#666; padding:18px; }
  .pill { display:inline-block; background:#e7f4ec; color:#005a38; border-radius:20px; padding:2px 10px; font-size:12px; font-weight:700; }
  details { font-size:13px; background:#f8faf9; border:1px solid #dde5e0; border-radius:8px; padding:10px 12px; margin-top:12px; }
  summary { cursor:pointer; font-weight:700; color:#005a38; }
  code { background:#eef2f0; padding:1px 5px; border-radius:4px; }
</style>
</head>
<body>
<header>
  <div class="wrap">
    <h1>🇿🇦 SA Smart ID Barcode Tool <span class="pill">TEST SPECIMENS</span></h1>
    <p>Generate <b>Code&nbsp;39</b> (ID number) + <b>PDF417</b> (personal details) barcodes in the style of the back of the South African Smart ID Card — for testing scanners &amp; software. Field list follows the public Wikipedia description. 100% offline: nothing leaves your computer.</p>
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
<footer>SA Smart ID Barcode Tool • For testing &amp; education only • Runs fully offline on your machine</footer>
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
function makeTestId(){
  const y=1960+Math.floor(Math.random()*46), m=1+Math.floor(Math.random()*12), d=1+Math.floor(Math.random()*28);
  const female=Math.random()<0.5;
  const seq=female?Math.floor(Math.random()*5000):5000+Math.floor(Math.random()*5000);
  const partial=String(y).slice(2)+String(m).padStart(2,"0")+String(d).padStart(2,"0")+String(seq).padStart(4,"0")+"08";
  let odd=0; for(let i=0;i<12;i+=2) odd+=+partial[i];
  let evenStr=""; for(let i=1;i<12;i+=2) evenStr+=partial[i];
  let evenSum=String(+evenStr*2).split("").reduce((a,c)=>a+ +c,0);
  const check=String((10-((odd+evenSum)%10))%10);
  document.getElementById("id_number").value=partial+check;
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
    banner:document.getElementById("banner").checked
  };
  try{
    const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    const j=await r.json();
    if(!j.ok){ err.textContent="⚠ "+j.errors.join(" "); return; }
    document.getElementById("img39").src="data:image/png;base64,"+j.code39;
    document.getElementById("img417").src="data:image/png;base64,"+j.pdf417;
    document.getElementById("dl39").href="data:image/png;base64,"+j.code39;
    document.getElementById("dl39").download="code39_"+body.id_number+".png";
    document.getElementById("dl417").href="data:image/png;base64,"+j.pdf417;
    document.getElementById("dl417").download="pdf417_"+body.id_number+".png";
    document.getElementById("payloadText").textContent=j.payload;
    document.getElementById("plen").textContent=j.payload.length;
  }catch(e){ err.textContent="⚠ Server error: "+e; }
}
function copyPayload(){ navigator.clipboard.writeText(document.getElementById("payloadText").textContent); }
checkId(false);
</script>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(PAGE)


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
    print(f"\n  SA Smart ID Barcode Tool running at http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
