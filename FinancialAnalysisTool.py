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
st.caption("Advanced Financial Diagnostics System - Comprehensive 10-Q/10-K Structural Mapping")
st.markdown("---")

if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT"]

search_col1, search_col2 = st.columns([1, 2])
ticker_final = "AAPL"

with search_col1:
    # index=1 설정을 통해 'By Company Name'을 기본 선택 상태로 지정합니다.
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
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
                title = item.find('title').text if item.find('title') is not None else "No Title"
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
            
        if bs is None or bs.empty:
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
        
        if market_metrics['currentPrice'] == 0.0:
            hist = stock.history(period="1d")
            if not hist.empty:
                market_metrics['currentPrice'] = float(hist['Close'].iloc[-1])
                
        bs_df = pd.DataFrame(bs.values, index=bs.index.astype(str), columns=bs.columns.astype(str))
        fi_df = pd.DataFrame(fi.values, index=fi.index.astype(str), columns=fi.columns.astype(str))
        
        return {"balance_sheet": bs_df, "financials": fi_df, "metrics": market_metrics}
    except:
        return None

data_bundle = fetch_raw_financial_data(ticker_final)
stock_news = fetch_google_news_rss(ticker_final)

if not data_bundle:
    st.error(f"⚠️ '{ticker_final}' 종목의 재무 데이터를 불러오지 못했습니다. 야후 파이낸스 트래픽 제한일 수 있으니 다른 종목을 선택하시거나 잠시 후 새로고침(F5) 해주세요.")
else:
    balance_sheet = data_bundle["balance_sheet"]
    financials = data_bundle["financials"]
    market_metrics = data_bundle["metrics"]
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
        current_year = balance_sheet.columns[0][:4]
        prior_year = balance_sheet.columns[1][:4]
        
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
            
        sga_cur, sga_pri = get_row_values_robust(financials, ['Selling General And Administrative', 'Selling General Administrative'])
        op_cur, op_pri = get_row_values_robust(financials, ['Operating Income', 'EBIT'])
        ebitda_cur, ebitda_pri = get_row_values_robust(financials, ['Normalized EBITDA', 'EBITDA'])
        net_cur, net_pri = get_row_values_robust(financials, ['Net Income', 'Net Income Common Stockholders'])
        
        cash_cur, cash_pri = get_row_values_robust(balance_sheet, ['Cash And Cash Equivalents', 'Cash'])
        inv_cur, inv_pri = get_row_values_robust(balance_sheet, ['Inventory', 'Inventories'])
        ar_cur, ar_pri = get_row_values_robust(balance_sheet, ['Receivables', 'Accounts Receivable'])
        ap_cur, ap_pri = get_row_values_robust(balance_sheet, ['Payables And Accrued Expenses', 'Accounts Payable'])
        
        ca_cur, ca_pri = get_row_values_robust(balance_sheet, ['Current Assets', 'Total Current Assets'])
        ppe_cur, ppe_pri = get_row_values_robust(balance_sheet, ['Properties', 'Net PPE', 'Property Plant And Equipment'])
        ta_cur, ta_pri = get_row_values_robust(balance_sheet, ['Total Assets', 'Assets'])
        cl_cur, cl_pri = get_row_values_robust(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
        tl_cur, tl_pri = get_row_values_robust(balance_sheet, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
        re_cur, re_pri = get_row_values_robust(balance_sheet, ['Retained Earnings'])
        te_cur, te_pri = get_row_values_robust(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity'])

        sales_growth_val = ((sales_cur - sales_pri) / sales_pri * 100) if sales_pri != 0 else 0
        net_growth_val = ((net_cur - net_pri) / net_pri * 100) if net_pri != 0 else 0
        debt_to_equity_cur = (tl_cur / te_cur * 100) if te_cur != 0 else 0
        debt_to_equity_pri = (tl_pri / te_pri * 100) if te_pri != 0 else 0
        current_ratio_cur = (ca_cur / cl_cur) if cl_cur != 0 else 0
        current_ratio_pri = (ca_pri / cl_pri) if cl_pri != 0 else 0
        
        quick_ratio_cur = ((ca_cur - inv_cur) / cl_cur) if cl_cur != 0 else 0
        quick_ratio_pri = ((ca_pri - inv_pri) / cl_pri) if cl_pri != 0 else 0
        
        inv_turnover_cur = (cogs_cur / inv_cur) if inv_cur != 0 else 0
        inv_turnover_pri = (cogs_pri / inv_pri) if inv_pri != 0 else 0
        ar_turnover_cur = (sales_cur / ar_cur) if ar_cur != 0 else 0
        ar_turnover_pri = (sales_pri / ar_pri) if ar_pri != 0 else 0
        
        days_inv_cur = 365 / inv_turnover_cur if inv_turnover_cur != 0 else 0
        days_ar_cur = 365 / ar_turnover_cur if ar_turnover_cur != 0 else 0
        days_ap_cur = 365 / ((cogs_cur / ap_cur) if ap_cur != 0 else 1)
        ccc_cur = (days_inv_cur + days_ar_cur) - days_ap_cur
        
        days_inv_pri = 365 / inv_turnover_pri if inv_turnover_pri != 0 else 0
        days_ar_pri = 365 / ar_turnover_pri if ar_turnover_pri != 0 else 0
        days_ap_pri = 365 / ((cogs_pri / ap_pri) if ap_pri != 0 else 1)
        ccc_pri = (days_inv_pri + days_ar_pri) - days_ap_pri

        fixed_cost_cur = max((sales_cur - gp_cur) - op_cur, sales_cur * 0.2)
        fixed_cost_pri = max((sales_pri - gp_pri) - op_pri, sales_pri * 0.2)
        
        cm_cur = sales_cur - cogs_cur
        cm_pri = sales_pri - cogs_pri
        
        cm_rate_cur = (cm_cur / sales_cur) if sales_cur != 0 else 0
        cm_rate_pri = (cm_pri / sales_pri) if sales_pri != 0 else 0
        
        bep_sales_cur = (fixed_cost_cur / cm_rate_cur) if cm_rate_cur != 0 else 0
        bep_sales_pri = (fixed_cost_pri / cm_rate_pri) if cm_rate_pri != 0 else 0

        shares_out = market_metrics.get('sharesOutstanding', 1.0)
        eps_cur = market_metrics.get('trailingEps', 0.0) or (net_cur / shares_out)
        eps_pri = net_pri / shares_out if shares_out else 0.0
        bps_cur = market_metrics.get('bookValue', 0.0) or (te_cur / shares_out)
        
        cur_price = market_metrics.get('currentPrice', 0.0)
        per_cur = market_metrics.get('trailingPE', 0.0) or (cur_price / eps_cur if eps_cur != 0 else 0.0)
        pbr_cur = market_metrics.get('priceToBook', 0.0) or (cur_price / bps_cur if bps_cur != 0 else 0.0)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📌 Overview", "🏢 Balance Sheet", "📊 Ratios", "📉 Valuation", "📰 News", "📝 종합의견 (Report)"
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

        with tab2:
            st.subheader("Balance Sheet Summary")
            bs_summary_data = {
                "Component": ["💵 Cash", "🤝 Receivables", "📦 Inventories", "🗂️ CURRENT ASSETS", "🏢 PPE", "💎 TOTAL ASSETS", "🛑 CURRENT LIAB", "💼 TOTAL LIABILITIES", "📈 Retained Earnings", "🧬 TOTAL EQUITY"],
                f"Cur ({current_year})": [f"{cash_cur:,.0f}", f"{ar_cur:,.0f}", f"{inv_cur:,.0f}", f"{ca_cur:,.0f}", f"{ppe_cur:,.0f}", f"{ta_cur:,.0f}", f"{cl_cur:,.0f}", f"{tl_cur:,.0f}", f"{re_cur:,.0f}", f"{te_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{cash_pri:,.0f}", f"{ar_pri:,.0f}", f"{inv_pri:,.0f}", f"{ca_pri:,.0f}", f"{ppe_pri:,.0f}", f"{ta_pri:,.0f}", f"{cl_pri:,.0f}", f"{tl_pri:,.0f}", f"{re_pri:,.0f}", f"{te_pri:,.0f}"],
                "Var": [calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(ca_cur, ca_pri), calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(ta_cur, ta_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(tl_cur, tl_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)]
            }
            st.dataframe(pd.DataFrame(bs_summary_data), use_container_width=True, hide_index=True)

        with tab3:
            st.subheader("Liquidity & Cycles")
            ratio_data = {
                "Metric Indicator": [" 부채비율", " 유동비율", " 당좌비율", " 재고자산회전율", " 매출채권회전율", " 현금전환주기"],
                f"Cur ({current_year})": [f"{debt_to_equity_cur:.1f}%", f"{current_ratio_cur:.2f}", f"{quick_ratio_cur:.2f}", f"{inv_turnover_cur:.1f}x", f"{ar_turnover_cur:.1f}x", f"{ccc_cur:.1f} Days"],
                f"Pri ({prior_year})": [f"{debt_to_equity_pri:.1f}%", f"{current_ratio_pri:.2f}", f"{quick_ratio_pri:.2f}", f"{inv_turnover_pri:.1f}x", f"{ar_turnover_pri:.1f}x", f"{ccc_pri:.1f} Days"],
                "Delta": [f"{debt_to_equity_cur - debt_to_equity_pri:+.1f}%p", f"{current_ratio_cur - current_ratio_pri:+.2f}", f"{quick_ratio_cur - quick_ratio_pri:+.2f}", f"{inv_turnover_cur - inv_turnover_pri:+.1f}x", f"{ar_turnover_cur - ar_turnover_pri:+.1f}x", f"{ccc_cur - ccc_pri:+.1f} D"]
            }
            st.dataframe(pd.DataFrame(ratio_data), use_container_width=True, hide_index=True)

        with tab4:
            st.subheader("CVP & Valuation Multiples")
            val_lev_data = {
                "Parameter Item": [" 공헌이익률", " 손익분기점 매출", " 주당순이익(EPS)", " 주당순자산(BPS)", " PER", " PBR"],
                f"Cur ({current_year})": [f"{cm_rate_cur*100:.1f}%", f"{bep_sales_cur:,.0f}", f"{eps_cur:,.2f}", f"{bps_cur:,.2f}", f"{per_cur:.1f}x", f"{pbr_cur:.1f}x"],
                f"Pri ({prior_year})": [f"{cm_rate_pri*100:.1f}%", f"{bep_sales_pri:,.0f}", f"{eps_pri:,.2f}", "N/A", "N/A", "N/A"],
                "Description": ["CVP Shift", "BEP Growth", calc_growth_raw(eps_cur, eps_pri), "Capital", "Multiples", "Multiples"]
            }
            st.dataframe(pd.DataFrame(val_lev_data), use_container_width=True, hide_index=True)
            
        with tab5:
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

        with tab6:
            st.header("📝 실시간 재무·주가 종합 진단 보고서")
            st.caption(f"대상 기업: {comp_name} ({ticker_final})")
            st.markdown("---")
            
            high_52 = market_metrics.get('fiftyTwoWeekHigh', 1.0)
            low_52 = market_metrics.get('fiftyTwoWeekLow', 1.0)
            avg_50 = market_metrics.get('fiftyDayAverage', 1.0)
            price_location_pct = ((cur_price - low_52) / (high_52 - low_52)) * 100 if (high_52 - low_52) != 0 else 50.0
                
            report_col1, report_col2 = st.columns(2)
            
            with report_col1:
                st.subheader("🔍 1. 최근 주가 수준 및 밸류에이션 평가")
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
                * **멀티플 분석:** 현재 PER 지표는 **{per_cur:.1f}x**, PBR 지표는 **{pbr_cur:.1f}x** 수준입니다. 주당순자산가치(${bps_cur:,.2f}) 대비 시장 프리미엄이 얼마나 형성되어 있는지 체크해 보세요.
                """)
                
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
        st.warning("📊 Not enough historical data to compare Current vs Prior periods.")
