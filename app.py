import streamlit as st
import requests
from PIL import Image
import pandas as pd
from datetime import datetime
import os

# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="AI Chest X-ray Assistant",
    page_icon="🩺",
    layout="wide"
)

# ==========================================================
# TITLE
# ==========================================================

st.title("🩺 AI Chest X-ray Disease Detection Assistant")

st.markdown("""
### Features

✅ FastAPI Backend

✅ ResNet18 Disease Detection

✅ Gemini Medical Explanation

✅ Professional AI Architecture

""")

# ==========================================================
# SIDEBAR
# ==========================================================

with st.sidebar:

    st.header("📌 Project Information")

    st.write("""

    **Frontend:** Streamlit

    **Backend:** FastAPI (Railway)

    **Deep Learning Model:** ResNet18

    **LLM:** Gemini

    **Diseases:** 15 Chest Diseases

    """)

    st.info(
        "Upload a Chest X-ray image for analysis."
    )

# ==========================================================
# FILE UPLOAD
# ==========================================================

uploaded_file = st.file_uploader(

    "📤 Upload Chest X-ray",

    type=["png", "jpg", "jpeg"]
)

# ==========================================================
# PREDICTION
# ==========================================================

if uploaded_file:

    image = Image.open(
        uploaded_file
    ).convert("RGB")

    col1, col2 = st.columns(2)

    # ======================================================
    # SHOW IMAGE
    # ======================================================

    with col1:

        st.image(

            image,

            caption="Uploaded X-ray",

            use_container_width=True
        )

    # ======================================================
    # SEND TO FASTAPI
    # ======================================================

    with st.spinner(

            "🔍 Sending image to FastAPI..."):

        files = {

            "file": (

                uploaded_file.name,

                uploaded_file.getvalue(),

                uploaded_file.type
            )
        }

        try:

            API_URL = "https://chestxray-production.up.railway.app/predict"

            response = requests.post(

                API_URL,

                files=files
            )

            result = response.json()

        except Exception as e:

            st.error(

                f"❌ Cannot connect to FastAPI Backend\n\n{e}"
            )

            st.stop()

    # ======================================================
    # GET RESULTS
    # ======================================================

    predicted_diseases = result.get(
        "predicted_diseases", []
    )

    probabilities = result.get(
        "probabilities", {}
    )

    explanation = result.get(
        "explanation",
        "No explanation received."
    )

    # ======================================================
    # PROBABILITY TABLE
    # ======================================================

    prob_df = pd.DataFrame({

        "Disease":

            list(probabilities.keys()),

        "Probability (%)":

            [

                round(v * 100, 2)

                for v in probabilities.values()
            ]
    })

    prob_df = prob_df.sort_values(

        "Probability (%)",

        ascending=False
    )

    with col2:

        st.subheader(

            "📊 Disease Probabilities"
        )

        st.dataframe(

            prob_df,

            use_container_width=True
        )

    # ======================================================
    # PREDICTED DISEASES
    # ======================================================

    st.subheader(

        "🩺 Predicted Diseases"
    )

    for disease in predicted_diseases:

        st.success(disease)

    # ======================================================
    # GEMINI EXPLANATION
    # ======================================================

    st.subheader(

        "🤖 AI Medical Explanation"
    )

    st.write(explanation)
    # ======================================================
# SHOW GRAD CAM
# ======================================================

if "gradcam" in result:

    import base64
    from io import BytesIO

    st.subheader(
        "🔥 Grad-CAM Visualization"
    )

    gradcam_bytes = base64.b64decode(
        result["gradcam"]
    )

    gradcam_image = Image.open(
        BytesIO(gradcam_bytes)
    )

    st.image(
        gradcam_image,
        caption="Important regions influencing prediction",
        use_container_width=True
    )

    # ======================================================
    # SAVE HISTORY
    # ======================================================

    history = pd.DataFrame({

        "Timestamp": [

            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ],

        "Image_Name": [

            uploaded_file.name
        ],

        "Predicted_Diseases": [

            ", ".join(
                predicted_diseases
            )
        ]
    })

    if os.path.exists(

            "prediction_history.csv"
    ):

        old = pd.read_csv(

            "prediction_history.csv"
        )

        history = pd.concat(

            [old, history],

            ignore_index=True
        )

    history.to_csv(

        "prediction_history.csv",

        index=False
    )

    # ======================================================
    # DOWNLOAD REPORT
    # ======================================================

    csv = prob_df.to_csv(

        index=False
    )

    st.download_button(

        "⬇️ Download Prediction Report",

        csv,

        "prediction_report.csv",

        "text/csv"
    )

    # ======================================================
    # DISCLAIMER
    # ======================================================

    st.warning("""

    ⚠️ Disclaimer

    This AI system is intended for educational
    and assistive purposes only.

    The predictions generated by this application
    should not be considered a final medical diagnosis.

    Always consult a qualified radiologist or
    healthcare professional.

    """)