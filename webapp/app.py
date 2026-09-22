import json
import os
import re

from flask import Flask, render_template, request, send_file, url_for, redirect, flash

import db
from docx_builder import save_document
from leveling import build_cache_key
from pipeline import build_content

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-only-secret")

GENERATED_DIR = os.path.join(os.path.dirname(__file__), "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)

db.init_db()

_ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")


@app.template_filter("ar_num")
def ar_num(value):
    return str(value).translate(_ARABIC_DIGITS)


def _safe_filename_part(text: str) -> str:
    text = re.sub(r"\s+", "_", text.strip())
    return re.sub(r"[\\/:*?\"<>|]", "", text)


def _download_display_name(job_title: str) -> str:
    return f"بطاقة_الوصف_الوظيفي_{_safe_filename_part(job_title)}.docx"


@app.route("/")
def index():
    history = db.list_history()
    for row in history:
        row["content"] = json.loads(row["content_json"])
    return render_template("index.html", history=history, result=None)


@app.route("/generate", methods=["POST"])
def generate():
    job_title = (request.form.get("job_title") or "").strip()
    sub_units_raw = (request.form.get("sub_units") or "").strip()
    force_regenerate = request.form.get("force_regenerate") == "1"

    if not job_title:
        flash("الرجاء إدخال مسمى وظيفي.", "error")
        return redirect(url_for("index"))

    cache_key = build_cache_key(job_title, sub_units_raw)
    cached = None if force_regenerate else db.get_latest_by_normalized(cache_key)

    if cached:
        content = json.loads(cached["content_json"])
        result = {"record": cached, "content": content, "from_cache": True}
    else:
        content = build_content(job_title, sub_units_raw)
        record = db.insert_record(
            job_title_raw=job_title,
            job_title_normalized=cache_key,
            sub_units_raw=sub_units_raw,
            level_tier=content["level_tier"],
            content=content,
            docx_file_path="",  # يُحدَّث أدناه بعد معرفة المعرّف والنسخة
        )
        final_path = os.path.join(GENERATED_DIR, f"{record['id']}_v{record['version']}.docx")
        save_document(content, final_path)
        conn = db.get_connection()
        conn.execute("UPDATE job_descriptions SET docx_file_path = ? WHERE id = ?",
                     (final_path, record["id"]))
        conn.commit()
        conn.close()
        record = db.get_by_id(record["id"])
        result = {"record": record, "content": content, "from_cache": False}

    history = db.list_history()
    for row in history:
        row["content"] = json.loads(row["content_json"])
    return render_template("index.html", history=history, result=result)


@app.route("/download/<int:record_id>")
def download(record_id):
    record = db.get_by_id(record_id)
    if not record or not os.path.exists(record["docx_file_path"]):
        flash("الملف غير موجود.", "error")
        return redirect(url_for("index"))
    display_name = _download_display_name(record["job_title_raw"])
    return send_file(record["docx_file_path"], as_attachment=True, download_name=display_name)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
