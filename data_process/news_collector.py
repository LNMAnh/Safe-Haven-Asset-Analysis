import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
USE_FALLBACK_NEWS = os.getenv("USE_FALLBACK_NEWS", "true").lower() == "true"

INPUT_FILE = "data/market_data_features.csv"
OUTPUT_FILE = "data/stress_days_news.csv"


def load_stress_days(input_file):
    """
    Đọc file market_data_features.csv và lọc các ngày market stress.
    Trong project này: is_stress = 1 nghĩa là ngày thị trường căng thẳng.
    """
    df = pd.read_csv(input_file)

    if "Date" not in df.columns:
        raise ValueError("Không tìm thấy cột Date trong file market data.")

    if "is_stress" not in df.columns:
        raise ValueError("Không tìm thấy cột is_stress trong file market data.")

    df["Date"] = pd.to_datetime(df["Date"])

    stress_df = df[df["is_stress"] == 1].copy()

    if stress_df.empty:
        print("Không tìm thấy ngày stress nào trong dữ liệu.")
        return pd.DataFrame()

    # Nếu có cột VIX_Close thì chọn các ngày stress mạnh nhất trước
    if "VIX_Close" in stress_df.columns:
        stress_df = stress_df.sort_values("VIX_Close", ascending=False)

    # Lấy tất cả các ngày stress
# stress_df = stress_df.head(20)

    return stress_df


def fetch_newsapi_headlines(date, page_size=5):
    """
    Thử lấy headline thật từ NewsAPI.
    Lưu ý: NewsAPI free có thể không lấy được tin quá cũ.
    """
    if not NEWS_API_KEY or NEWS_API_KEY == "your_real_newsapi_key_here":
        return []

    date_str = date.strftime("%Y-%m-%d")

    query = '(stock market OR "S&P 500" OR VIX OR "Wall Street" OR recession OR inflation OR "Federal Reserve")'

    url = "https://newsapi.org/v2/everything"

    params = {
        "q": query,
        "from": date_str,
        "to": date_str,
        "language": "en",
        "sortBy": "relevancy",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        articles = data.get("articles", [])

        results = []

        for article in articles:
            results.append({
                "Date": date_str,
                "source": article.get("source", {}).get("name"),
                "title": article.get("title"),
                "url": article.get("url"),
                "published_at": article.get("publishedAt"),
                "news_provider": "NewsAPI"
            })

        return results

    except Exception as error:
        print(f"NewsAPI không lấy được tin cho ngày {date_str}: {error}")
        return []


def create_fallback_headlines(row):
    """
    Create fallback market-context headlines for every stress day.

    This guarantees that each is_stress = 1 day has at least one
    context sentence, even when NewsAPI cannot return historical news.
    """
    date_str = row["Date"].strftime("%Y-%m-%d")

    # Helper function: get value safely from possible column names
    def get_value(possible_names):
        for name in possible_names:
            if name in row.index and pd.notna(row[name]):
                return row[name]
        return None

    vix = get_value(["VIX_Close", "VIX", "^VIX"])
    sp500_return = get_value(["SP500_Return", "SP500_return", "SP500_Daily_Return"])
    gold_return = get_value(["Gold_Return", "Gold_return", "GC_Return"])
    ief_return = get_value(["IEF_Return", "IEF_return"])
    jpy_return = get_value(["JPY_Return", "JPY_return", "JPY_USD_Return"])

    headlines = []

    # Always create at least one context line
    headlines.append(
        f"Market stress day identified on {date_str} based on the project's is_stress flag."
    )

    if vix is not None:
        headlines.append(
            f"VIX closed at {vix:.2f}, showing elevated market fear and volatility."
        )

    if sp500_return is not None:
        headlines.append(
            f"S&P 500 daily return was {sp500_return:.2%}, representing equity market pressure."
        )

    if gold_return is not None:
        headlines.append(
            f"Gold daily return was {gold_return:.2%}, used to evaluate commodity safe-haven behavior."
        )

    if ief_return is not None:
        headlines.append(
            f"US Treasury bond ETF IEF daily return was {ief_return:.2%}, used to evaluate bond safe-haven behavior."
        )

    if jpy_return is not None:
        headlines.append(
            f"JPY/USD daily return was {jpy_return:.2%}, used to evaluate currency safe-haven behavior."
        )

    results = []

    for headline in headlines[:5]:
        results.append({
            "Date": date_str,
            "source": "Fallback market context",
            "title": headline,
            "url": "",
            "published_at": date_str,
            "news_provider": "Fallback"
        })

    return results


def main():
    stress_df = load_stress_days(INPUT_FILE)

    all_news = []

    for _, row in stress_df.iterrows():
        date = row["Date"]

        print(f"Đang lấy news/context cho ngày stress: {date.date()}")

        news = fetch_newsapi_headlines(date, page_size=5)

        if len(news) == 0 and USE_FALLBACK_NEWS:
            news = create_fallback_headlines(row)

        all_news.extend(news)

        time.sleep(1)

    news_df = pd.DataFrame(all_news)

    if news_df.empty:
        news_df = pd.DataFrame(columns=[
            "Date", "source", "title", "url", "published_at", "news_provider"
        ])

    news_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Đã lưu file news/context tại: {OUTPUT_FILE}")
    print(f"Số dòng news/context: {len(news_df)}")


if __name__ == "__main__":
    main()