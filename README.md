# IT-Application-in-Banking-and-Finance
# 🛡️ SafeHaven AI

An automated financial analysis agent that identifies which safe haven asset — **Gold**, **US Treasury Bonds (IEF)**, or **Japanese Yen (JPY)** — best protects capital when the stock market enters a period of stress.

---

## 🔍 Tracked Assets

| Ticker | Asset | Role |
|--------|-------|------|
| `^GSPC` | S&P 500 | Stock market benchmark |
| `^VIX` | CBOE Volatility Index | Market stress indicator |
| `GC=F` | Gold Futures | Safe haven — commodity |
| `IEF` | iShares 7–10Y Treasury ETF | Safe haven — bonds |
| `JPY=X` | USD/JPY | Safe haven — currency |

---

## ⚙️ Setup

**Requirements:** Python 3.10+, Git

```bash
git clone https://github.com/your-team/IT-Application-in-Banking-and-Finance.git
cd IT-Application-in-Banking-and-Finance

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env            # Fill in your API keys in the .env file
```

---

## 🔑 API Key Configuration

Open the `.env` file and fill in:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Get a free Groq API key at: https://console.groq.com

Verify the key works:

```bash
python test_key.py
```

---

## 🚀 Running the Pipeline

Run in order:

```bash
python data_process/1_data_collector    # Collect data
python data_process/2_data_cleaner      # Clean data
python analysis/3_data_features         # Compute features & detect stress periods
python analysis/4_safe_haven_score      # Score safe haven assets
python visualization/Chart              # Generate 8 charts
python AI/6_ai_analysis.py              # Generate AI report
```

Or let the pipeline run automatically every day via **GitHub Actions** (`daily_run.yml`) — no manual steps required.

---

## 📊 Output

**Charts** — saved to `visualization/output/`:

| File | Description |
|------|-------------|
| `chart1_stress_timeline.png` | S&P 500 with detected stress periods highlighted |
| `chart2_performance.png` | Normalized performance (base 100) of Gold, IEF, JPY |
| `chart3_correlation.png` | Correlation heatmap: full period vs. stress days |
| `chart4_distribution.png` | Daily return distribution during stress periods |
| `chart5_score_ranking.png` | Composite Safe Haven score ranking |
| `chart6_stress_episodes.png` | Cumulative performance across the 3 largest stress episodes |
| `chart7_drawdown_comparison.png` | Drawdown comparison: S&P 500 vs. safe haven assets |
| `chart8_rolling_correlation_sp500.png` | 30-day rolling correlation with S&P 500 |

**AI Report** — covers 4 sections: Trend Summary · Anomaly Detection · Risk Commentary · Asset Comparison.

---

## 📁 Project Structure

```
├── .github/workflows/daily_run.yml   # Automated daily pipeline
├── data/                             # CSV data files (auto-generated, do not edit manually)
├── data_process/                     # Data collection & cleaning
├── analysis/                         # Feature engineering & scoring
├── AI/                               # Groq API integration
├── visualization/                    # Chart generation & output
├── .env.example                      # API key configuration template
├── requirements.txt
└── test_key.py
```

---

## 📦 Main Libraries

`yfinance` · `pandas` · `numpy` · `matplotlib` · `seaborn` · `plotly` · `groq` · `python-dotenv`

---

## 📚 References

- Groq API: https://console.groq.com/docs
- yfinance: https://github.com/ranaroussi/yfinance
- CBOE VIX: https://www.cboe.com/tradable-products/vix/
- S&P 500: https://www.spglobal.com/spdji/en/indices/equity/sp-500/
