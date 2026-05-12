import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIG
# ============================================================

INPUT_PATH = "data/market_data_features.csv"
OUTPUT_DIR = "outputs/figures"

PRICE_COLUMNS = {
    "S&P 500": "SP500_Close",
    "Gold": "Gold_Close",
    "IEF": "IEF_Close",
    "JPY": "JPY_Close",
}

RETURN_COLUMNS = {
    "S&P 500": "SP500_Return",
    "Gold": "Gold_Return",
    "IEF": "IEF_Return",
    "JPY": "JPY_Return",
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_data():
    """
    Load processed market data.
    Required file:
    data/market_data_features.csv
    """
    df = pd.read_csv(INPUT_PATH)

    if "Date" not in df.columns:
        raise ValueError("Missing required column: Date")

    if "is_stress" not in df.columns:
        raise ValueError("Missing required column: is_stress")

    required_columns = [
        "SP500_Close",
        "Gold_Close",
        "IEF_Close",
        "JPY_Close",
        "SP500_Return",
        "Gold_Return",
        "IEF_Return",
        "JPY_Return",
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").reset_index(drop=True)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    return df


def save_chart(filename):
    """
    Save chart as both PNG and PDF.
    """
    png_path = os.path.join(OUTPUT_DIR, f"{filename}.png")
    pdf_path = os.path.join(OUTPUT_DIR, f"{filename}.pdf")

    plt.tight_layout()
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, bbox_inches="tight")
    plt.close()

    print(f"Saved: {png_path}")
    print(f"Saved: {pdf_path}")


def get_stress_periods(df):
    """
    Convert is_stress column into continuous stress periods.
    Example:
    is_stress = 1 from 2020-03-01 to 2020-04-15
    """
    periods = []
    in_stress = False
    start_date = None

    for i in range(len(df)):
        stress = df.loc[i, "is_stress"] == 1

        if stress and not in_stress:
            start_date = df.loc[i, "Date"]
            in_stress = True

        if in_stress and (not stress or i == len(df) - 1):
            end_idx = i if stress else i - 1
            end_date = df.loc[end_idx, "Date"]
            periods.append((start_date, end_date))
            in_stress = False

    return periods


# ============================================================
# CHART 6: DRAWDOWN COMPARISON
# ============================================================

def calculate_drawdown(series):
    """
    Drawdown = current price / previous peak - 1

    Example:
    If price peak = 100 and current price = 80,
    drawdown = 80 / 100 - 1 = -20%
    """
    running_max = series.cummax()
    drawdown = series / running_max - 1
    return drawdown


def chart_6_drawdown_comparison(df):
    """
    Chart 6:
    Compare drawdowns of S&P 500, Gold, IEF, and JPY.

    Interpretation:
    A safe haven asset should have smaller drawdown than S&P 500
    during market stress periods.
    """
    stress_periods = get_stress_periods(df)

    plt.figure(figsize=(14, 7))

    for asset, col in PRICE_COLUMNS.items():
        drawdown = calculate_drawdown(df[col]) * 100

        plt.plot(
            df["Date"],
            drawdown,
            linewidth=1.6,
            label=asset
        )

    for start, end in stress_periods:
        plt.axvspan(start, end, alpha=0.18)

    plt.axhline(0, linewidth=1, linestyle="--")

    plt.title("Chart 6: Drawdown Comparison")
    plt.xlabel("Date")
    plt.ylabel("Drawdown (%)")
    plt.legend()
    plt.grid(True, alpha=0.3)

    save_chart("chart_6_drawdown_comparison")


# ============================================================
# CHART 7: ROLLING CORRELATION WITH S&P 500
# ============================================================

def chart_7_rolling_correlation(df, window=60):
    """
    Chart 7:
    Rolling 60-day correlation between each safe haven asset and S&P 500.

    Interpretation:
    Lower or negative correlation means stronger diversification benefit.
    """
    stress_periods = get_stress_periods(df)

    plt.figure(figsize=(14, 7))

    sp500_return = df["SP500_Return"]

    safe_haven_returns = {
        "Gold": "Gold_Return",
        "IEF": "IEF_Return",
        "JPY": "JPY_Return",
    }

    for asset, col in safe_haven_returns.items():
        rolling_corr = df[col].rolling(window).corr(sp500_return)

        plt.plot(
            df["Date"],
            rolling_corr,
            linewidth=1.6,
            label=f"{asset} vs S&P 500"
        )

    for start, end in stress_periods:
        plt.axvspan(start, end, alpha=0.18)

    plt.axhline(0, linewidth=1, linestyle="--")

    plt.title("Chart 7: Rolling 60-Day Correlation with S&P 500")
    plt.xlabel("Date")
    plt.ylabel("Rolling Correlation")
    plt.legend()
    plt.grid(True, alpha=0.3)

    save_chart("chart_7_rolling_correlation_sp500")


# ============================================================
# CHART 8: STRESS VS NORMAL RETURN COMPARISON
# ============================================================

def chart_8_stress_vs_normal_return(df):
    """
    Chart 8:
    Compare average daily returns of Gold, IEF, and JPY
    during normal periods and stress periods.

    Interpretation:
    A good safe haven asset should perform better or lose less
    during stress periods.
    """
    assets = ["Gold", "IEF", "JPY"]

    normal_df = df[df["is_stress"] == 0].copy()
    stress_df = df[df["is_stress"] == 1].copy()

    normal_returns = []
    stress_returns = []

    for asset in assets:
        return_col = RETURN_COLUMNS[asset]

        normal_mean = normal_df[return_col].dropna().mean() * 100
        stress_mean = stress_df[return_col].dropna().mean() * 100

        normal_returns.append(normal_mean)
        stress_returns.append(stress_mean)

    x = np.arange(len(assets))
    width = 0.35

    plt.figure(figsize=(10, 6))

    plt.bar(
        x - width / 2,
        normal_returns,
        width,
        label="Normal Period"
    )

    plt.bar(
        x + width / 2,
        stress_returns,
        width,
        label="Stress Period"
    )

    plt.axhline(0, linewidth=1, linestyle="--")

    plt.xticks(x, assets)
    plt.title("Chart 8: Average Daily Returns in Normal vs Stress Periods")
    plt.xlabel("Asset")
    plt.ylabel("Average Daily Return (%)")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)

    for i, value in enumerate(normal_returns):
        plt.text(
            i - width / 2,
            value,
            f"{value:.3f}%",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=9
        )

    for i, value in enumerate(stress_returns):
        plt.text(
            i + width / 2,
            value,
            f"{value:.3f}%",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=9
        )

    save_chart("chart_8_stress_vs_normal_return")


# ============================================================
# MAIN
# ============================================================

def main():
    df = load_data()

    chart_6_drawdown_comparison(df)
    chart_7_rolling_correlation(df, window=60)
    chart_8_stress_vs_normal_return(df)

    print("Charts 6, 7, and 8 generated successfully.")


if __name__ == "__main__":
    main()