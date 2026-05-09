import pandas as pd

MARKET_FILE = "data/market_data_features.csv"
NEWS_FILE = "data/stress_days_news.csv"
OUTPUT_FILE = "data/safe_haven_master.csv"


def main():
    """
    Merge market feature data with stress-day news/context.

    Input:
    - data/market_data_features.csv
    - data/stress_days_news.csv

    Output:
    - data/safe_haven_master.csv
    """

    # 1. Read market data and news/context data
    market_df = pd.read_csv(MARKET_FILE)
    news_df = pd.read_csv(NEWS_FILE)

    # 2. Check required Date column
    if "Date" not in market_df.columns:
        raise ValueError("Market data must contain Date column.")

    if "Date" not in news_df.columns:
        raise ValueError("News data must contain Date column.")

    # 3. Convert Date column to datetime format
    market_df["Date"] = pd.to_datetime(market_df["Date"])
    news_df["Date"] = pd.to_datetime(news_df["Date"])

    # 4. Group multiple headlines/context rows into one cell per stress day
    if not news_df.empty:
        news_grouped = (
            news_df
            .dropna(subset=["title"])
            .groupby("Date")["title"]
            .apply(lambda titles: " || ".join(titles.head(5)))
            .reset_index()
            .rename(columns={"title": "news_headlines"})
        )
    else:
        news_grouped = pd.DataFrame(columns=["Date", "news_headlines"])

    # 5. Merge market data with news headlines by Date
    master_df = market_df.merge(news_grouped, on="Date", how="left")

    # 6. Normal days do not have news/context
    master_df["news_headlines"] = master_df["news_headlines"].fillna("")

    # 7. Forward-fill numeric missing values
    numeric_cols = master_df.select_dtypes(include=["number"]).columns
    master_df[numeric_cols] = master_df[numeric_cols].ffill()

    # 8. Remove duplicated dates
    master_df = master_df.drop_duplicates(subset=["Date"], keep="last")

    # 9. Sort by date
    master_df = master_df.sort_values("Date")

    # 10. Save final master dataset
    master_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"Saved master dataset to: {OUTPUT_FILE}")
    print(f"Rows: {len(master_df)}")
    print(f"Columns: {list(master_df.columns)}")

    # Quick check: show stress rows with news/context
    if "is_stress" in master_df.columns:
        stress_preview = master_df[master_df["is_stress"] == 1][
            ["Date", "is_stress", "news_headlines"]
        ].head(10)

        print("\nStress-day preview:")
        print(stress_preview)


if __name__ == "__main__":
    main()