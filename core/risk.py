import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 유틸
# ------------------------------------------------------------
def normalize_score(value, min_val, max_val):
    if value is None or np.isnan(value):
        return 50
    value = max(min(value, max_val), min_val)
    return (value - min_val) / (max_val - min_val) * 100


# ------------------------------------------------------------
# 1. 변동성 기반 리스크 (Volatility Risk)
# ------------------------------------------------------------
def volatility_risk(price: pd.DataFrame):
    close = price["Close"]

    # 단기/장기 변동성
    vol20 = close.pct_change().rolling(20).std().iloc[-1]
    vol120 = close.pct_change().rolling(120).std().iloc[-1]

    # 단기 변동성 자체 점수 → 변동 높을수록 위험
    score_vol = normalize_score(-vol20, -0.1, 0.1)

    # 변동성 압축/폭발 판단 (단기 / 장기)
    if vol120 == 0:
        ratio_score = 50
    else:
        ratio = vol20 / vol120
        ratio_score = normalize_score(2 - ratio, -0.5, 2.0)

    total = score_vol * 0.6 + ratio_score * 0.4
    return total


# ------------------------------------------------------------
# 2. ATR 리스크 (가격 진폭 기반)
# ------------------------------------------------------------
def atr_risk(price: pd.DataFrame):
    high = price["High"]
    low = price["Low"]
    close = price["Close"]

    tr = np.maximum(high - low, 
                    np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1))))
    atr = tr.rolling(14).mean().iloc[-1]

    last_price = close.iloc[-1]

    if last_price == 0:
        return 50

    atr_ratio = atr / last_price  # 비율이 높을수록 위험

    return normalize_score(-atr_ratio, -0.05, 0.05)  # 5% 이상 변동이면 위험


# ------------------------------------------------------------
# 3. 베타 리스크 (시장 민감도)
# ------------------------------------------------------------
def beta_risk(beta):
    # 베타 1.0 = 시장과 동일 → 중간 점수
    # 베타 2.0 = 매우 위험
    # 베타 0.5 = 방어적

    if beta is None:
        return 50

    return normalize_score(1 - beta, -1, 1)  # 낮을수록 안전


# ------------------------------------------------------------
# 4. Shock Risk (갭다운, 급락 빈도)
# ------------------------------------------------------------
def shock_risk(price: pd.DataFrame):
    close = price["Close"]

    # 최근 60일 기준
    returns = close.pct_change()

    # 급락 횟수 (-5% 이하)
    drops = (returns < -0.05).sum()

    # 갭다운(시가 기준)
    openp = price["Open"]
    gap = (openp.pct_change() < -0.03).sum()

    # 위험할수록 점수 ↓
    score_drop = normalize_score(-drops, -10, 0)
    score_gap = normalize_score(-gap, -10, 0)

    total = score_drop * 0.6 + score_gap * 0.4
    return total


# ------------------------------------------------------------
# 5. 최종 Risk Score (0~100)
#    안전할수록 높은 점수
# ------------------------------------------------------------
def risk_score(data: dict):
    price = data.get("price")
    beta = data.get("beta")

    if price is None or len(price) < 200:
        return 50

    v_score = volatility_risk(price)
    a_score = atr_risk(price)
    b_score = beta_risk(beta)
    s_score = shock_risk(price)

    final = (
        v_score * 0.35 +
        a_score * 0.25 +
        b_score * 0.20 +
        s_score * 0.20
    )

    return min(max(final, 0), 100)
