import yfinance as yf
import pandas as pd


def fetch_company_data(ticker: str):
    """
    티커 하나에 대해:
    - 가격 히스토리 (10년)
    - 재무제표 (재무상태표/손익계산서/현금흐름표)
    - 기본 정보 (베타, 시총, PER/PBR/PSR 등)
    - Free Cash Flow 5년치
    를 자동 수집하여 dict 형태로 반환
    """

    stock = yf.Ticker(ticker)

    # ----------------------------------------
    # 기본 정보
    # ----------------------------------------
    info = stock.info

    current_price = info.get("currentPrice")
    market_cap = info.get("marketCap")
    shares_outstanding = info.get("sharesOutstanding")
    beta = info.get("beta")

    per = info.get("trailingPE")
    pbr = info.get("priceToBook")
    psr = info.get("priceToSalesTrailing12Months")

    total_cash = info.get("totalCash")
    total_debt = info.get("totalDebt")

    # ----------------------------------------
    # 가격 데이터 (10년)
    # ----------------------------------------
    price = stock.history(period="10y")

    # ----------------------------------------
    # 재무제표
    # ----------------------------------------
    financials = stock.financials
    cashflow = stock.cashflow
    balance = stock.balance_sheet

    # ----------------------------------------
    # FCF 계산
    # FCF = Operating Cash Flow - Capital Expenditure
    # ----------------------------------------
    fcf_series = None

    try:
        ocf = cashflow.loc["Total Cash From Operating Activities"]
        capex = cashflow.loc["Capital Expenditures"]
        fcf_series = ocf + capex  # capex는 음수라 +가 맞음
    except:
        fcf_series = None

    return {
        "info": info,
        "price": price,
        "financials": financials,
        "cashflow": cashflow,
        "balance": balance,
        "current_price": current_price,
        "market_cap": market_cap,
        "shares_outstanding": shares_outstanding,
        "beta": beta,
        "per": per,
        "pbr": pbr,
        "psr": psr,
        "total_cash": total_cash,
        "total_debt": total_debt,
        "fcf": fcf_series,
    }
