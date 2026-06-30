import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

st.set_page_config(
    page_title="PhonePe Transaction Insights",
    page_icon="📱",
    layout="wide"
)

# ── Database connection ───────────────────────────────────────────────────────
DB_PATH = "phonpe_project.db"

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        st.error("Database file 'phonpe_project.db' not found in the repo root.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_conn()

GEOJSON_URL = (
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112"
    "/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
)

def clean_state_names(df, col="State"):
    df = df.copy()
    df[col] = (df[col]
               .str.replace("-", " ")
               .str.replace("&", "and")
               .str.title()
               .str.strip())
    return df

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("📱 PhonePe Dashboard")
st.sidebar.markdown("---")

page = st.sidebar.selectbox("Go to", [
    "Home",
    "Case 1 - Transaction Dynamics",
    "Case 2 - Device Analysis",
    "Case 3 - Insurance Analysis",
    "Case 4 - Market Expansion",
    "Case 5 - User Registration",
    "India Map Explorer"
])

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")
year    = st.sidebar.selectbox("Year",    [2018, 2019, 2020, 2021, 2022, 2023, 2024], index=2)
quarter = st.sidebar.selectbox("Quarter", [1, 2, 3, 4])

# ══════════════════════════════════════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════════════════════════════════════
if page == "Home":
    st.title("📱 PhonePe Transaction Insights")
    st.write("Interactive dashboard built on PhonePe Pulse open data")
    st.markdown("---")

    st.subheader("About This Project")
    st.write("""
    This dashboard analyses PhonePe Pulse — India's open-source digital payments dataset.

    **What's covered:**
    - Transaction trends across all Indian states
    - Device brand usage and user engagement
    - Insurance product penetration
    - Geographic heatmaps on India map
    - Top districts by user registration
    """)

# ══════════════════════════════════════════════════════════════════════════════
# CASE 1 — TRANSACTION DYNAMICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 1 - Transaction Dynamics":
    st.title("Case 1 — Decoding Transaction Dynamics")
    st.write("Analyse how transaction amounts vary across Indian states and payment categories.")
    st.markdown("---")

    try:
        df = pd.read_sql(f"""
            SELECT State,
                   SUM(Transaction_Amount) AS Total_Amount,
                   SUM(Transaction_Count)  AS Total_Count
            FROM Aggregated_Transaction
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Amount DESC
        """, conn)
        df = clean_state_names(df)

        df_type = pd.read_sql(f"""
            SELECT Transaction_Type,
                   SUM(Transaction_Amount) AS Total_Amount,
                   SUM(Transaction_Count)  AS Total_Count
            FROM Aggregated_Transaction
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY Transaction_Type
            ORDER BY Total_Amount DESC
        """, conn)

        st.subheader(f"State-wise Transaction Amount — {year} Q{quarter}")
        fig_map = px.choropleth(
            df,
            geojson=GEOJSON_URL,
            featureidkey="properties.ST_NM",
            locations="State",
            color="Total_Amount",
            hover_name="State",
            color_continuous_scale="Purples",
            title=f"Transaction Amount by State — {year} Q{quarter}"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_map, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 15 States — Bar Chart")
            fig_bar = px.bar(
                df.head(15), x="State", y="Total_Amount",
                color="Total_Amount", color_continuous_scale="Purples",
                title="Top 15 States by Transaction Amount"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Transaction Type Breakdown")
            fig_pie = px.pie(
                df_type, names="Transaction_Type", values="Total_Amount",
                hole=0.4, title="Amount by Payment Type"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── Quarter-wise trend within the selected year ──────────────────────
        st.subheader(f"Quarter-wise Transaction Trend — {year}")
        df_qtr = pd.read_sql(f"""
            SELECT Quarter, SUM(Transaction_Amount) AS Total_Amount,
                   SUM(Transaction_Count) AS Total_Count
            FROM Aggregated_Transaction
            WHERE Year = {year}
            GROUP BY Quarter
            ORDER BY Quarter
        """, conn)
        if not df_qtr.empty:
            df_qtr["Quarter_Label"] = "Q" + df_qtr["Quarter"].astype(str)
            fig_qtr = px.line(
                df_qtr, x="Quarter_Label", y="Total_Amount", markers=True,
                title=f"Transaction Amount by Quarter — {year}"
            )
            st.plotly_chart(fig_qtr, use_container_width=True)

        # ── Year-over-year growth/decline ─────────────────────────────────────
        st.subheader("Growth / Decline Analysis — Year vs Transaction Amount")
        df_year = pd.read_sql("""
            SELECT Year, SUM(Transaction_Amount) AS Total_Amount,
                   SUM(Transaction_Count) AS Total_Count
            FROM Aggregated_Transaction
            GROUP BY Year
            ORDER BY Year
        """, conn)
        if not df_year.empty:
            df_year["YoY_Growth_Pct"] = df_year["Total_Amount"].pct_change() * 100
            fig_year = px.line(
                df_year, x="Year", y="Total_Amount", markers=True,
                title="Total Transaction Amount by Year (National)"
            )
            st.plotly_chart(fig_year, use_container_width=True)
            st.dataframe(
                df_year[["Year", "Total_Amount", "Total_Count", "YoY_Growth_Pct"]]
                .round({"YoY_Growth_Pct": 1}),
                use_container_width=True
            )

        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

        # ── Insights section ───────────────────────────────────────────────────
        st.subheader("Insights")
        if not df.empty:
            st.info(f"📌 Highest Transaction State ({year} Q{quarter}): {df.iloc[0]['State']} — ₹{df.iloc[0]['Total_Amount']:,.0f}")
            lowest_state = df.sort_values('Total_Amount').iloc[0]
            st.info(f"📌 Lowest Transaction State ({year} Q{quarter}): {lowest_state['State']} — ₹{lowest_state['Total_Amount']:,.0f}")
        if not df_type.empty:
            st.info(f"📌 Most Popular Payment Category: {df_type.iloc[0]['Transaction_Type']} — ₹{df_type.iloc[0]['Total_Amount']:,.0f}")
        if len(df_year) >= 2:
            latest = df_year.iloc[-1]
            prev = df_year.iloc[-2]
            direction = "grew" if latest["Total_Amount"] > prev["Total_Amount"] else "declined"
            st.info(
                f"📌 National transactions {direction} from ₹{prev['Total_Amount']:,.0f} ({int(prev['Year'])}) "
                f"to ₹{latest['Total_Amount']:,.0f} ({int(latest['Year'])}) — "
                f"a {latest['YoY_Growth_Pct']:.1f}% change."
            )

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 2 — DEVICE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 2 - Device Analysis":
    st.title("Case 2 — Device Dominance & User Engagement")
    st.write("Understand which device brands drive PhonePe usage and how engagement varies.")
    st.markdown("---")

    try:
        df = pd.read_sql(f"""
            SELECT Brand,
                   SUM(Count) AS Total_Users
            FROM Aggregated_User
            WHERE Year = {year} AND Quarter = {quarter}
              AND Brand IS NOT NULL AND Brand != ''
            GROUP BY Brand
            ORDER BY Total_Users DESC
            LIMIT 10
        """, conn)

        df_trend = pd.read_sql("""
            SELECT Year, Quarter, Brand,
                   SUM(Count) AS Total_Users
            FROM Aggregated_User
            WHERE Brand IS NOT NULL AND Brand != ''
            GROUP BY Year, Quarter, Brand
            ORDER BY Year, Quarter
        """, conn)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Market Share — {year} Q{quarter}")
            if df.empty:
                st.warning(
                    f"No device brand data is available for {year} Q{quarter}. "
                    "PhonePe Pulse only publishes this dataset from 2018 to 2022. "
                    "Try selecting a year between 2018 and 2022."
                )
            else:
                fig_pie = px.pie(
                    df, names="Brand", values="Total_Users",
                    hole=0.45, title="Device Brand Market Share"
                )
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader(f"Top 10 Brands — {year} Q{quarter}")
            if not df.empty:
                fig_bar = px.bar(
                    df, x="Brand", y="Total_Users",
                    color="Total_Users", color_continuous_scale="Purples",
                    title="Users by Device Brand"
                )
                fig_bar.update_xaxes(tickangle=45)
                st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Brand Trend Over Time — Top 5 Brands")
        if not df_trend.empty and not df.empty:
            top5 = df["Brand"].head(5).tolist()
            dft = df_trend[df_trend["Brand"].isin(top5)].copy()
            dft["Period"] = dft["Year"].astype(str) + "-Q" + dft["Quarter"].astype(str)
            fig_line = px.line(
                dft, x="Period", y="Total_Users", color="Brand",
                title="Top 5 Brands — User Count Over Time"
            )
            fig_line.update_xaxes(tickangle=45)
            st.plotly_chart(fig_line, use_container_width=True)

        # ── Regional variation: top brand per state ──────────────────────────
        st.subheader(f"Regional Variation — Leading Brand by State ({year} Q{quarter})")
        df_region = pd.read_sql(f"""
            SELECT State, Brand, SUM(Count) AS Total_Users
            FROM Aggregated_User
            WHERE Year = {year} AND Quarter = {quarter}
              AND Brand IS NOT NULL AND Brand != ''
            GROUP BY State, Brand
        """, conn)

        if df_region.empty:
            st.warning(
                f"No regional device data is available for {year} Q{quarter}. "
                "Try a year between 2018 and 2022."
            )
        else:
            top_per_state = (
                df_region.loc[df_region.groupby("State")["Total_Users"].idxmax()]
                .sort_values("Total_Users", ascending=False)
                .reset_index(drop=True)
            )
            top_per_state = clean_state_names(top_per_state)

            col3, col4 = st.columns([3, 2])
            with col3:
                fig_region_map = px.choropleth(
                    top_per_state,
                    geojson=GEOJSON_URL,
                    featureidkey="properties.ST_NM",
                    locations="State",
                    color="Brand",
                    hover_name="State",
                    hover_data={"Total_Users": ":,"},
                    title=f"Leading Device Brand by State — {year} Q{quarter}"
                )
                fig_region_map.update_geos(fitbounds="locations", visible=False)
                fig_region_map.update_layout(height=450, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(fig_region_map, use_container_width=True)

            with col4:
                st.markdown("**How many states each brand leads in**")
                brand_counts = top_per_state["Brand"].value_counts().reset_index()
                brand_counts.columns = ["Brand", "States_Led"]
                st.dataframe(brand_counts, use_container_width=True, hide_index=True)

            st.dataframe(
                top_per_state[["State", "Brand", "Total_Users"]],
                use_container_width=True
            )

            leading_brand = top_per_state["Brand"].mode()[0]
            num_states_leading = (top_per_state["Brand"] == leading_brand).sum()
            total_states = len(top_per_state)
            st.info(
                f"📌 {leading_brand} leads in {num_states_leading} out of {total_states} states "
                f"for {year} Q{quarter}, but the remaining states show different brand preferences — "
                f"this is the regional variation the case study asks about."
            )

        if not df.empty:
            st.subheader("Data Table")
            st.dataframe(df, use_container_width=True)
            st.info(f"📌 Top Device Brand (National): {df.iloc[0]['Brand']} — {df.iloc[0]['Total_Users']:,} users")

        # ── App Opens & Engagement Ratio (state-level — see note below) ──────
        st.markdown("---")
        st.subheader(f"App Opens & Engagement Ratio by State — {year} Q{quarter}")
        st.caption(
            "PhonePe Pulse publishes App Opens at the state/district level, not broken "
            "down by device brand. So this section shows engagement by region rather than "
            "by brand — a true 'App Opens per brand' figure isn't available in the source data."
        )
        df_engage = pd.read_sql(f"""
            SELECT State, SUM(RegisteredUsers) AS Total_Users, SUM(AppOpens) AS Total_AppOpens
            FROM Map_User
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Users DESC
        """, conn)

        if df_engage.empty:
            st.warning(f"No app-opens data available for {year} Q{quarter}.")
        else:
            df_engage = clean_state_names(df_engage)
            df_engage["Engagement_Ratio"] = (df_engage["Total_AppOpens"] / df_engage["Total_Users"]).round(2)

            col5, col6 = st.columns(2)
            with col5:
                fig_appopens = px.bar(
                    df_engage.head(10), x="State", y="Total_AppOpens",
                    color="Total_AppOpens", color_continuous_scale="Purples",
                    title="Top 10 States by App Opens"
                )
                fig_appopens.update_xaxes(tickangle=45)
                st.plotly_chart(fig_appopens, use_container_width=True)

            with col6:
                fig_ratio = px.bar(
                    df_engage.sort_values("Engagement_Ratio", ascending=False).head(10),
                    x="State", y="Engagement_Ratio",
                    color="Engagement_Ratio", color_continuous_scale="Oranges",
                    title="Top 10 States by Engagement Ratio (App Opens ÷ Registered Users)"
                )
                fig_ratio.update_xaxes(tickangle=45)
                st.plotly_chart(fig_ratio, use_container_width=True)

            st.markdown("**Underutilized regions — high registrations, low app opens relative to users**")
            underutilized = df_engage.sort_values("Engagement_Ratio").head(10)
            st.dataframe(
                underutilized[["State", "Total_Users", "Total_AppOpens", "Engagement_Ratio"]],
                use_container_width=True, hide_index=True
            )

            top_engage = df_engage.sort_values("Engagement_Ratio", ascending=False).iloc[0]
            low_engage = df_engage.sort_values("Engagement_Ratio").iloc[0]
            st.info(
                f"📌 Highest Engagement Region: {top_engage['State']} "
                f"(ratio {top_engage['Engagement_Ratio']:.1f} app opens per registered user)"
            )
            st.info(
                f"📌 Underutilized Region: {low_engage['State']} "
                f"(ratio {low_engage['Engagement_Ratio']:.1f}) — high registrations but comparatively low repeat usage"
            )

        # ── State dropdown: select a state, see its top brands ───────────────
        st.markdown("---")
        st.subheader("State-wise Device Preference")
        all_states_df = pd.read_sql(f"""
            SELECT DISTINCT State FROM Aggregated_User
            WHERE Year = {year} AND Quarter = {quarter}
              AND Brand IS NOT NULL AND Brand != ''
            ORDER BY State
        """, conn)

        if all_states_df.empty:
            st.warning(f"No state-level brand data available for {year} Q{quarter}.")
        else:
            state_display = clean_state_names(all_states_df.copy())
            state_map = dict(zip(state_display["State"], all_states_df["State"]))
            chosen_display = st.selectbox("Select a State", sorted(state_map.keys()))
            chosen_state = state_map[chosen_display]

            df_state_brands = pd.read_sql(f"""
                SELECT Brand, SUM(Count) AS Total_Users
                FROM Aggregated_User
                WHERE Year = {year} AND Quarter = {quarter} AND State = '{chosen_state}'
                  AND Brand IS NOT NULL AND Brand != ''
                GROUP BY Brand
                ORDER BY Total_Users DESC
            """, conn)

            if not df_state_brands.empty:
                fig_state_brand = px.bar(
                    df_state_brands, x="Brand", y="Total_Users",
                    color="Total_Users", color_continuous_scale="Purples",
                    title=f"Top Brands in {chosen_display} — {year} Q{quarter}"
                )
                st.plotly_chart(fig_state_brand, use_container_width=True)
                st.dataframe(df_state_brands, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 3 — INSURANCE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 3 - Insurance Analysis":
    st.title("Case 3 — Insurance Penetration & Growth")
    st.write("Identify states with high insurance adoption and track growth over time.")
    st.markdown("---")

    try:
        df = pd.read_sql(f"""
            SELECT State,
                   SUM(Insurance_Amount) AS Total_Insurance,
                   SUM(Insurance_Count)  AS Total_Policies
            FROM Aggregated_Insurance
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Insurance DESC
        """, conn)
        df = clean_state_names(df)

        df_trend = pd.read_sql("""
            SELECT Year, Quarter,
                   SUM(Insurance_Amount) AS Total_Amount,
                   SUM(Insurance_Count)  AS Total_Policies
            FROM Aggregated_Insurance
            GROUP BY Year, Quarter
            ORDER BY Year, Quarter
        """, conn)

        st.subheader(f"Insurance Amount by State — {year} Q{quarter}")
        if not df.empty:
            fig_map = px.choropleth(
                df,
                geojson=GEOJSON_URL,
                featureidkey="properties.ST_NM",
                locations="State",
                color="Total_Insurance",
                hover_name="State",
                color_continuous_scale="Greens",
                title=f"Insurance Penetration — {year} Q{quarter}"
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("No insurance data for this year and quarter.")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 15 States — Bar Chart")
            fig_bar = px.bar(
                df.head(15), x="State", y="Total_Insurance",
                color="Total_Insurance", color_continuous_scale="Greens",
                title="Top 15 States by Insurance Amount"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Growth Over All Quarters")
            if not df_trend.empty:
                df_trend["Period"] = (df_trend["Year"].astype(str)
                                      + "-Q" + df_trend["Quarter"].astype(str))
                fig_line = px.line(
                    df_trend, x="Period", y="Total_Amount",
                    title="Insurance Amount Growth Over Time",
                    markers=True
                )
                fig_line.update_xaxes(tickangle=45)
                st.plotly_chart(fig_line, use_container_width=True)

        # ── District-wise insurance ───────────────────────────────────────────
        st.subheader(f"District-wise Insurance Analysis — {year} Q{quarter}")
        df_district = pd.read_sql(f"""
            SELECT District, State, SUM(Amount) AS Total_Amount, SUM(Count) AS Total_Count
            FROM Map_Insurance
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY District, State
            ORDER BY Total_Amount DESC
            LIMIT 10
        """, conn)
        if not df_district.empty:
            fig_district = px.bar(
                df_district, x="District", y="Total_Amount",
                color="Total_Amount", color_continuous_scale="Greens",
                title="Top 10 Districts by Insurance Amount"
            )
            fig_district.update_xaxes(tickangle=45)
            st.plotly_chart(fig_district, use_container_width=True)
        else:
            st.warning(f"No district-level insurance data for {year} Q{quarter}.")

        # ── Top 10 states - horizontal bar ───────────────────────────────────
        st.subheader(f"Top 10 States in Insurance — {year} Q{quarter}")
        if not df.empty:
            fig_hbar = px.bar(
                df.head(10).sort_values("Total_Insurance"),
                x="Total_Insurance", y="State", orientation="h",
                color="Total_Insurance", color_continuous_scale="Greens",
                title="Top 10 States — Insurance Amount"
            )
            st.plotly_chart(fig_hbar, use_container_width=True)

        # ── Count vs Amount scatter ───────────────────────────────────────────
        st.subheader("Insurance Transaction Count vs Amount")
        if not df.empty:
            fig_scatter = px.scatter(
                df, x="Total_Policies", y="Total_Insurance",
                hover_name="State", size="Total_Insurance",
                color="Total_Insurance", color_continuous_scale="Greens",
                title=f"Policy Count vs Insurance Amount by State — {year} Q{quarter}",
                labels={"Total_Policies": "Number of Policies", "Total_Insurance": "Insurance Amount"}
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ── Low insurance adoption states ────────────────────────────────────
        st.subheader("Low Insurance Adoption States")
        if not df.empty:
            low_adoption = df.sort_values("Total_Insurance").head(10)
            st.dataframe(
                low_adoption[["State", "Total_Insurance", "Total_Policies"]],
                use_container_width=True, hide_index=True
            )

        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

        # ── Insights ──────────────────────────────────────────────────────────
        st.subheader("Insights")
        if not df.empty:
            st.info(f"📌 Highest Insurance State: {df.iloc[0]['State']} — ₹{df.iloc[0]['Total_Insurance']:,.0f}")
            lowest_ins = df.sort_values("Total_Insurance").iloc[0]
            st.info(f"📌 Lowest Insurance State: {lowest_ins['State']} — ₹{lowest_ins['Total_Insurance']:,.0f}")
        if len(df_trend) >= 2:
            latest_t = df_trend.iloc[-1]
            first_t = df_trend.iloc[0]
            st.info(
                f"📌 Growth Opportunity: National insurance amount rose from "
                f"₹{first_t['Total_Amount']:,.0f} ({first_t['Period']}) to "
                f"₹{latest_t['Total_Amount']:,.0f} ({latest_t['Period']}) — "
                f"states still in the bottom 10 above represent the biggest untapped potential."
            )

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 4 — MARKET EXPANSION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 4 - Market Expansion":
    st.title("Case 4 — Transaction Analysis for Market Expansion")
    st.write("Identify the top-performing states and year-over-year growth for strategic expansion.")
    st.markdown("---")

    try:
        df_top10 = pd.read_sql(f"""
            SELECT State,
                   SUM(Amount) AS Total_Amount,
                   SUM(Count)  AS Total_Count
            FROM Map_Transaction
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Amount DESC
            LIMIT 10
        """, conn)
        df_top10 = clean_state_names(df_top10)

        df_all = pd.read_sql(f"""
            SELECT State,
                   SUM(Amount) AS Total_Amount
            FROM Map_Transaction
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
        """, conn)
        df_all = clean_state_names(df_all)

        df_yoy = pd.read_sql("""
            SELECT Year,
                   SUM(Amount) AS Total_Amount
            FROM Map_Transaction
            GROUP BY Year
            ORDER BY Year
        """, conn)

        st.subheader(f"All States — Transaction Map ({year} Q{quarter})")
        if not df_all.empty:
            fig_map = px.choropleth(
                df_all,
                geojson=GEOJSON_URL,
                featureidkey="properties.ST_NM",
                locations="State",
                color="Total_Amount",
                hover_name="State",
                color_continuous_scale="Blues",
                title=f"Transaction Amount — {year} Q{quarter}"
            )
            fig_map.update_geos(fitbounds="locations", visible=False)
            fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_map, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Top 10 States — {year} Q{quarter}")
            fig_bar = px.bar(
                df_top10, x="State", y="Total_Amount",
                color="Total_Amount", color_continuous_scale="Blues",
                title="Top 10 States by Transaction Amount"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Year-over-Year Growth")
            if not df_yoy.empty:
                fig_yoy = px.bar(
                    df_yoy, x="Year", y="Total_Amount",
                    title="Year-over-Year Total Transaction Amount",
                    color_discrete_sequence=["#5F2D82"]
                )
                st.plotly_chart(fig_yoy, use_container_width=True)

        # ── Bottom 10 states ──────────────────────────────────────────────────
        st.subheader(f"Bottom 10 States — {year} Q{quarter}")
        df_bottom10 = pd.read_sql(f"""
            SELECT State, SUM(Amount) AS Total_Amount
            FROM Map_Transaction
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Amount ASC
            LIMIT 10
        """, conn)
        df_bottom10 = clean_state_names(df_bottom10)
        if not df_bottom10.empty:
            fig_bottom = px.bar(
                df_bottom10, x="State", y="Total_Amount",
                color="Total_Amount", color_continuous_scale="Reds",
                title="Bottom 10 States by Transaction Amount"
            )
            fig_bottom.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bottom, use_container_width=True)

        # ── Potential expansion states: low volume but high recent growth ────
        st.subheader("Potential Expansion States (Low Current Volume, High Growth)")
        df_growth = pd.read_sql("""
            SELECT State, Year, SUM(Amount) AS Total_Amount
            FROM Map_Transaction
            WHERE Year IN (2023, 2024)
            GROUP BY State, Year
        """, conn)

        if not df_growth.empty and df_growth["Year"].nunique() == 2:
            pivot = df_growth.pivot(index="State", columns="Year", values="Total_Amount").reset_index()
            pivot.columns = ["State", "Amount_Prev", "Amount_Latest"]
            pivot["Growth_Pct"] = (
                (pivot["Amount_Latest"] - pivot["Amount_Prev"]) / pivot["Amount_Prev"] * 100
            )
            median_amt = pivot["Amount_Latest"].median()
            expansion = (
                pivot[pivot["Amount_Latest"] < median_amt]
                .sort_values("Growth_Pct", ascending=False)
                .head(10)
            )
            expansion = clean_state_names(expansion)
            st.caption("States with below-median current transaction volume but the fastest 2023→2024 growth — good candidates for early investment before they become saturated.")
            st.dataframe(
                expansion[["State", "Amount_Prev", "Amount_Latest", "Growth_Pct"]]
                .round({"Growth_Pct": 1}),
                use_container_width=True, hide_index=True
            )
        else:
            expansion = pd.DataFrame()
            st.warning("Not enough year coverage (need both 2023 and 2024 data) to compute expansion candidates.")

        st.subheader("Data Table — Top 10 States")
        st.dataframe(df_top10, use_container_width=True)

        # ── Insights ──────────────────────────────────────────────────────────
        st.subheader("Insights")
        if not df_top10.empty:
            st.info(f"📌 Best Market: {df_top10.iloc[0]['State']} — ₹{df_top10.iloc[0]['Total_Amount']:,.0f} ({year} Q{quarter})")
        if not df_bottom10.empty:
            st.info(f"📌 Untapped Market (lowest volume): {df_bottom10.iloc[0]['State']} — ₹{df_bottom10.iloc[0]['Total_Amount']:,.0f} ({year} Q{quarter})")
        if not expansion.empty:
            top_expansion = expansion.iloc[0]
            st.info(
                f"📌 Recommended Expansion State: {top_expansion['State']} — "
                f"grew {top_expansion['Growth_Pct']:.1f}% from 2023 to 2024 despite still being below the national median volume"
            )

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 5 — USER REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 5 - User Registration":
    st.title("Case 5 — User Registration Analysis")
    st.write("Find the top states and districts by registered users.")
    st.markdown("---")

    try:
        df_state = pd.read_sql(f"""
            SELECT State,
                   SUM(RegisteredUsers) AS Total_Users,
                   SUM(AppOpens)        AS Total_AppOpens
            FROM Map_User
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY State
            ORDER BY Total_Users DESC
        """, conn)
        df_state = clean_state_names(df_state)

        df_district = pd.read_sql(f"""
            SELECT District, State,
                   SUM(RegisteredUsers) AS Total_Users
            FROM Map_User
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY District, State
            ORDER BY Total_Users DESC
            LIMIT 10
        """, conn)

        st.subheader(f"Registered Users by State — {year} Q{quarter}")
        fig_map = px.choropleth(
            df_state,
            geojson=GEOJSON_URL,
            featureidkey="properties.ST_NM",
            locations="State",
            color="Total_Users",
            hover_name="State",
            color_continuous_scale="Reds",
            title=f"Registered Users — {year} Q{quarter}"
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_map, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 10 States")
            fig_bar = px.bar(
                df_state.head(10), x="State", y="Total_Users",
                color="Total_Users", color_continuous_scale="Reds",
                title="Top 10 States by Registered Users"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Top 10 Districts")
            if not df_district.empty:
                fig_d = px.bar(
                    df_district, x="District", y="Total_Users",
                    color="Total_Users", color_continuous_scale="Oranges",
                    title="Top 10 Districts by Registered Users"
                )
                fig_d.update_xaxes(tickangle=45)
                st.plotly_chart(fig_d, use_container_width=True)
            else:
                st.warning("No district data available for this period.")

        # ── Top Pincodes ───────────────────────────────────────────────────────
        st.subheader(f"Top 10 Pincodes by Registered Users — {year} Q{quarter}")
        df_pin = pd.read_sql(f"""
            SELECT Pincode, State, SUM(RegisteredUsers) AS Total_Users
            FROM Top_User_Pincodes
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY Pincode, State
            ORDER BY Total_Users DESC
            LIMIT 10
        """, conn)
        if not df_pin.empty:
            df_pin["Pincode"] = df_pin["Pincode"].astype(str)
            fig_pin = px.bar(
                df_pin, x="Pincode", y="Total_Users",
                color="Total_Users", color_continuous_scale="Reds",
                title="Top 10 Pincodes by Registered Users",
                hover_data=["State"]
            )
            fig_pin.update_xaxes(type="category", tickangle=45)
            st.plotly_chart(fig_pin, use_container_width=True)
            st.dataframe(df_pin, use_container_width=True, hide_index=True)
        else:
            st.warning(f"No pincode data available for {year} Q{quarter}.")

        # ── Registration growth trend ────────────────────────────────────────
        st.subheader("Registration Growth Trend (National)")
        df_growth_trend = pd.read_sql("""
            SELECT Year, Quarter, SUM(RegisteredUsers) AS Total_Users
            FROM Map_User
            GROUP BY Year, Quarter
            ORDER BY Year, Quarter
        """, conn)
        if not df_growth_trend.empty:
            df_growth_trend["Period"] = (
                df_growth_trend["Year"].astype(str) + "-Q" + df_growth_trend["Quarter"].astype(str)
            )
            fig_growth = px.line(
                df_growth_trend, x="Period", y="Total_Users", markers=True,
                title="Cumulative Registered Users Over Time (National)"
            )
            fig_growth.update_xaxes(tickangle=45)
            st.plotly_chart(fig_growth, use_container_width=True)

        st.subheader("All States — Data Table")
        st.dataframe(df_state, use_container_width=True)

        # ── Insights ──────────────────────────────────────────────────────────
        st.subheader("Insights")
        if not df_state.empty:
            st.info(f"📌 Highest Registered State: {df_state.iloc[0]['State']} — {df_state.iloc[0]['Total_Users']:,} users")
        if not df_district.empty:
            st.info(f"📌 Highest Registered District: {df_district.iloc[0]['District']} ({df_district.iloc[0]['State']}) — {df_district.iloc[0]['Total_Users']:,} users")
        if len(df_growth_trend) >= 2:
            df_growth_trend["QoQ_Growth"] = df_growth_trend["Total_Users"].diff()
            fastest = df_growth_trend.sort_values("QoQ_Growth", ascending=False).iloc[0]
            st.info(
                f"📌 Fastest Growing Period: {fastest['Period']} added "
                f"{fastest['QoQ_Growth']:,.0f} new registered users nationally compared to the prior quarter"
            )

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# INDIA MAP EXPLORER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "India Map Explorer":
    st.title("🗺️ India Map Explorer")
    st.write("Switch between metrics to explore India-wide trends on a single map.")
    st.markdown("---")

    metric = st.radio(
        "Pick a metric to display",
        ["Transaction Amount", "Registered Users", "Insurance Amount"],
        horizontal=True
    )

    try:
        if metric == "Transaction Amount":
            df_map = pd.read_sql(f"""
                SELECT State, SUM(Transaction_Amount) AS Value
                FROM Aggregated_Transaction
                WHERE Year = {year} AND Quarter = {quarter}
                GROUP BY State
            """, conn)
            color_scale = "Purples"
            title = f"Transaction Amount — {year} Q{quarter}"

        elif metric == "Registered Users":
            df_map = pd.read_sql(f"""
                SELECT State, SUM(RegisteredUsers) AS Value
                FROM Map_User
                WHERE Year = {year} AND Quarter = {quarter}
                GROUP BY State
            """, conn)
            color_scale = "Reds"
            title = f"Registered Users — {year} Q{quarter}"

        else:
            df_map = pd.read_sql(f"""
                SELECT State, SUM(Insurance_Amount) AS Value
                FROM Aggregated_Insurance
                WHERE Year = {year} AND Quarter = {quarter}
                GROUP BY State
            """, conn)
            color_scale = "Greens"
            title = f"Insurance Amount — {year} Q{quarter}"

        df_map = clean_state_names(df_map)

        if df_map.empty:
            st.warning("No data for this year and quarter combination.")
        else:
            fig = px.choropleth(
                df_map,
                geojson=GEOJSON_URL,
                featureidkey="properties.ST_NM",
                locations="State",
                color="Value",
                hover_name="State",
                color_continuous_scale=color_scale,
                title=title
            )
            fig.update_geos(fitbounds="locations", visible=False)
            fig.update_layout(height=550, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 5 States")
                st.dataframe(
                    df_map.sort_values("Value", ascending=False).head(5).reset_index(drop=True),
                    use_container_width=True
                )
            with col2:
                st.subheader("Bottom 5 States")
                st.dataframe(
                    df_map.sort_values("Value").head(5).reset_index(drop=True),
                    use_container_width=True
                )

    except Exception as e:
        st.error(f"Error: {e}")
