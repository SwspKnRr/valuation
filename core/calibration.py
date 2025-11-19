# core/calibration.py

import numpy as np
import pandas as pd

from core.fetch_data import fetch_company_data
from core.valuation import dcf_fair_value
from core.model_profiles import MODEL_PROFILES


def _prepare_fcf_series(data: dict):
    """fundamental_score에서 쓰는 것과 동일한 FCF 시리즈 구성 로직"""
    info = data.get("info", {})
    fcf_series = data.get("fcf")

    if fcf_series is not None:
        try:
            fcf_clean = fcf_series.dropna()
            if len(fcf_clean) > 0:
                return fcf_clean
        except Exception:
            pass

    # fallback: info["freeCashflow"] 단일 값
    fcf_last = info.get("freeCashflow")
    if fcf_last is not None:
        return pd.Series([fcf_last])

    return None


def _mean_log_diff_for_discount(ref_tickers, mode, discount_rate):
    """
    주어진 할인율에서, 기준 종목들의
    평균 log(Fair / Price)를 계산.
    이 값이 0에 가까울수록 '시장과 맞게' 캘리브레이션된 상태.
    """
    profile = MODEL_PROFILES.get(mode, MODEL_PROFILES["bluechip"])

    g1 = profile["g1"]
    g2 = profile["g2"]
    terminal = profile["terminal"]

    diffs = []

    for t in ref_tickers:
        try:
            data = fetch_company_data(t)
            price = data.get("current_price")
            if price is None or price <= 0:
                continue

            fcf_series = _prepare_fcf_series(data)
            if fcf_series is None:
                continue

            fair = dcf_fair_value(
                fcf_series=fcf_series,
                shares_outstanding=data.get("shares_outstanding"),
                discount_rate=discount_rate,
                g1=g1,
                g2=g2,
                terminal_growth=terminal,
                total_debt=data.get("total_debt"),
                total_cash=data.get("total_cash"),
            )

            if fair is None or fair <= 0:
                continue

            diffs.append(np.log(fair / price))
        except Exception:
            continue

    if not diffs:
        return None

    return float(np.mean(diffs))


def calibrate_discount_rate(ref_tickers, mode="bluechip"):
    """
    기준 종목 리스트(ref_tickers)를 받아,
    '평균 log(Fair/Price) ≈ 0' 이 되도록 할인율을 조정.
    간단한 grid search로 base ± 3% 구간에서 탐색.
    """
    # 공백 제거 + 대문자 정리
    ref_tickers = [t.strip().upper() for t in ref_tickers if t.strip()]

    if not ref_tickers:
        return None

    base_profile = MODEL_PROFILES.get(mode, MODEL_PROFILES["bluechip"])
    base_d = base_profile["discount_rate"]

    # 탐색 구간: base - 3% ~ base + 3%
    low = max(0.03, base_d - 0.03)
    high = base_d + 0.03

    best_d = base_d
    best_score = None

    # 단순 grid search (31 포인트)
    for d in np.linspace(low, high, 31):
        mean_log_diff = _mean_log_diff_for_discount(ref_tickers, mode, d)
        if mean_log_diff is None:
            continue

        score = abs(mean_log_diff)  # 0에 가까울수록 좋음

        if best_score is None or score < best_score:
            best_score = score
            best_d = float(d)

    return best_d if best_score is not None else None
