import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# 1. 웹 페이지 기본 설정 및 모바일 맞춤형 CSS 주입
st.set_page_config(page_title="Corporate Financial Analysis Tool", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stMarkdownContainer"] {
        font-size: 15px !important;
    }
    .lang-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }
    @media (max-width: 768px) {
        .stDataFrame div {
            font-size: 12px !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.1rem !important; }
        .stButton button {
            padding: 0.25rem 0.5rem !important;
            font-size: 13px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# 2. 다국어 세션 상태 초기화 및 딕셔너리 정의
if "lang" not in st.session_state:
    st.session_state.lang = "ko"  # 기본값: 한국어

MESSAGES = {
    "ko": {
        "title": "📊 기업 재무 분석 도구",
        "subtitle": "고급 재무 진단 시스템 - 포괄적인 기술적 및 기본적 구조 매핑",
        "search_method": "검색 방법 선택:",
        "by_ticker": "티커(Ticker)로 검색",
        "by_name": "회사명으로 검색",
        "enter_ticker": "미국 주식 티커 입력:",
        "enter_name": "회사명 입력 (예: Apple, Tesla, Oracle):",
        "select_company": "정확한 회사 선택:",
        "search_error": "⚠️ 검색 한계량 도달 혹은 네트워크 지연이 발생했습니다. 티커 검색 방식을 이용하시면 막힘없이 사용 가능합니다.",
        "fetch_error": "⚠️ 종목의 데이터를 가져오지 못했습니다. 올바른 US 티커 명칭인지 확인하시거나 잠시 후 다시 검색해 주세요.",
        "insufficient_data": "📊 재무 데이터의 열 개수가 비교 분석하기에 충분하지 않습니다.",
        "tab_report": "📝 종합의견 (Report)",
        "tab_overview": "📌 개요 (Overview)",
        "tab_ichimoku": "📐 일목균형표 (Ichimoku)",
        "tab_bs": "🏢 재무상태표 (Balance Sheet)",
        "tab_ratios": "📊 주요 비율 (Ratios)",
        "tab_valuation": "📉 가치평가 (Valuation)",
        "tab_news": "📰 뉴스 (News)",
        "report_title": "📝 실시간 재무·주가 종합 진단 보고서",
        "target_comp": "대상 기업",
        "section1": "🔍 1. 최근 주가 수준 및 기술적·밸류에이션 평가",
        "section2": "📊 2. 핵심 재무 상태 스코어링",
        "section3": "💡 3. 최종 투자 전략 가이드라인 (CVP 융합)",
        "curr_price": "현재 주가",
        "range_52": "52주 주가 변동 범위",
        "at_location": "현재 변동폭의",
        "location_end": "지점 위치",
        "avg_50": "단기 균형 가격 (50일 평균)",
        "multiple_analysis": "멀티플 분석: 현재 PER 지표는",
        "ichimoku_analysis": "##### 📐 일목균형표(Ichimoku) 추세 모멘텀 분석",
        "growth_score": "성장성 점수 (매출액 변동)",
        "profit_score": "수익성 점수 (당기순이익 변동)",
        "stability_score": "부채 안정성 (부채비율)",
        "liquidity_score": "유동성 리스크 (유동비율)",
        "total_score_text": "종합 재무 건전성 평점",
        "excellent": "✅ 우수",
        "stagnant": "❌ 정체",
        "safe": "✅ 안전",
        "high_debt": "🚨 부채 과다",
        "caution_cash": "🚨 현금 주의",
        "report_good": "💎 **재무 종합 의견:** 펀더멘탈이 대단히 우량한 기업입니다. 주가 조정 발생 시 분할 매수 접근 전략이 유효합니다.",
        "report_neutral": "⚠️ **재무 종합 의견:** 성장성 혹은 안정성 중 특정 지표의 둔화가 관찰됩니다. 마진율 변동 추이를 추적 관찰해야 합니다.",
        "report_bad": "🚨 **재무 종합 의견:** 전반적인 재무 지표 역성장 및 유동성 리스크가 우려됩니다. 보수적인 투자 관점이 필요합니다.",
        "guideline_1": "1. **비용 구조 개방:** 본 기업의 현재 분기 추정 손익분기점(BEP) 매출액은 **${bep_sales:,.0f}**입니다. 현재 매출이 손익분기점을 안전하게 상회하고 있으므로 고정비 레버리지 효과에 따른 수익성 확대 국면입니다.",
        "guideline_2": "2. **운전 자본 효율성:** 현금전환주기(CCC)가 **{ccc:.1f}일**로 측정되어 자금 회수 속도가 원활한 편입니다. 공급망 리스크에 따른 재고자산 누적 여부를 체크하시기 바랍니다.",
        "guideline_3": "3. **최종 결론:** 본 재무분석 시스템의 추정치인 주당 가치 스케일링을 기준으로 볼 때, 현재 주가는 재무 기초체력 대비 합리적인 흐름을 보이고 있으나, 단기 변동성을 감안하여 실시간 뉴스 탭에 올라오는 글로벌 이슈들을 병행 모니터링하시기 바랍니다.",
        "disclaimer": "⚠️ **Investment Disclaimer** ※ 본 자료 및 검토의견은 재무제표와 관련 자료를 기초로 작성된 참고용 정보이며, 투자 권유 또는 투자 수익을 보장하는 내용이 아닙니다.",
        "status_high": "🔴 **52주 최고점 근접 구역 (과열 경계):** 현재 주가는 52주 가격 밴드 최상단에 위치하고 있습니다.",
        "status_low": "🟢 **52주 최저점 근접 구역 (바닥권 메리트):** 현재 주가는 52주 가격 밴드 하단에 있어 가격 부담이 적습니다.",
        "status_mid": "🟡 **중간 밴드 구역 (균형 가격):** 현재 주가는 52주 중간 이동평균선 부근에서 안정적인 흐름을 유지 중입니다.",
        "ichimoku_title": "일목 기술적 분석",
        "tenkan": "전환선 (단기 추세선)",
        "kijun": "기준선 (중기 균형선)",
        "signal": "일목 종합 판단 시그널",
        "detail_feedback": "🔍 실시간 차트 세부 진단 피드백",
        "chart_trend": "📈 핵심 지표 시각화 트렌드 (최근 60거래일 동향)",
        "no_news": "ℹ️ 현재 제공된 실시간 뉴스가 없습니다.",
        "latest_news": "최신 뉴스"
    },
    "en": {
        "title": "📊 Corporate Financial Analysis Tool",
        "subtitle": "Advanced Financial Diagnostics System - Comprehensive Technical & Fundamental Structural Mapping",
        "search_method": "Select Search Method:",
        "by_ticker": "By Ticker",
        "by_name": "By Company Name",
        "enter_ticker": "Enter US Stock Ticker:",
        "enter_name": "Enter Company Name (e.g., Apple, Tesla, Oracle):",
        "select_company": "Select exact company:",
        "search_error": "⚠️ Search limit reached or network delay. Using 'By Ticker' method works without interruption.",
        "fetch_error": "⚠️ Failed to fetch data. Please check if the US ticker is correct or try again later.",
        "insufficient_data": "📊 Insufficient financial data columns for comparative analysis.",
        "tab_report": "📝 Report",
        "tab_overview": "📌 Overview",
        "tab_ichimoku": "📐 Ichimoku Indicator",
        "tab_bs": "🏢 Balance Sheet",
        "tab_ratios": "📊 Ratios",
        "tab_valuation": "📉 Valuation",
        "tab_news": "📰 News",
        "report_title": "📝 Financial & Stock Comprehensive Diagnostic Report",
        "target_comp": "Target Company",
        "section1": "🔍 1. Recent Stock Price Level & Valuation Evaluation",
        "section2": "📊 2. Core Financial Status Scoring",
        "section3": "💡 3. Final Investment Strategy Guideline (CVP Fusion)",
        "curr_price": "Current Price",
        "range_52": "52-Week Price Range",
        "at_location": "Currently at",
        "location_end": "of the variation range",
        "avg_50": "Short-term Equilibrium Price (50-Day Avg)",
        "multiple_analysis": "Multiple Analysis: Current PER is",
        "ichimoku_analysis": "##### 📐 Ichimoku Cloud Trend Momentum Analysis",
        "growth_score": "Growth Score (Revenue Change)",
        "profit_score": "Profitability Score (Net Income Change)",
        "stability_score": "Debt Stability (Debt to Equity)",
        "liquidity_score": "Liquidity Risk (Current Ratio)",
        "total_score_text": "Comprehensive Financial Health Rating",
        "excellent": "✅ Excellent",
        "stagnant": "❌ Stagnant",
        "safe": "✅ Safe",
        "high_debt": "🚨 High Debt",
        "caution_cash": "🚨 Liquidity Caution",
        "report_good": "💎 **Financial Summary:** Fundamentals are exceptionally strong. A dollar-cost averaging strategy during stock corrections is recommended.",
        "report_neutral": "⚠️ **Financial Summary:** Slowdown observed in specific growth or stability metrics. Margins should be tracked closely.",
        "report_bad": "🚨 **Financial Summary:** Risks regarding negative growth and liquidity. A conservative investment approach is advised.",
        "guideline_1": "1. **Cost Structure Insight:** The estimated Break-Even Point (BEP) revenue for the current quarter is **${bep_sales:,.0f}**. Since current revenue safely exceeds BEP, the company is in a profitability expansion phase due to fixed-cost leverage.",
        "guideline_2": "2. **Working Capital Efficiency:** The Cash Conversion Cycle (CCC) is **{ccc:.1f} Days**, indicating smooth cash recovery. Check for inventory accumulation risks from supply chain issues.",
        "guideline_3": "3. **Final Conclusion:** Based on the value-per-share scaling estimates, the current price is reasonable relative to financial strength. However, consider short-term volatility and monitor global issues in the News tab.",
        "disclaimer": "⚠️ **Investment Disclaimer** * This analysis is for informational purposes based on financial statements and does not guarantee investment returns or constitute advice.",
        "status_high": "🔴 **Near 52-Week High (Overheated Zone):** The stock price is currently at the top of its 52-week band.",
        "status_low": "🟢 **Near 52-Week Low (Bargain Zone):** The price is at the bottom of the band, presenting lower downside risk.",
        "status_mid": "🟡 **Mid-Band Zone (Equilibrium Price):** The price is stable near its 50-day moving average.",
        "ichimoku_title": "Ichimoku Technical Analysis",
        "tenkan": "Tenkan-Sen (Short-term)",
        "kijun": "Kijun-Sen (Medium-term)",
        "signal": "Ichimoku Signal Status",
        "detail_feedback": "🔍 Real-time Chart Detailed Diagnostic Feedback",
        "chart_trend": "📈 Key Metrics Visualization Trend (Last 60 Trading Days)",
        "no_news": "ℹ️ No real-time news articles available currently.",
        "latest_news": "Latest News"
    }
}

# 3. 타이틀 및 다국어 버튼 레이아웃 구성
title_col, lang_col = st.columns([3, 1])
with title_col:
    st.title(MESSAGES[st.session_state.lang]["title"])
    st.caption(MESSAGES[st.session_state.lang]["subtitle"])

with lang_col:
    st.write("<div class='lang-container'>", unsafe_allow_html=True)
    btn_ko, btn_en = st.columns(2)
    with btn_ko:
        if st.button("한글", use_container_width=True):
            st.session_state.lang = "ko"
            st.rerun()
    with btn_en:
        if st.button("English", use_container_width=True):
            st.session_state.lang = "en"
            st.rerun()
    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

# 언어 단축 바인딩
L = MESSAGES[st.session_state.lang]

# 안심 세션 공급 함수
def get_highly_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7',
        'Connection': 'keep-alive'
    })
    return session

# 주소 창구 및 검색창 레이아웃
search_col1, search_col2 = st.columns([1, 2])
ticker_final = "AAPL" # 기본 설정

with search_col1:
    search_type = st.radio(L["search_method"], [L["by_ticker"], L["by_name"]], index=0, horizontal=True)

with search_col2:
    if search_type == L["by_ticker"]:
        ticker_input = st.text_input(L["enter_ticker"], "AAPL", key="ticker_input_field", label_visibility="collapsed").upper().strip()
        ticker_final = ticker_input if ticker_input else "AAPL"
    else:
        company_input = st.text_input(L["enter_name"], "Oracle", key="company_input_field", label_visibility="collapsed").strip()
        if company_input:
            try:
                custom_session = get_highly_secure_session()
                search_results = yf.Search(company_input, max_results=5, session=custom_session).quotes
                us_quotes = [q for q in search_results if q.get('exchange') in ['NMS', 'NYQ', 'ASE', 'BTS', 'NGM', 'NCM']]
                target_quotes = us_quotes if us_quotes else search_results
                
                if target_quotes:
                    options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))}": q['symbol'] for q in target_quotes}
                    selected_display = st.selectbox(L["select_company"], list(options.keys()), label_visibility="collapsed")
                    # [🚨 버그 수정 핵심 지점] 선택된 회사 고유 딕셔너리에서 티커를 동적으로 전달받아 최종 확정합니다.
                    ticker_final = options[selected_display]
                else:
                    st.error("❌ No companies found.")
            except Exception as e:
                st.error(L["search_error"])

st.markdown("---")

def fetch_google_news_rss(ticker_symbol, lang_mode):
    news_items = []
    try:
        hl_gl = "hl=ko&gl=KR&ceid=KR:ko" if lang_mode == "ko" else "hl=en-US&gl=US&ceid=US:en"
        url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock&{hl_gl}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:12]:
                title = item.find('title').text if item.find('title') is not None else "No Title Available"
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                source = item.find('source').text if item.find('source') is not None else "Google News"
                if " - " in title:
                    parts = title.split(" - ")
                    source = parts[-1]
                    title = " - ".join(parts[:-1])
                news_items.append({"title": title, "link": link, "publisher": source, "date_str": pub_date})
    except:
        pass
    return news_items

@st.cache_data(ttl=120)
def fetch_raw_financial_data(ticker_symbol):
    try:
        session = get_highly_secure_session()
        stock = yf.Ticker(ticker_symbol, session=session)
        
        bs = stock.balance_sheet
        fi = stock.financials
        
        if bs is None or bs.empty or fi is None or fi.empty:
            bs = stock.quarterly_balance_sheet
            fi = stock.quarterly_financials
            
        if bs is None or bs.empty or fi is None or fi.empty:
            return None
            
        info = stock.info
        market_metrics = {
            'trailingEps': info.get('trailingEps', 0.0),
            'forwardEps': info.get('forwardEps', 0.0),
            'bookValue': info.get('bookValue', 0.0),
            'sharesOutstanding': info.get('sharesOutstanding', 1.0),
            'trailingPE': info.get('trailingPE', 0.0),
            'priceToBook': info.get('priceToBook', 0.0),
            'currentPrice': info.get('currentPrice', 0.0),
            'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', 0.0),
            'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', 0.0),
            'fiftyDayAverage': info.get('fiftyDayAverage', 0.0),
            'longName': info.get('longName', ticker_symbol)
        }
        
        hist_df = stock.history(period="1y")
        if market_metrics['currentPrice'] == 0.0 and not hist_df.empty:
            market_metrics['currentPrice'] = float(hist_df['Close'].iloc[-1])
                
        bs_df = pd.DataFrame(bs.values, index=bs.index.astype(str), columns=bs.columns.astype(str))
        fi_df = pd.DataFrame(fi.values, index=fi.index.astype(str), columns=fi.columns.astype(str))
        
        return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics, "history": hist_df}
    except:
        return None

# 최종 도출된 티커 데이터 조회 호출
data_bundle = fetch_raw_financial_data(ticker_final)
stock_news = fetch_google_news_rss(ticker_final, st.session_state.lang)

if not data_bundle:
    st.error(L["fetch_error"])
else:
    balance_sheet = data_bundle["balance_sheet"]
    financials = data_bundle["financials"]
    market_metrics = data_bundle["metrics"]
    hist_df = data_bundle["history"]
    comp_name = market_metrics["longName"]

    st.subheader(f"📈 {comp_name} ({ticker_final})")

    if balance_sheet.shape[1] >= 2 and financials.shape[1] >= 2:
        current_year = balance_sheet.columns[0][:7] if len(balance_sheet.columns[0]) > 4 else balance_sheet.columns[0]
        prior_year = balance_sheet.columns[1][:7] if len(balance_sheet.columns[1]) > 4 else balance_sheet.columns[1]
        
        def get_row_values_robust(df, keys_list):
            idx_clean = {str(k).strip().lower(): k for k in df.index}
            for key in keys_list:
                key_lower = str(key).strip().lower()
                if key_lower in idx_clean:
                    vals = df.loc[idx_clean[key_lower]].values
                    v1 = float(vals[0]) if not np.isnan(vals[0]) else 0.0
                    v2 = float(vals[1]) if not np.isnan(vals[1]) else 0.0
                    return v1, v2
            return 0.0, 0.0

        def calc_growth_raw(current, prior):
            if prior and prior != 0:
                return f"{((current - prior) / prior) * 100:.1f}%"
            return "N/A"

        sales_cur, sales_pri = get_row_values_robust(financials, ['Total Revenue', 'Revenue', 'Operating Revenue'])
        cogs_cur, cogs_pri = get_row_values_robust(financials, ['Cost Of Revenue', 'Cost of Goods Sold'])
        gp_cur, gp_pri = get_row_values_robust(financials, ['Gross Profit'])
        if gp_cur == 0 and sales_cur != 0: 
            gp_cur, gp_pri = sales_cur - cogs_cur, sales_pri - cogs_pri
            
        sga_cur, sga_pri = get_row_values_robust(financials, ['Selling General And Administrative', 'Selling General Administrative', 'Selling General & Administrative Expenses'])
        op_cur, op_pri = get_row_values_robust(financials, ['Operating Income', 'Operating Income Status', 'EBIT'])
        ebitda_cur, ebitda_pri = get_row_values_robust(financials, ['Normalized EBITDA', 'EBITDA'])
        net_cur, net_pri = get_row_values_robust(financials, ['Net Income', 'Net Income Common Stockholders'])
        
        cash_cur, cash_pri = get_row_values_robust(balance_sheet, ['Cash And Cash Equivalents', 'Cash', 'Cash Cash Equivalents And Short Term Investments'])
        inv_cur, inv_pri = get_row_values_robust(balance_sheet, ['Inventory', 'Inventories', 'Total Inventories'])
        ar_cur, ar_pri = get_row_values_robust(balance_sheet, ['Receivables', 'Accounts Receivable', 'Net Receivables'])
        ap_cur, ap_pri = get_row_values_robust(balance_sheet, ['Payables And Accrued Expenses', 'Accounts Payable', 'Total Payables'])
        
        ca_cur, ca_pri = get_row_values_robust(balance_sheet, ['Current Assets', 'Total Current Assets'])
        ppe_cur, ppe_pri = get_row_values_robust(balance_sheet, ['Properties', 'Net PPE', 'Property Plant And Equipment', 'Net Property Plant Equipment'])
        ta_cur, ta_pri = get_row_values_robust(balance_sheet, ['Total Assets', 'Assets'])
        cl_cur, cl_pri = get_row_values_robust(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
        tl_cur, tl_pri = get_row_values_robust(balance_sheet, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
        re_cur, re_pri = get_row_values_robust(balance_sheet, ['Retained Earnings'])
        te_cur, te_pri = get_row_values_robust(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity', '🧬 TOTAL EQUITY'])

        sales_growth_val = ((sales_cur - sales_pri) / sales_pri * 100) if sales_pri != 0 else 0.0
        net_growth_val = ((net_cur - net_pri) / net_pri * 100) if net_pri != 0 else 0.0
        debt_to_equity_cur = (tl_cur / te_cur * 100) if te_cur != 0 else 0.0
        debt_to_equity_pri = (tl_pri / te_pri * 100) if te_pri != 0 else 0.0
        current_ratio_cur = (ca_cur / cl_cur) if cl_cur != 0 else 0.0
        current_ratio_pri = (ca_pri / cl_pri) if cl_pri != 0 else 0.0
        quick_ratio_cur = ((ca_cur - inv_cur) / cl_cur) if cl_cur != 0 else 0.0
        quick_ratio_pri = ((ca_pri - inv_pri) / cl_pri) if cl_pri != 0 else 0.0
        
        inv_turnover_cur = (cogs_cur / inv_cur) if inv_cur != 0 else 0.0
        inv_turnover_pri = (cogs_pri / inv_pri) if inv_pri != 0 else 0.0
        ar_turnover_cur = (sales_cur / ar_cur) if ar_cur != 0 else 0.0
        ar_turnover_pri = (sales_pri / ar_pri) if ar_pri != 0 else 0.0
        
        days_inv_cur = 365 / inv_turnover_cur if inv_turnover_cur != 0 else 0.0
        days_ar_cur = 365 / ar_turnover_cur if ar_turnover_cur != 0 else 0.0
        days_ap_cur = 365 / ((cogs_cur / ap_cur) if ap_cur != 0 else 1.0)
        ccc_cur = (days_inv_cur + days_ar_cur) - days_ap_cur
        
        days_inv_pri = 365 / inv_turnover_pri if inv_turnover_pri != 0 else 0.0
        days_ar_pri = 365 / ar_turnover_pri if ar_turnover_pri != 0 else 0.0
        days_ap_pri = 365 / ((cogs_pri / ap_pri) if ap_pri != 0 else 1.0)
        ccc_pri = (days_inv_pri + days_ar_pri) - days_ap_pri

        fixed_cost_cur = max((sales_cur - gp_cur) - op_cur, sales_cur * 0.2)
        fixed_cost_pri = max((sales_pri - gp_pri) - op_pri, sales_pri * 0.2)
        cm_cur = sales_cur - cogs_cur
        cm_pri = sales_pri - cogs_pri
        cm_rate_cur = (cm_cur / sales_cur) if sales_cur != 0 else 0.0
        cm_rate_pri = (cm_pri / sales_pri) if sales_pri != 0 else 0.0
        bep_sales_cur = (fixed_cost_cur / cm_rate_cur) if cm_rate_cur != 0 else 0.0
        bep_sales_pri = (fixed_cost_pri / cm_rate_pri) if cm_rate_pri != 0 else 0.0

        shares_out = market_metrics.get('sharesOutstanding', 1.0)
        eps_cur = market_metrics.get('trailingEps', 0.0) or (net_cur / shares_out)
        eps_pri = net_pri / shares_out if shares_out else 0.0
        bps_cur = market_metrics.get('bookValue', 0.0) or (te_cur / shares_out)
        cur_price = market_metrics.get('currentPrice', 0.0)
        per_cur = market_metrics.get('trailingPE', 0.0) or (cur_price / eps_cur if eps_cur != 0 else 0.0)
        pbr_cur = market_metrics.get('priceToBook', 0.0) or (cur_price / bps_cur if bps_cur != 0 else 0.0)

        # 일목균형표 계산 및 다국어 텍스트 매핑
        ichimoku_ready = False
        ichimoku_text = "📊 Data is insufficient to generate Ichimoku analysis." if st.session_state.lang == "en" else "📊 데이터 축적량이 부족하여 기술적 지표 진단을 생성할 수 없습니다."
        signal_badge = "🔄 Processing" if st.session_state.lang == "en" else "🔄 분석중"
        
        if not hist_df.empty and len(hist_df) >= 52:
            low_9 = hist_df['Low'].rolling(window=9).min()
            high_9 = hist_df['High'].rolling(window=9).max()
            hist_df['Tenkan_Sen'] = (low_9 + high_9) / 2
            low_26 = hist_df['Low'].rolling(window=26).min()
            high_26 = hist_df['High'].rolling(window=26).max()
            hist_df['Kijun_Sen'] = (low_26 + high_26) / 2
            hist_df['Senkou_Span_A'] = ((hist_df['Tenkan_Sen'] + hist_df['Kijun_Sen']) / 2).shift(26)
            low_52 = hist_df['Low'].rolling(window=52).min()
            high_52_ichimoku = hist_df['High'].rolling(window=52).max()
            hist_df['Senkou_Span_B'] = ((low_52 + high_52_ichimoku) / 2).shift(26)

            t_curr = hist_df['Tenkan_Sen'].iloc[-1]
            k_curr = hist_df['Kijun_Sen'].iloc[-1]
            sa_curr = hist_df['Senkou_Span_A'].dropna().iloc[-1] if not hist_df['Senkou_Span_A'].dropna().empty else 0.0
            sb_curr = hist_df['Senkou_Span_B'].dropna().iloc[-1] if not hist_df['Senkou_Span_B'].dropna().empty else 0.0
            lagging_price = hist_df['Close'].iloc[-26] if len(hist_df) >= 26 else cur_price

            if sa_curr != 0.0 and sb_curr != 0.0:
                ichimoku_ready = True
                
                if st.session_state.lang == "ko":
                    if cur_price > max(sa_curr, sb_curr):
                        cloud_status, position_status = f"구름대 상단(${max(sa_curr, sb_curr):,.2f}) 위", "확고한 정배열형 상승 추세"
                    elif cur_price < min(sa_curr, sb_curr):
                        cloud_status, position_status = f"구름대 하단(${min(sa_curr, sb_curr):,.2f}) 아래", "매물대 저항 압박에 직면한 하락 위험"
                    else:
                        cloud_status, position_status = f"구름대 가두리권 범위(${min(sa_curr, sb_curr):,.2f} ~ ${max(sa_curr, sb_curr):,.2f}) 내부", "단기 방향성 탐색을 위한 횡보 조정"
                    
                    cross_status = f"🔼 **호전 지속:** 전환선(${t_curr:,.2f})이 기준선(${k_curr:,.2f}) 위에 위치하여 매수세가 우세합니다." if t_curr > k_curr else (f"🔽 **역전 발생:** 전환선(${t_curr:,.2f})이 기준선(${k_curr:,.2f})을 하회하여 가격 조정 중입니다." if t_curr < k_curr else f"🔀 **수렴:** 전환선과 기준선이 ${t_curr:,.2f} 부근에서 결집 중입니다.")
                    lagging_status = f"🟢 **후행스팬 우위:** 현재 주가가 26거래일 전 주가(${lagging_price:,.2f})보다 높아 모멘텀이 좋습니다." if cur_price > lagging_price else f"🚨 **후행스팬 부담:** 현재 주가가 26거래일 전 주가(${lagging_price:,.2f}) 아래에 갇혀 매물 소화가 필요합니다."
                else:
                    if cur_price > max(sa_curr, sb_curr):
                        cloud_status, position_status = f"Above Cloud Top (${max(sa_curr, sb_curr):,.2f})", "Strong Bullish Uptrend"
                    elif cur_price < min(sa_curr, sb_curr):
                        cloud_status, position_status = f"Below Cloud Bottom (${min(sa_curr, sb_curr):,.2f})", "Bearish Risk with Heavy Resistance"
                    else:
                        cloud_status, position_status = f"Inside Cloud Bounds (${min(sa_curr, sb_curr):,.2f} ~ ${max(sa_curr, sb_curr):,.2f})", "Neutral Consolidation Phase"
                    
                    cross_status = f"🔼 **Bullish Cross:** Tenkan (${t_curr:,.2f}) is above Kijun (${k_curr:,.2f}), buying momentum dominates." if t_curr > k_curr else (f"🔽 **Bearish Cross:** Tenkan (${t_curr:,.2f}) broke below Kijun (${k_curr:,.2f}), undergoing correction." if t_curr < k_curr else f"🔀 **Convergence:** Lines are merging around ${t_curr:,.2f}.")
                    lagging_status = f"🟢 **Chikou Advantage:** Price is higher than 26 periods ago (${lagging_price:,.2f}), showing strong momentum." if cur_price > lagging_price else f"🚨 **Chikou Lagging:** Price is below 26 periods ago (${lagging_price:,.2f}), facing overhead supply."

                score = 0
                if cur_price > max(sa_curr, sb_curr): score += 2
                elif cur_price >= min(sa_curr, sb_curr): score += 1
                if t_curr > k_curr: score += 1
                if cur_price > lagging_price: score += 1

                if score >= 3:
                    signal_badge = "🟢 Bullish Trend" if st.session_state.lang == "en" else "🟢 매수 우위"
                elif score == 2:
                    signal_badge = "🟡 Neutral Box" if st.session_state.lang == "en" else "🟡 관망/중립"
                else:
                    signal_badge = "🚨 Bearish Shock" if st.session_state.lang == "en" else "🚨 리스크 관리"

                if st.session_state.lang == "ko":
                    ichimoku_text = f"""
                    * **구름대 위치 진단:** 현재 주가는 {cloud_status}에 위치하고 있으며, 현재 구간은 **{position_status}** 국면으로 해석됩니다.
                    * **추세 교차 시그널:** {cross_status}
                    * **매물대 지지선 파악:** 선행스팬A는 `${sa_curr:,.2f}`, 선행스팬B는 `${sb_curr:,.2f}`에 형성되어 있습니다.
                    * **후행 시그널 검증:** {lagging_status}
                    """
                else:
                    ichimoku_text = f"""
                    * **Cloud Position Diagnostic:** Stock price is {cloud_status}, indicating a **{position_status}** state.
                    * **Trend Cross Signal:** {cross_status}
                    * **Support/Resistance Bounds:** Senkou Span A is `${sa_curr:,.2f}`, Senkou Span B is `${sb_curr:,.2f}`.
                    * **Chikou Line Validation:** {lagging_status}
                    """

        # ---------------- [ 📐 탭 레이아웃 렌더링 ] ----------------
        tab_report, tab_overview, tab_ichimoku, tab_bs, tab_ratios, tab_valuation, tab_news = st.tabs([
            L["tab_report"], L["tab_overview"], L["tab_ichimoku"], L["tab_bs"], L["tab_ratios"], L["tab_valuation"], L["tab_news"]
        ])
        
        with tab_report:
            st.header(L["report_title"])
            st.caption(f"{L['target_comp']}: {comp_name} ({ticker_final})")
            st.markdown("---")
            
            high_52 = market_metrics.get('fiftyTwoWeekHigh', 1.0)
            low_52 = market_metrics.get('fiftyTwoWeekLow', 1.0)
            avg_50 = market_metrics.get('fiftyDayAverage', 1.0)
            price_location_pct = ((cur_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) != 0 else 50.0
                
            report_col1, report_col2 = st.columns(2)
            with report_col1:
                st.subheader(L["section1"])
                st.metric(label=L["curr_price"], value=f"${cur_price:,.2f}")
                
                status_text = L["status_high"] if price_location_pct >= 80 else (L["status_low"] if price_location_pct <= 30 else L["status_mid"])
                
                st.markdown(f"""
                * **{L['range_52']}:** ${low_52:,.2f} ~ ${high_52:,.2f} ({L['at_location']} **{price_location_pct:.1f}%** {L['location_end']})
                * **{L['avg_50']}:** ${avg_50:,.2f}
                * {status_text}
                * **{L['multiple_analysis']} **{per_cur:.1f}x**, PBR은 **{pbr_cur:.1f}x**입니다.**
                """)
                st.markdown(L["ichimoku_analysis"])
                st.info(ichimoku_text)
                
            with report_col2:
                st.subheader(L["section2"])
                growth_score = 1 if sales_growth_val > 0 else 0
                profit_score = 1 if net_growth_val > 0 else 0
                stability_score = 1 if debt_to_equity_cur <= 120 else 0
                liquidity_score = 1 if current_ratio_cur >= 1.2 else 0
                total_score = growth_score + profit_score + stability_score + liquidity_score
                
                st.markdown(f"""
                * **{L['growth_score']}:** { L['excellent'] if growth_score else L['stagnant'] } ({sales_growth_val:+.1f}%)
                * **{L['profit_score']}:** { L['excellent'] if profit_score else L['stagnant'] } ({net_growth_val:+.1f}%)
                * **{L['stability_score']}:** { L['safe'] if stability_score else L['high_debt'] } ({debt_to_equity_cur:.1f}%)
                * **{L['liquidity_score']}:** { L['safe'] if liquidity_score else L['caution_cash'] } ({current_ratio_cur:.2f})
                * **{L['total_score_text']}:** `{total_score} / 4`
                """)
                
                if total_score >= 3: st.success(L["report_good"])
                elif total_score == 2: st.warning(L["report_neutral"])
                else: st.error(L["report_bad"])

            st.markdown("---")
            st.subheader(L["section3"])
            st.info(f"""
            {L['guideline_1'].format(bep_sales=bep_sales_cur)}
            {L['guideline_2'].format(ccc=ccc_cur)}
            {L['guideline_3']}
            """)
            st.markdown("---")
            st.caption(L["disclaimer"])

        with tab_overview:
            st.subheader("Earnings & Comprehensive Income")
            earnings_data = {
                "Item": ["Sales", "COGS", "Gross Profit", "SG&A", "Operating Inc.", "EBITDA", "Net Income"],
                f"Cur ({current_year})": [f"{sales_cur:,.0f}", f"{cogs_cur:,.0f}", f"{gp_cur:,.0f}", f"{sga_cur:,.0f}", f"{op_cur:,.0f}", f"{ebitda_cur:,.0f}", f"{net_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{sales_pri:,.0f}", f"{cogs_pri:,.0f}", f"{gp_pri:,.0f}", f"{sga_pri:,.0f}", f"{op_pri:,.0f}", f"{ebitda_pri:,.0f}", f"{net_pri:,.0f}"],
                "Growth": [calc_growth_raw(sales_cur, sales_pri), calc_growth_raw(cogs_cur, cogs_pri), calc_growth_raw(gp_cur, gp_pri), calc_growth_raw(sga_cur, sga_pri), calc_growth_raw(op_cur, op_pri), calc_growth_raw(ebitda_cur, ebitda_pri), calc_growth_raw(net_cur, net_pri)]
            }
            st.dataframe(pd.DataFrame(earnings_data), use_container_width=True, hide_index=True)
            st.bar_chart(pd.DataFrame({'Current': [sales_cur, op_cur, net_cur], 'Prior': [sales_pri, op_pri, net_pri]}, index=['Sales', 'Operating', 'Net Income']))

        with tab_ichimoku:
            st.subheader(f"📐 {ticker_final} {L['ichimoku_title']}")
            if ichimoku_ready:
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1: st.metric(L["curr_price"], f"${cur_price:,.2f}")
                with m_col2: st.metric(L["tenkan"], f"${t_curr:,.2f}", f"{t_curr - k_curr:+.2f}")
                with m_col3: st.metric(L["kijun"], f"${k_curr:,.2f}")
                with m_col4: st.metric(L["signal"], signal_badge)
                st.markdown("---")
                
                st.markdown(f"#### {L['detail_feedback']}")
                if "위" in signal_badge or "Bullish" in signal_badge:
                    st.success(ichimoku_text)
                elif "관망" in signal_badge or "Neutral" in signal_badge:
                    st.warning(ichimoku_text)
                else:
                    st.error(ichimoku_text)
                    
                st.markdown(f"#### {L['chart_trend']}")
                st.line_chart(hist_df[['Close', 'Tenkan_Sen', 'Kijun_Sen', 'Senkou_Span_A', 'Senkou_Span_B']].tail(60), use_container_width=True)
            else:
                st.info(ichimoku_text)

        with tab_bs:
            st.subheader("Balance Sheet Summary")
            bs_summary_data = {
                "Component": ["💵 Cash", "🤝 Receivables", "📦 Inventories", "🗂️ CURRENT ASSETS", "🏢 PPE", "💎 TOTAL ASSETS", "🛑 CURRENT LIAB", "💼 TOTAL LIABILITIES", "📈 Retained Earnings", "🧬 TOTAL EQUITY"],
                f"Cur ({current_year})": [f"{cash_cur:,.0f}", f"{ar_cur:,.0f}", f"{inv_cur:,.0f}", f"{ca_cur:,.0f}", f"{ppe_cur:,.0f}", f"{ta_cur:,.0f}", f"{cl_cur:,.0f}", f"{tl_cur:,.0f}", f"{re_cur:,.0f}", f"{te_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{cash_pri:,.0f}", f"{ar_pri:,.0f}", f"{inv_pri:,.0f}", f"{ca_pri:,.0f}", f"{ppe_pri:,.0f}", f"{ta_pri:,.0f}", f"{cl_pri:,.0f}", f"{tl_pri:,.0f}", f"{re_pri:,.0f}", f"{te_pri:,.0f}"],
                "Var": [calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(ca_cur, ca_pri), calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(ta_cur, ta_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(tl_cur, tl_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)]
            }
            st.dataframe(pd.DataFrame(bs_summary_data), use_container_width=True, hide_index=True)

        with tab_ratios:
            st.subheader("Liquidity & Cycles")
            ratio_data = {
                "Metric Indicator": [" Debt Ratio", " Current Ratio", " Quick Ratio", " Inventory Turnover", " Receivables Turnover", " Cash Conversion Cycle"],
                f"Cur ({current_year})": [f"{debt_to_equity_cur:.1f}%", f"{current_ratio_cur:.2f}", f"{quick_ratio_cur:.2f}", f"{inv_turnover_cur:.1f}x", f"{ar_turnover_cur:.1f}x", f"{ccc_cur:.1f} Days"],
                f"Pri ({prior_year})": [f"{debt_to_equity_pri:.1f}%", f"{current_ratio_pri:.2f}", f"{quick_ratio_pri:.2f}", f"{inv_turnover_pri:.1f}x", f"{ar_turnover_pri:.1f}x", f"{ccc_pri:.1f} Days"],
                "Delta": [f"{debt_to_equity_cur - debt_to_equity_pri:+.1f}%p", f"{current_ratio_cur - current_ratio_pri:+.2f}", f"{quick_ratio_cur - quick_ratio_pri:+.2f}", f"{inv_turnover_cur - inv_turnover_pri:+.1f}x", f"{ar_turnover_cur - ar_turnover_pri:+.1f}x", f"{ccc_cur - ccc_pri:+.1f} D"]
            }
            st.dataframe(pd.DataFrame(ratio_data), use_container_width=True, hide_index=True)

        with tab_valuation:
            st.subheader("CVP & Valuation Multiples")
            val_lev_data = {
                "Parameter Item": [" Contribution Margin", " Break-Even Point Sales", " EPS", " BPS", " PER", " PBR"],
                f"Cur ({current_year})": [f"{cm_rate_cur*100:.1f}%", f"{bep_sales_cur:,.0f}", f"{eps_cur:,.2f}", f"{bps_cur:,.2f}", f"{per_cur:.1f}x", f"{pbr_cur:.1f}x"],
                f"Pri ({prior_year})": [f"{cm_rate_pri*100:.1f}%", f"{bep_sales_pri:,.0f}", f"{eps_pri:,.2f}", "N/A", "N/A", "N/A"],
                "Description": ["CVP Shift", "BEP Growth", calc_growth_raw(eps_cur, eps_pri), "Capital", "Multiples", "Multiples"]
            }
            st.dataframe(pd.DataFrame(val_lev_data), use_container_width=True, hide_index=True)
            
        with tab_news:
            st.subheader(f"📰 {L['latest_news']}: {ticker_final}")
            if stock_news:
                for article in stock_news[:10]:
                    st.markdown(f"""
                    <div style="padding: 12px; border-radius: 8px; background-color: rgba(128,128,128,0.1); margin-bottom: 10px;">
                        <a href="{article['link']}" target="_blank" style="text-decoration: none; font-weight: bold; font-size: 15px; color: #1E88E5;">🔗 {article['title']}</a>
                        <p style="margin: 6px 0 0 0; font-size: 12px; color: gray;">🏢 Source: {article['publisher']} | 📅 {article['date_str']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info(L["no_news"])
    else:
        st.warning(L["insufficient_data"])
