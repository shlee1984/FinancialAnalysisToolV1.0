import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 웹 페이지 기본 설정
st.set_page_config(page_title="Corporate Financial Analysis Tool", layout="wide")

st.title("📊 Corporate Financial Analysis Tool")
st.caption("Advanced Financial Diagnostics System - Comprehensive 10-Q/10-K Structural Mapping")
st.markdown("---")

# --- 관심종목(Watchlist) 세션 상태 초기화 ---
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AAPL", "TSLA", "NVDA", "MSFT"]

# 2. 사이드바 - 검색 및 데이터 로드 설정
st.sidebar.header("Search Configuration")
search_type = st.sidebar.radio("Select Search Method:", ["By Ticker", "By Company Name"])

ticker_final = "AAPL"  # 기본값

if search_type == "By Ticker":
    ticker_input = st.sidebar.text_input("Enter US Stock Ticker:", "AAPL").upper().strip()
    ticker_final = ticker_input
else:
    company_input = st.sidebar.text_input("Enter Company Name (e.g., Apple, Tesla, Nvidia):", "Apple").strip()
    
    if company_input:
        with st.sidebar.spinner("Searching for ticker..."):
            try:
                search_results = yf.Search(company_input, max_results=5).quotes
                us_quotes = [q for q in search_results if q.get('exchange') in ['NMS', 'NYQ', 'ASE', 'BTS', 'NGM', 'NCM']]
                target_quotes = us_quotes if us_quotes else search_results
                
                if target_quotes:
                    options = {f"{q['symbol']} - {q.get('longname', q.get('shortname', 'Unknown'))} ({q.get('exchange', '')})": q['symbol'] for q in target_quotes}
                    selected_display = st.sidebar.selectbox("Select the exact company:", list(options.keys()))
                    ticker_final = options[selected_display]
                else:
                    st.sidebar.error("❌ No companies found. Try another keyword.")
            except Exception as e:
                st.sidebar.error("⚠️ Error searching company name.")

# --- 사이드바 관심종목 클릭 처리 ---
st.sidebar.markdown("---")
st.sidebar.subheader("⭐ My Watchlist (Max 10)")

for ticker in st.session_state.watchlist[:10]:
    if st.sidebar.button(f"📌 {ticker}", key=f"wl_{ticker}", use_container_width=True):
        st.session_state["selected_ticker"] = ticker

if "selected_ticker" in st.session_state and st.session_state["selected_ticker"] in st.session_state.watchlist:
    ticker_final = st.session_state["selected_ticker"]


# --- [수정] 야후 파이낸스 차단 우회 및 직렬화 에러를 방지하는 데이터 로더 ---
@st.cache_data(ttl=3600)
def load_financial_data(ticker_symbol):
    try:
        # 안전하게 Ticker 데이터를 가져오기 위해 구조화
        stock = yf.Ticker(ticker_symbol)
        
        # 순수 데이터프레임만 캐싱에 저장 (객체 자체를 리턴하지 않음)
        balance_sheet = stock.balance_sheet
        financials = stock.financials
        
        # info 딕셔너리 안전하게 로드
        info_dict = stock.info
        comp_name = info_dict.get('longName', ticker_symbol)
        
        # 필요한 마켓 멀티플 지표들 추출
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
        
        if balance_sheet.empty or financials.empty:
            return None, None, {}, ticker_symbol, False
            
        return balance_sheet, financials, market_metrics, comp_name, True
    except Exception as e:
        return None, None, {}, ticker_symbol, False

balance_sheet, financials, market_metrics, comp_name, success = load_financial_data(ticker_final)

if not success or balance_sheet is None or balance_sheet.empty:
    st.error(f"⚠️ Could not find sufficient financial data for '{ticker_final}'. Please verify the ticker or try again later.")
else:
    # --- 관심종목 추가/제거 컨트롤 ---
    head_col1, head_col2 = st.columns([3, 1])
    with head_col1:
        st.header(f"{comp_name} ({ticker_final}) - Financial Analysis")
    
    with head_col2:
        if ticker_final in st.session_state.watchlist:
            if st.button("❌ Remove from Watchlist", use_container_width=True):
                st.session_state.watchlist.remove(ticker_final)
                if "selected_ticker" in st.session_state:
                    del st.session_state["selected_ticker"]
                st.rerun()
        else:
            if len(st.session_state.watchlist) >= 10:
                st.caption("⚠️ Watchlist is full (Max 10).")
            else:
                if st.button("⭐ Add to Watchlist", use_container_width=True):
                    st.session_state.watchlist.append(ticker_final)
                    st.rerun()

    if balance_sheet.shape[1] >= 2 and financials.shape[1] >= 2:
        current_year = balance_sheet.columns[0].strftime('%Y-%m-%d')
        prior_year = balance_sheet.columns[1].strftime('%Y-%m-%d')
        
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
                return f"{((current - prior) / prior) * 100:.2f}%"
            return "N/A"

        def display_centered_table(df):
            styled_df = df.style.set_properties(**{
                'text-align': 'center',
                'vertical-align': 'middle'
            })
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

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
        dtl_cur = dol_cur * dfl_cur
        dtl_pri = dol_pri * dfl_pri

        # 사전 추출된 market_metrics 딕셔너리 활용
        shares_out = market_metrics.get('sharesOutstanding', 1.0)
        eps_cur = market_metrics.get('trailingEps', 0.0) or (net_cur / shares_out)
        eps_pri = market_metrics.get('forwardEps', 0.0) or (net_pri / shares_out)
        bps_cur = market_metrics.get('bookValue', 0.0) or (te_cur / shares_out)
        sps_cur = (sales_cur / shares_out) if shares_out else 0.0
        sps_pri = (sales_pri / shares_out) if shares_out else 0.0
        
        per_cur = market_metrics.get('trailingPE', 0.0) or (market_metrics.get('currentPrice', 1.0) / eps_cur if eps_cur != 0 else 0.0)
        pbr_cur = market_metrics.get('priceToBook', 0.0) or (market_metrics.get('currentPrice', 1.0) / bps_cur if bps_cur != 0 else 0.0)
        ev_to_sales = market_metrics.get('enterpriseToRevenue', 0.0)
        ev_to_ebitda = market_metrics.get('enterpriseToEbitda', 0.0)

        # --- 4개 탭 화면 구성 ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "📌 Overview & Detailed Earnings", 
            "🏢 Asset, Liability & Equity Structural", 
            "📊 Advanced Ratios & Conversion Cycles",
            "📉 Valuation, Marketability & Leverage"
        ])
        
        with tab1:
            st.subheader("Statement of Earnings & Comprehensive Income Detailed Analysis")
            earnings_data = {
                "Financial Statement Item": [
                    "Sales (Total Revenue / 매출액)", "Cost of Goods Sold (매출원가)", "Gross Profit (매출총이익)", 
                    "Selling, General & Administrative Expense (판관비)", "Operating Income (영업이익)",
                    "Financial / Non-Operating Revenue (영업외수익)", "Interest / Non-Operating Expense (이자비용)",
                    "EBITDA (법인세·이자·감가상각 전 영업이익)", "EBIT (법인세·이자 차감 전 영업이익)",
                    "Income Tax Expense (법인세비용)", "Net Income (당기순이익)"
                ],
                f"Current Period ({current_year})": [
                    f"{sales_cur:,.0f}", f"{cogs_cur:,.0f}", f"{gp_cur:,.0f}", f"{sga_cur:,.0f}",
                    f"{op_cur:,.0f}", f"{op_rev_cur:,.0f}", f"{op_exp_cur:,.0f}", f"{ebitda_cur:,.0f}",
                    f"{ebit_cur:,.0f}", f"{tax_cur:,.0f}", f"{net_cur:,.0f}"
                ],
                f"Prior Period ({prior_year})": [
                    f"{sales_pri:,.0f}", f"{cogs_pri:,.0f}", f"{gp_pri:,.0f}", f"{sga_pri:,.0f}",
                    f"{op_pri:,.0f}", f"{op_rev_pri:,.0f}", f"{op_exp_pri:,.0f}", f"{ebitda_pri:,.0f}",
                    f"{ebit_pri:,.0f}", f"{tax_pri:,.0f}", f"{net_pri:,.0f}"
                ],
                "Growth Rate / Var": [
                    calc_growth_raw(sales_cur, sales_pri), calc_growth_raw(cogs_cur, cogs_pri), calc_growth_raw(gp_cur, gp_pri), calc_growth_raw(sga_cur, sga_pri),
                    calc_growth_raw(op_cur, op_pri), calc_growth_raw(op_rev_cur, op_rev_pri), calc_growth_raw(op_exp_cur, op_exp_pri), calc_growth_raw(ebitda_cur, ebitda_pri),
                    calc_growth_raw(ebit_cur, ebit_pri), calc_growth_raw(tax_cur, tax_pri), calc_growth_raw(net_cur, net_pri)
                ]
            }
            display_centered_table(pd.DataFrame(earnings_data))
            
            st.subheader("Key Earnings & Profitability Trend")
            chart_data = pd.DataFrame({
                'Current Period': [sales_cur, op_cur, ebitda_cur, net_cur],
                'Prior Period': [sales_pri, op_pri, ebitda_pri, net_pri]
            }, index=['Sales', 'Operating Inc.', 'EBITDA', 'Net Income'])
            st.bar_chart(chart_data)

            st.markdown("---")
            st.header("📋 종합 분석 결과 및 재무 검토 의견")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("💡 주요 재무 지표 진단 요약")
                if sales_growth_val > 0 and net_growth_val > 0:
                    st.success(f"📈 **성장성 및 수익성:** 전년 대비 매출({sales_growth_val:.1f}%)과 순이익({net_growth_val:.1f}%)이 개선되는 건강한 구조를 보이고 있습니다.")
                elif sales_growth_val > 0 and net_growth_val <= 0:
                    st.warning(f"⚠️ **성장성 및 수익성:** 매출은 {sales_growth_val:.1f}% 증가했으나 순이익은 감소세입니다. 원가 및 판관비 통제 요인을 확인하십시오.")
                else:
                    st.error(f"📉 **성장성 및 수익성:** 매출과 순이익이 모두 역성장 국면에 위치해 있어, 대대적인 고정비 통제가 요구됩니다.")
                    
                if debt_to_equity_cur <= 100 and current_ratio_cur >= 1.5:
                    st.success(f"🛡️ **안정성:** 부채비율({debt_to_equity_cur:.1f}%)이 우수하고 유동비율({current_ratio_cur:.2f}) 구조가 견고하여 유동성 리스크가 최소화된 안정 상태입니다.")
                elif debt_to_equity_cur > 150:
                    st.error(f"🚨 **안정성:** 부채비율이 {debt_to_equity_cur:.1f}%로 위험선을 상회합니다. 자본 조달 구조 조정을 검토해야 합니다.")
                else:
                    st.warning(f"ℹ️ **안정성:** 재무 지표는 전반적으로 안정적이나, 현금성 자산의 유입 주기 추이를 모니터링할 필요가 있습니다.")

            with col2:
                st.subheader("📑 재무 검토 의견 (Financial Review Opinion)")
                opinion_text = f"""
                본 재무 검토 의견서는 **{comp_name}**의 최신 감사보고서 및 통합 다차원 재무비율 모형을 활용하여 심층 진단되었습니다.
                
                1. **수익구조 및 마진 추이:** 당기 매출총이익은 **{gp_cur:,.0f}** 규모이며, 비용 구조 측면에서 판관비의 효율성이 마진율 결정의 주요 변수로 식별됩니다.
                
                2. **운전자본 효율성 진단:** 재고자산회전주기와 매출채권회전주기를 반영한 현금전환주기(CCC) 관리가 자금 조달 스프레드 방어에 긍정적인 영향을 주고 있는지 정밀 진단이 수반되어야 합니다.
                
                3. **CVP 연계형 투자 제언:** 당기 추정 고정비 **{fixed_cost_cur:,.0f}**를 상회하는 분기점 매출 도달 능력을 갖췄으나, 경기 변동 레버리지에 대응할 수 있도록 탄력적 원가 관리를 제언합니다.
                """
                st.info(opinion_text)

        with tab2:
            st.subheader("Balance Sheet Summary & Structural Component Analysis")
            bs_summary_data = {
                "Asset / Liability / Equity Component": [
                    "💵 Cash And Cash Equivalents (현금 및 현금성자산)", "📈 Short-Term Investments (단기투자자산)",
                    "🤝 Trade Receivables (매출채권)", "📉 Allowance for Bad Debt (대손충당금 차감)",
                    "📦 Inventories (재고자산)", "📋 Prepaid & Other Quick Assets (선급금 및 기타유동)",
                    "🗂️ TOTAL CURRENT ASSETS (유동자산 총계)", "🏢 Property, Plant and Equipment (유형자산)",
                    "🧬 Intangible Assets & Goodwill (무형자산 및 영업권)", "🏛️ Long-Term Investments & Others (장기투자 및 기타비유동)",
                    "📂 TOTAL NON-CURRENT ASSETS (비유동자산 총계)", "💎 TOTAL ASSETS (자산총계)",
                    "⚠️ Trade Payables (매입채무)", "🛑 TOTAL CURRENT LIABILITIES (유동부채 총계)",
                    "🏦 TOTAL NON-CURRENT LIABILITIES (비유동부채 총계)", "💼 TOTAL LIABILITIES (부채총계)",
                    "🏛️ Common / Capital Stock (자본금)", "💰 Additional Paid-in Capital (자본잉여금)",
                    "📈 Retained Earnings (이익잉여금)", "🧬 TOTAL STOCKHOLDERS EQUITY (자본총계)"
                ],
                f"Current Period ({current_year})": [
                    f"{cash_cur:,.0f}", f"{st_inv_cur:,.0f}", f"{ar_cur:,.0f}", f"-{allowance_cur:,.0f}", f"{inv_cur:,.0f}", f"{prepaid_cur:,.0f}", f"{ca_cur:,.0f}",
                    f"{ppe_cur:,.0f}", f"{intangible_cur:,.0f}", f"{other_nca_cur:,.0f}", f"{nca_cur:,.0f}", f"{ta_cur:,.0f}",
                    f"{ap_cur:,.0f}", f"{cl_cur:,.0f}", f"{ncl_cur:,.0f}", f"{tl_cur:,.0f}",
                    f"{cap_stock_cur:,.0f}", f"{additional_cap_cur:,.0f}", f"{re_cur:,.0f}", f"{te_cur:,.0f}"
                ],
                f"Prior Period ({prior_year})": [
                    f"{cash_pri:,.0f}", f"{st_inv_pri:,.0f}", f"{ar_pri:,.0f}", f"-{allowance_pri:,.0f}", f"{inv_pri:,.0f}", f"{prepaid_pri:,.0f}", f"{ca_pri:,.0f}",
                    f"{ppe_pri:,.0f}", f"{intangible_pri:,.0f}", f"{other_nca_pri:,.0f}", f"{nca_pri:,.0f}", f"{ta_pri:,.0f}",
                    f"{ap_pri:,.0f}", f"{cl_pri:,.0f}", f"{ncl_pri:,.0f}", f"{tl_pri:,.0f}",
                    f"{cap_stock_pri:,.0f}", f"{additional_cap_pri:,.0f}", f"{re_pri:,.0f}", f"{te_pri:,.0f}"
                ],
                "Structural Variance Ratio": [
                    calc_growth_raw(cash_cur, cash_pri), calc_growth_raw(st_inv_cur, st_inv_pri), calc_growth_raw(ar_cur, ar_pri), calc_growth_raw(allowance_cur, allowance_pri), calc_growth_raw(inv_cur, inv_pri), calc_growth_raw(prepaid_cur, prepaid_pri), calc_growth_raw(ca_cur, ca_pri),
                    calc_growth_raw(ppe_cur, ppe_pri), calc_growth_raw(intangible_cur, intangible_pri), calc_growth_raw(other_nca_cur, other_nca_pri), calc_growth_raw(nca_cur, nca_pri), calc_growth_raw(ta_cur, ta_pri),
                    calc_growth_raw(ap_cur, ap_pri), calc_growth_raw(cl_cur, cl_pri), calc_growth_raw(ncl_cur, ncl_pri), calc_growth_raw(tl_cur, tl_pri),
                    calc_growth_raw(cap_stock_cur, cap_stock_pri), calc_growth_raw(additional_cap_cur, additional_cap_pri), calc_growth_raw(re_cur, re_pri), calc_growth_raw(te_cur, te_pri)
                ]
            }
            display_centered_table(pd.DataFrame(bs_summary_data))

        with tab3:
            st.subheader("Liquidity, Solvency & Activity Turning Cycles")
            ratio_data = {
                "Advanced Financial Metric Indicator": [
                    "🛡️ Debt to Equity Ratio (부채비율)", "💧 Current Ratio (유동비율)", "⚡ Quick Ratio (당좌비율)", 
                    "💵 Cash Ratio (현금비율)", "📊 Cash to Asset Ratio (현금자산총액비율)", "📦 Inventory Turnover (재고자산회전율)", 
                    "🤝 Trade Receivable Turnover (매출채권회전율)", "📈 Accounts Payable Turnover (매입채무회전율)",
                    "🔄 Operating Cycle (영업주기 - Days)", "⏱️ Cash Conversion Period (현금전환주기 - Days)"
                ],
                f"Current Period ({current_year})": [
                    f"{debt_to_equity_cur:.2f}%", f"{current_ratio_cur:.2f}", f"{quick_ratio_cur:.2f}", f"{cash_ratio_cur:.2f}", f"{cash_to_asset_cur:.2f}%",
                    f"{inv_turnover_cur:.2f}x", f"{ar_turnover_cur:.2f}x", f"{ap_turnover_cur:.2f}x", f"{stop_cycle_cur:.1f} Days", f"{ccc_cur:.1f} Days"
                ],
                f"Prior Period ({prior_year})": [
                    f"{debt_to_equity_pri:.2f}%", f"{current_ratio_pri:.2f}", f"{quick_ratio_pri:.2f}", f"{cash_ratio_pri:.2f}", f"{cash_to_asset_pri:.2f}%",
                    f"{inv_turnover_pri:.2f}x", f"{ar_turnover_pri:.2f}x", f"{ap_turnover_pri:.2f}x", f"{stop_cycle_pri:.1f} Days", f"{ccc_pri:.1f} Days"
                ],
                "Index Variance Basis": [
                    f"{debt_to_equity_cur - debt_to_equity_pri:+.2f}%p", f"{current_ratio_cur - current_ratio_pri:+.2f}", f"{quick_ratio_cur - quick_ratio_pri:+.2f}", f"{cash_ratio_cur - cash_ratio_pri:+.2f}", f"{cash_to_asset_cur - cash_to_asset_pri:+.2f}%p",
                    f"{inv_turnover_cur - inv_turnover_pri:+.2f}x", f"{ar_turnover_cur - ar_turnover_pri:+.2f}x", f"{ap_turnover_cur - ap_turnover_pri:+.2f}x", f"{stop_cycle_cur - stop_cycle_pri:+.1f} Days", f"{ccc_cur - ccc_pri:+.1f} Days"
                ]
            }
            display_centered_table(pd.DataFrame(ratio_data))

        with tab4:
            st.subheader("CVP Analysis, Structural Leverage & Market Valuation Indexes")
            val_lev_data = {
                "Valuation / Leverage Parameter Item": [
                    "🎯 Contribution Margin Rate (공헌이익률)", "🏁 BREAK-EVEN POINT (손익분기점 매출액)", "🛡️ Margin of Safety Ratio (안전한계율)",
                    "📊 Degree of Operating Leverage (DOL)", "💸 Degree of Financial Leverage (DFL)", "🧬 Degree of Total Leverage (DTL)",
                    "💵 EPS (주당순이익)", "💎 BPS (주당순자산)", "📈 SPS (주당매출액)", "📌 PER (주가수익비율)", "📐 PBR (주가순자산비율)",
                    "🏢 EV / Sales (기업가치 대비 매출액 비율)", "⚡ EV / EBITDA (기업가치 관점 현금창출지표)"
                ],
                f"Current Period ({current_year})": [
                    f"{cm_rate_cur*100:.2f}%", f"{bep_sales_cur:,.0f}", f"{mos_cur:.2f}%",
                    f"{dol_cur:.2f}", f"{dfl_cur:.2f}", f"{dtl_cur:.2f}",
                    f"{eps_cur:,.2f}", f"{bps_cur:,.2f}", f"{sps_cur:,.2f}",
                    f"{per_cur:.2f}x", f"{pbr_cur:.2f}x", f"{ev_to_sales:.2f}x", f"{ev_to_ebitda:.2f}x"
                ],
                f"Prior Period ({prior_year})": [
                    f"{calc_growth_raw(cm_cur, cm_pri)} (Var Basis)" if cm_pri != 0 else "N/A", f"{bep_sales_pri:,.0f}", "N/A",
                    f"{dol_pri:.2f}", f"{dfl_pri:.2f}", f"{dtl_pri:.2f}",
                    f"{eps_pri:,.2f}", "N/A", f"{sps_pri:,.2f}",
                    "N/A", "N/A", "N/A", "N/A"
                ],
                "Structural Variance Description": [
                    "CVP Structural Shift", calc_growth_raw(bep_sales_cur, bep_sales_pri), "Margin Buffer Delta",
                    f"{dol_cur - dol_pri:+.2f}", f"{dfl_cur - dfl_pri:+.2f}", f"{dtl_cur - dtl_pri:+.2f}",
                    calc_growth_raw(eps_cur, eps_pri), "Capital Allocation Basis", calc_growth_raw(sps_cur, sps_pri),
                    "Market Multiples Value", "Market Multiples Value", "Enterprise Multiples", "Enterprise Multiples"
                ]
            }
            display_centered_table(pd.DataFrame(val_lev_data))
            
    else:
        st.warning("📊 Not enough historical data to compare Current vs Prior periods.")
