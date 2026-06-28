import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
import json
import subprocess

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PhonePe Transaction Insights",
    page_icon="📱",
    layout="wide"
)

# ── Constants ─────────────────────────────────────────────────────────────────
DB_PATH    = "phonep_project.db"
PULSE_PATH = "pulse"
GEOJSON_URL = (
    "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112"
    "/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
)

# ── Database builder (runs once on first launch) ───────────────────────────────
def clone_pulse():
    if not os.path.exists(PULSE_PATH):
        st.write("📥 Cloning PhonePe Pulse repository...")
        subprocess.run(
            ["git", "clone", "--depth=1",
             "https://github.com/PhonePe/pulse.git", PULSE_PATH],
            check=True
        )

def load_agg_insurance(base):
    rows = []
    path = os.path.join(base, "aggregated/insurance/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                for i in data["data"]["transactionData"]:
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "Insurance_Type": i["name"],
                        "Insurance_Count": i["paymentInstruments"][0]["count"],
                        "Insurance_Amount": i["paymentInstruments"][0]["amount"]
                    })
    return pd.DataFrame(rows)

def load_agg_transaction(base):
    rows = []
    path = os.path.join(base, "aggregated/transaction/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                for i in data["data"]["transactionData"]:
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "Transaction_Type": i["name"],
                        "Transaction_Count": i["paymentInstruments"][0]["count"],
                        "Transaction_Amount": i["paymentInstruments"][0]["amount"]
                    })
    return pd.DataFrame(rows)

def load_agg_user(base):
    rows = []
    path = os.path.join(base, "aggregated/user/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                if data["data"] and data["data"].get("usersByDevice"):
                    for u in data["data"]["usersByDevice"]:
                        rows.append({
                            "State": state, "Year": int(year),
                            "Quarter": int(f.strip(".json")),
                            "Brand": u["brand"],
                            "Count": u["count"],
                            "Percentage": u["percentage"]
                        })
    return pd.DataFrame(rows)

def load_map_insurance(base):
    rows = []
    path = os.path.join(base, "map/insurance/hover/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                for e in data["data"]["hoverDataList"]:
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "District": e["name"],
                        "Count": e["metric"][0]["count"],
                        "Amount": e["metric"][0]["amount"]
                    })
    return pd.DataFrame(rows)

def load_map_transaction(base):
    rows = []
    path = os.path.join(base, "map/transaction/hover/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                for i in data["data"]["hoverDataList"]:
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "District": i["name"],
                        "Count": i["metric"][0]["count"],
                        "Amount": i["metric"][0]["amount"]
                    })
    return pd.DataFrame(rows)

def load_map_user(base):
    rows = []
    path = os.path.join(base, "map/user/hover/country/india/state")
    for state in os.listdir(path):
        for year in os.listdir(os.path.join(path, state)):
            for f in os.listdir(os.path.join(path, state, year)):
                with open(os.path.join(path, state, year, f)) as fp:
                    data = json.load(fp)
                for dist, val in data["data"]["hoverData"].items():
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "District": dist,
                        "RegisteredUsers": val["registeredUsers"],
                        "AppOpens": val["appOpens"]
                    })
    return pd.DataFrame(rows)

def load_top_user_pincodes(base):
    rows = []
    path = os.path.join(base, "top/user/country/india/state")
    for state in os.listdir(path):
        state_path = os.path.join(path, state)
        if not os.path.isdir(state_path):
            continue
        for year in os.listdir(state_path):
            year_path = os.path.join(state_path, year)
            if not os.path.isdir(year_path):
                continue
            for f in os.listdir(year_path):
                with open(os.path.join(year_path, f)) as fp:
                    data = json.load(fp)
                for pin in data["data"].get("pincodes", []):
                    rows.append({
                        "State": state, "Year": int(year),
                        "Quarter": int(f.strip(".json")),
                        "Pincode": str(pin["name"]),
                        "RegisteredUsers": pin["registeredUsers"]
                    })
    return pd.DataFrame(rows)

def build_database():
    base = os.path.join(PULSE_PATH, "data")
    progress = st.progress(0, text="Starting setup...")

    clone_pulse()
    progress.progress(10, text="Loading Aggregated Insurance...")
    df_agg_ins  = load_agg_insurance(base)

    progress.progress(22, text="Loading Aggregated Transaction...")
    df_agg_txn  = load_agg_transaction(base)

    progress.progress(36, text="Loading Aggregated User...")
    df_agg_user = load_agg_user(base)

    progress.progress(50, text="Loading Map Insurance...")
    df_map_ins  = load_map_insurance(base)

    progress.progress(62, text="Loading Map Transaction...")
    df_map_txn  = load_map_transaction(base)

    progress.progress(74, text="Loading Map User...")
    df_map_user = load_map_user(base)

    progress.progress(86, text="Loading Top User Pincodes...")
    df_top_pin  = load_top_user_pincodes(base)

    progress.progress(94, text="Writing to database...")
    conn = sqlite3.connect(DB_PATH)
    df_agg_ins.to_sql("Aggregated_Insurance",   conn, if_exists="replace", index=False)
    df_agg_txn.to_sql("Aggregated_Transaction", conn, if_exists="replace", index=False)
    df_agg_user.to_sql("Aggregated_User",       conn, if_exists="replace", index=False)
    df_map_ins.to_sql("Map_Insurance",          conn, if_exists="replace", index=False)
    df_map_txn.to_sql("Map_Transaction",        conn, if_exists="replace", index=False)
    df_map_user.to_sql("Map_User",              conn, if_exists="replace", index=False)
    df_top_pin.to_sql("Top_User_Pincodes",      conn, if_exists="replace", index=False)
    conn.close()

    progress.progress(100, text="Done!")
    st.success("Database ready! The app will now reload.")
    st.rerun()

# ── First-time setup ──────────────────────────────────────────────────────────
if not os.path.exists(DB_PATH):
    st.title("📱 PhonePe Transaction Insights")
    st.info("Setting up for the first time — this takes about 2-3 minutes and only happens once.")
    build_database()
    st.stop()

# ── Connect to database ────────────────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

conn = get_conn()

# ── Helper: clean state name for choropleth matching ──────────────────────────
def clean_state_names(df, col="State"):
    df = df.copy()
    df[col] = (df[col]
               .str.replace("-", " ")
               .str.replace("&", "and")
               .str.title()
               .str.strip())
    return df

# ── Sidebar ────────────────────────────────────────────────────────────────────
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
year    = st.sidebar.selectbox("Year",    [2018, 2019, 2020, 2021, 2022, 2023, 2024], index=5)
quarter = st.sidebar.selectbox("Quarter", [1, 2, 3, 4])

# ══════════════════════════════════════════════════════════════════════════════
# HOME PAGE
# ══════════════════════════════════════════════════════════════════════════════
if page == "Home":
    st.title("📱 PhonePe Transaction Insights")
    st.write("Interactive dashboard built on PhonePe Pulse open data")
    st.markdown("---")

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    try:
        total_txn     = pd.read_sql("SELECT SUM(Transaction_Amount) FROM Aggregated_Transaction", conn).iloc[0,0]
        total_users   = pd.read_sql("SELECT SUM(RegisteredUsers) FROM Map_User", conn).iloc[0,0]
        total_ins     = pd.read_sql("SELECT SUM(Insurance_Amount) FROM Aggregated_Insurance", conn).iloc[0,0]
        total_records = pd.read_sql("SELECT COUNT(*) FROM Aggregated_Transaction", conn).iloc[0,0]

        col1.metric("Total Transaction Value", f"₹{total_txn/1e12:.2f} T")
        col2.metric("Registered Users",        f"{total_users/1e6:.1f} M")
        col3.metric("Insurance Amount",        f"₹{total_ins/1e9:.1f} B")
        col4.metric("Transaction Records",     f"{int(total_records):,}")
    except Exception as e:
        st.warning(f"Could not load KPIs: {e}")

    st.markdown("---")

    # About section
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("About This Project")
        st.write("""
        This dashboard analyses PhonePe Pulse — India's open-source digital payments dataset.

        **What's covered:**
        - Transaction trends across all Indian states
        - Device brand usage and user engagement
        - Insurance product penetration
        - Geographic heatmaps on India map
        - Top districts and pincodes by user registration
        """)

    with col_b:
        st.subheader("Database Tables")
        tables = [
            "Aggregated_Transaction",
            "Aggregated_User",
            "Aggregated_Insurance",
            "Map_Transaction",
            "Map_User",
            "Map_Insurance",
            "Top_User_Pincodes"
        ]
        for t in tables:
            st.write(f"✅  {t}")

    st.markdown("---")
    st.subheader("How to use")
    st.write("Use the **sidebar** to navigate between the 5 business case studies. "
             "Select a **Year** and **Quarter** from the sidebar filters to update all charts.")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 1 — TRANSACTION DYNAMICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 1 - Transaction Dynamics":
    st.title("Case 1 — Decoding Transaction Dynamics")
    st.write("Analyse how transaction amounts and counts vary across Indian states and payment categories.")
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

        # India map
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
            st.subheader("Bar Chart — Top States")
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
            st.info(f"📌 **Top State:** {df.iloc[0]['State']} with ₹{df.iloc[0]['Total_Amount']:,.0f}")

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
            fig_pie = px.pie(
                df, names="Brand", values="Total_Users",
                hole=0.45, title="Device Brand Market Share"
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader(f"Top 10 Brands — {year} Q{quarter}")
            fig_bar = px.bar(
                df, x="Brand", y="Total_Users",
                color="Total_Users", color_continuous_scale="Purples",
                title="Users by Device Brand"
            )
            fig_bar.update_xaxes(tickangle=45)
            st.plotly_chart(fig_bar, use_container_width=True)

        st.subheader("Brand Trend Over Time (Top 5 Brands)")
        if not df_trend.empty:
            top5 = df["Brand"].head(5).tolist()
            df_trend_top = df_trend[df_trend["Brand"].isin(top5)].copy()
            df_trend_top["Period"] = (df_trend_top["Year"].astype(str)
                                      + "-Q" + df_trend_top["Quarter"].astype(str))
            fig_line = px.line(
                df_trend_top, x="Period", y="Total_Users", color="Brand",
                title="Top 5 Brands — User Count Over Time"
            )
            fig_line.update_xaxes(tickangle=45)
            st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("Data Table")
        st.dataframe(df, use_container_width=True)

        if not df.empty:
            st.info(f"📌 **Top Device Brand:** {df.iloc[0]['Brand']} "
                    f"with {df.iloc[0]['Total_Users']:,} users")

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

        # India map
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
            st.subheader("Bar Chart — Top States")
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
            st.info(f"📌 **Top 3 States:** {', '.join(top3)}")

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
                   SUM(Amount) AS Total_Amount,
                   SUM(Count)  AS Total_Count
            FROM Map_Transaction
            GROUP BY Year
            ORDER BY Year
        """, conn)

        # India map
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
            st.subheader("Treemap — Top 10 States")
            if not df_top10.empty:
                fig_tree = px.treemap(
                    df_top10, path=["State"], values="Total_Amount",
                    title="Treemap: Top 10 States by Transaction Amount"
                )
                st.plotly_chart(fig_tree, use_container_width=True)

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
            st.info(f"📌 **Top State:** {df_top10.iloc[0]['State']}")

    except Exception as e:
        st.error(f"Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# CASE 5 — USER REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Case 5 - User Registration":
    st.title("Case 5 — User Registration Analysis")
    st.write("Find the top states, districts, and pincodes by registered users.")
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

        df_pin = pd.read_sql(f"""
            SELECT Pincode, State,
                   SUM(RegisteredUsers) AS Total_Users
            FROM Top_User_Pincodes
            WHERE Year = {year} AND Quarter = {quarter}
            GROUP BY Pincode, State
            ORDER BY Total_Users DESC
            LIMIT 10
        """, conn)
        # Fix: cast Pincode to string so it shows as label not numeric axis
        if not df_pin.empty:
            df_pin["Pincode"] = df_pin["Pincode"].astype(str)

        # India map
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

        st.subheader("Top 10 Pincodes")
        if not df_pin.empty:
            fig_pin = px.bar(
                df_pin, x="Pincode", y="Total_Users",
                color="Total_Users", color_continuous_scale="Reds",
                title="Top 10 Pincodes by Registered Users",
                text="Pincode"
            )
            fig_pin.update_traces(textposition="outside")
            fig_pin.update_xaxes(type="category")  # treats pincode as label not number
            st.plotly_chart(fig_pin, use_container_width=True)
            st.dataframe(df_pin, use_container_width=True)
        else:
            st.warning("No pincode data available for this period.")

        st.subheader("All States — Data Table")
        st.dataframe(df_state, use_container_width=True)

        if not df_state.empty:
            st.info(f"📌 **Top State:** {df_state.iloc[0]['State']} "
                    f"with {df_state.iloc[0]['Total_Users']:,} registered users")

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
