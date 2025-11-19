def final_score(fundamental: float, momentum: float, risk: float):
    """
    3개 점수를 받아 최종 0~100 점수 반환
    fundamental, momentum, risk: 0~100
    """

    if fundamental is None:
        fundamental = 50
    if momentum is None:
        momentum = 50
    if risk is None:
        risk = 50

    score = (
        fundamental * 0.45 +
        momentum * 0.35 +
        risk * 0.20
    )

    return min(max(score, 0), 100)


def signal_from_score(score: float):
    """최종 점수 → 매수/매도 신호 문자열"""

    if score >= 80:
        return "강매수"
    elif score >= 65:
        return "매수"
    elif score >= 45:
        return "중립"
    elif score >= 25:
        return "보류"
    else:
        return "매도"


def full_scoring_pipeline(fundamental, momentum, risk):
    """
    전체 파이프라인 실행:
    → 최종 점수 + 신호 반환
    """

    f_score = fundamental if fundamental is not None else 50
    m_score = momentum if momentum is not None else 50
    r_score = risk if risk is not None else 50

    final = final_score(f_score, m_score, r_score)
    signal = signal_from_score(final)

    return {
        "fundamental": f_score,
        "momentum": m_score,
        "risk": r_score,
        "final_score": final,
        "signal": signal
    }
