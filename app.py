import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 한글 폰트: 굴림
matplotlib.rcParams["font.family"] = "Gulim"
matplotlib.rcParams["axes.unicode_minus"] = False

import pandas as pd
import yfinance as yf

from core.fetch_data import fetch_company_data
from core.valuation import fundamental_score
from core.momentum import momentum_score
from core.risk import risk_score
from core.scoring import full_scoring_pipeline


# ---------------------------------------------------------
# Streamlit 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="기업 가치·모멘텀·리스크 종합 평가",
    page_icon="📈",
    layout="wide",
)


st.title("📈 종합 가치평가 시스템 (Fundamental + Momentum + Risk)")
st.write("기업의 가치, 가격 흐름, 리스크를 한 번에 분석하는 시스템입니다.")


# ---------------------------------------------------------
# 티커 입력 UI
# ---------------------------------------------------------
ticker = st.text_input("종목 티커 입력 (예: AAPL, MSFT, TSLA)", value="AAPL")

if st.button("데이터 불러오기 🔍"):
    with st.spinner("데이터 불러오는 중..."):
        data = fetch_company_data(ticker)

    if data is None or data.get("price") is None:
        st.error("데이터를 불러올 수 없습니다.")
        st.stop()

    st.success(f"{ticker} 데이터 로딩 완료!")

    # ---------------------------------------------------------
    # 데이터 기초 정보
    # ---------------------------------------------------------
    st.subheader("📘 기본 정보")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("현재 주가", data.get("current_price"))
        st.metric("PER", data.get("per"))
        st.metric("PBR", data.get("pbr"))

    with col2:
        st.metric("PSR", data.get("psr"))
        st.metric("베타 (Beta)", data.get("beta"))
        st.metric("시가총액", data.get("market_cap"))

    with col3:
        st.metric("총 현금", data.get("total_cash"))
        st.metric("총 부채", data.get("total_debt"))
        st.metric("발행주식수", data.get("shares_outstanding"))

    st.divider()

    # ---------------------------------------------------------
    # Score 계산
    # ---------------------------------------------------------
    f_score, fair_value = fundamental_score(data)
    m_score = momentum_score(data)
    r_score = risk_score(data)
    final_result = full_scoring_pipeline(f_score, m_score, r_score)

    # ---------------------------------------------------------
    # Score 요약
    # ---------------------------------------------------------
    st.header("⭐ 종합 점수 요약")

    colA, colB, colC, colD = st.columns(4)
    colA.metric("기업 가치 (Fundamental)", round(f_score, 2))
    colB.metric("모멘텀 (Momentum)", round(m_score, 2))
    colC.metric("리스크 (Risk)", round(r_score, 2))
    colD.metric("최종 점수", round(final_result["final_score"], 2))

    st.subheader(f"**📌 투자 신호: `{final_result['signal']}`**")

    st.divider()


    # ---------------------------------------------------------
    # 탭 구성 (Fundamental / Momentum / Risk / DCF / 재무제표)
    # ---------------------------------------------------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📊 Fundamental", "📈 Momentum", "⚠ Risk", "💵 DCF 분석", "📑 재무제표"]
    )

    # ---------------------------------------------------------
    # Fundamental 탭
    # ---------------------------------------------------------
    with tab1:
        st.subheader("📊 Fundamental 상세")

        if fair_value is not None:
            st.metric("적정 가치(Fair Value)", round(fair_value, 2))
            if data["current_price"]:
                diff = (fair_value - data["current_price"]) / data["current_price"] * 100
                st.metric("저평가율", f"{diff:.2f} %")

        # 가격 vs 적정가 비교 차트
        if data["current_price"]:
            fig, ax = plt.subplots()
            ax.bar(["현재주가", "적정가"], [data["current_price"], fair_value])
            ax.set_title("현재 주가 vs 적정 가치")
            st.pyplot(fig)

        st.write("---")
        st.write("**기본 정보(info)**")
        st.json(data["info"])


    # ---------------------------------------------------------
    # Momentum 탭
    # ---------------------------------------------------------
    with tab2:
        st.subheader("📈 Momentum 분석")

        price = data["price"]
        st.line_chart(price["Close"], height=300)

        st.write("**최근 가격 데이터**")
        st.dataframe(price.tail(30))


    # ---------------------------------------------------------
    # Risk 탭
    # ---------------------------------------------------------
    with tab3:
        st.subheader("⚠ 리스크 분석")

        price = data["price"]
        returns = price["Close"].pct_change()

        fig, ax = plt.subplots()
        ax.hist(returns.dropna(), bins=50)
        ax.set_title("수익률 분포 (변동성 시각화)")
        st.pyplot(fig)

        st.write("**최근 30일 가격**")
        st.dataframe(price.tail(30))


    # ---------------------------------------------------------
    # DCF 탭
    # ---------------------------------------------------------
    with tab4:
        st.subheader("💵 DCF 상세 분석")

        fcf = data.get("fcf")
        if fcf is not None:
            st.write("**Free Cash Flow (최근 연도 기준)**")
            st.dataframe(pd.DataFrame(fcf, columns=["FCF"]))

        st.info("DCF 민감도 분석(Heatmap)은 추후 확장 기능으로 추가할 수 있습니다.")


    # ---------------------------------------------------------
    # 재무제표 탭
    # ---------------------------------------------------------
    with tab5:
        st.subheader("📑 손익계산서 (Financials)")
        st.dataframe(data["financials"])

        st.subheader("📑 현금흐름표 (Cashflow)")
        st.dataframe(data["cashflow"])

        st.subheader("📑 재무상태표 (Balance Sheet)")
        st.dataframe(data["balance"])
