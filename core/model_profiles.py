MODEL_PROFILES = {
    "conservative": {
        "name": "보수적 가치평가",
        "discount_rate": 0.10,
        "g1": 0.06,
        "g2": 0.03,
        "terminal": 0.02,
        "dcf_weight": 0.30,
        "ratio_weight": 0.30,
        "growth_weight": 0.15,
        "profit_weight": 0.15,
        "stability_weight": 0.10,
    },

    "bluechip": {
        "name": "우량주 기준",
        "discount_rate": 0.085,    # 핵심: 빅테크 프리미엄 인정
        "g1": 0.10,
        "g2": 0.05,
        "terminal": 0.03,
        "dcf_weight": 0.20,
        "ratio_weight": 0.25,
        "growth_weight": 0.25,
        "profit_weight": 0.20,
        "stability_weight": 0.10,
    },

    "hypergrowth": {
        "name": "고성장 모드",
        "discount_rate": 0.075,
        "g1": 0.18,
        "g2": 0.10,
        "terminal": 0.04,
        "dcf_weight": 0.15,        # 성장주에선 DCF 신뢰도 낮음 → 비중 감소
        "ratio_weight": 0.20,
        "growth_weight": 0.35,
        "profit_weight": 0.20,
        "stability_weight": 0.10,
    },
}
