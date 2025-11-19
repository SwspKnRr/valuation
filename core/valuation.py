import numpy as np
import pandas as pd


# ------------------------------------------------------------
# 0. 유틸 함수
# ------------------------------------------------------------
def safe(value, default=None):
    """None 또는 NaN → default로 변환"""
    if value is None:
        return default
    if isinstance(value, float) and np.isnan(value):
        return default
    return value


def normalize_score(value, min_val, max_val):
    """구간 내에서 0~100 점수로 정규화"""
    if value is None:
        return 0
    value = max(min(value, max_val), min_val)
    return (value - min_val) / (max_val - min_val) * 100


# ------------------------------------------------------------
# 1. 상대가치 점수 (PER, PBR, PSR)
# ------------------------------------------------------------
def valuation_ratio_score(per, pbr, psr):
    """
    PER/PBR/PSR 낮을수록 고득점
    구간:
    PER: 5~40
    PBR: 0.5~6
    PSR: 1~20
    """

    per_score = normalize_score(40 - safe(per, 40), 0, 35)
    pbr_score = normalize_score(6 - safe(pbr, 6), 0, 6)
    psr_score = normalize_score(20 - safe(psr, 20), 0, 19)

    total = (per_score * 0.5) + (pbr_score * 0.3) + (psr_score * 0.2)
    return total  # 0~100 점수 아님 (비중 합산이니까 0~100 근사)


# ------------------------------------------------------------
# 2. EPS, FCF 성장률 점수
# ------------------------------------------------------------
def cagr(start, end, years):
    if start is None or end is None or start <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def growth_score(eps_series: pd.Series, fcf_series: pd.Series):
    """
    EPS 3년/5년 CAGR
    FCF 5년 CAGR
    """

    eps_score = 0
    fcf_score = 0

    # EPS
    if eps_series is not None and len(eps_series.dropna()) >= 2:
        eps_vals = eps_series.dropna().values
        eps_cagr = cagr(eps_vals[-2], eps_vals[-1], 1)
        if eps_cagr is not None:
            eps_score = normalize_score(eps_cagr, -0.1, 0.3)  # -10% ~ 30%

    # FCF
    if fcf_series is not None and len(fcf_series.dropna()) >= 2:
        fcf_vals = fcf_series.dropna().values
        fcf_cagr_value = cagr(fcf_vals[-5], fcf_vals[-1], 5) if len(fcf_vals) >= 5 else None
        if fcf_cagr_value is not None:
            fcf_score = normalize_score(fcf_cagr_value, -0.1, 0.3)

    total = (eps_score * 0.6) + (fcf_score * 0.4)
    return total


# ------------------------------------------------------------
# 3. 수익성 평가 (ROE, 마진)
# ------------------------------------------------------------
def profitability_score(roe, op_margin):
    """
    ROE: 5~30% 구간
    영업이익률: 0~40% 구간
    """

    roe_score = normalize_score(safe(roe, 0), 5, 30)
    opm_score = normalize_score(safe(op_margin, 0), 0, 40)

    total = roe_score * 0.6 + opm_score * 0.4
    return total


# ------------------------------------------------------------
# 4. 안정성 평가 (부채)
# ------------------------------------------------------------
def stability_score(total_debt, total_cash, market_cap):
    """
    Debt-to-Cap 비율로 안정성 평가
    부채 < 시총 * 20% → 매우 안전 (고득점)
    부채 = 시총과 비슷 → 위험 (저득점)
    """

    if market_cap is None or total_debt is None:
        return 30  # 중간 점수

    debt_ratio = total_debt / market_cap
    # 낮을수록 안전 → 점수↑
    score = normalize_score(0.5 - debt_ratio, -0.5, 0.5)
    return score


# ------------------------------------------------------------
# 5. DCF (간소화)
# ------------------------------------------------------------
def dcf_fair_value(fcf_series: pd.Series,
                   shares_outstanding: int,
                   discount_rate=0.10,
                   g1=0.08, years1=5,
                   g2=0.04, years2=5,
                   terminal_growth=0.03,
                   total_debt=0, total_cash=0):
    """
    FCF 기반 간소화 DCF
    Phase 1: 5년 성장 g1
    Phase 2: 5년 성장 g2
    Terminal: 영구 성장률
    """

    if fcf_series is None or len(fcf_series.dropna()) == 0:
        return None

    fcf0 = fcf_series.dropna().iloc[-1]

    # Phase 1
    fcf_phase1 = [(fcf0 * ((1 + g1) ** t)) / ((1 + discount_rate) ** t) for t in range(1, years1 + 1)]

    # Phase 2
    fcf_end_phase1 = fcf0 * ((1 + g1) ** years1)
    fcf_phase2 = [
        (fcf_end_phase1 * ((1 + g2) ** t)) / ((1 + discount_rate) ** (years1 + t))
        for t in range(1, years2 + 1)
    ]

    # Terminal Value
    fcf_terminal_start = fcf_end_phase1 * ((1 + g2) ** years2)
    terminal_value = fcf_terminal_start * (1 + terminal_growth) / (discount_rate - terminal_growth)
    terminal_value_pv = terminal_value / ((1 + discount_rate) ** (years1 + years2))

    # Total value
    enterprise_value = sum(fcf_phase1) + sum(fcf_phase2) + terminal_value_pv

    # Equity value
    equity_value = enterprise_value + safe(total_cash, 0) - safe(total_debt, 0)

    if shares_outstanding is None or shares_outstanding == 0:
        return None

    fair_value = equity_value / shares_outstanding
    return fair_value


# ------------------------------------------------------------
# 6. 최종 Fundamental Score 계산
# ------------------------------------------------------------
def fundamental_score(data: dict):
    """
    fetch_data.py에서 받아온 'data' dict 입력
    → Fundamental Score 0~100 반환
    """

    # 1) 상대가치
    ratio = valuation_ratio_score(data.get("per"),
                                  data.get("pbr"),
                                  data.get("psr"))

    # 2) 성장성
    eps_series = None  # yfinance는 EPS 시계열을 제공하지 않음 → 추후 API 확장 예정
    growth = growth_score(eps_series, data.get("fcf"))

    # 3) 수익성
    # 재무제표에서 ROE 계산 가능하지만 기본값은 info에서 가져오는 것을 추천
    roe = data["info"].get("returnOnEquity", None)
    opm = data["info"].get("operatingMargins", None)
    profit = profitability_score(roe, opm)

    # 4) 안정성
    stability = stability_score(data.get("total_debt"),
                                data.get("total_cash"),
                                data.get("market_cap"))

    # 5) DCF 평가
    fair = dcf_fair_value(
        fcf_series=data.get("fcf"),
        shares_outstanding=data.get("shares_outstanding"),
        discount_rate=0.10
    )

    dcf_score = 0
    if fair is not None and data["current_price"] is not None:
        diff = (fair - data["current_price"]) / data["current_price"]
        dcf_score = normalize_score(diff, -0.5, 0.5)  # -50% ~ +50%

    # ------------------------------------------------------------
    # 가중합
    # ------------------------------------------------------------
    total_score = (
        ratio * 0.25 +
        growth * 0.20 +
        profit * 0.20 +
        stability * 0.10 +
        dcf_score * 0.25
    )

    return min(max(total_score, 0), 100), fair
