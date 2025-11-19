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
    if isinstance(value, float) and np.isnan(value):
        return 0
    # 클리핑
    value = max(min(value, max_val), min_val)
    return (value - min_val) / (max_val - min_val) * 100


# ------------------------------------------------------------
# 1. 상대가치 점수 (PER, PBR, PSR)
# ------------------------------------------------------------
def valuation_ratio_score(per, pbr, psr):
    """
    PER/PBR/PSR 낮을수록 고득점.
    PER: 5~40
    PBR: 0.5~6
    PSR: 1~20
    """

    # per가 낮을수록 좋으니 (40 - per)를 정규화
    per = safe(per, 40)
    pbr = safe(pbr, 6)
    psr = safe(psr, 20)

    per_score = normalize_score(40 - per, 0, 35)   # 역변환
    pbr_score = normalize_score(6 - pbr, 0, 5.5)
    psr_score = normalize_score(20 - psr, 0, 19)

    total = (per_score * 0.5) + (pbr_score * 0.3) + (psr_score * 0.2)
    return total  # 0~100 근사


# ------------------------------------------------------------
# 2. EPS, FCF 성장률 점수
# ------------------------------------------------------------
def cagr(start, end, years):
    if start is None or end is None:
        return None
    if start <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1


def growth_score(eps_series: pd.Series | None,
                 fcf_series: pd.Series | None):
    """
    EPS 3년/5년 CAGR (지금은 eps_series 없으니 사실상 FCF 위주)
    FCF 5년 CAGR
    """

    eps_score = 0
    fcf_score = 0

    # EPS 쪽은 지금은 API에서 시계열을 못 가져오니 비워두는 형태
    if eps_series is not None:
        eps_clean = eps_series.dropna()
        if len(eps_clean) >= 2:
            eps_vals = eps_clean.values
            eps_cagr_val = cagr(eps_vals[-2], eps_vals[-1], 1)
            if eps_cagr_val is not None:
                eps_score = normalize_score(eps_cagr_val, -0.1, 0.3)  # -10% ~ 30%

    # FCF 성장률
    if fcf_series is not None:
        fcf_clean = fcf_series.dropna()
        if len(fcf_clean) >= 2:
            # 5년치 이상 있으면 5년 CAGR, 아니면 마지막 2개로 근사
            if len(fcf_clean) >= 5:
                fcf_cagr_val = cagr(fcf_clean.iloc[-5], fcf_clean.iloc[-1], 5)
            else:
                fcf_cagr_val = cagr(fcf_clean.iloc[0], fcf_clean.iloc[-1],
                                    len(fcf_clean) - 1)
            if fcf_cagr_val is not None:
                fcf_score = normalize_score(fcf_cagr_val, -0.1, 0.3)

    total = (eps_score * 0.6) + (fcf_score * 0.4)
    return total


# ------------------------------------------------------------
# 3. 수익성 평가 (ROE, 영업이익률)
# ------------------------------------------------------------
def profitability_score(roe, op_margin):
    """
    ROE: 5~30% 구간
    영업이익률: 0~40% 구간
    """
    roe = safe(roe, 0)
    op_margin = safe(op_margin, 0)

    # roe, op_margin이 비율(0.x)로 들어올 수도 있으니 100x 처리
    if abs(roe) < 1:      # 0.32 같은 값
        roe *= 100
    if abs(op_margin) < 1:
        op_margin *= 100

    roe_score = normalize_score(roe, 5, 30)
    opm_score = normalize_score(op_margin, 0, 40)

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

    total_debt = safe(total_debt, None)
    market_cap = safe(market_cap, None)

    if market_cap is None or total_debt is None or market_cap <= 0:
        return 50  # 정보 부족 → 중간 점수

    debt_ratio = total_debt / market_cap  # 높을수록 위험
    # 낮을수록 안전 → (0.5 - ratio)를 정규화
    score = normalize_score(0.5 - debt_ratio, -0.5, 0.5)
    return score


# ------------------------------------------------------------
# 5. DCF (간소화)
# ------------------------------------------------------------
def dcf_fair_value(
    fcf_series: pd.Series,
    shares_outstanding: int,
    discount_rate=0.10,
    g1=0.08,
    years1=5,
    g2=0.04,
    years2=5,
    terminal_growth=0.03,
    total_debt=0,
    total_cash=0,
):
    """
    FCF 기반 간소화 DCF
    Phase 1: years1년 성장 g1
    Phase 2: years2년 성장 g2
    Terminal: 영구 성장률

    fcf_series: 최근 FCF 시계열 (가장 마지막 값이 최신)
    """

    if fcf_series is None:
        return None

    fcf_clean = fcf_series.dropna()
    if len(fcf_clean) == 0:
        return None

    fcf0 = fcf_clean.iloc[-1]

    # Phase 1
    fcf_phase1 = [
        (fcf0 * ((1 + g1) ** t)) / ((1 + discount_rate) ** t)
        for t in range(1, years1 + 1)
    ]

    # Phase 2
    fcf_end_phase1 = fcf0 * ((1 + g1) ** years1)
    fcf_phase2 = [
        (fcf_end_phase1 * ((1 + g2) ** t)) /
        ((1 + discount_rate) ** (years1 + t))
        for t in range(1, years2 + 1)
    ]

    # Terminal Value
    fcf_terminal_start = fcf_end_phase1 * ((1 + g2) ** years2)
    if discount_rate <= terminal_growth:
        # 비정상적인 경우 → Terminal 계산 불가
        return None

    terminal_value = (
        fcf_terminal_start * (1 + terminal_growth)
        / (discount_rate - terminal_growth)
    )
    terminal_value_pv = terminal_value / (
        (1 + discount_rate) ** (years1 + years2)
    )

    # Total enterprise value
    enterprise_value = sum(fcf_phase1) + sum(fcf_phase2) + terminal_value_pv

    # Equity value 조정 (현금 +, 부채 -)
    equity_value = enterprise_value + safe(total_cash, 0) - safe(total_debt, 0)

    if shares_outstanding is None or shares_outstanding <= 0:
        return None

    fair_value = equity_value / shares_outstanding
    return fair_value


# ------------------------------------------------------------
# 6. 최종 Fundamental Score 계산
# ------------------------------------------------------------
def fundamental_score(data: dict):
    """
    fetch_data.py에서 받아온 'data' dict 입력
    → (Fundamental Score 0~100, Fair Value) 반환
    """

    info = data.get("info", {})

    # 1) 상대가치
    ratio = valuation_ratio_score(
        data.get("per"),
        data.get("pbr"),
        data.get("psr"),
    )

    # 2) 성장성 (EPS는 일단 None, FCF 위주)
    eps_series = None  # yfinance로는 EPS 시계열이 없어서 확장용 슬롯만
    fcf_series = data.get("fcf")

    # 🔥 FCF 시계열이 없으면 info["freeCashflow"]를 fallback으로 사용
    if fcf_series is None or (
        hasattr(fcf_series, "dropna")
        and len(fcf_series.dropna()) == 0
    ):
        fcf_last = info.get("freeCashflow")
        if fcf_last is not None:
            # 최근 FCF 하나만이라도 시리즈로 만들어 사용
            fcf_series = pd.Series([fcf_last])

    growth = growth_score(eps_series, fcf_series)

    # 3) 수익성
    roe = info.get("returnOnEquity", None)
    opm = info.get("operatingMargins", None)
    profit = profitability_score(roe, opm)

    # 4) 안정성
    stability = stability_score(
        data.get("total_debt"),
        data.get("total_cash"),
        data.get("market_cap"),
    )

    # 5) DCF 평가
    fair = dcf_fair_value(
        fcf_series=fcf_series,
        shares_outstanding=data.get("shares_outstanding"),
        discount_rate=0.10,  # 기본 10%, 나중에 UI에서 조정 가능
        total_debt=data.get("total_debt"),
        total_cash=data.get("total_cash"),
    )

    dcf_score = 0
    current_price = data.get("current_price")
    if fair is not None and current_price is not None and current_price > 0:
        diff = (fair - current_price) / current_price  # +면 저평가
        # -50% 고평가 ~ +50% 저평가 구간에서 스코어링
        dcf_score = normalize_score(diff, -0.5, 0.5)

    # ------------------------------------------------------------
    # 가중합 → Fundamental Score
    # ------------------------------------------------------------
    total_score = (
        ratio * 0.25 +
        growth * 0.20 +
        profit * 0.20 +
        stability * 0.10 +
        dcf_score * 0.25
    )

    total_score = min(max(total_score, 0), 100)
    return total_score, fair
