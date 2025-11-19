# core/model_profiles.py

MODEL_PROFILES = {
    "conservative": {
        "name": "보수적 가치평가",
        # DCF 파라미터
        "discount_rate": 0.10,
        "g1": 0.06,   # Phase1 성장률
        "g2": 0.03,   # Phase2 성장률
        "terminal": 0.02,
        # 가중치
        "dcf_weight": 0.30,
        "ratio_weight": 0.30,
        "growth_weight": 0.15,
        "profit_weight": 0.15,
        "stability_weight": 0.10,
    },

    "bluechip": {
    "name": "우량주 기준 (빅테크용)",
    # ▶ 할인율을 낮추고, 성장률을 조금 더 높게
    "discount_rate": 0.07,   # 0.085 → 0.07
    "g1": 0.12,              # 10% → 12% (앞 5년)
    "g2": 0.06,              # 5%  → 6%  (그 다음 5년)
    "terminal": 0.035,       # 3%  → 3.5%

    # ▶ DCF 비중도 살짝 줄이고, 성장성/수익성 비중↑
    "dcf_weight": 0.15,      # 0.20 → 0.15
    "ratio_weight": 0.25,
    "growth_weight": 0.30,   # 0.25 → 0.30
    "profit_weight": 0.20,
    "stability_weight": 0.10,
    },


    "hypergrowth": {
        "name": "고성장 모드",
        "discount_rate": 0.075,
        "g1": 0.18,
        "g2": 0.10,
        "terminal": 0.04,
        "dcf_weight": 0.15,       # 성장주는 DCF 신뢰도 떨어지니 비중 낮춤
        "ratio_weight": 0.20,
        "growth_weight": 0.35,
        "profit_weight": 0.20,
        "stability_weight": 0.10,
    },
}
