"""Flask web application — A/B Test Validity Diagnostics.

Multi-page academic site with an OpenAI-powered research chatbot.

Run:
    pip install flask openai python-dotenv pandas
    set OPENAI_API_KEY=sk-...   (or put it in webapp/.env)
    python webapp/app.py
Then open http://localhost:5000
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Đảm bảo thư mục webapp nằm trong sys.path để import được context_builder khi chạy trên Render (Gunicorn)
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

from context_builder import build_system_prompt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
TABLES = OUTPUT / "tables"
FIGURES = OUTPUT / "figures"
PAPER = ROOT / "paper"

load_dotenv(Path(__file__).parent / ".env", override=True)

app = Flask(__name__)

# ---------------------------------------------------------------- data layer
KPI = {
    "cr_control": "9.85%",
    "cr_test": "8.64%",
    "rel_diff": "-12.28%",
    "dispersion": "162.95",
    "aa_fpr": "87.8%",
    "srm_chi2": "1646.44",
    "glm_p": "0.342",
    "welch_p": "0.135",
    "bootstrap_ci": "[-32.2%, +12.7%]",
}

FUNNEL_LABELS = {
    "ctr": "CTR (clicks / impressions)",
    "view_rate": "View-content per click",
    "atc_rate": "Add-to-cart per view",
    "purchase_rate": "Purchase given add-to-cart",
    "cr": "Overall CR (purchase / clicks)",
}


def _load_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / name)


def funnel_chart_data() -> dict:
    df = _load_csv("funnel_step_tests.csv")
    return {
        "steps": [FUNNEL_LABELS.get(s, s) for s in df["step"]],
        "rel_diff": [round(v * 100, 1) for v in df["rel_diff"]],
        "rate_control": [round(v * 100, 2) for v in df["rate_control"]],
        "rate_test": [round(v * 100, 2) for v in df["rate_test"]],
        "p_holm": [f"{v:.2e}" for v in df["p_holm"]],
    }


def weekday_chart_data() -> dict:
    df = _load_csv("hte_weekday.csv")
    err = (1.96 * (df["abs_uplift"] / df["z"]).abs() * 100).round(3)
    return {
        "weekdays": df["segment"].tolist(),
        "abs_uplift_pp": [round(v * 100, 2) for v in df["abs_uplift"]],
        "err": err.tolist(),
        "rel_uplift": [round(v * 100, 1) for v in df["rel_uplift"]],
        "significant": df["significant_holm"].astype(bool).tolist(),
        "n_control": df["n_control"].tolist(),
        "n_test": df["n_test"].tolist(),
    }


def aggregate_table() -> list[dict]:
    rows = [
        ("Impressions", "3,250,111", "2,237,544"),
        ("Clicks", "157,368", "180,970"),
        ("View-content events", "57,352", "55,740"),
        ("Add-to-cart events", "38,883", "26,446"),
        ("Purchases", "15,501", "15,637"),
        ("Spend (USD)", "68,653", "76,892"),
        ("Click-through rate", "4.84%", "8.09%"),
        ("View-content per click", "36.44%", "30.80%"),
        ("Add-to-cart per view", "67.80%", "47.45%"),
        ("Purchase per click (CR)", "9.85%", "8.64%"),
    ]
    return [{"q": q, "c": c, "t": t} for q, c, t in rows]


# ---------------------------------------------------------------- pages
@app.route("/")
def home():
    return render_template("home.html", page="home", kpi=KPI)


@app.route("/dataset")
def dataset():
    return render_template(
        "dataset.html", page="dataset", kpi=KPI,
        agg_rows=aggregate_table(),
    )


@app.route("/diagnostics")
def diagnostics():
    outliers = _load_csv("outlier_days.csv").to_dict("records")
    return render_template(
        "diagnostics.html", page="diagnostics", kpi=KPI, outliers=outliers,
    )


@app.route("/results")
def results():
    return render_template("results.html", page="results", kpi=KPI)


@app.route("/funnel")
def funnel():
    return render_template(
        "funnel.html", page="funnel", kpi=KPI,
        chart=json.dumps(funnel_chart_data()),
    )


@app.route("/weekday")
def weekday():
    return render_template(
        "weekday.html", page="weekday", kpi=KPI,
        chart=json.dumps(weekday_chart_data()),
    )


@app.route("/paper")
def paper():
    return render_template("paper.html", page="paper", kpi=KPI)


@app.route("/chatbot")
def chatbot():
    has_key = bool(os.environ.get("OPENAI_API_KEY"))
    return render_template("chatbot.html", page="chatbot", kpi=KPI,
                           has_key=has_key)


# ---------------------------------------------------------------- assets
@app.route("/figures/<path:fname>")
def figures(fname: str):
    return send_from_directory(FIGURES, fname)


@app.route("/download/<path:fname>")
def download(fname: str):
    return send_from_directory(PAPER, fname, as_attachment=True)


# ---------------------------------------------------------------- chat API
_SYSTEM_PROMPT: str | None = None


def _get_system_prompt() -> str:
    global _SYSTEM_PROMPT
    if _SYSTEM_PROMPT is None:
        _SYSTEM_PROMPT = build_system_prompt(OUTPUT, TABLES)
    return _SYSTEM_PROMPT


@app.route("/api/chat", methods=["POST"])
def api_chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    history = payload.get("history") or []
    if not message:
        return jsonify({"error": "empty message"}), 400

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return jsonify({
            "reply": "⚠️ OPENAI_API_KEY not configured. "
                     "Create a webapp/.env file with: OPENAI_API_KEY=sk-..."
        })

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        messages = [{"role": "system", "content": _get_system_prompt()}]
        for turn in history[-10:]:
            role = turn.get("role")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": turn.get("content", "")})
        messages.append({"role": "user", "content": message})

        resp = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            max_completion_tokens=900,
        )
        return jsonify({"reply": resp.choices[0].message.content})
    except Exception as exc:  # surface the real cause to the demo user
        return jsonify({"reply": f"⚠️ Lỗi gọi OpenAI API: {exc}"}), 200


if __name__ == "__main__":
    app.run(debug=True, port=5000)
