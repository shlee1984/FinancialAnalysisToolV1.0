import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 스트림릿이 패키지를 못 찾을 때 경로를 강제로 지정해주는 치트키
python_packages_path = r"C:\Users\shlee\AppData\Local\Python\pythoncore-3.14-64\Lib\site-packages"
if python_packages_path not in sys.path:
    sys.path.append(python_packages_path)



import streamlit as st

if "lang" not in st.session.state:
    st.session.state.lang = "ko"
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import FinanceDataReader as fdr
from opendartreader import OpenDartReader



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
if "market" not in st.session_state:
    st.session_state.market = "kr"
if "lang" not in st.session_state:
    st.session_state.lang = "ko"

MESSAGES = {
    "ko": {
        "title": "📊 기업 재무 분석 도구",
        "subtitle": "고급 재무 진단 시스템 - 포괄적인 기술적 및 기본적 구조 매핑",
        "market_select": "시장 선택:",
        "market_us": "🇺🇸 미국 주식 (Yahoo Finance)",
        "market_kr": "🇰🇷 한국 주식 (FDR + DART)",
        "search_method": "검색 방법 선택:",
        "by_ticker": "티커/종목코드로 검색",
        "by_name": "회사명으로 검색",
        "enter_ticker": "미국 주식 티커 입력 (예: AAPL):",
        "enter_ticker_kr": "한국 주식 종목코드 6자리 입력 (예: 005380):",
        "enter_name": "회사명 입력 (예: Apple, Tesla, Oracle):",
        "enter_name_kr": "회사명 입력 (예: 현대차, 삼성전자, 카카오):",
        "select_company": "정확한 회사 선택:",
        "search_error": "⚠️ 검색 한계량 도달 혹은 네트워크 지연이 발생했습니다. 티커 검색 방식을 이용하시면 막힘없이 사용 가능합니다.",
        "search_error_kr": "⚠️ 한국 주식 종목 검색 중 오류가 발생했습니다. 종목 코드(6자리 숫자)로 직접 입력해 주세요.",
        "fetch_error": "⚠️ 종목의 데이터를 가져오지 못했습니다. 올바른 US 티커 명칭인지 확인하시거나 잠시 후 다시 검색해 주세요.",
        "fetch_error_kr": "⚠️ 한국 주식 데이터를 가져오지 못했습니다. DART API Key가 올바른지, 종목 코드가 맞는지 확인해 주세요.",
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
        "guideline_1": "1. **비용 구조 개방:** 본 기업의 현재 분기 추정 손익분기점(BEP) 매출액은 **{currency}{bep_sales:,.0f}**입니다. 현재 매출이 손익분기점을 안전하게 상회하고 있으므로 고정비 레버리지 효과에 따른 수익성 확대 국면입니다.",
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
        "market_select": "Select Market:",
        "market_us": "🇺🇸 US Stocks (Yahoo)",
        "market_kr": "🇰🇷 KR Stocks (DART)",
        "search_method": "Select Search Method:",
        "by_ticker": "By Ticker/Code",
        "by_name": "By Company Name",
        "enter_ticker": "Enter US Stock Ticker (e.g., AAPL):",
        "enter_ticker_kr": "Enter 6-digit KR Stock Code (e.g., 005380):",
        "enter_name": "Enter Company Name (e.g., Apple, Tesla, Oracle):",
        "enter_name_kr": "Enter Company Name (e.g., Hyundai, Samsung, Kakao):",
        "select_company": "Select exact company:",
        "search_error": "⚠️ Search limit reached or network delay. Using 'By Ticker' method works without interruption.",
        "search_error_kr": "⚠️ Error searching Korean stocks. Please enter the 6-digit stock code directly.",
        "fetch_error": "⚠️ Failed to fetch data. Please check if the US ticker is correct or try again later.",
        "fetch_error_kr": "⚠️ Failed to fetch Korean stock data. Please check your DART API Key and Stock Code.",
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
        "guideline_1": "1. **Cost Structure Insight:** The estimated Break-Even Point (BEP) revenue for the current quarter is **{currency}{bep_sales:,.0f}**. Since current revenue safely exceeds BEP, the company is in a profitability expansion phase due to fixed-cost leverage.",
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

# --- 사이드바: DART API 설정 (백엔드에서만 작동, UI 숨김) ---
# Streamlit Secrets 또는 환경 변수에서 API 키 로드
try:
    dart_api_key = st.secrets["DART_API_KEY"]
except:
    dart_api_key = os.getenv("DART_API_KEY", "")

title_col, lang_col = st.columns([3, 1])
with title_col:
    st.title(MESSAGES[st.session.state.lang]["title"])
    st.caption(MESSAGES[st.session.state.lang]["subtitle"])

with lang_col:
    st.write("<div class='lang-container'>", unsafe_allow_html=True)
    btn_ko, btn_en = st.columns(2)
    with btn_ko:
        if st.button("한글", use_container_width=True):
            st.session.state.lang = "ko"
            st.rerun()
    with btn_en:
        if st.button("English", use_container_width=True):
            st.session.state.lang = "en"
            st.rerun()
    st.write("</div>", unsafe_allow_html=True)

st.markdown("---")

L = MESSAGES[st.session.state.lang]

# 시장 선택 UI
market_col1, market_col2 = st.columns([1, 3])
with market_col1:
    st.markdown(f"**{L['market_select']}**")
with market_col2:
    m_btn_us, m_btn_kr = st.columns(2)
    with m_btn_us:
        us_type = "primary" if st.session.state.market == "us" else "secondary"
        if st.button(L["market_us"], use_container_width=True, type=us_type):
            st.session.state.market = "us"
            st.rerun()
    with m_btn_kr:
        kr_type = "primary" if st.session.state.market == "kr" else "secondary"
        if st.button(L["market_kr"], use_container_width=True, type=kr_type):
            st.session.state.market = "kr"
            st.rerun()

st.markdown("---")

def get_highly_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive'
    })
    return session

# ── 내장 KRX 종목 데이터 (한글명 검색용) ─────────────────────────────
_KR_TICKERS_BUILTIN = {
    "005930": ("삼성전자", "KOSPI"), "000660": ("SK하이닉스", "KOSPI"),
    "005380": ("현대차", "KOSPI"), "000270": ("기아", "KOSPI"),
    "035420": ("NAVER", "KOSPI"), "035720": ("카카오", "KOSDAQ"),
    "068270": ("셀트리온", "KOSPI"), "207940": ("삼성바이오로직스", "KOSPI"),
    "005490": ("POSCO홀딩스", "KOSPI"), "051910": ("LG화학", "KOSPI"),
    "006400": ("삼성SDI", "KOSPI"), "028260": ("삼성물산", "KOSPI")
}

def search_krx_by_name(query: str) -> dict:
    """한국 주식 검색 (내장 데이터 및 외부 API fallback)"""
    query_strip = query.strip()
    if not query_strip: return {}
    result = {}
    query_lower = query_strip.lower()
    
    # 1순위: 내장 데이터
    for code, (name, market) in _KR_TICKERS_BUILTIN.items():
        if query_lower in name.lower():
            result[f"{name} ({code}) [{market}]"] = code
    if result: return result

    # 2순위: FinanceDataReader 거래소 리스트 캐싱 활용 (간단 구현)
    try:
        krx_df = fdr.StockListing('KRX')
        matches = krx_df[krx_df['Name'].str.contains(query_strip, case=False, na=False)]
        for _, row in matches.head(10).iterrows():
            result[f"{row['Name']} ({row['Code']}) [{row.get('Market', 'KRX')}]"] = row['Code']
    except Exception:
        pass
    return result

def get_currency_symbol(market: str) -> str:
    return "₩" if market == "kr" else "$"

# 검색 UI 레이아웃
search_col1, search_col2 = st.columns([1, 2])
ticker_final = "AAPL" if st.session.state.market == "us" else "005380"

with search_col1:
    search_type = st.radio(L["search_method"], [L["by_ticker"], L["by_name"]], index=0, horizontal=True)

with search_col2:
    if st.session.state.market == "us":
        if search_type == L["by_ticker"]:
            ticker_input = st.text_input(L["enter_ticker"], "AAPL", label_visibility="collapsed").upper().strip()
            ticker_final = ticker_input if ticker_input else "AAPL"
        else:
            company_input = st.text_input(L["enter_name"], "Oracle", label_visibility="collapsed").strip()
            if company_input:
                try:
                    custom_session = get_highly_secure_session()
                    search_results = yf.Search(company_input, max_results=5, session=custom_session).quotes
                    if search_results:
                        options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))}": q['symbol'] for q in search_results}
                        selected_display = st.selectbox(L["select_company"], list(options.keys()), label_visibility="collapsed")
                        ticker_final = options[selected_display]
                except Exception:
                    st.error(L["search_error"])
    else:
        if search_type == L["by_ticker"]:
            kr_code_input = st.text_input(L["enter_ticker_kr"], "005380", label_visibility="collapsed", placeholder="예: 005380").strip()
            ticker_final = kr_code_input.zfill(6) if kr_code_input else "005380"
        else:
            name_col_input, name_col_btn = st.columns([5, 1])
            with name_col_input:
                kr_name_input = st.text_input(L["enter_name_kr"], "", label_visibility="collapsed").strip()
            with name_col_btn:
                do_search = st.button("검색", use_container_width=True)

            if do_search and kr_name_input:
                st.session.state["kr_search_query"] = kr_name_input
                st.session.state["kr_search_results"] = search_krx_by_name(kr_name_input)

            kr_options = st.session.state.get("kr_search_results", {})
            if kr_options:
                selected_kr = st.selectbox(L["select_company"], list(kr_options.keys()), label_visibility="collapsed")
                ticker_final = kr_options[selected_kr]
            else:
                ticker_final = "005380"

st.markdown("---")

def fetch_google_news_rss(ticker_symbol, lang_mode):
    news_items = []
    search_term = ticker_symbol.replace(".KS", "").replace(".KQ", "") if st.session.state.market == "kr" else ticker_symbol
    try:
        hl_gl = "hl=ko&gl=KR&ceid=KR:ko" if lang_mode == "ko" else "hl=en-US&gl=US&ceid=US:en"
        url = f"https://news.google.com/rss/search?q={search_term}+stock&{hl_gl}"
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            for item in root.findall('.//item')[:10]:
                title = item.find('title').text if item.find('title') is not None else "No Title Available"
                link = item.find('link').text if item.find('link') is not None else "#"
                pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
                source = item.find('source').text if item.find('source') is not None else "Google News"
                news_items.append({"title": title, "link": link, "publisher": source, "date_str": pub_date})
    except Exception:
        pass
    return news_items

def parse_dart_to_yf_format(dart_df, year):
    """
    DART의 raw DataFrame을 yfinance의 financials/balance_sheet 형식으로 변환하는 헬퍼 함수
    """
    if dart_df is None or dart_df.empty: return pd.DataFrame(), pd.DataFrame()
    
    # 연결재무제표(CFS) 우선, 없으면 별도재무제표(OFS)
    # fs_div 또는 fs_type 컬럼 확인
    fs_col = 'fs_div' if 'fs_div' in dart_df.columns else 'fs_type' if 'fs_type' in dart_df.columns else None
    
    if fs_col is None:
        # 컬럼이 없으면 전체 데이터 사용
        cfs_df = dart_df
    else:
        cfs_df = dart_df[dart_df[fs_col] == 'CFS']
        if cfs_df.empty:
            cfs_df = dart_df[dart_df[fs_col] == 'OFS']
        
    def safe_float(val):
        try: return float(str(val).replace(',', ''))
        except: return 0.0

    mapped_data = {}
    
    # DART account_nm을 기반으로 맵핑 (한국어 계정명 -> yfinance 스타일 영문 키)
    for _, row in cfs_df.iterrows():
        acc_name = row['account_nm'].strip()
        cur_amt = safe_float(row['thstrm_amount'])
        pri_amt = safe_float(row['frmtrm_amount'])
        
        # 재무상태표 맵핑
        if acc_name == '자산총계': mapped_data['Total Assets'] = (cur_amt, pri_amt)
        elif acc_name == '부채총계': mapped_data['Total Liabilities'] = (cur_amt, pri_amt)
        elif acc_name == '자본총계': mapped_data['Total Stockholders Equity'] = (cur_amt, pri_amt)
        elif acc_name == '유동자산': mapped_data['Current Assets'] = (cur_amt, pri_amt)
        elif acc_name == '유동부채': mapped_data['Current Liabilities'] = (cur_amt, pri_amt)
        elif acc_name == '비유동자산': mapped_data['Total Non Current Assets'] = (cur_amt, pri_amt)
        elif '현금및현금성자산' in acc_name: mapped_data['Cash'] = (cur_amt, pri_amt)
        elif '재고자산' in acc_name: mapped_data['Inventory'] = (cur_amt, pri_amt)
        elif '매출채권' in acc_name: mapped_data['Net Receivables'] = (cur_amt, pri_amt)
        
        # 손익계산서 맵핑
        elif acc_name in ['매출액', '영업수익']: mapped_data['Total Revenue'] = (cur_amt, pri_amt)
        elif acc_name == '매출원가': mapped_data['Cost Of Revenue'] = (cur_amt, pri_amt)
        elif acc_name == '매출총이익': mapped_data['Gross Profit'] = (cur_amt, pri_amt)
        elif acc_name in ['판매비와관리비', '영업비용']: mapped_data['Selling General And Administrative'] = (cur_amt, pri_amt)
        elif acc_name == '영업이익': mapped_data['Operating Income'] = (cur_amt, pri_amt)
        elif acc_name == '당기순이익': mapped_data['Net Income'] = (cur_amt, pri_amt)

    # 데이터프레임 조립 (columns: [현재연도, 이전연도])
    col_cur = f"{year}-12-31"
    col_pri = f"{year-1}-12-31"
    
    combined_df = pd.DataFrame.from_dict(mapped_data, orient='index', columns=[col_cur, col_pri])
    
    # 분리: BS 계정과 FI 계정을 대략적으로 나눔
    bs_keys = ['Total Assets', 'Total Liabilities', 'Total Stockholders Equity', 'Current Assets', 'Current Liabilities', 'Cash', 'Inventory', 'Net Receivables', 'Total Non Current Assets']
    fi_keys = ['Total Revenue', 'Cost Of Revenue', 'Gross Profit', 'Selling General And Administrative', 'Operating Income', 'Net Income']
    
    bs_df = combined_df[combined_df.index.isin(bs_keys)]
    fi_df = combined_df[combined_df.index.isin(fi_keys)]
    
    return bs_df, fi_df

@st.cache_data(ttl=120)
def fetch_raw_financial_data(ticker_symbol, market, dart_key):
    try:
        # ==========================================
        # [1] 미국 주식 (US): Yahoo Finance API 활용
        # ==========================================
        if market == "us":
            session = get_highly_secure_session()
            stock = yf.Ticker(ticker_symbol, session=session)
            bs = stock.balance_sheet
            fi = stock.financials
            if bs is None or bs.empty or fi is None or fi.empty:
                return None
                
            info = stock.info
            hist_df = stock.history(period="1y")
            
            market_metrics = {
                'trailingEps': info.get('trailingEps', 0.0),
                'bookValue': info.get('bookValue', 0.0),
                'sharesOutstanding': info.get('sharesOutstanding', 1.0),
                'trailingPE': info.get('trailingPE', 0.0),
                'priceToBook': info.get('priceToBook', 0.0),
                'currentPrice': info.get('currentPrice', float(hist_df['Close'].iloc[-1]) if not hist_df.empty else 0.0),
                'fiftyTwoWeekHigh': info.get('fiftyTwoWeekHigh', float(hist_df['High'].max()) if not hist_df.empty else 0.0),
                'fiftyTwoWeekLow': info.get('fiftyTwoWeekLow', float(hist_df['Low'].min()) if not hist_df.empty else 0.0),
                'fiftyDayAverage': info.get('fiftyDayAverage', float(hist_df['Close'].tail(50).mean()) if not hist_df.empty else 0.0),
                'longName': info.get('longName', ticker_symbol),
                'currency': info.get('currency', 'USD')
            }
            
            bs_df = pd.DataFrame(bs.values, index=bs.index.astype(str), columns=bs.columns.astype(str))
            fi_df = pd.DataFrame(fi.values, index=fi.index.astype(str), columns=fi.columns.astype(str))
            
            return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics, "history": hist_df}
            
        # ==========================================
        # [2] 한국 주식 (KR): FinanceDataReader + DART
        # ==========================================
        elif market == "kr":
            if not dart_key:
                return "NO_API_KEY"
                
            code = ticker_symbol.zfill(6)
            
            # 1. 주가 데이터 수집 (FinanceDataReader)
            end_date = datetime.today()
            start_date = end_date - pd.DateOffset(years=1)
            hist_df = fdr.DataReader(code, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if hist_df.empty: return None
            
            # 2. 기업 개황 및 재무 데이터 수집 (DART)
            dart = OpenDartReader(dart_key)
            company_info = dart.company(code)
            corp_name = company_info['corp_name'] if company_info else code
            
            # 보통 작년도 사업보고서(11011)를 기준으로 전체 재무제표 가져오기
            target_year = end_date.year - 1
            try:
                dart_fs = dart.finstate_all(code, target_year)
            except Exception:
                try:
                    dart_fs = dart.finstate_all(code, target_year, fs_type='CFS')
                except Exception:
                    try:
                        dart_fs = dart.finstate_all(code, target_year - 1, fs_type='CFS')
                        target_year -= 1
                    except Exception:
                        dart_fs = None
            
            # DART 데이터를 yfinance와 호환되는 형태로 파싱
            bs_df, fi_df = parse_dart_to_yf_format(dart_fs, target_year)
            
            # 시장 지표 계산
            cur_price = float(hist_df['Close'].iloc[-1])
            high_52 = float(hist_df['High'].max())
            low_52 = float(hist_df['Low'].min())
            avg_50 = float(hist_df['Close'].tail(50).mean())
            
            # DART에서 발행주식수를 가져오기는 까다로우므로 기본값 혹은 근사치 적용
            shares_out = 10000000  # Default fallback
            
            market_metrics = {
                'trailingEps': 0.0, # 추후 재무제표에서 계산됨
                'bookValue': 0.0,
                'sharesOutstanding': shares_out,
                'trailingPE': 0.0,
                'priceToBook': 0.0,
                'currentPrice': cur_price,
                'fiftyTwoWeekHigh': high_52,
                'fiftyTwoWeekLow': low_52,
                'fiftyDayAverage': avg_50,
                'longName': corp_name,
                'currency': 'KRW'
            }
            
            return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics, "history": hist_df}
            
    except Exception as e:
        print(f"Data Fetch Error: {e}")
        return None

# 데이터 조회
data_bundle = fetch_raw_financial_data(ticker_final, st.session_state.market, dart_api_key)
stock_news = fetch_google_news_rss(ticker_final, st.session_state.lang)

if data_bundle == "NO_API_KEY":
    st.error("사이드바에 DART API Key를 입력해야 한국 주식 데이터를 불러올 수 있습니다.")
elif not data_bundle:
    err_key = "fetch_error_kr" if st.session.state.market == "kr" else "fetch_error"
    st.error(L[err_key])
else:
    balance_sheet = data_bundle["balance_sheet"]
    financials = data_bundle["financials"]
    market_metrics = data_bundle["metrics"]
    hist_df = data_bundle["history"]
    comp_name = market_metrics["longName"]

    CURRENCY = "₩" if market_metrics.get("currency") == "KRW" else "$"

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

        sga_cur, sga_pri = get_row_values_robust(financials, ['Selling General And Administrative'])
        op_cur, op_pri = get_row_values_robust(financials, ['Operating Income', 'EBIT'])
        ebitda_cur, ebitda_pri = get_row_values_robust(financials, ['Normalized EBITDA', 'EBITDA'])
        net_cur, net_pri = get_row_values_robust(financials, ['Net Income', 'Net Income Common Stockholders'])

        cash_cur, cash_pri = get_row_values_robust(balance_sheet, ['Cash And Cash Equivalents', 'Cash'])
        inv_cur, inv_pri = get_row_values_robust(balance_sheet, ['Inventory', 'Inventories'])
        ar_cur, ar_pri = get_row_values_robust(balance_sheet, ['Receivables', 'Accounts Receivable', 'Net Receivables'])
        ap_cur, ap_pri = get_row_values_robust(balance_sheet, ['Payables And Accrued Expenses', 'Accounts Payable'])

        ca_cur, ca_pri = get_row_values_robust(balance_sheet, ['Current Assets', 'Total Current Assets'])
        ppe_cur, ppe_pri = get_row_values_robust(balance_sheet, ['Properties', 'Net PPE', 'Property Plant And Equipment'])
        ta_cur, ta_pri = get_row_values_robust(balance_sheet, ['Total Assets', 'Assets'])
        cl_cur, cl_pri = get_row_values_robust(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
        tl_cur, tl_pri = get_row_values_robust(balance_sheet, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
        re_cur, re_pri = get_row_values_robust(balance_sheet, ['Retained Earnings'])
        te_cur, te_pri = get_row_values_robust(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'])

        sales_growth_val = ((sales_cur - sales_pri) / sales_pri * 100) if sales_pri != 0 else 0.0
        net_growth_val = ((net_cur - net_pri) / net_pri * 100) if net_pri != 0 else 0.0

        de_ratio_cur = (tl_cur / te_cur * 100) if te_cur != 0 else 0.0
        de_ratio_pri = (tl_pri / te_pri * 100) if te_pri != 0 else 0.0

        debt_ratio_cur = (tl_cur / ta_cur * 100) if ta_cur != 0 else 0.0
        debt_ratio_pri = (tl_pri / ta_pri * 100) if ta_pri != 0 else 0.0

        current_ratio_cur = (ca_cur / cl_cur) if cl_cur != 0 else 0.0
        current_ratio_pri = (ca_pri / cl_pri) if cl_pri != 0 else 0.0
        quick_ratio_cur = ((ca_cur - inv_cur) / cl_cur) if cl_cur != 0 else 0.0
        quick_ratio_pri = ((ca_pri - inv_pri) / cl_pri) if cl_pri != 0 else 0.0

        avg_inv_cur = (inv_cur + inv_pri) / 2 if (inv_cur + inv_pri) != 0 else inv_cur
        avg_ar_cur  = (ar_cur  + ar_pri)  / 2 if (ar_cur  + ar_pri)  != 0 else ar_cur
        avg_ap_cur  = (ap_cur  + ap_pri)  / 2 if (ap_cur  + ap_pri)  != 0 else ap_cur
        
        avg_inv_pri = inv_pri
        avg_ar_pri  = ar_pri
        avg_ap_pri  = ap_pri

        inv_turnover_cur = (cogs_cur / avg_inv_cur) if avg_inv_cur != 0 else 0.0
        inv_turnover_pri = (cogs_pri / avg_inv_pri) if avg_inv_pri != 0 else 0.0
        ar_turnover_cur  = (sales_cur / avg_ar_cur)  if avg_ar_cur  != 0 else 0.0
        ar_turnover_pri  = (sales_pri / avg_ar_pri)  if avg_ar_pri  != 0 else 0.0
        ap_turnover_cur  = (cogs_cur / avg_ap_cur)   if avg_ap_cur  != 0 else 1.0
        ap_turnover_pri  = (cogs_pri / avg_ap_pri)   if avg_ap_pri  != 0 else 1.0

        days_inv_cur = 365 / inv_turnover_cur if inv_turnover_cur != 0 else 0.0
        days_ar_cur  = 365 / ar_turnover_cur  if ar_turnover_cur  != 0 else 0.0
        days_ap_cur  = 365 / ap_turnover_cur
        ccc_cur = (days_inv_cur + days_ar_cur) - days_ap_cur

        days_inv_pri = 365 / inv_turnover_pri if inv_turnover_pri != 0 else 0.0
        days_ar_pri  = 365 / ar_turnover_pri  if ar_turnover_pri  != 0 else 0.0
        days_ap_pri  = 365 / ap_turnover_pri
        ccc_pri = (days_inv_pri + days_ar_pri) - days_ap_pri

        fixed_cost_cur = sga_cur if sga_cur > 0 else max(gp_cur - op_cur, sales_cur * 0.2)
        fixed_cost_pri = sga_pri if sga_pri > 0 else max(gp_pri - op_pri, sales_pri * 0.2)

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

        # 일목균형표 계산
        ichimoku_ready = False
        ichimoku_text = "📊 데이터 축적량이 부족하여 기술적 지표 진단을 생성할 수 없습니다." if st.session.state.lang == "ko" else "📊 Data is insufficient to generate Ichimoku analysis."
        signal_badge = "🔄 분석중" if st.session.state.lang == "ko" else "🔄 Processing"

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

            chikou_current = hist_df['Close'].iloc[-1]
            past_close_26  = hist_df['Close'].iloc[-26] if len(hist_df) >= 26 else chikou_current

            if sa_curr != 0.0 and sb_curr != 0.0:
                ichimoku_ready = True

                if st.session.state.lang == "ko":
                    if cur_price > max(sa_curr, sb_curr):
                        cloud_status, position_status = f"구름대 상단({CURRENCY}{max(sa_curr, sb_curr):,.2f}) 위", "확고한 정배열형 상승 추세"
                    elif cur_price < min(sa_curr, sb_curr):
                        cloud_status, position_status = f"구름대 하단({CURRENCY}{min(sa_curr, sb_curr):,.2f}) 아래", "매물대 저항 압박에 직면한 하락 위험"
                    else:
                        cloud_status, position_status = f"구름대 가두리권 범위({CURRENCY}{min(sa_curr, sb_curr):,.2f} ~ {CURRENCY}{max(sa_curr, sb_curr):,.2f}) 내부", "단기 방향성 탐색을 위한 횡보 조정"

                    cross_status = f"🔼 **호전 지속:** 전환선({CURRENCY}{t_curr:,.2f})이 기준선({CURRENCY}{k_curr:,.2f}) 위에 위치하여 매수세가 우세합니다." if t_curr > k_curr else (f"🔽 **역전 발생:** 전환선({CURRENCY}{t_curr:,.2f})이 기준선({CURRENCY}{k_curr:,.2f})을 하회하여 가격 조정 중입니다." if t_curr < k_curr else f"🔀 **수렴:** 전환선과 기준선이 {CURRENCY}{t_curr:,.2f} 부근에서 결집 중입니다.")
                    if chikou_current > past_close_26:
                        lagging_status = f"🟢 **후행스팬 상승우위:** 현재 종가({CURRENCY}{chikou_current:,.2f})가 26봉 전 가격({CURRENCY}{past_close_26:,.2f})을 상회, 매수 모멘텀이 우세합니다."
                    else:
                        lagging_status = f"🚨 **후행스팬 하락부담:** 현재 종가({CURRENCY}{chikou_current:,.2f})가 26봉 전 가격({CURRENCY}{past_close_26:,.2f}) 아래, 매물 소화 압력이 존재합니다."
                else:
                    if cur_price > max(sa_curr, sb_curr):
                        cloud_status, position_status = f"Above Cloud Top ({CURRENCY}{max(sa_curr, sb_curr):,.2f})", "Strong Bullish Uptrend"
                    elif cur_price < min(sa_curr, sb_curr):
                        cloud_status, position_status = f"Below Cloud Bottom ({CURRENCY}{min(sa_curr, sb_curr):,.2f})", "Bearish Risk with Heavy Resistance"
                    else:
                        cloud_status, position_status = f"Inside Cloud Bounds ({CURRENCY}{min(sa_curr, sb_curr):,.2f} ~ {CURRENCY}{max(sa_curr, sb_curr):,.2f})", "Neutral Consolidation Phase"

                    cross_status = f"🔼 **Bullish Cross:** Tenkan ({CURRENCY}{t_curr:,.2f}) is above Kijun ({CURRENCY}{k_curr:,.2f}), buying momentum dominates." if t_curr > k_curr else (f"🔽 **Bearish Cross:** Tenkan ({CURRENCY}{t_curr:,.2f}) broke below Kijun ({CURRENCY}{k_curr:,.2f}), undergoing correction." if t_curr < k_curr else f"🔀 **Convergence:** Lines are merging around {CURRENCY}{t_curr:,.2f}.")
                    if chikou_current > past_close_26:
                        lagging_status = f"🟢 **Chikou Bullish:** Current close ({CURRENCY}{chikou_current:,.2f}) is above price 26 periods ago ({CURRENCY}{past_close_26:,.2f}), confirming upward momentum."
                    else:
                        lagging_status = f"🚨 **Chikou Bearish:** Current close ({CURRENCY}{chikou_current:,.2f}) is below price 26 periods ago ({CURRENCY}{past_close_26:,.2f}), indicating overhead supply pressure."

                score = 0
                if cur_price > max(sa_curr, sb_curr): score += 2
                elif cur_price >= min(sa_curr, sb_curr): score += 1
                if t_curr > k_curr: score += 1
                if chikou_current > past_close_26: score += 1

                if score >= 3:
                    signal_badge = "🟢 매수 우위" if st.session.state.lang == "ko" else "🟢 Bullish Trend"
                elif score == 2:
                    signal_badge = "🟡 관망/중립" if st.session.state.lang == "ko" else "🟡 Neutral Box"
                else:
                    signal_badge = "🚨 리스크 관리" if st.session.state.lang == "ko" else "🚨 Bearish Shock"

                if st.session.state.lang == "ko":
                    ichimoku_text = f"""
                    * **구름대 위치 진단:** 현재 주가는 {cloud_status}에 위치하고 있으며, 현재 구간은 **{position_status}** 국면으로 해석됩니다.
                    * **추세 교차 시그널:** {cross_status}
                    * **매물대 지지선 파악:** 선행스팬A는 `{CURRENCY}{sa_curr:,.2f}`, 선행스팬B는 `{CURRENCY}{sb_curr:,.2f}`에 형성되어 있습니다.
                    * **후행스팬(Chikou) 검증:** {lagging_status}
                    """
                else:
                    ichimoku_text = f"""
                    * **Cloud Position Diagnostic:** Stock price is {cloud_status}, indicating a **{position_status}** state.
                    * **Trend Cross Signal:** {cross_status}
                    * **Support/Resistance Bounds:** Senkou Span A is `{CURRENCY}{sa_curr:,.2f}`, Senkou Span B is `{CURRENCY}{sb_curr:,.2f}`.
                    * **Chikou Span Validation:** {lagging_status}
                    """

        # 탭 레이아웃
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
                st.metric(label=L["curr_price"], value=f"{CURRENCY}{cur_price:,.2f}")

                status_text = L["status_high"] if price_location_pct >= 80 else (L["status_low"] if price_location_pct <= 30 else L["status_mid"])

                st.markdown(f"""
                * **{L['range_52']}:** {CURRENCY}{low_52:,.2f} ~ {CURRENCY}{high_52:,.2f} ({L['at_location']} **{price_location_pct:.1f}%** {L['location_end']})
                * **{L['avg_50']}:** {CURRENCY}{avg_50:,.2f}
                * {status_text}
                * **{L['multiple_analysis']} **{per_cur:.1f}x**, PBR은 **{pbr_cur:.1f}x**입니다.**
                """)
                st.markdown(L["ichimoku_analysis"])
                st.info(ichimoku_text)

            with report_col2:
                st.subheader(L["section2"])
                growth_score = 1 if sales_growth_val > 0 else 0
                profit_score = 1 if net_growth_val > 0 else 0
                stability_score = 1 if (de_ratio_cur <= 200 and debt_ratio_cur <= 60) else 0
                liquidity_score = 1 if current_ratio_cur >= 1.2 else 0
                total_score = growth_score + profit_score + stability_score + liquidity_score

                st.markdown(f"""
                * **{L['growth_score']}:** { L['excellent'] if growth_score else L['stagnant'] } ({sales_growth_val:+.1f}%)
                * **{L['profit_score']}:** { L['excellent'] if profit_score else L['stagnant'] } ({net_growth_val:+.1f}%)
                * **{L['stability_score']}:** { L['safe'] if stability_score else L['high_debt'] } (D/E: {de_ratio_cur:.1f}% | Debt: {debt_ratio_cur:.1f}%)
                * **{L['liquidity_score']}:** { L['safe'] if liquidity_score else L['caution_cash'] } ({current_ratio_cur:.2f})
                * **{L['total_score_text']}:** `{total_score} / 4`
                """)

                if total_score >= 3: st.success(L["report_good"])
                elif total_score == 2: st.warning(L["report_neutral"])
                else: st.error(L["report_bad"])

            st.markdown("---")
            st.subheader(L["section3"])
            st.info(f"""
            {L['guideline_1'].format(currency=CURRENCY, bep_sales=bep_sales_cur)}
            {L['guideline_2'].format(ccc=ccc_cur)}
            {L['guideline_3']}
            """)
            st.markdown("---")
            st.caption(L["disclaimer"])

        with tab_overview:
            st.subheader("Earnings & Comprehensive Income")
            earnings_data = {
                "Item": ["Sales", "COGS", "Gross Profit", "SG&A", "Operating Inc.", "EBITDA", "Net Income"],
                f"Cur ({current_year})": [f"{CURRENCY}{sales_cur:,.0f}", f"{CURRENCY}{cogs_cur:,.0f}", f"{CURRENCY}{gp_cur:,.0f}", f"{CURRENCY}{sga_cur:,.0f}", f"{CURRENCY}{op_cur:,.0f}", f"{CURRENCY}{ebitda_cur:,.0f}", f"{CURRENCY}{net_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{CURRENCY}{sales_pri:,.0f}", f"{CURRENCY}{cogs_pri:,.0f}", f"{CURRENCY}{gp_pri:,.0f}", f"{CURRENCY}{sga_pri:,.0f}", f"{CURRENCY}{op_pri:,.0f}", f"{CURRENCY}{ebitda_pri:,.0f}", f"{CURRENCY}{net_pri:,.0f}"],
                "Growth": [calc_growth_raw(sales_cur, sales_pri), calc_growth_raw(cogs_cur, cogs_pri), calc_growth_raw(gp_cur, gp_pri), calc_growth_raw(sga_cur, sga_pri), calc_growth_raw(op_cur, op_pri), calc_growth_raw(ebitda_cur, ebitda_pri), calc_growth_raw(net_cur, net_pri)]
            }
            st.dataframe(pd.DataFrame(earnings_data), use_container_width=True, hide_index=True)
            st.bar_chart(pd.DataFrame({'Current': [sales_cur, op_cur, net_cur], 'Prior': [sales_pri, op_pri, net_pri]}, index=['Sales', 'Operating', 'Net Income']))

        with tab_ichimoku:
            st.subheader(f"📐 {ticker_final} {L['ichimoku_title']}")
            if ichimoku_ready:
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1: st.metric(L["curr_price"], f"{CURRENCY}{cur_price:,.2f}")
                with m_col2: st.metric(L["tenkan"], f"{CURRENCY}{t_curr:,.2f}", f"{t_curr - k_curr:+.2f}")
                with m_col3: st.metric(L["kijun"], f"{CURRENCY}{k_curr:,.2f}")
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
                f"Cur ({current_year})": [f"{CURRENCY}{cash_cur:,.0f}", f"{CURRENCY}{ar_cur:,.0f}", f"{CURRENCY}{inv_cur:,.0f}", f"{CURRENCY}{ca_cur:,.0f}", f"{CURRENCY}{ppe_cur:,.0f}", f"{CURRENCY}{ta_cur:,.0f}", f"{CURRENCY}{cl_cur:,.0f}", f"{CURRENCY}{tl_cur:,.0f}", f"{CURRENCY}{re_cur:,.0f}", f"{CURRENCY}{te_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{CURRENCY}{cash_pri:,.0f}", f"{CURRENCY}{ar_pri:,.0f}", f"{CURRENCY}{inv_pri:,.0f}", f"{CURRENCY}{ca_pri:,.0f}", f"{CURRENCY}{ppe_pri:,.0f}", f"{CURRENCY}{ta_pri:,.0f}", f"{CURRENCY}{cl_pri:,.0f}", f"{CURRENCY}{tl_pri:,.0f}", f"{CURRENCY}{re_pri:,.0f}", f"{CURRENCY}{te_pri:,.0f}"],
                "Var": [calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(ca_cur, ca_pri), calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(ta_cur, ta_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(tl_cur, tl_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)]
            }
            st.dataframe(pd.DataFrame(bs_summary_data), use_container_width=True, hide_index=True)

        with tab_ratios:
            st.subheader("Liquidity & Cycles")
            ratio_data = {
                "Metric Indicator": [
                    " D/E Ratio (부채/자본)",
                    " Debt Ratio (부채/자산)",
                    " Current Ratio",
                    " Quick Ratio",
                    " Inventory Turnover (avg)",
                    " Receivables Turnover (avg)",
                    " Cash Conversion Cycle"
                ],
                f"Cur ({current_year})": [
                    f"{de_ratio_cur:.1f}%",
                    f"{debt_ratio_cur:.1f}%",
                    f"{current_ratio_cur:.2f}",
                    f"{quick_ratio_cur:.2f}",
                    f"{inv_turnover_cur:.1f}x",
                    f"{ar_turnover_cur:.1f}x",
                    f"{ccc_cur:.1f} Days"
                ],
                f"Pri ({prior_year})": [
                    f"{de_ratio_pri:.1f}%",
                    f"{debt_ratio_pri:.1f}%",
                    f"{current_ratio_pri:.2f}",
                    f"{quick_ratio_pri:.2f}",
                    f"{inv_turnover_pri:.1f}x",
                    f"{ar_turnover_pri:.1f}x",
                    f"{ccc_pri:.1f} Days"
                ],
                "Delta": [
                    f"{de_ratio_cur - de_ratio_pri:+.1f}%p",
                    f"{debt_ratio_cur - debt_ratio_pri:+.1f}%p",
                    f"{current_ratio_cur - current_ratio_pri:+.2f}",
                    f"{quick_ratio_cur - quick_ratio_pri:+.2f}",
                    f"{inv_turnover_cur - inv_turnover_pri:+.1f}x",
                    f"{ar_turnover_cur - ar_turnover_pri:+.1f}x",
                    f"{ccc_cur - ccc_pri:+.1f} D"
                ],
                "기준 (안전)": [
                    "≤200% (제조업 기준)",
                    "≤60%",
                    "≥1.5",
                    "≥1.0",
                    "높을수록 우수",
                    "높을수록 우수",
                    "낮을수록 우수"
                ]
            }
            st.dataframe(pd.DataFrame(ratio_data), use_container_width=True, hide_index=True)

        with tab_valuation:
            st.subheader("CVP & Valuation Multiples")
            val_lev_data = {
                "Parameter Item": [
                    " Gross Margin (CM Proxy) ⚠️",
                    " Break-Even Point Sales (추정)",
                    " EPS",
                    " BPS",
                    " PER",
                    " PBR"
                ],
                f"Cur ({current_year})": [f"{cm_rate_cur*100:.1f}%", f"{CURRENCY}{bep_sales_cur:,.0f}", f"{CURRENCY}{eps_cur:,.2f}", f"{CURRENCY}{bps_cur:,.2f}", f"{per_cur:.1f}x", f"{pbr_cur:.1f}x"],
                f"Pri ({prior_year})": [f"{cm_rate_pri*100:.1f}%", f"{CURRENCY}{bep_sales_pri:,.0f}", f"{CURRENCY}{eps_pri:,.2f}", "N/A", "N/A", "N/A"],
                "Description": [
                    "COGS 전체 변동비 가정 (근사치)",
                    "SG&A 기반 고정비 추정",
                    calc_growth_raw(eps_cur, eps_pri),
                    "Capital",
                    "Multiples",
                    "Multiples"
                ]
            }
            st.dataframe(pd.DataFrame(val_lev_data), use_container_width=True, hide_index=True)
            st.caption("⚠️ CM(공헌이익)은 외부 재무제표 특성상 매출총이익률로 근사 계산됩니다. BEP는 SG&A를 고정비로 가정한 추정치입니다.")

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
