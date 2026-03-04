import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import os
import sys

# --- CONFIG ---
st.set_page_config(page_title="Professional Risk Diagnostic Tool", layout="wide")

DATA_FILE = "data/market_data_cleaned.csv"

# --- HELPER FUNCTIONS ---
@st.cache_data
def load_data(uploaded_file=None):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    else:
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
        else:
            return pd.DataFrame(), pd.DataFrame()
            
    # Basic validation
    required_cols = ['Date', 'Asset', 'Price']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Invalid format! CSV must contain columns: {', '.join(required_cols)}")
        return pd.DataFrame(), pd.DataFrame()
        
    df['Date'] = pd.to_datetime(df['Date'])
    
    price_wide = df.pivot(index='Date', columns='Asset', values='Price').ffill().dropna()
    
    if 'Log_Return' in df.columns:
        returns_wide = df.pivot(index='Date', columns='Asset', values='Log_Return').dropna()
    else:
        returns_wide = np.log(price_wide / price_wide.shift(1)).dropna()
        
    return price_wide, returns_wide

def compute_var_95(returns):
    return np.percentile(returns, 5)

# --- MAIN APP ---
def main():
    st.markdown("""
        <style>
        .glass-card {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 1rem;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .card-green { border-top: 4px solid #22c55e; }
        .card-orange { border-top: 4px solid #f59e0b; }
        .card-red { border-top: 4px solid #ef4444; }
        .card-neutral { border-top: 4px solid #64748b; }
        .insight-banner {
            background-color: rgba(30, 41, 59, 0.8);
            border: 1px solid rgba(51, 65, 85, 0.5);
            border-radius: 0.75rem;
            padding: 1rem;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
        }
        .metric-title {
            font-size: 0.75rem;
            font-weight: 700;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.25rem;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 900;
            color: #ffffff;
            line-height: 1;
        }
        .metric-subtext {
            font-size: 0.625rem;
            color: #64748b;
            margin-top: 1rem;
            text-transform: uppercase;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🛡️ Professional Risk Diagnostic Tool")
    
    # --- SIDEBAR ---
    st.sidebar.header("Settings")
    
    uploaded_file = st.sidebar.file_uploader("Upload your tidy CSV", type=["csv"])
    price_df, log_returns = load_data(uploaded_file)

    if price_df.empty:
        st.info("Please upload a CSV file or ensure `data/market_data_cleaned.csv` exists.")
        return

    asset_options = ["All"] + list(price_df.columns)
    selected_asset = st.sidebar.selectbox("Select Asset", asset_options, index=1 if len(asset_options) > 1 else 0)
    
    rolling_window = st.sidebar.slider("Rolling Window (Returns)", 5, 252, 20)
    annualize = st.sidebar.checkbox("Annualize Volatility", value=True)
    corr_window = st.sidebar.number_input("Rolling Correlation Window", 30, 252, 60)

    # Filter data for display if not "All"
    filtered_price = price_df if selected_asset == "All" else price_df[[selected_asset]]
    filtered_returns = log_returns if selected_asset == "All" else log_returns[[selected_asset]]

    # 1. KEY INSIGHTS (Lecture 2) & PREDICTIVE RISK HEADER
    if selected_asset != "All":
        r = filtered_returns[selected_asset].dropna()
        if len(r) >= rolling_window:
            ann_factor = np.sqrt(252) if annualize else 1
            
            # Historical Stats
            hist_vol = r.std() * ann_factor
            hist_mean_vol = r.rolling(rolling_window).std().mean() * ann_factor
            
            # Current Stats
            current_vol = r.tail(rolling_window).std() * ann_factor
            var95 = compute_var_95(r)
            mean_ret = r.mean()
            std_ret = r.std()
            z_score_var = abs((var95 - mean_ret) / std_ret)
            
            # Pre-calculate z_score_vol for both insights banner and vol card
            z_score_vol = (current_vol - hist_mean_vol) / (r.rolling(rolling_window).std().std() * ann_factor) if (r.rolling(rolling_window).std().std() > 0) else 0

            # --- KEY INSIGHTS BANNER ---
            diff_pct = ((current_vol - hist_mean_vol) / hist_mean_vol) * 100
            direction = "higher" if diff_pct > 0 else "lower"
            insight_color = "#ef4444" if (current_vol > hist_mean_vol and z_score_vol > 3) else ("#f59e0b" if current_vol > hist_mean_vol else "#22c55e")
            
            st.markdown(f"""
            <div class="insight-banner">
                <div>
                    <h3 class="metric-title">Key Insights</h3>
                    <p style="font-size: 0.875rem; color: #e2e8f0; margin: 0; font-weight: 500;">
                        Market volatility is currently <strong style="color: {insight_color};">{abs(diff_pct):.1f}% {direction}</strong> than the historical mean.
                    </p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Task 3 & 5: Early Warning System & "So What?" Summary
            vol_trend = "Increasing" if current_vol > hist_mean_vol else "Stable"
            if z_score_vol > 2:
                status_color = "#ef4444"
                icon = "🚨"
                ew_title = "High Risk Regime (Fat Tails Detected)"
                ew_text = f"**Warning:** Predicted Volatility is **{vol_trend}** (Z > 2).<br>**Recommendation:** Check diversification strategies. Capital protection is advised."
            elif z_score_vol > 1:
                status_color = "#f59e0b"
                icon = "⚠️"
                ew_title = "Elevated Volatility"
                ew_text = f"**Warning:** Predicted Volatility is **{vol_trend}** (1 < Z < 2).<br>**Recommendation:** Check diversification strategies."
            else:
                status_color = "#22c55e"
                icon = "✅"
                ew_title = "Market Pulse: Normal"
                ew_text = f"Market conditions are operating within normal baseline expectations (Z < 1)."
            
            st.markdown(f"""
            <div style="padding: 1rem; border-left: 4px solid {status_color}; background: rgba(30,41,59,0.5); border-radius: 0.5rem; margin-bottom: 1.5rem;">
                <div style="display: flex; gap: 0.75rem; align-items: flex-start;">
                    <span style="font-size: 1.5rem;">{icon}</span>
                    <div>
                        <div style="font-weight: 700; color: {status_color}; text-transform: uppercase; font-size: 0.875rem;">{ew_title}</div>
                        <div style="font-size: 0.875rem; color: #e2e8f0; margin-top: 0.25rem;">{ew_text}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- PREDICTIVE RISK HEADER ---
            c1, c2, c3 = st.columns(3)
            
            with c1:
                # 1-Day VaR Forecast
                if z_score_var > 3:
                    state = "High Risk (Statistical Outlier)"
                    color = "#ef4444"
                    card_class = "card-red"
                elif z_score_var > 2:
                    state = "Elevated"
                    color = "#f59e0b"
                    card_class = "card-orange"
                else:
                    state = "Safe Zone"
                    color = "#22c55e"
                    card_class = "card-green"
                
                st.markdown(f"""
                <div class="glass-card {card_class}">
                    <div class="metric-title" title="Calculate the 95% Value at Risk using the Quantile Score method.">1-Day VaR Forecast</div>
                    <div class="metric-value">{var95*100:.2f}%</div>
                    <div class="metric-subtext">Max predicted loss tomorrow: <span style="font-weight: bold; color: {color};">{state}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with c2:
                # Volatility Regime
                if z_score_vol > 3:
                    v_state = "High Risk (Outlier Z>3)"
                    v_color = "#ef4444"
                    v_class = "card-red"
                elif z_score_vol > 2:
                    v_state = "Elevated (Z>2)"
                    v_color = "#f59e0b"
                    v_class = "card-orange"
                else:
                    v_state = "Stable"
                    v_color = "#22c55e"
                    v_class = "card-green"
                    
                st.markdown(f"""
                <div class="glass-card {v_class}">
                    <div class="metric-title">Volatility Regime</div>
                    <div class="metric-value">{current_vol*100:.2f}%</div>
                    <div class="metric-subtext">Status: <span style="font-weight: bold; color: {v_color};">{v_state}</span></div>
                </div>
                """, unsafe_allow_html=True)
                
            with c3:
                # Baseline Comparison
                last_price = filtered_price[selected_asset].iloc[-1]
                prev_price = filtered_price[selected_asset].iloc[-2]
                diff = (last_price - prev_price) / prev_price * 100
                b_color = "#22c55e" if diff >= 0 else "#ef4444"
                
                st.markdown(f"""
                <div class="glass-card card-neutral">
                    <div class="metric-title">Baseline Comparison</div>
                    <div class="metric-value" style="color: {b_color};">{last_price:.2f}</div>
                    <div class="metric-subtext">Vs Naive Forecast: <span style="font-weight: bold; color: {b_color};">{diff:.2f}%</span></div>
                </div>
                """, unsafe_allow_html=True)

            st.write("---")

    # --- TABS FOR SECTIONS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Data Quality", 
        "📈 Price & Predictive Models", 
        "📉 Distribution Diagnostics", 
        "🎲 Rolling Risk", 
        "🔗 Relationships",
        "📖 Methodology Appendix"
    ])

    # 1. Data Quality
    with tab1:
        st.header("1. Data Quality Footer & Overview")
        st.write("**Risk Monitoring Insight:** Reliable risk models require clean data.")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Date Range", f"{price_df.index[0].date()} to {price_df.index[-1].date()}")
        c2.metric("Total Observations", len(price_df))
        c3.metric("Missing Values", price_df.isna().sum().sum())
            
        st.subheader("Quality Summary / Outlier Detection (Z > 3)")
        outlier_summary = {}
        for col in log_returns.columns:
            series = log_returns[col].dropna()
            z_scores = np.abs(stats.zscore(series))
            outlier_summary[col] = (z_scores > 3).sum()
        
        st.dataframe(pd.Series(outlier_summary, name="Detected Outliers (>3σ)"))
        st.info("Note on Outliers: The outlier counts reflect returns with |z-score| > 3. These often represent real market shocks (Statistical Outliers = Danger Red).")

    # 2. Price & Predictive Models (Lecture 4)
    with tab2:
        st.header("2. Price & Return Performance")
        
        if selected_asset == "All":
            norm_price = price_df / price_df.iloc[0] * 100
            fig_price = px.line(norm_price, title="Normalized Price Time Series (Base=100)")
            st.plotly_chart(fig_price, use_container_width=True)
        else:
            # Drift Model Forecast & 95% Prediction Fan
            prices = filtered_price[selected_asset].values
            returns = filtered_returns[selected_asset].dropna().values
            dates = list(filtered_price.index)
            
            fig_price = go.Figure()
            fig_price.add_trace(go.Scatter(x=dates, y=prices, name="Historical Price", line=dict(color="#0ea5e9", width=2)))
            
            if len(returns) > 20:
                recent_rets = returns[-20:]
                std_dev = np.std(recent_rets)
                drift = np.mean(returns)
                last_price = prices[-1]
                last_date = dates[-1]
                
                future_dates = []
                expected = []
                upper = []
                lower = []
                
                for i in range(6): # 5 days into future (including day 0)
                    f_date = last_date + pd.Timedelta(days=i)
                    future_dates.append(f_date)
                    
                    exp_mean = last_price * np.exp(drift * i)
                    expected.append(exp_mean)
                    upper.append(exp_mean * np.exp(1.96 * std_dev * np.sqrt(i)))
                    lower.append(exp_mean * np.exp(-1.96 * std_dev * np.sqrt(i)))
                
                # Drift Forecast Line
                fig_price.add_trace(go.Scatter(x=future_dates, y=expected, name="Drift Forecast", 
                                               line=dict(color="rgba(255, 255, 255, 0.8)", dash="dot", width=2)))
                # 95% Prediction Fan
                fig_price.add_trace(go.Scatter(
                    x=future_dates + future_dates[::-1], 
                    y=upper + lower[::-1], 
                    fill="toself",
                    fillcolor="rgba(59, 130, 246, 0.2)", # Shaded blue area
                    line=dict(color="rgba(255,255,255,0)", width=0),
                    name="95% Prediction Interval"
                ))

            fig_price.update_layout(title=f"{selected_asset} Price History & Drift Forecast", yaxis_title="Price (USD)")
            st.plotly_chart(fig_price, use_container_width=True)

        fig_returns = px.line(filtered_returns, title=f"Daily Log Returns - {selected_asset}")
        st.plotly_chart(fig_returns, use_container_width=True)

    # 3. Distribution Diagnostics (Lecture 3)
    with tab3:
        st.header("3. Return Distribution & Diagnostics")
        st.write("**Risk Monitoring Insight:** Financial returns rarely follow a normal distribution. Fat tails indicate extreme risk.")
        
        if selected_asset == "All":
            st.warning("Please select a specific asset in the sidebar.")
        else:
            asset_returns = filtered_returns[selected_asset].dropna()
            
            c1, c2 = st.columns(2)
            with c1:
                fig_hist = px.histogram(asset_returns, nbins=50, marginal="box", title=f"Histogram of {selected_asset} Returns")
                st.plotly_chart(fig_hist, use_container_width=True)
                
            with c2:
                qq = stats.probplot(asset_returns, dist="norm")
                qq_df = pd.DataFrame({
                    "Theoretical Quantiles": qq[0][0],
                    "Sample Quantiles": qq[0][1]
                })
                fig_qq = px.scatter(qq_df, x="Theoretical Quantiles", y="Sample Quantiles", title=f"Q-Q Plot vs Normal - {selected_asset}")
                
                # Correct Theoretical Line y = intercept + slope * x
                slope, intercept, r = qq[1]
                x_min = qq_df["Theoretical Quantiles"].min()
                x_max = qq_df["Theoretical Quantiles"].max()
                y_min = intercept + slope * x_min
                y_max = intercept + slope * x_max
                
                fig_qq.add_shape(type="line", x0=x_min, y0=y_min,
                                 x1=x_max, y1=y_max, line=dict(color="rgba(255,255,255,0.2)", dash="dash"))
                
                # Professional Tooltip update
                fig_qq.update_traces(
                    hovertemplate="%{y:.4f}<br>Theoretical: %{x:.4f}<br><b>Professional Diagnostic:</b> Points off the line indicate Fat Tails, meaning high-impact 'Black Swan' events are more likely.<extra></extra>"
                )
                st.plotly_chart(fig_qq, use_container_width=True)

    # 4. Rolling Risk Measures
    with tab4:
        st.header("4. Rolling Risk Measures")
        if selected_asset == "All":
            st.warning("Select a specific asset to see rolling statistics.")
        else:
            r = filtered_returns[selected_asset].dropna()
            r_mean = r.rolling(window=rolling_window).mean()
            r_std = r.rolling(window=rolling_window).std()
            
            ann_factor = np.sqrt(252) if annualize else 1
            r_std = r_std * ann_factor
            vol_label = "Annualized Volatility" if annualize else "Daily Volatility"
            
            # Add Threshold Indicators (Mean + 2sigma)
            valid_vols = r_std.dropna()
            vol_mean = valid_vols.mean()
            vol_stdev = valid_vols.std()
            vol_threshold = vol_mean + 2 * vol_stdev
            
            # Tasks 1 & 2: Volatility Prediction & Model Comparison (Naive vs MA)
            valid_arr = valid_vols.values
            if len(valid_arr) > 6:
                sum_sq_naive, sum_abs_naive = 0, 0
                sum_sq_ma, sum_abs_ma = 0, 0
                count = 0
                for k in range(5, len(valid_arr)):
                    actual = valid_arr[k]
                    naive_pred = valid_arr[k-1]
                    ma_pred = np.mean(valid_arr[k-5:k])
                    sum_sq_naive += (actual - naive_pred)**2
                    sum_abs_naive += abs(actual - naive_pred)
                    sum_sq_ma += (actual - ma_pred)**2
                    sum_abs_ma += abs(actual - ma_pred)
                    count += 1
                
                naive_rmse = np.sqrt(sum_sq_naive / count)
                naive_mae = sum_abs_naive / count
                ma_rmse = np.sqrt(sum_sq_ma / count)
                ma_mae = sum_abs_ma / count
                winner = "Trust Factor: Naive Baseline is currently more accurate" if naive_rmse < ma_rmse else "Trust Factor: MA Model is currently more accurate"
                winner_color = "#f59e0b" if naive_rmse < ma_rmse else "#22c55e"
                
                # 5-Day Forecast Fan
                last_vol = valid_arr[-1]
                last_date = valid_vols.index[-1]
                future_dates = [last_date + pd.Timedelta(days=i) for i in range(6)]
                naive_path = [last_vol] * 6
                ma_path = [last_vol]
                upper = [last_vol]
                lower = [last_vol]
                
                curr_window = list(valid_arr[-5:])
                vol_std_ma = np.sqrt(sum_sq_ma / count)
                vol_std_naive = np.sqrt(sum_sq_naive / count)
                
                for i in range(1, 6):
                    pred_ma = np.mean(curr_window)
                    ma_path.append(pred_ma)
                    curr_window.pop(0)
                    curr_window.append(pred_ma)
                    
                    if naive_rmse < ma_rmse:
                        upper.append(last_vol + 1.96 * vol_std_naive * np.sqrt(i))
                        lower.append(max(0, last_vol - 1.96 * vol_std_naive * np.sqrt(i)))
                    else:
                        upper.append(pred_ma + 1.96 * vol_std_ma * np.sqrt(i))
                        lower.append(max(0, pred_ma - 1.96 * vol_std_ma * np.sqrt(i)))
            
            # Rolling Vol
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(x=r_std.index, y=r_std, name=vol_label, line=dict(color="#0ea5e9", width=2)))
            
            if len(valid_arr) > 6:
                fig_vol.add_trace(go.Scatter(x=future_dates, y=naive_path, name="Naive Forecast", line=dict(color="rgba(255,255,255,0.4)", dash="dot", width=2)))
                fig_vol.add_trace(go.Scatter(x=future_dates, y=ma_path, name="MA Forecast", line=dict(color="#22d3ee", dash="dash", width=2)))
                
                fan_name = "95% Naive Interval" if naive_rmse < ma_rmse else "95% MA Interval"
                fig_vol.add_trace(go.Scatter(
                    x=future_dates + future_dates[::-1],
                    y=upper + lower[::-1],
                    fill="toself", fillcolor="rgba(34, 211, 238, 0.15)",
                    line=dict(color="rgba(255,255,255,0)", width=0),
                    name=fan_name
                ))

            # Dashed Red Line: Mean + 2 sigma
            fig_vol.add_shape(type="line", x0=r_std.index[0], x1=r_std.index[-1], y0=vol_threshold, y1=vol_threshold,
                              line=dict(color="#ef4444", width=2, dash="dash")) # Danger red dashed
            
            fig_vol.update_layout(title=f"Rolling {vol_label} & Warning Threshold (Mean+2σ)", yaxis_title="Volatility")
            
            # Display Plot and Metrics
            st.plotly_chart(fig_vol, use_container_width=True)
            
            if len(valid_arr) > 6:
                st.markdown(f"""
                <div style="background: rgba(30,41,59,0.5); padding: 1rem; border-radius: 0.5rem; border: 1px solid rgba(255,255,255,0.1); margin-top: -1rem; margin-bottom: 2rem;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; font-weight: bold; margin-bottom: 0.5rem; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem;">Model Performance Metrics (5-Day Predict)</div>
                    <div style="display: flex; justify-content: space-around;">
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #64748b; font-weight: bold; text-transform: uppercase; margin-bottom: 0.25rem;">Naive Baseline</div>
                            <div style="font-size: 0.8rem; font-family: monospace;">RMSE: <span style="color: #22d3ee;">{naive_rmse:.4f}</span></div>
                            <div style="font-size: 0.8rem; font-family: monospace;">MAE: &nbsp;<span style="color: #22d3ee;">{naive_mae:.4f}</span></div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 0.7rem; color: #64748b; font-weight: bold; text-transform: uppercase; margin-bottom: 0.25rem;">MA Model</div>
                            <div style="font-size: 0.8rem; font-family: monospace;">RMSE: <span style="color: #22d3ee;">{ma_rmse:.4f}</span></div>
                            <div style="font-size: 0.8rem; font-family: monospace;">MAE: &nbsp;<span style="color: #22d3ee;">{ma_mae:.4f}</span></div>
                        </div>
                    </div>
                    <div style="text-align: center; font-size: 0.75rem; font-weight: bold; color: {winner_color}; margin-top: 0.75rem;">{winner}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Rolling Mean with +/- 2 Std Bands
            fig_mean = go.Figure()
            fig_mean.add_trace(go.Scatter(x=r_mean.index, y=r_mean, name="Rolling Mean", line=dict(color="#0ea5e9", width=2)))
            
            raw_std = r.rolling(window=rolling_window).std()
            fig_mean.add_trace(go.Scatter(x=r_mean.index, y=r_mean + 2*raw_std, name="+2 Std", line=dict(color="#ef4444", dash='dash', width=1.5)))
            fig_mean.add_trace(go.Scatter(x=r_mean.index, y=r_mean - 2*raw_std, name="-2 Std", fill='tonexty', fillcolor='rgba(239, 68, 68, 0.05)', line=dict(color="#ef4444", dash='dash', width=1.5)))
            
            fig_mean.update_layout(title=f"Rolling Mean & ±2σ Danger Bands ({rolling_window} days)", yaxis_title="Return")
            st.plotly_chart(fig_mean, use_container_width=True)

    # 5. Cross-Asset Relationships
    with tab5:
        st.header("5. Cross-Asset Relationships")
        
        corr = log_returns.corr()
        fig_heat = px.imshow(corr, text_auto=True, title="Return Correlation Matrix", color_continuous_scale="RdBu_r")
        st.plotly_chart(fig_heat, use_container_width=True)
        
        st.subheader("Rolling Correlation")
        pair = st.multiselect("Select two assets for rolling correlation", options=list(log_returns.columns), default=list(log_returns.columns)[:2])
        if len(pair) == 2:
            roll_corr = log_returns[pair[0]].rolling(window=corr_window).corr(log_returns[pair[1]])
            fig_roll_corr = px.line(roll_corr, title=f"Rolling {corr_window}-day Correlation: {pair[0]} vs {pair[1]}")
            st.plotly_chart(fig_roll_corr, use_container_width=True)

    # 6. Professional Technical Appendix (Task 4)
    with tab6:
        st.header("6. Professional Technical Appendix")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            ### Log Returns & 1-Day VaR (Value at Risk)
            Log returns are used for statistical properties. VaR is calculated using the historical simulation method directly identifying the 5th percentile quantile score to reflect empirical downside exposure.
            
            ```math
            R_t = \ln(P_t / P_{t-1})
            ```
            
            ```math
            VaR_{95} = Quantile(R_t, 0.05)
            ```
            
            ### Data Quality & Outliers
            Missing values were forward-filled or dropped sequentially. Statistical Outliers were identified using a robust Z-score standard identifying events greater than 3 standard deviations from the zero mean.
            
            ```math
            |Z| = \\left| \\frac{x - \\mu_{historical}}{\\sigma_{historical}} \\right| > 3
            ```
            """)
        with c2:
            st.markdown("""
            ### Price & Volatility Projections
            **Price Drift Model:** Forecasted forward geometrically using the compound daily drift mean.
            
            ```math
            E[P_{T+h}] = P_T \cdot \exp(\\mu_{historical} \cdot h)
            ```
            
            **95% Prediction Interval Fan:** Upper and lower bounds mapped across a forward-expanding root-time horizon.
            
            ```math
            Upper/Lower = E[P_{T+h}] \cdot \exp(\\pm 1.96 \cdot \sigma \cdot \sqrt{h})
            ```
            
            **Volatility Naive vs MA Models:** Naive baseline holds constant ($\\hat{\\sigma}_{T+h} = \\sigma_T$) while MA uses a fast 5-day smoothing average to predict changing standard derivations.
            """)

if __name__ == "__main__":
    if st.runtime.exists():
        main()
    else:
        from streamlit.web import cli as stcli
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
