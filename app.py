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

        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.info(f"📌 Top State: {df.iloc[0]['State']} — ₹{df.iloc[0]['Total_Amount']:,.0f}")

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

        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            top3 = df.head(3)["State"].tolist()
            st.info(f"📌 Top 3 States: {', '.join(top3)}")

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

        st.subheader("Data Table — Top 10 States")
        st.dataframe(df_top10, use_container_width=True)

        if not df_top10.empty:
            st.info(f"📌 Top State: {df_top10.iloc[0]['State']}")

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

        st.subheader("All States — Data Table")
        st.dataframe(df_state, use_container_width=True)

        if not df_state.empty:
            st.info(f"📌 Top State: {df_state.iloc[0]['State']} — {df_state.iloc[0]['Total_Users']:,} users")

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
