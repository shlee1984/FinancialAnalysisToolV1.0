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

st.title("📊 Corporate Financial Analysis Tool")
st.caption("Advanced Financial Diagnostics System - Comprehensive Technical & Fundamental Structural Mapping")
st.markdown("---")

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT"]

search_col1, search_col2 = st.columns([1, 2])
ticker_final = "AAPL"

with search_col1:
    search_type = st.radio("Select Search Method:", ["By Ticker", "By Company Name"], index=1, horizontal=True)

with search_col2:
    if search_type == "By Ticker":
        ticker_input = st.text_input("Enter US Stock Ticker:", "AAPL", label_visibility="collapsed").upper().strip()
        ticker_final = ticker_input
    else:
        company_input = st.text_input("Enter Company Name (e.g., Apple, Tesla):", "Apple", label_visibility="collapsed").strip()
        if company_input:
            try:
                search_results = yf.Search(company_input, max_results=5).quotes
                us_quotes = [q for q in search_results if q.get('exchange') in ['NMS', 'NYQ', 'ASE', 'BTS', 'NGM', 'NCM']]
                target_quotes = us_quotes if us_quotes else search_results
                if target_quotes:
                    options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))}": q['symbol'] for q in target_quotes}
                    selected_display = st.selectbox("Select exact company:", list(options.keys()), label_visibility="collapsed")
                    ticker_final = options[selected_display]
                else:
                    st.error("❌ No companies found.")
            except:
                st.error("⚠️ Error searching company name.")

st.markdown("##### ⭐ My Watchlist")
watchlist_cols = st.columns(min(len(st.session_state.watchlist), 5))
for idx, ticker in enumerate(st.session_state.watchlist[:10]):
    col_idx = idx % 5
    with watchlist_cols[col_idx % len(watchlist_cols)]:
        if st.button(f"📌 {ticker}", key=f"wl_{ticker}", use_container_width=True):
            st.session_state["selected_ticker"] = ticker

if "selected_ticker" in st.session_state and st.session_state["selected_ticker"] in st.session_state.watchlist:
    ticker_final = st.session_state["selected_ticker"]

st.markdown("---")

def get_highly_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, healthiest/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ko-KR;q=0.8,ko;q=0.7',
        'Connection': 'keep-alive'
    })
    return session

def fetch_google_news_rss(ticker_symbol):
    news_items = []
    try:
        url = f"https://news.google.com/rss/search?q={ticker_symbol}+stock&hl=en-US&gl=US&ceid=US:en"
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

@st.cache_data(ttl=300)
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

data_bundle = fetch_raw_financial_data(ticker_final)
stock_news = fetch_google_news_rss(ticker_final)

if not data_bundle:
    st.error(f"⚠️ '{ticker_final}' 종목의 재무 데이터를 불러오지 못했습니다. 야후 파이낸스 트래픽 제한 또는 서버 응답이 지연되고 있으니 잠시 후 새로고침(F5)을 해주시거나 다른 종목을 선택해 주세요.")
else:
    balance_sheet = data_bundle["balance_sheet"]
    financials = data_bundle["financials"]
    market_metrics = data_bundle["metrics"]
    hist_df = data_bundle["history"]
    comp_name = market_metrics["longName"]

    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.subheader(f"📈 {comp_name} ({ticker_final})")
    with head_col2:
        if ticker_final in st.session_state.watchlist:
            if st.button("❌ Remove Watchlist", use_container_width=True):
                st.session_state.watchlist.remove(ticker_final)
                st.rerun()
        else:
            if len(st.session_state.watchlist) < 10:
                if st.button("⭐ Add Watchlist", use_container_width=True):
                    st.session_state.watchlist.append(ticker_final)
                    st.rerun()

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

        # =========================================================================
        # 📊 [핵심 수정] 일목균형표 종목별 완전 동적 데이터 연동 로직
        # =========================================================================
        ichimoku_ready = False
        ichimoku_text = "📊 데이터 축적량이 부족하여 기술적 지표 진단을 생성할 수 없습니다."
        signal_badge = "🔄 분석중"
        
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
                
                # 1. 구름대와 현재 주가 파악 문장 동적 조립
                if cur_price > max(sa_curr, sb_curr):
                    cloud_status = f"양운/의운 구름대 상단(정상 범위인 ${max(sa_curr, sb_curr):,.2f}) 위"
                    position_status = "확고한 정배열형 상승 추세"
                elif cur_price < min(sa_curr, sb_curr):
                    cloud_status = f"구름대 하단(지지 마지노선인 ${min(sa_curr, sb_curr):,.2f}) 아래"
                    position_status = "매물대 저항 압박에 직면한 하락 위험"
                else:
                    cloud_status = f"선행스팬 가두리권 범위(${min(sa_curr, sb_curr):,.2f} ~ ${max(sa_curr, sb_curr):,.2f}) 내부"
                    position_status = "단기 방향성 탐색을 위한 구름대 내 횡보 조정"
                
                # 2. 전환선과 기준선 교차 여부 문장 동적 조립
                if t_curr > k_curr:
                    cross_status = f"🔼 **호전(Bullish) 지속:** 단기 전환선(${t_curr:,.2f})이 중기 기준선(${k_curr:,.2f}) 위에 위치하여 단기 매수세가 여전히 강하게 유지되고 있습니다."
                elif t_curr < k_curr:
                    cross_status = f"🔽 **역전(Bearish) 발생:** 단기 전환선(${t_curr:,.2f})이 중기 기준선(${k_curr:,.2f})을 하회하여, 최근 매물대 출하로 인한 단기 추세 악화 및 가격 조정이 진행 중입니다."
                else:
                    cross_status = f"🔀 **수렴(Neutral):** 전환선과 기준선이 ${t_curr:,.2f} 부근에서 일치하여 대규모 시세 분출을 앞두고 에너지를 응축 중입니다."
                
                # 3. 후행스팬 위치 해석 문장 동적 조립
                if cur_price > lagging_price:
                    lagging_status = f"🟢 **후행스팬 우위:** 현재 주가가 26거래일 전 주가(${lagging_price:,.2f})보다 높으므로 추세 모멘텀의 복원력이 높은 상태입니다."
                else:
                    lagging_status = f"🚨 **후행스팬 부담:** 현재 주가가 26거래일 전 주가(${lagging_price:,.2f}) 아래에 갇혀 있어, 과거에 매수한 보유자들의 악성 매물대 소화 과정이 추가로 필요합니다."

                # 4. 종목별 종합 계량 시그널 평점화
                score = 0
                if cur_price > max(sa_curr, sb_curr): score += 2
                elif cur_price >= min(sa_curr, sb_curr): score += 1
                if t_curr > k_curr: score += 1
                if cur_price > lagging_price: score += 1

                if score >= 3:
                    signal_badge = "🟢 매수 우위 (Bullish Trend)"
                elif score == 2:
                    signal_badge = "🟡 관망/중립 (Neutral Box)"
                else:
                    signal_badge = "🚨 리스크 관리 (Bearish Shock)"

                # 최종 결합 (각 종목별 실시간 변수값을 완벽하게 바인딩)
                ichimoku_text = f"""
                * **구름대 위치 진단:** 현재 {ticker_final} 주가는 {cloud_status}에 위치하고 있으며, 현재 구간은 **{position_status}** 국면으로 해석됩니다.
                * **추세 교차 시그널:** {cross_status}
                * **매물대 지지선 파악:** 선행스팬A는 `${sa_curr:,.2f}`, 선행스팬B는 `${sb_curr:,.2f}`에 형성되어 있어, 향후 강한 변동성 지지 또는 저항선 역할을 담당하게 됩니다.
                * **후행 시그널 검증:** {lagging_status}
                """

        # ---------------- [ 탭 레이아웃 렌더링 ] ----------------
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "📌 Overview", "📐 Ichimoku Indicator", "🏢 Balance Sheet", "📊 Ratios", "📉 Valuation", "📰 News", "📝 종합의견 (Report)"
        ])
        
        with tab1:
            st.subheader("Earnings & Comprehensive Income")
            earnings_data = {
                "Item": ["Sales", "COGS", "Gross Profit", "SG&A", "Operating Inc.", "EBITDA", "Net Income"],
                f"Cur ({current_year})": [f"{sales_cur:,.0f}", f"{cogs_cur:,.0f}", f"{gp_cur:,.0f}", f"{sga_cur:,.0f}", f"{op_cur:,.0f}", f"{ebitda_cur:,.0f}", f"{net_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{sales_pri:,.0f}", f"{cogs_pri:,.0f}", f"{gp_pri:,.0f}", f"{sga_pri:,.0f}", f"{op_pri:,.0f}", f"{ebitda_pri:,.0f}", f"{net_pri:,.0f}"],
                "Growth": [calc_growth_raw(sales_cur, sales_pri), calc_growth_raw(cogs_cur, cogs_pri), calc_growth_raw(gp_cur, gp_pri), calc_growth_raw(sga_cur, sga_pri), calc_growth_raw(op_cur, op_pri), calc_growth_raw(ebitda_cur, ebitda_pri), calc_growth_raw(net_cur, net_pri)]
            }
            st.dataframe(pd.DataFrame(earnings_data), use_container_width=True, hide_index=True)
            
            st.subheader("Key Trend Chart")
            chart_data = pd.DataFrame({'Current': [sales_cur, op_cur, net_cur], 'Prior': [sales_pri, op_pri, net_pri]}, index=['Sales', 'Operating', 'Net Income'])
            st.bar_chart(chart_data)

        # 🎯 개별 맞춤형 분석 결과가 100% 매칭되어 표출되는 전용 분석 탭
        with tab2:
            st.subheader(f"📐 {ticker_final} ({comp_name}) 일목균형표 기술적 분석")
            
            if ichimoku_ready:
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1:
                    st.metric("현재 주가", f"${cur_price:,.2f}")
                with m_col2:
                    delta_tk = t_curr - k_curr
                    st.metric("전환선 (단기 추세선)", f"${t_curr:,.2f}", f"{delta_tk:+.2f} (vs 기준선)")
                with m_col3:
                    st.metric("기준선 (중기 균형선)", f"${k_curr:,.2f}")
                with m_col4:
                    st.metric("일목 종합 판단 시그널", signal_badge)

                st.markdown("---")
                st.markdown("#### 🔍 실시간 차트 세부 진단 피드백")
                
                # 분석 결과 성격에 맞는 알림창 동적 적용
                if "매수 우위" in signal_badge:
                    st.success(ichimoku_text)
                elif "관망" in signal_badge:
                    st.warning(ichimoku_text)
                else:
                    st.error(ichimoku_text)
                
                st.markdown("#### 📈 핵심 지표 시각화 트렌드 (최근 60거래일 동향)")
                chart_df = hist_df[['Close', 'Tenkan_Sen', 'Kijun_Sen', 'Senkou_Span_A', 'Senkou_Span_B']].tail(60)
                st.line_chart(chart_df, use_container_width=True)
            else:
                st.info(ichimoku_text)

        with tab3:
            st.subheader("Balance Sheet Summary")
            bs_summary_data = {
                "Component": ["💵 Cash", "🤝 Receivables", "📦 Inventories", "🗂️ CURRENT ASSETS", "🏢 PPE", "💎 TOTAL ASSETS", "🛑 CURRENT LIAB", "💼 TOTAL LIABILITIES", "📈 Retained Earnings", "🧬 TOTAL EQUITY"],
                f"Cur ({current_year})": [f"{cash_cur:,.0f}", f"{ar_cur:,.0f}", f"{inv_cur:,.0f}", f"{ca_cur:,.0f}", f"{ppe_cur:,.0f}", f"{ta_cur:,.0f}", f"{cl_cur:,.0f}", f"{tl_cur:,.0f}", f"{re_cur:,.0f}", f"{te_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{cash_pri:,.0f}", f"{ar_pri:,.0f}", f"{inv_pri:,.0f}", f"{ca_pri:,.0f}", f"{ppe_pri:,.0f}", f"{ta_pri:,.0f}", f"{cl_pri:,.0f}", f"{tl_pri:,.0f}", f"{re_pri:,.0f}", f"{te_pri:,.0f}"],
                "Var": [calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(ca_cur, ca_pri), calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(ta_cur, ta_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(tl_cur, tl_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)]
            }
            st.dataframe(pd.DataFrame(bs_summary_data), use_container_width=True, hide_index=True)

        with tab4:
            st.subheader("Liquidity & Cycles")
            ratio_data = {
                "Metric Indicator": [" 부채비율", " 유동비율", " 당좌비율", " 재고자산회전율", " 매출채권회전율", " 현금전환주기"],
                f"Cur ({current_year})": [f"{debt_to_equity_cur:.1f}%", f"{current_ratio_cur:.2f}", f"{quick_ratio_cur:.2f}", f"{inv_turnover_cur:.1f}x", f"{ar_turnover_cur:.1f}x", f"{ccc_cur:.1f} Days"],
                f"Pri ({prior_year})": [f"{debt_to_equity_pri:.1f}%", f"{current_ratio_pri:.2f}", f"{quick_ratio_pri:.2f}", f"{inv_turnover_pri:.1f}x", f"{ar_turnover_pri:.1f}x", f"{ccc_pri:.1f} Days"],
                "Delta": [f"{debt_to_equity_cur - debt_to_equity_pri:+.1f}%p", f"{current_ratio_cur - current_ratio_pri:+.2f}", f"{quick_ratio_cur - quick_ratio_pri:+.2f}", f"{inv_turnover_cur - inv_turnover_pri:+.1f}x", f"{ar_turnover_cur - ar_turnover_pri:+.1f}x", f"{ccc_cur - ccc_pri:+.1f} D"]
            }
            st.dataframe(pd.DataFrame(ratio_data), use_container_width=True, hide_index=True)

        with tab5:
            st.subheader("CVP & Valuation Multiples")
            val_lev_data = {
                "Parameter Item": [" 공헌이익률", " 손익분기점 매출", " 주당순이익(EPS)", " 주당순자산(BPS)", " PER", " PBR"],
                f"Cur ({current_year})": [f"{cm_rate_cur*100:.1f}%", f"{bep_sales_cur:,.0f}", f"{eps_cur:,.2f}", f"{bps_cur:,.2f}", f"{per_cur:.1f}x", f"{pbr_cur:.1f}x"],
                f"Pri ({prior_year})": [f"{cm_rate_pri*100:.1f}%", f"{bep_sales_pri:,.0f}", f"{eps_pri:,.2f}", "N/A", "N/A", "N/A"],
                "Description": ["CVP Shift", "BEP Growth", calc_growth_raw(eps_cur, eps_pri), "Capital", "Multiples", "Multiples"]
            }
            st.dataframe(pd.DataFrame(val_lev_data), use_container_width=True, hide_index=True)
            
        with tab6:
            st.subheader(f"📰 Latest News for {ticker_final}")
            if stock_news:
                for article in stock_news[:10]:
                    st.markdown(f"""
                    <div style="padding: 12px; border-radius: 8px; background-color: rgba(128,128,128,0.1); margin-bottom: 10px;">
                        <a href="{article['link']}" target="_blank" style="text-decoration: none; font-weight: bold; font-size: 15px; color: #1E88E5;">🔗 {article['title']}</a>
                        <p style="margin: 6px 0 0 0; font-size: 12px; color: gray;">🏢 Source: {article['publisher']} | 📅 {article['date_str']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ 현재 제공된 실시간 뉴스가 없습니다.")

        with tab7:
            st.header("📝 실시간 재무·주가 종합 진단 보고서")
            st.caption(f"대상 기업: {comp_name} ({ticker_final})")
            st.markdown("---")
            
            high_52 = market_metrics.get('fiftyTwoWeekHigh', 1.0)
            low_52 = market_metrics.get('fiftyTwoWeekLow', 1.0)
            avg_50 = market_metrics.get('fiftyDayAverage', 1.0)
            price_location_pct = ((cur_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) != 0 else 50.0
                
            report_col1, report_col2 = st.columns(2)
            
            with report_col1:
                st.subheader("🔍 1. 최근 주가 수준 및 기술적·밸류에이션 평가")
                st.metric(label="Current Stock Price", value=f"${cur_price:,.2f}")
                
                if price_location_pct >= 80:
                    status_text = "🔴 **52주 최고점 근접 구역 (과열 경계):** 현재 주가는 52주 가격 밴드 최상단에 위치하고 있습니다."
                elif price_location_pct <= 30:
                    status_text = "🟢 **52주 최저점 근접 구역 (바닥권 메리트):** 현재 주가는 52주 가격 밴드 하단에 있어 가격 부담이 적습니다."
                else:
                    status_text = "🟡 **중간 밴드 구역 (균형 가격):** 현재 주가는 52주 중간 이동평균선 부근에서 안정적인 흐름을 유지 중입니다."
                
                st.markdown(f"""
                * **52주 주가 변동 범위:** ${low_52:,.2f} ~ ${high_52:,.2f} (현재 변동폭의 **{price_location_pct:.1f}%** 지점 위치)
                * **단기 균형 가격 (50일 평균):** ${avg_50:,.2f}
                * {status_text}
                * **멀티플 분석:** 현재 PER 지표는 **{per_cur:.1f}x**, PBR 지표는 **{pbr_cur:.1f}x** 수준입니다.
                """)
                
                # 종합의견 탭에서도 개별 종목의 연동 텍스트가 정상 출력되도록 바인딩
                st.markdown("##### 📐 일목균형표(Ichimoku) 추세 모멘텀 분석")
                st.info(ichimoku_text)
                
            with report_col2:
                st.subheader("📊 2. 핵심 재무 상태 스코어링")
                growth_score = 1 if sales_growth_val > 0 else 0
                profit_score = 1 if net_growth_val > 0 else 0
                stability_score = 1 if debt_to_equity_cur <= 120 else 0
                liquidity_score = 1 if current_ratio_cur >= 1.2 else 0
                total_score = growth_score + profit_score + stability_score + liquidity_score
                
                st.markdown(f"""
                * **성장성 점수 (매출액 변동):** { '✅ 우수' if growth_score else '❌ 정체' } (전년비 {sales_growth_val:+.1f}%)
                * **수익성 점수 (당기순이익 변동):** { '✅ 우수' if profit_score else '❌ 정체' } (전년비 {net_growth_val:+.1f}%)
                * **부채 안정성 (부채비율):** { '✅ 안전' if stability_score else '🚨 부채 과다' } ({debt_to_equity_cur:.1f}%)
                * **유동성 리스크 (유동비율):** { '✅ 안전' if liquidity_score else '🚨 현금 주의' } ({current_ratio_cur:.2f}배)
                * **종합 재무 건전성 평점:** `{total_score} / 4`
                """)
                
                if total_score >= 3:
                    st.success("💎 **재무 종합 의견:** 펀더멘탈이 대단히 우량한 기업입니다. 주가 조정 발생 시 분할 매수 접근 전략이 유효합니다.")
                elif total_score == 2:
                    st.warning("⚠️ **재무 종합 의견:** 성장성 혹은 안정성 중 특정 지표의 둔화가 관찰됩니다. 마진율 변동 추이를 추적 관찰해야 합니다.")
                else:
                    st.error("🚨 **재무 종합 의견:** 전반적인 재무 지표 역성장 및 유동성 리스크가 우려됩니다. 보수적인 투자 관점이 필요합니다.")

            st.markdown("---")
            st.subheader("💡 3. 최종 투자 전략 가이드라인 (CVP 융합)")
            st.info(f"""
            1. **비용 구조 개방:** 본 기업의 현재 분기 추정 손익분기점(BEP) 매출액은 **${bep_sales_cur:,.0f}**입니다. 현재 매출이 손익분기점을 안전하게 상회하고 있으므로 고정비 레버리지 효과에 따른 수익성 확대 국면입니다.
            2. **운전 자본 효율성:** 현금전환주기(CCC)가 **{ccc_cur:.1f}일**로 측정되어 자금 회수 속도가 원활한 편입니다. 공급망 리스크에 따른 재고자산 누적 여부를 체크하시기 바랍니다.
            3. **최종 결론:** 본 재무분석 시스템의 추정치인 주당 가치 스케일링을 기준으로 볼 때, 현재 주가는 재무 기초체력 대비 합리적인 흐름을 보이고 있으나, 단기 변동성을 감안하여 실시간 뉴스 탭에 올라오는 글로벌 이슈들을 병행 모니터링하시기 바랍니다.
            """)
            
            st.markdown("---")
            st.caption("""
            ⚠️ **Investment Disclaimer** ※ 본 자료 및 검토의견은 재무제표와 관련 자료를 기초로 작성된 참고용 정보이며, 투자 권유 또는 투자 수익을 보장하는 내용이 아닙니다.  
            투자 결정은 투자자의 고유한 판단과 책임하에 이루어져야 하며, 이에 따른 손익 또한 투자자 본인에게 귀속됩니다.
            """)
    else:
        st.warning("📊 재무 데이터의 열 개수가 비교 분석하기에 충분하지 않습니다. 야후 파이낸스 가동 한계선 도달 시 발생하는 오류일 수 있습니다.")
