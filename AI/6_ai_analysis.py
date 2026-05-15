import json
import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent  # AI/ -> project root

load_dotenv(BASE_DIR / ".env")  # ← chuyển xuống đây, SAU khi BASE_DIR có giá trị

DATA_DIR = BASE_DIR / "data"
ANALYSIS_DIR = BASE_DIR / "analysis"
VIZ_DIR = BASE_DIR / "visualization" / "output"

INPUT_FEATURES = DATA_DIR / "market_data_features.csv"
INPUT_SCORE = DATA_DIR / "safe_haven_score.csv"
OUTPUT_REPORT = ANALYSIS_DIR / "ai_report.md"

MODEL_NAME = "llama-3.3-70b-versatile"


# ─────────────────────────────────────────────
# HELPER: MARKDOWN IMAGE
# ─────────────────────────────────────────────
def img_tag(chart_name: str) -> str:
    """
    Return markdown image only if chart exists.
    If chart is missing -> return empty string.
    """

    path = VIZ_DIR / chart_name

    if not path.exists():
        return ""

    rel_path = f"../visualization/output/{chart_name}"

    return f"![{chart_name}]({rel_path})\n\n"


def render_charts(chart_list):
    """
    Render multiple charts safely.
    Missing charts will be skipped automatically.
    """

    return "".join(
        img_tag(chart)
        for chart in chart_list
    )


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
def load_data():

    print("[INFO] Loading CSV files...")

    if not INPUT_FEATURES.exists():
        print(f"ERROR: Missing file -> {INPUT_FEATURES}")
        sys.exit(1)

    if not INPUT_SCORE.exists():
        print(f"ERROR: Missing file -> {INPUT_SCORE}")
        sys.exit(1)

    features = pd.read_csv(
        INPUT_FEATURES,
        index_col="Date",
        parse_dates=True
    )

    score = pd.read_csv(
        INPUT_SCORE,
        index_col=0
    )

    print("[INFO] Data loaded successfully")

    return features, score


# ─────────────────────────────────────────────
# BUILD CONTEXT
# ─────────────────────────────────────────────
def build_context(features, score):

    print("[1/4] Building statistics context...")

    total_stress = int(features["is_stress"].sum())

    vix_peak_row = features.loc[
        features["VIX_Close"].idxmax()
    ]

    sp500_worst_row = features.loc[
        features["SP500_Return"].idxmin()
    ]

    sp500_best_row = features.loc[
        features["SP500_Return"].idxmax()
    ]

    stress_df = (
        features[features["is_stress"] == 1]
        .sort_values("VIX_Close", ascending=False)
        .head(10)
    )

    top_assets = score.sort_values(
        "final_score",
        ascending=False
    )

    stress_data = {}

    cols = [
        "VIX_Close",
        "SP500_Return",
        "Gold_Return",
        "IEF_Return",
        "JPY_Return",
    ]

    for idx, row in stress_df[cols].iterrows():

        stress_data[str(idx.date())] = {
            "VIX_Close": float(row["VIX_Close"]),
            "SP500_Return": float(row["SP500_Return"]),
            "Gold_Return": float(row["Gold_Return"]),
            "IEF_Return": float(row["IEF_Return"]),
            "JPY_Return": float(row["JPY_Return"]),
        }

    ctx = {
        "metadata": {
            "start_date": str(features.index.min().date()),
            "end_date": str(features.index.max().date()),
            "stress_days": total_stress,

            "vix_peak": {
                "val": round(vix_peak_row["VIX_Close"], 2),
                "date": str(vix_peak_row.name.date()),
            },

            "sp500_worst": {
                "val": f"{round(sp500_worst_row['SP500_Return'] * 100, 2)}%",
                "date": str(sp500_worst_row.name.date()),
            },

            "sp500_best": {
                "val": f"{round(sp500_best_row['SP500_Return'] * 100, 2)}%",
                "date": str(sp500_best_row.name.date()),
            },
        },

        "rankings": top_assets[
            ["final_score", "rank", "win_rate"]
        ].to_dict("index"),

        "stress_data": stress_data,
    }

    return ctx


# ─────────────────────────────────────────────
# CALL GROQ
# ─────────────────────────────────────────────
def call_llm(prompt, context, max_retries=3):

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return "ERROR: Missing GROQ_API_KEY"
    
    print(f"[DEBUG] API Key loaded: {api_key[:8]}...{api_key[-4:]}")

    client = Groq(api_key=api_key)

    for attempt in range(1, max_retries + 1):

        try:

            completion = client.chat.completions.create(
                model=MODEL_NAME,

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional financial analyst. "
                            "Write concise institutional-style analysis "
                            "based on the provided market data."
                        ),
                    },

                    {
                        "role": "user",
                        "content": (
                            f"Task:\n{prompt}\n\n"
                            f"Dataset:\n{context}\n\n"

                            "Requirements:\n"
                            "- Professional analyst tone\n"
                            "- Reference actual numbers\n"
                            "- Mention VIX, SP500, Gold, IEF, JPY\n"
                            "- Keep concise\n"
                            "- 3-5 paragraphs"
                        ),
                    },
                ],

                temperature=0.4,
                max_tokens=600,
            )

            return (
                completion
                .choices[0]
                .message.content
                .strip()
            )

        except Exception as e:

            err = str(e)

            print(
                f"[ERROR] Attempt "
                f"{attempt}/{max_retries}: {err}"
            )

            if attempt < max_retries:

                wait = 5 * attempt

                print(f"Retrying in {wait}s...")

                time.sleep(wait)

            else:
                return f"[AI ERROR] {err}"


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():

    print("===================================")
    print(" AI FINANCIAL ANALYSIS GENERATOR ")
    print("===================================")

    print("[DEBUG] Working directory:")
    print(os.getcwd())

    # LOAD DATA
    features, score = load_data()

    # BUILD CONTEXT
    ctx = build_context(features, score)

    ctx_small = {
        "metadata": ctx["metadata"],
        "rankings": ctx["rankings"],
        "stress_data": dict(
            list(ctx["stress_data"].items())[:5]
        ),
    }

    ctx_json = json.dumps(
        ctx_small,
        indent=2
    )

    # AI TASKS
    print("[2/4] Running AI analysis...")

    tasks = {

        "trend": (
            "Analyze the overall market trend and "
            "VIX behavior during stress periods."
        ),

        "anomaly": (
            "Analyze the most extreme stress "
            "episodes in the dataset."
        ),

        "risk": (
            "Explain why the top-ranked safe haven "
            "asset is safer than others."
        ),

        "comparison": (
            "Compare Gold, IEF, and JPY during "
            "market panic periods."
        ),
    }

    results = {}

    for key, prompt in tasks.items():

        print(f"[AI] Processing: {key}")

        results[key] = call_llm(
            prompt,
            ctx_json
        )

        time.sleep(2)

    # BUILD REPORT
    print("[3/4] Building markdown report...")

    m = ctx["metadata"]

    report = f"""# AI Financial Analysis Report

**Generated by:** `analysis/6_ai_analysis.py`  
**Observation Period:** {m['start_date']} → {m['end_date']}  
**Stress Days Flagged:** {m['stress_days']} days

---

## Key Metrics Snapshot

| Metric | Value |
|--------|-------|
| VIX Peak | **{m['vix_peak']['val']}** on {m['vix_peak']['date']} |
| SP500 Worst Day | **{m['sp500_worst']['val']}** on {m['sp500_worst']['date']} |
| SP500 Best Day | **{m['sp500_best']['val']}** on {m['sp500_best']['date']} |

---

## Safe Haven Score Summary

| Rank | Asset | Score | Win Rate |
|------|-------|-------|----------|
"""

    for asset, info in ctx["rankings"].items():

        report += (
            f"| #{int(info['rank'])} "
            f"| **{asset}** "
            f"| {round(info['final_score'], 4)} "
            f"| {round(info['win_rate'] * 100, 1)}% |\n"
        )

    # ─────────────────────────────────────────────
    # CHART GROUPS
    # ─────────────────────────────────────────────
    trend_charts = [
        "chart1_stress_timeline.png",
        "chart2_performance.png",
    ]

    anomaly_charts = [
        "chart6_stress_episodes.png",
        "chart_8_stress_vs_normal_return.png",
    ]

    risk_charts = [
        "chart5_score_ranking.png",
        "chart_6_drawdown_comparison.png",
    ]

    comparison_charts = [
        "chart3_correlation.png",
        "chart_7_rolling_correlation_sp500.png",
        "chart4_distribution.png",
    ]

    # ─────────────────────────────────────────────
    # REPORT BODY
    # ─────────────────────────────────────────────
    report += f"""

---

## 1. Trend Summary

{render_charts(trend_charts)}

{results['trend']}

---

## 2. Anomaly Detection

{render_charts(anomaly_charts)}

{results['anomaly']}

---

## 3. Risk Commentary

{render_charts(risk_charts)}

{results['risk']}

---

## 4. Asset Comparison

{render_charts(comparison_charts)}

{results['comparison']}

---

## Appendix: Top Stress Episodes

| Date | VIX | SP500 | Gold | IEF | JPY |
|------|-----|-------|------|-----|-----|
"""

    for date, row in ctx["stress_data"].items():

        report += (
            f"| {date} "
            f"| {round(row['VIX_Close'], 2)} "
            f"| {round(row['SP500_Return'] * 100, 2)}% "
            f"| {round(row['Gold_Return'] * 100, 2)}% "
            f"| {round(row['IEF_Return'] * 100, 2)}% "
            f"| {round(row['JPY_Return'] * 100, 2)}% |\n"
        )

    # SAVE REPORT
    ANALYSIS_DIR.mkdir(exist_ok=True)

    OUTPUT_REPORT.write_text(
        report,
        encoding="utf-8"
    )

    print("[4/4] SUCCESS!")
    print(f"Report saved to:\n{OUTPUT_REPORT}")

    print("\nOpen:")
    print("analysis/ai_report.md")

    print("\nThen press:")
    print("Ctrl + Shift + V")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    main()