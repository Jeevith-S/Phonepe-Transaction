import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import matplotlib.pyplot as plt
import os

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="PhonePe Transaction Insights",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #5F2D82;
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #888;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #5F2D82 0%, #9B59B6 100%);
        padding: 1.2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .metric-label {
        font-size: 0.85rem;
        opacity: 0.85;
    }
    .section-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #5F2D82;
        border-left: 4px solid #5F2D82;
        padding-left: 0.7rem;
        margin: 1.5rem 0 1rem 0;
    }
    .stSelectbox > label { font-weight: 600; }
    .stRadio > label { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# INDIA GEOJSON URL
# ─────────────────────────────────────────
INDIA_GEOJSON = (
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112"
    "/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
)

# ─────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────
@st.cache_resource
def get_connection():
    db_path = "phonepe_project.db"  # corrected extension from .bd to .db
    if not os.path.exists(db_path):
        st.error(
            "❌ Database file 'phonepe_project.db' not found. "
            "Please run the data extraction notebook first and upload the .db file to this repo."
        )
        st.stop()
    return sqlite3.connect(db_path, check_same_thread=False)

conn = get_connection()

# ─────────────────────────────────────────
# HELPER: clean state names for choropleth
# ─────────────────────────────────────────
def clean_state(df, col="State"):
    df[col] = (
        df[col]
        .str.replace("-", " ")
        .str.replace("&", "and")
        .str.title()
        .str.strip()
    )
    return df


def make_choropleth(df, loc_col, color_col, title, color_scale="Purples"):
    fig = px.choropleth(
        df,
        geojson=INDIA_GEOJSON,
        featureidkey="properties.ST_NM",
        locations=loc_col,
        color=color_col,
        hover_name=loc_col,
        color_continuous_scale=color_scale,
        title=title,
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(thickness=12),
        height=500,
    )
    return fig


def make_bar(df, x, y, title, color="#5F2D82", rotate=90):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(df[x], df[y], color=color, edgecolor="white", linewidth=0.5)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.set_xlabel(x, fontsize=11)
    ax.set_ylabel(y.replace("_", " "), fontsize=11)
    ax.yaxis.get_major_formatter().set_scientific(False)
    plt.xticks(rotation=rotate, ha="right", fontsize=9)
    plt.tight_layout()
    return fig


# ─────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5f/PhonePe_Logo.svg/640px-PhonePe_Logo.svg.png",
        width=160,
    )
    st.markdown("---")
    page = st.radio(
        "Navigate",
        ["🏠 Home", "📊 Business Case Studies", "🗺️ India Map Explorer"],
    )
    st.markdown("---")
    st.markdown("**Filters**")
    year = st.selectbox("Year", list(range(2018, 2025)), index=5)
    quarter = st.selectbox("Quarter", [1, 2, 3, 4])
    st.markdown("---")
    st.caption("GUVI × IIT Madras | PhonePe Pulse")


# ─────────────────────────────────────────
# PAGE: HOME
# ─────────────────────────────────────────
if page == "🏠 Home":
    st.markdown('<div class="main-header">📱 PhonePe Transaction Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive dashboard built on PhonePe Pulse open data</div>',
        unsafe_allow_html=True,
    )

    # KPI row
    try:
        total_txn = pd.read_sql("SELECT SUM(Transaction_Amount) AS v FROM Aggregated_Transaction", conn).iloc[0, 0]
        total_users = pd.read_sql("SELECT SUM(RegisteredUsers) AS v FROM Map_User", conn).iloc[0, 0]
        total_ins = pd.read_sql("SELECT SUM(Insurance_Amount) AS v FROM Aggregated_Insurance", conn).iloc[0, 0]
        total_records = pd.read_sql("SELECT COUNT(*) AS v FROM Aggregated_Transaction", conn).iloc[0, 0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">₹{total_txn/1e12:.2f}T</div>
                <div class="metric-label">Total Transaction Value</div></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{total_users/1e6:.1f}M</div>
                <div class="metric-label">Registered Users</div></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">₹{total_ins/1e9:.1f}B</div>
                <div class="metric-label">Insurance Amount</div></div>""", unsafe_allow_html=True)
        with c4:
            st.markdown(f"""<div class="metric-card">
                <div class="metric-value">{int(total_records):,}</div>
                <div class="metric-label">Transaction Records</div></div>""", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Could not load KPIs: {e}")

    st.markdown("---")

    # About
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="section-title">About This Dashboard</div>', unsafe_allow_html=True)
        st.write("""
        This project analyzes **PhonePe Pulse** — India's open-source digital payment data repository.
        The dashboard covers:
        - 📈 Transaction dynamics across states, years, and payment categories
        - 📱 Device dominance and user engagement patterns
        - 🛡️ Insurance penetration and growth analysis
        - 🗺️ Geographic heatmaps at the state level
        - 👥 User registration trends
        """)
    with col2:
        st.markdown('<div class="section-title">Data Tables</div>', unsafe_allow_html=True)
        tables = [
            "Aggregated_Transaction", "Aggregated_User", "Aggregated_Insurance",
            "Map_Transaction", "Map_User", "Map_Insurance",
            "Top_Transaction", "Top_User", "Top_User_Pincodes"
        ]
        for t in tables:
            st.markdown(f"✅ `{t}`")


# ─────────────────────────────────────────
# PAGE: BUSINESS CASE STUDIES
# ─────────────────────────────────────────
elif page == "📊 Business Case Studies":
    st.markdown('<div class="main-header">Business Case Studies</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">5 analytical scenarios based on PhonePe transaction data</div>',
        unsafe_allow_html=True,
    )

    case = st.selectbox(
        "Choose a Business Case Study",
        [
            "1. Decoding Transaction Dynamics on PhonePe",
            "2. Device Dominance and User Engagement Analysis",
            "3. Insurance Penetration and Growth Potential Analysis",
            "4. Transaction Analysis for Market Expansion",
            "5. User Registration Analysis (User Engagement & Growth)",
        ],
    )

    st.markdown(f"**Filters applied:** Year = {year}, Quarter = Q{quarter}")
    st.markdown("---")

    # ── CASE 1 ──────────────────────────────────────────────────────────────
    if case.startswith("1."):
        st.markdown('<div class="section-title">Case 1: Decoding Transaction Dynamics on PhonePe</div>', unsafe_allow_html=True)
        st.write("""
        **Scenario:** PhonePe has identified significant variations in transaction behavior across states,
        quarters, and payment categories. The leadership team seeks a deeper understanding of these patterns
        to drive targeted business strategies.
        """)

        try:
            # State-level total transaction amount
            df1 = pd.read_sql(
                f"""SELECT State, SUM(Transaction_Amount) AS Total_Transaction_Value
                    FROM Aggregated_Transaction
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State
                    ORDER BY Total_Transaction_Value DESC""",
                conn,
            )
            df1 = clean_state(df1)

            # Transaction type breakdown
            df1b = pd.read_sql(
                f"""SELECT Transaction_Type, SUM(Transaction_Count) AS Total_Count,
                           SUM(Transaction_Amount) AS Total_Amount
                    FROM Aggregated_Transaction
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY Transaction_Type
                    ORDER BY Total_Amount DESC""",
                conn,
            )

            tab1, tab2, tab3 = st.tabs(["🗺️ State Map", "📊 Bar Chart", "🥧 Type Breakdown"])

            with tab1:
                st.plotly_chart(
                    make_choropleth(df1, "State", "Total_Transaction_Value",
                                    f"State-Wise Transaction Amount — {year} Q{quarter}", "Purples"),
                    use_container_width=True,
                )

            with tab2:
                st.pyplot(make_bar(df1, "State", "Total_Transaction_Value",
                                   f"State-Wise Transaction Amount — {year} Q{quarter}"))
                st.dataframe(df1.head(10), use_container_width=True)

            with tab3:
                if not df1b.empty:
                    fig_pie = px.pie(df1b, names="Transaction_Type", values="Total_Amount",
                                     hole=0.45, title="Transaction Amount by Type",
                                     color_discrete_sequence=px.colors.sequential.Purples_r)
                    st.plotly_chart(fig_pie, use_container_width=True)
                    st.dataframe(df1b, use_container_width=True)

            # Insight box
            if not df1.empty:
                top_state = df1.iloc[0]["State"]
                top_val = df1.iloc[0]["Total_Transaction_Value"]
                st.info(f"💡 **Insight:** {top_state} leads in transaction value for {year} Q{quarter} with ₹{top_val:,.0f}")

        except Exception as e:
            st.error(f"Query error: {e}")

    # ── CASE 2 ──────────────────────────────────────────────────────────────
    elif case.startswith("2."):
        st.markdown('<div class="section-title">Case 2: Device Dominance and User Engagement Analysis</div>', unsafe_allow_html=True)
        st.write("""
        **Scenario:** PhonePe aims to enhance user engagement and improve app performance by understanding
        user preferences across different device brands. Trends in device usage vary significantly across
        regions, and some devices are disproportionately underutilized despite high registration numbers.
        """)

        try:
            df2 = pd.read_sql(
                f"""SELECT Brand, SUM(Count) AS Total_Users, AVG(Percentage)*100 AS Avg_Share
                    FROM Aggregated_User
                    WHERE Year = {year} AND Quarter = {quarter}
                      AND Brand IS NOT NULL AND Brand != ''
                    GROUP BY Brand
                    ORDER BY Total_Users DESC
                    LIMIT 10""",
                conn,
            )

            df2_trend = pd.read_sql(
                """SELECT Year, Quarter, Brand, SUM(Count) AS Total_Users
                   FROM Aggregated_User
                   WHERE Brand IS NOT NULL AND Brand != ''
                   GROUP BY Year, Quarter, Brand
                   ORDER BY Year, Quarter""",
                conn,
            )

            tab1, tab2, tab3 = st.tabs(["🥧 Market Share", "📊 Top Brands", "📈 Trend Over Time"])

            with tab1:
                fig_d = px.pie(df2, names="Brand", values="Total_Users", hole=0.5,
                               title=f"Device Brand Market Share — {year} Q{quarter}",
                               color_discrete_sequence=px.colors.sequential.Purples_r)
                fig_d.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_d, use_container_width=True)

            with tab2:
                st.pyplot(make_bar(df2, "Brand", "Total_Users",
                                   f"Top 10 Device Brands by Users — {year} Q{quarter}", rotate=45))
                st.dataframe(df2, use_container_width=True)

            with tab3:
                if not df2_trend.empty:
                    top_brands = df2["Brand"].head(5).tolist()
                    df2_trend_top = df2_trend[df2_trend["Brand"].isin(top_brands)]
                    df2_trend_top = df2_trend_top.copy()
                    df2_trend_top["Period"] = df2_trend_top["Year"].astype(str) + "-Q" + df2_trend_top["Quarter"].astype(str)
                    fig_line = px.line(df2_trend_top, x="Period", y="Total_Users", color="Brand",
                                       title="Top 5 Brands — User Trend",
                                       color_discrete_sequence=px.colors.sequential.Purples_r)
                    fig_line.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_line, use_container_width=True)

            if not df2.empty:
                dom_brand = df2.iloc[0]["Brand"]
                dom_pct = df2.iloc[0]["Avg_Share"]
                st.info(f"💡 **Insight:** {dom_brand} dominates with an average share of {dom_pct:.1f}% in {year} Q{quarter}")

        except Exception as e:
            st.error(f"Query error: {e}")

    # ── CASE 3 ──────────────────────────────────────────────────────────────
    elif case.startswith("3."):
        st.markdown('<div class="section-title">Case 3: Insurance Penetration and Growth Potential Analysis</div>', unsafe_allow_html=True)
        st.write("""
        **Scenario:** PhonePe has ventured into the insurance domain. The company seeks to analyze
        its growth trajectory and identify untapped opportunities for insurance adoption at the state level
        to prioritize regions for marketing efforts and partnerships with insurers.
        """)

        try:
            df3 = pd.read_sql(
                f"""SELECT State, SUM(Insurance_Amount) AS Total_Insurance,
                           SUM(Insurance_Count) AS Total_Policies
                    FROM Aggregated_Insurance
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State
                    ORDER BY Total_Insurance DESC""",
                conn,
            )
            df3 = clean_state(df3)

            df3_trend = pd.read_sql(
                """SELECT Year, Quarter,
                          SUM(Insurance_Amount) AS Total_Amount,
                          SUM(Insurance_Count) AS Total_Policies
                   FROM Aggregated_Insurance
                   GROUP BY Year, Quarter
                   ORDER BY Year, Quarter""",
                conn,
            )

            tab1, tab2, tab3 = st.tabs(["🗺️ State Map", "📊 Bar Chart", "📈 Growth Trend"])

            with tab1:
                if not df3.empty:
                    st.plotly_chart(
                        make_choropleth(df3, "State", "Total_Insurance",
                                        f"Insurance Penetration by State — {year} Q{quarter}", "Greens"),
                        use_container_width=True,
                    )
                else:
                    st.warning("No insurance data for this period.")

            with tab2:
                if not df3.empty:
                    st.pyplot(make_bar(df3, "State", "Total_Insurance",
                                       f"State-Wise Insurance Amount — {year} Q{quarter}", color="#27AE60"))
                    st.dataframe(df3.head(10), use_container_width=True)

            with tab3:
                if not df3_trend.empty:
                    df3_trend["Period"] = df3_trend["Year"].astype(str) + "-Q" + df3_trend["Quarter"].astype(str)
                    fig_ins = px.bar(df3_trend, x="Period", y="Total_Amount",
                                     title="Insurance Amount Growth Over Time",
                                     color_discrete_sequence=["#27AE60"])
                    fig_ins.update_xaxes(tickangle=45)
                    st.plotly_chart(fig_ins, use_container_width=True)

            if not df3.empty:
                top3 = df3.head(3)["State"].tolist()
                st.info(f"💡 **Insight:** Top 3 states by insurance uptake in {year} Q{quarter}: {', '.join(top3)}")

        except Exception as e:
            st.error(f"Query error: {e}")

    # ── CASE 4 ──────────────────────────────────────────────────────────────
    elif case.startswith("4."):
        st.markdown('<div class="section-title">Case 4: Transaction Analysis for Market Expansion</div>', unsafe_allow_html=True)
        st.write("""
        **Scenario:** PhonePe operates in a highly competitive market. Understanding transaction
        dynamics at the state level is crucial for strategic decision-making to identify trends,
        opportunities, and potential areas for expansion.
        """)

        try:
            df4 = pd.read_sql(
                f"""SELECT state AS State, SUM(Amount) AS Total_Amount,
                           SUM(Count) AS Total_Count
                    FROM Map_Transaction
                    WHERE year = {year} AND Quarter = {quarter}
                    GROUP BY state
                    ORDER BY Total_Amount DESC
                    LIMIT 10""",
                conn,
            )
            df4 = clean_state(df4)

            df4_all = pd.read_sql(
                f"""SELECT state AS State, SUM(Amount) AS Total_Amount
                    FROM Map_Transaction
                    WHERE year = {year} AND Quarter = {quarter}
                    GROUP BY state""",
                conn,
            )
            df4_all = clean_state(df4_all)

            df4_yoy = pd.read_sql(
                """SELECT year AS Year, SUM(Amount) AS Total_Amount, SUM(Count) AS Total_Count
                   FROM Map_Transaction
                   GROUP BY year
                   ORDER BY year""",
                conn,
            )

            tab1, tab2, tab3 = st.tabs(["🏆 Top 10 States", "🗺️ All States Map", "📈 Year-over-Year"])

            with tab1:
                st.pyplot(make_bar(df4, "State", "Total_Amount",
                                   f"Top 10 States by Transaction Amount — {year} Q{quarter}", rotate=45))
                c1, c2 = st.columns(2)
                with c1:
                    st.dataframe(df4, use_container_width=True)
                with c2:
                    fig_t = px.treemap(df4, path=["State"], values="Total_Amount",
                                       title="Treemap: Top 10 States",
                                       color_discrete_sequence=px.colors.sequential.Purples_r)
                    st.plotly_chart(fig_t, use_container_width=True)

            with tab2:
                if not df4_all.empty:
                    st.plotly_chart(
                        make_choropleth(df4_all, "State", "Total_Amount",
                                        f"All-State Transaction Map — {year} Q{quarter}", "Blues"),
                        use_container_width=True,
                    )

            with tab3:
                if not df4_yoy.empty:
                    fig_yoy = px.bar(df4_yoy, x="Year", y="Total_Amount",
                                     title="Year-over-Year Transaction Growth",
                                     color_discrete_sequence=["#5F2D82"])
                    st.plotly_chart(fig_yoy, use_container_width=True)

            if not df4.empty:
                top_state = df4.iloc[0]["State"]
                st.info(f"💡 **Insight:** {top_state} is the top market for expansion focus in {year} Q{quarter}")

        except Exception as e:
            st.error(f"Query error: {e}")

    # ── CASE 5 ──────────────────────────────────────────────────────────────
    elif case.startswith("5."):
        st.markdown('<div class="section-title">Case 5: User Registration Analysis</div>', unsafe_allow_html=True)
        st.write("""
        **Scenario:** PhonePe seeks to enhance its market position by analyzing user engagement
        across different states and districts. Understanding user behavior provides valuable insights
        for strategic decision-making and growth opportunities.
        """)

        try:
            df5_state = pd.read_sql(
                f"""SELECT State, SUM(RegisteredUsers) AS Total_Users,
                           SUM(AppOpens) AS Total_AppOpens
                    FROM Map_User
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State
                    ORDER BY Total_Users DESC""",
                conn,
            )
            df5_state = clean_state(df5_state)

            df5_district = pd.read_sql(
                f"""SELECT District, State, SUM(RegisteredUsers) AS Total_Users
                    FROM Map_User
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY District, State
                    ORDER BY Total_Users DESC
                    LIMIT 10""",
                conn,
            )

            df5_pin = pd.read_sql(
                f"""SELECT Pincode, State, SUM(RegisteredUsers) AS Total_Users
                    FROM Top_User_Pincodes
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY Pincode, State
                    ORDER BY Total_Users DESC
                    LIMIT 10""",
                conn,
            )

            tab1, tab2, tab3 = st.tabs(["🗺️ State Map", "🏙️ Top Districts", "📮 Top Pincodes"])

            with tab1:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.plotly_chart(
                        make_choropleth(df5_state, "State", "Total_Users",
                                        f"Registered Users by State — {year} Q{quarter}", "Reds"),
                        use_container_width=True,
                    )
                with c2:
                    st.markdown("**Top 10 States**")
                    st.dataframe(
                        df5_state[["State", "Total_Users"]].head(10)
                        .rename(columns={"Total_Users": "Users"}),
                        use_container_width=True,
                        hide_index=True,
                    )

            with tab2:
                if not df5_district.empty:
                    st.pyplot(make_bar(
                        df5_district.sort_values("Total_Users"),
                        "District", "Total_Users",
                        f"Top 10 Districts by Registered Users — {year} Q{quarter}",
                        color="#C0392B", rotate=45,
                    ))
                    st.dataframe(df5_district, use_container_width=True)
                else:
                    st.warning("No district data for this period.")

            with tab3:
                if not df5_pin.empty:
                    fig_pin = px.bar(
                        df5_pin, x=df5_pin["Pincode"].astype(str), y="Total_Users",
                        title=f"Top 10 Pincodes by Registered Users — {year} Q{quarter}",
                        color_discrete_sequence=["#C0392B"],
                    )
                    fig_pin.update_xaxes(title="Pincode", tickangle=45)
                    st.plotly_chart(fig_pin, use_container_width=True)
                    st.dataframe(df5_pin, use_container_width=True)
                else:
                    st.warning("No pincode data for this period.")

            if not df5_state.empty:
                top_state = df5_state.iloc[0]["State"]
                top_users = df5_state.iloc[0]["Total_Users"]
                st.info(f"💡 **Insight:** {top_state} has the highest user base in {year} Q{quarter} with {top_users:,.0f} registered users")

        except Exception as e:
            st.error(f"Query error: {e}")


# ─────────────────────────────────────────
# PAGE: INDIA MAP EXPLORER
# ─────────────────────────────────────────
elif page == "🗺️ India Map Explorer":
    st.markdown('<div class="main-header">🗺️ India Map Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Interactive choropleth maps for all three data domains</div>',
        unsafe_allow_html=True,
    )

    metric_choice = st.radio(
        "Select Metric",
        ["Transaction Amount", "Registered Users", "Insurance Amount"],
        horizontal=True,
    )

    try:
        if metric_choice == "Transaction Amount":
            df_map = pd.read_sql(
                f"""SELECT State, SUM(Transaction_Amount) AS Value
                    FROM Aggregated_Transaction
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State""", conn,
            )
            color_scale, title = "Purples", f"Transaction Amount — {year} Q{quarter}"

        elif metric_choice == "Registered Users":
            df_map = pd.read_sql(
                f"""SELECT State, SUM(RegisteredUsers) AS Value
                    FROM Map_User
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State""", conn,
            )
            color_scale, title = "Reds", f"Registered Users — {year} Q{quarter}"

        else:
            df_map = pd.read_sql(
                f"""SELECT State, SUM(Insurance_Amount) AS Value
                    FROM Aggregated_Insurance
                    WHERE Year = {year} AND Quarter = {quarter}
                    GROUP BY State""", conn,
            )
            color_scale, title = "Greens", f"Insurance Amount — {year} Q{quarter}"

        df_map = clean_state(df_map)

        if df_map.empty:
            st.warning("No data available for this year/quarter combination.")
        else:
            st.plotly_chart(
                make_choropleth(df_map, "State", "Value", title, color_scale),
                use_container_width=True,
            )

            st.markdown('<div class="section-title">State-wise Rankings</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Top 5 States**")
                st.dataframe(
                    df_map.sort_values("Value", ascending=False).head(5).reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                )
            with col2:
                st.markdown("**Bottom 5 States**")
                st.dataframe(
                    df_map.sort_values("Value").head(5).reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True,
                )

    except Exception as e:
        st.error(f"Query error: {e}")
