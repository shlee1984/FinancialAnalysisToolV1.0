import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests

# 1. 웹 페이지 기본 설정 및 모바일 맞춤형 CSS 주입
st.set_page_config(page_title="Corporate Financial Analysis Tool", layout="wide")

st.markdown("""
    <style>
    /* 전체 폰트 스케일링 최적화 */
    html, body, [data-testid="stMarkdownContainer"] {
        font-size: 15px !important;
    }
    
    /* 모바일(화면 너비 768px 이하)에서 글자 크기 및 테이블 가동성 조정 */
    @media (max-width: 768px) {
        .stDataFrame div {
            font-size: 12px !important;
        }
        h1 {
            font-size: 1.8rem !important;
        }
        h2 {
            font-size: 1.4rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
        .stButton button {
            padding: 0.25rem 0.5rem !important;
            font-size: 13px !important;
        }
    }
    </style>
""", unsafe_allow_html=True)

# --- 타이틀 및 서브 타이틀 ---
st.title("📊 Corporate Financial Analysis Tool")
st.caption("Advanced Financial Diagnostics System - Comprehensive 10-Q/10-K Structural Mapping")
st.markdown("---")

# --- 관심종목(Watchlist) 세션 상태 초기화 ---
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT"]

# --- 검색창 영역 메인 상단 배치 ---
search_col1, search_col2 = st.columns([1, 2])

with search_col1:
    search_type = st.radio("Select Search Method:", ["By Ticker", "By Company Name"], horizontal=True)

ticker_final = "AAPL"  # 기본값

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
            except Exception as e:
                st.error("⚠️ Error searching company name.")

# --- 메인 화면 상단 "My Watchlist" 수평 배치 ---
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


# --- 야후 파이낸스 차단 우회용 가상 세션 헤더 설정 ---
def get_highly_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive'
    })
    return session


# --- 캐싱 시스템 (UnserializableReturnValueError 현상 해결) ---
@st.cache_resource(ttl=300)
def load_financial_data(ticker_symbol):
    try:
        secure_session = get_highly_secure_session()
        stock = yf.Ticker(ticker_symbol, session=secure_session)
        
        balance_sheet = stock.balance_sheet
        financials = stock.financials
        
        if balance_sheet is None or balance_sheet.empty or financials is None or financials.empty:
            balance_sheet = stock.quarterly_balance_sheet
            financials = stock.quarterly_financials
            if balance_sheet is None or balance_sheet.empty or financials is None or financials.empty:
                return None, None, {}, ticker_symbol, False
            
        try:
            info_dict = stock.info
            comp_name = info_dict.get('longName', ticker_symbol)
        except:
            info_dict = {}
            comp_name = ticker_symbol
        
        market_metrics = {
            'trailingEps': info_dict.get('trailingEps', 0.0),
            'forwardEps': info_dict.get('forwardEps', 0.0),
            'bookValue': info_dict.get('bookValue', 0.0),
            'sharesOutstanding': info_dict.get('sharesOutstanding', 1.0),
            'trailingPE': info_dict.get('trailingPE', 0.0),
            'priceToBook': info_dict.get('priceToBook', 0.0),
            'currentPrice': info_dict.get('currentPrice', 1.0),
            'enterpriseToRevenue': info_dict.get('enterpriseToRevenue', 0.0),
            'enterpriseToEbitda': info_dict.get('enterpriseToEbitda', 0.0)
        }
        
        return balance_sheet, financials, market_metrics, comp_name, True
    except Exception as e:
        return None, None, {}, ticker_symbol, False

# 데이터 로드 실행
balance_sheet, financials, market_metrics, comp_name, success = load_financial_data(ticker_final)

if not success or balance_sheet is None or balance_sheet.empty:
    st.error(f"⚠️ Could not find sufficient financial data for '{ticker_final}'. 야후 파이낸스 서버 보호막 작동으로 응답이 일시 차단되었습니다. 다른 관심종목 단추를 터치하시거나 잠시 후 페이지를 새로고침 해주세요.")
else:
    # --- 관심종목 추가/제거 컨트롤 ---
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.subheader(f"📈 {comp_name} ({ticker_final})")
    
    with head_col2:
        if ticker_final in st.session_state.watchlist:
            if st.button("❌ Remove Watchlist", use_container_width=True):
                st.session_state.watchlist.remove(ticker_final)
                if "selected_ticker" in st.session_state:
                    del st.session_state["selected_ticker"]
                st.rerun()
        else:
            if len(st.session_state.watchlist) < 10:
                if st.button("⭐ Add Watchlist", use_container_width=True):
                    st.session_state.watchlist.append(ticker_final)
                    st.rerun()

    if balance_sheet.shape[1] >= 2 and financials.shape[1] >= 2:
        current_year = balance_sheet.columns[0].strftime('%Y')
        prior_year = balance_sheet.columns[1].strftime('%Y')
        
        # Robust 데이터 추출 함수
        def get_row_values_robust(df, keys_list):
            idx_clean = {str(k).strip().lower(): k for k in df.index}
            for key in keys_list:
                key_lower = str(key).strip().lower()
                if key_lower in idx_clean:
                    vals = df.loc[idx_clean[key_lower]].values
                    if len(vals) >= 2:
                        try:
                            v1 = float(vals[0]) if not np.isnan(vals[0]) else 0.0
                            v2 = float(vals[1]) if not np.isnan(vals[1]) else 0.0
                            return v1, v2
                        except:
                            pass
            return 0.0, 0.0

        def calc_growth_raw(current, prior):
            if prior and prior != 0:
                return f"{((current - prior) / prior) * 100:.1f}%"
            return "N/A"

        def display_centered_table(df):
            st.dataframe(df, use_container_width=True, hide_index=True)

        # --- 데이터 매핑 및 연산 ---
        sales_cur, sales_pri = get_row_values_robust(financials, ['Total Revenue', 'Revenue', 'Operating Revenue'])
        cogs_cur, cogs_pri = get_row_values_robust(financials, ['Cost Of Revenue', 'Cost of Goods Sold', 'CostofRevenue'])
        gp_cur, gp_pri = get_row_values_robust(financials, ['Gross Profit'])
        if gp_cur == 0 and sales_cur != 0: 
            gp_cur, gp_pri = sales_cur - cogs_cur, sales_pri - cogs_pri
            
        sga_cur, sga_pri = get_row_values_robust(financials, ['Selling General And Administrative', 'Selling General Administrative'])
        op_cur, op_pri = get_row_values_robust(financials, ['Operating Income', 'Operating Income Status', 'EBIT'])
        
        op_rev_cur, op_rev_pri = get_row_values_robust(financials, ['Total Non Operating Income Expense Summary', 'Non Operating Income Expenses'])
        op_exp_cur, op_exp_pri = get_row_values_robust(financials, ['Interest Expense', 'Interest Expense Supplemental Data'])
        
        ebitda_cur, ebitda_pri = get_row_values_robust(financials, ['Normalized EBITDA', 'EBITDA'])
        ebit_cur, ebit_pri = get_row_values_robust(financials, ['EBIT', 'Operating Income'])
        
        tax_cur, tax_pri = get_row_values_robust(financials, ['Tax Provision', 'Income Tax Expense'])
        net_cur, net_pri = get_row_values_robust(financials, ['Net Income', 'Net Income Common Stockholders'])
        
        cash_cur, cash_pri = get_row_values_robust(balance_sheet, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Cash'])
        st_inv_cur, st_inv_pri = get_row_values_robust(balance_sheet, ['Other Short Term Investments', 'Available For Sale Securities'])
        ar_cur, ar_pri = get_row_values_robust(balance_sheet, ['Receivables', 'Accounts Receivable', 'Gross Accounts Receivable'])
        allowance_cur, allowance_pri = get_row_values_robust(balance_sheet, ['Allowance For Doubtful Accounts Receivable'])
        prepaid_cur, prepaid_pri = get_row_values_robust(balance_sheet, ['Prepaid Assets', 'Other Current Assets'])
        inv_cur, inv_pri = get_row_values_robust(balance_sheet, ['Inventory', 'Gross Inventory', 'Inventories'])
        
        ca_cur, ca_pri = get_row_values_robust(balance_sheet, ['Current Assets', 'Total Current Assets'])
        lt_inv_cur, lt_inv_pri = get_row_values_robust(balance_sheet, ['Long Term Equity Investments', 'Investment Properties'])
        ppe_cur, ppe_pri = get_row_values_robust(balance_sheet, ['Properties', 'Net PPE', 'Property Plant And Equipment'])
        intangible_cur, intangible_pri = get_row_values_robust(balance_sheet, ['Goodwill And Other Intangible Assets', 'Intangible Assets'])
        other_nca_cur, other_nca_pri = get_row_values_robust(balance_sheet, ['Other Non Current Assets'])
        nca_cur, nca_pri = get_row_values_robust(balance_sheet, ['Total Non Current Assets', 'Non Current Assets'])
        ta_cur, ta_pri = get_row_values_robust(balance_sheet, ['Total Assets', 'Assets'])
        
        cl_cur, cl_pri = get_row_values_robust(balance_sheet, ['Current Liabilities', 'Total Current Liabilities'])
        ap_cur, ap_pri = get_row_values_robust(balance_sheet, ['Payables And Accrued Expenses', 'Accounts Payable'])
        ncl_cur, ncl_pri = get_row_values_robust(balance_sheet, ['Total Non Current Liabilities Net Minority Interest', 'Non Current Liabilities'])
        tl_cur, tl_pri = get_row_values_robust(balance_sheet, ['Total Liabilities Net Minority Interest', 'Total Liabilities', 'Liabilities'])
        
        cap_stock_cur, cap_stock_pri = get_row_values_robust(balance_sheet, ['Capital Stock', 'Common Stock'])
        additional_cap_cur, additional_cap_pri = get_row_values_robust(balance_sheet, ['Surplus Capital', 'Capital Surplus'])
        re_cur, re_pri = get_row_values_robust(balance_sheet, ['Retained Earnings'])
        te_cur, te_pri = get_row_values_robust(balance_sheet, ['Stockholders Equity', 'Total Stockholders Equity', 'Equity'])

        # --- 주요 재무 지표 연산 ---
        sales_growth_val = ((sales_cur - sales_pri) / sales_pri * 100) if sales_pri != 0 else 0
        net_growth_val = ((net_cur - net_pri) / net_pri * 100) if net_pri != 0 else 0
        
        debt_to_equity_cur = (tl_cur / te_cur * 100) if te_cur != 0 else 0
        debt_to_equity_pri = (tl_pri / te_pri * 100) if te_pri != 0 else 0
        
        current_ratio_cur = (ca_cur / cl_cur) if cl_cur != 0 else 0
        current_ratio_pri = (ca_pri / cl_pri) if cl_pri != 0 else 0
        
        quick_ratio_cur = ((ca_cur - inv_cur) / cl_cur) if cl_cur != 0 else 0
        quick_ratio_pri = ((ca_pri - inv_pri) / cl_pri) if cl_pri != 0 else 0
        
        cash_ratio_cur = (cash_cur / cl_cur) if cl_cur != 0 else 0
        cash_ratio_pri = (cash_pri / cl_pri) if cl_pri != 0 else 0
        
        cash_to_asset_cur = (cash_cur / ta_cur * 100) if ta_cur != 0 else 0
        cash_to_asset_pri = (cash_pri / ta_pri * 100) if ta_pri != 0 else 0
        
        inv_turnover_cur = (cogs_cur / inv_cur) if inv_cur != 0 else 0
        inv_turnover_pri = (cogs_pri / inv_pri) if inv_pri != 0 else 0
        
        ar_turnover_cur = (sales_cur / ar_cur) if ar_cur != 0 else 0
        ar_turnover_pri = (sales_pri / ar_cur) if ar_pri != 0 else 0
        
        ap_turnover_cur = (cogs_cur / ap_cur) if ap_cur != 0 else 0
        ap_turnover_pri = (cogs_pri / ap_pri) if ap_pri != 0 else 0
        
        days_inv_cur = 365 / inv_turnover_cur if inv_turnover_cur != 0 else 0
        days_ar_cur = 365 / ar_turnover_cur if ar_turnover_cur != 0 else 0
        days_ap_cur = 365 / ap_turnover_cur if ap_turnover_cur != 0 else 0
        stop_cycle_cur = days_inv_cur + days_ar_cur
        ccc_cur = stop_cycle_cur - days_ap_cur

        days_inv_pri = 365 / inv_turnover_pri if inv_turnover_pri != 0 else 0
        days_ar_pri = 365 / ar_turnover_pri if ar_turnover_pri != 0 else 0
        days_ap_pri = 365 / ap_turnover_pri if ap_turnover_pri != 0 else 0
        stop_cycle_pri = days_inv_pri + days_ar_pri
        ccc_pri = stop_cycle_pri - days_ap_pri

        fixed_cost_cur = (sales_cur - gp_cur) - op_cur
        fixed_cost_pri = (sales_pri - gp_pri) - op_pri
        if fixed_cost_cur <= 0: fixed_cost_cur = sales_cur * 0.25
        if fixed_cost_pri <= 0: fixed_cost_pri = sales_pri * 0.25
        
        # [해결 포인트] 사전 차단 및 오타 처리 완료
        cm_cur = sales_cur - cogs_cur
        cm_pri = sales_pri - cogs_pri
        
        cm_rate_cur = (cm_cur / sales_cur) if sales_cur != 0 else 0
        cm_rate_pri = (cm_pri / sales_pri) if sales_pri != 0 else 0
        
        bep_sales_cur = (fixed_cost_cur / cm_rate_cur) if cm_rate_cur != 0 else 0
        bep_sales_pri = (fixed_cost_pri / cm_rate_pri) if cm_rate_pri != 0 else 0
        mos_cur = ((sales_cur - bep_sales_cur) / sales_cur * 100) if sales_cur != 0 else 0

        dol_cur = (cm_cur / op_cur) if op_cur != 0 else 1.0
        dol_pri = ((sales_pri - cogs_pri) / op_pri) if op_pri != 0 else 1.0
        dfl_cur = (op_cur / (op_cur - max(0, op_exp_cur))) if (op_cur - op_exp_cur) != 0 else 1.0
        dfl_pri = (op_pri / (op_pri - max(0, op_exp_pri))) if (op_pri - op_exp_pri) != 0 else 1.0
        
        # [해결 포인트] dtl_pri NameError 오타 수정 완료
        dtl_cur = dol_cur * dfl_cur
        dtl_pri = dol_pri * dfl_pri

        shares_out = market_metrics.get('sharesOutstanding', 1.0)
        eps_cur = market_metrics.get('trailingEps', 0.0) or (net_cur / shares_out)
        eps_pri = market_metrics.get('forwardEps', 0.0) or (net_pri / shares_out)
        bps_cur = market_metrics.get('bookValue', 0.0) or (te_cur / shares_out)
        sps_cur = (sales_cur / shares_out) if shares_out else 0.0
        sps_pri = (sales_pri / shares_out) if shares_out else 0.0
        
        per_cur = market_metrics.get('trailingPE', 0.0) or (market_metrics.get('currentPrice', 1.0) / eps_cur if eps_cur != 0 else 0.0)
        pbr_cur = market_metrics.get('priceToBook', 0.0) or (market_metrics.get('currentPrice', 1.0) / bps_cur if bps_cur != 0 else 0.0)

        # --- 4개 탭 화면 구성 ---
        tab1, tab2, tab3, tab4 = st.tabs(["📌 Overview", "🏢 Balance Sheet", "📊 Ratios", "📉 Valuation"])
        
        with tab1:
            st.subheader("Earnings & Comprehensive Income")
            earnings_data = {
                "Item": ["Sales", "COGS", "Gross Profit", "SG&A", "Operating Inc.", "EBITDA", "Net Income"],
                f"Cur ({current_year})": [f"{sales_cur:,.0f}", f"{cogs_cur:,.0f}", f"{gp_cur:,.0f}", f"{sga_cur:,.0f}", f"{op_cur:,.0f}", f"{ebitda_cur:,.0f}", f"{net_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{sales_pri:,.0f}", f"{cogs_pri:,.0f}", f"{gp_pri:,.0f}", f"{sga_pri:,.0f}", f"{op_pri:,.0f}", f"{ebitda_pri:,.0f}", f"{net_pri:,.0f}"],
                "Growth": [calc_growth_raw(sales_cur, sales_pri), calc_growth_raw(cogs_cur, cogs_pri), calc_growth_raw(gp_cur, gp_pri), calc_growth_raw(sga_cur, sga_pri), calc_growth_raw(op_cur, op_pri), calc_growth_raw(ebitda_cur, ebitda_pri), calc_growth_raw(net_cur, net_pri)]
            }
            display_centered_table(pd.DataFrame(earnings_data))
            
            st.subheader("Key Trend Chart")
            chart_data = pd.DataFrame({
                'Current': [sales_cur, op_cur, net_cur],
                'Prior': [sales_pri, op_pri, net_pri]
            }, index=['Sales', 'Operating', 'Net Income'])
            st.bar_chart(chart_data)

            st.markdown("---")
            st.header("📋 종합 분석 결과 및 재무 검토 의견")
            
            if sales_growth_val > 0 and net_growth_val > 0:
                st.success(f"📈 **성장성 및 수익성:** 전년 대비 매출({sales_growth_val:.1f}%)과 순이익({net_growth_val:.1f}%)이 개선되는 구조입니다.")
            elif sales_growth_val > 0 and net_growth_val <= 0:
                st.warning(f"⚠️ **성장성 및 수익성:** 매출은 {sales_growth_val:.1f}% 증가했으나 순이익은 감소세입니다.")
            else:
                st.error(f"📉 **성장성 및 수익성:** 매출과 순이익이 모두 역성장 국면입니다.")
                
            if debt_to_equity_cur <= 100 and current_ratio_cur >= 1.5:
                st.success(f"🛡️ **안정성:** 부채비율({debt_to_equity_cur:.1f}%)이 우수하고 유동비율({current_ratio_cur:.2f}) 구조가 견고합니다.")
            elif debt_to_equity_cur > 150:
                st.error(f"🚨 **안정성:** 부채비율이 {debt_to_equity_cur:.1f}%로 위험선을 상회합니다.")
            else:
                st.warning(f"ℹ️ **안정성:** 재무 지표는 전반적으로 평이한 수준입니다.")

            st.subheader("📑 재무 검토 의견 (Financial Review)")
            opinion_text = f"""
            **{comp_name}** 재무 의견 요약:
            
            1. 당기 매출총이익은 **{gp_cur:,.0f}** 규모이며, 비용 관리 효율성이 중요합니다.
            2. 현금전환주기(CCC) **{ccc_cur:.1f}일** 관리가 자금 유동성 방어에 미치는 영향을 모니터링해야 합니다.
            3. 당기 추정 고정비는 **{fixed_cost_cur:,.0f}** 수준으로 파악됩니다.
            """
            st.info(opinion_text)

        with tab2:
            st.subheader("Balance Sheet Summary")
            bs_summary_data = {
                "Component": ["💵 Cash", "🤝 Receivables", "📦 Inventories", "🗂️ CURRENT ASSETS", "🏢 PPE", "💎 TOTAL ASSETS", "🛑 CURRENT LIAB", "💼 TOTAL LIABILITIES", "📈 Retained Earnings", "🧬 TOTAL EQUITY"],
                f"Cur ({current_year})": [f"{cash_cur:,.0f}", f"{ar_cur:,.0f}", f"{inv_cur:,.0f}", f"{ca_cur:,.0f}", f"{ppe_cur:,.0f}", f"{ta_cur:,.0f}", f"{cl_cur:,.0f}", f"{tl_cur:,.0f}", f"{re_cur:,.0f}", f"{te_cur:,.0f}"],
                f"Pri ({prior_year})": [f"{cash_pri:,.0f}", f"{ar_pri:,.0f}", f"{inv_pri:,.0f}", f"{ca_pri:,.0f}", f"{ppe_pri:,.0f}", f"{ta_pri:,.0f}", f"{cl_pri:,.0f}", f"{tl_pri:,.0f}", f"{re_pri:,.0f}", f"{te_pri:,.0f}"],
                "Var": [calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(ca_cur, ca_pri), calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(ta_cur, ta_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(tl_cur, tl_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)]
            }
            display_centered_table(pd.DataFrame(bs_summary_data))

        with tab3:
            st.subheader("Liquidity & Cycles")
            ratio_data = {
                "Metric Indicator": [" 부채비율", " 유동비율", " 당좌비율", " 재고자산회전율", " 매출채권회전율", " 현금전환주기"],
                f"Cur ({current_year})": [f"{debt_to_equity_cur:.1f}%", f"{current_ratio_cur:.2f}", f"{quick_ratio_cur:.2f}", f"{inv_turnover_cur:.1f}x", f"{ar_turnover_cur:.1f}x", f"{ccc_cur:.1f} Days"],
                f"Pri ({prior_year})": [f"{debt_to_equity_pri:.1f}%", f"{current_ratio_pri:.2f}", f"{quick_ratio_pri:.2f}", f"{inv_turnover_pri:.1f}x", f"{ar_turnover_pri:.1f}x", f"{ccc_pri:.1f} Days"],
                "Delta": [f"{debt_to_equity_cur - debt_to_equity_pri:+.1f}%p", f"{current_ratio_cur - current_ratio_pri:+.2f}", f"{quick_ratio_cur - quick_ratio_pri:+.2f}", f"{inv_turnover_cur - inv_turnover_pri:+.1f}x", f"{ar_turnover_cur - ar_turnover_pri:+.1f}x", f"{ccc_cur - ccc_pri:+.1f} D"]
            }
            display_centered_table(pd.DataFrame(ratio_data))

        with tab4:
            st.subheader("CVP & Valuation Multiples")
            val_lev_data = {
                "Parameter Item": [" 공헌이익률", " 손익분기점 매출", " 주당순이익(EPS)", " 주당순자산(BPS)", " PER", " PBR"],
                f"Cur ({current_year})": [f"{cm_rate_cur*100:.1f}%", f"{bep_sales_cur:,.0f}", f"{eps_cur:,.2f}", f"{bps_cur:,.2f}", f"{per_cur:.1f}x", f"{pbr_cur:.1f}x"],
                f"Pri ({prior_year})": [f"{cm_rate_pri*100:.1f}%" if cm_rate_pri else "N/A", f"{bep_sales_pri:,.0f}" if bep_sales_pri else "N/A", f"{eps_pri:,.2f}", "N/A", "N/A", "N/A"],
                "Description": ["CVP Shift", "BEP Growth", calc_growth_raw(eps_cur, eps_pri), "Capital", "Multiples", "Multiples"]
            }
            display_centered_table(pd.DataFrame(val_lev_data))
            
    else:
        st.warning("📊 Not enough historical data to compare Current vs Prior periods.")
