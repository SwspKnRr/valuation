import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 유틸 함수
# ------------------------------------------------------------
def normalize_score(value, min_val, max_val):
    """구간 내에서 0~100 정규화"""
    if value is None or np.isnan(value):
        return 0
    value = max(min(value, max_val), min_val)
    return (value - min_val) / (max_val - min_val) * 100


def safe_pct_change(series, periods):
    try:
        return series.pct_change(periods=periods).iloc[-1]
    except:
        return None


# ------------------------------------------------------------
# 1. SMA 기반 추세 점수
# ------------------------------------------------------------
def trend_score(price: pd.DataFrame):
    """
    SMA20 / SMA60 / SMA200 기반 추세 점수
    가격이 장기선 위일수록 고득점
    """

    close = price["Close"]

    sma20 = close.rolling(20).mean()
    sma60 = close.rolling(60).mean()
    sma200 = close.rolling(200).mean()

    last = close.iloc[-1]

    score20 = normalize_score((last - sma20.iloc[-1]) / last, -0.1, 0.1)
    score60 = normalize_score((last - sma60.iloc[-1]) / last, -0.2, 0.2)
    score200 = normalize_score((last - sma200.iloc[-1]) / last, -0.3, 0.3)

    total = score20 * 0.4 + score60 * 0.3 + score200 * 0.3
    return total


# ------------------------------------------------------------
# 2. 1M / 3M / 6M 모멘텀 점수
# ------------------------------------------------------------
def return_momentum_score(price: pd.DataFrame):
    close = price["Close"]

    r1m = safe_pct_change(close, 21)
    r3m = safe_pct_change(close, 63)
    r6m = safe_pct_change(close, 126)

    s1 = normalize_score(r1m, -0.20, 0.20)   # -20% ~ +20%
    s3 = normalize_score(r3m, -0.40, 0.40)   # -40% ~ +40%
    s6 = normalize_score(r6m, -0.60, 0.60)   # -60% ~ +60%

    total = s1 * 0.4 + s3 * 0.3 + s6 * 0.3
    return total


# ------------------------------------------------------------
# 3. OBV (On-Balance Volume) 기반 모멘텀
# ------------------------------------------------------------
def obv_score(price: pd.DataFrame):
    close = price["Close"]
    volume = price["Volume"]

    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    obv_ma = obv.rolling(20).mean()

    if obv_ma.iloc[-2] == 0:
        return 0

    trend = (obv_ma.iloc[-1] - obv_ma.iloc[-20]) / abs(obv_ma.iloc[-20])
    return normalize_score(trend, -1, 1)


# ------------------------------------------------------------
# 4. 거래량 모멘텀
# ------------------------------------------------------------
def volume_momentum(price: pd.DataFrame):
    volume = price["Volume"]

    short = volume.rolling(10).mean().iloc[-1]
    long = volume.rolling(60).mean().iloc[-1]

    if long == 0:
        return 50

    ratio = (short - long) / long  # 최근 거래량이 얼마나 증가/감소했는가

    return normalize_score(ratio, -0.5, 0.5)  # -50% ~ +50%


# ------------------------------------------------------------
# 5. 최종 Momentum Score
# ------------------------------------------------------------
def momentum_score(data: dict):
    """
    fetch_data.py에서 넘겨준 data(dict):
    data["price"] 필요
    """

    price = data.get("price")
    if price is None or len(price) < 250:
        return 50  # 데이터 부족 → 중간 점수 반환

    score_trend = trend_score(price)
    score_return = return_momentum_score(price)
    score_obv = obv_score(price)
    score_vol = volume_momentum(price)

    final = (
        score_trend * 0.35 +
        score_return * 0.35 +
        score_obv * 0.20 +
        score_vol * 0.10
    )

    return min(max(final, 0), 100)
