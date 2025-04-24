
import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt

st.set_page_config(page_title="AI Credit Disputer", layout="wide")
st.title("📄 AI Credit Disputer")

# Directories
storage_dir = Path("stored_reports")
storage_dir.mkdir(exist_ok=True)

# Upload report
st.subheader("📤 Upload Credit Report (JSON Format)")
uploaded_file = st.file_uploader("Upload your credit report", type="json")

if uploaded_file:
    report_data = json.load(uploaded_file)
    consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown")
    credit_score = report_data.get("consumer_info", {}).get("credit_score", 0)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Save report by consumer name
    consumer_key = consumer_name.replace(" ", "_")
    save_path = storage_dir / consumer_key / timestamp
    save_path.mkdir(parents=True, exist_ok=True)
    with open(save_path / "report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    st.success(f"Report uploaded for {consumer_name} ({timestamp})")

    # === Score Tracker ===
    st.subheader("📈 Credit Score")
    if credit_score:
        color = "#e74c3c" if credit_score < 580 else "#f1c40f" if credit_score < 670 else "#2ecc71"
        status = "📉 Poor" if credit_score < 580 else "⚠️ Fair" if credit_score < 670 else "📈 Good"
        st.markdown(f"<div style='padding:10px; border-left: 6px solid {color};'><h3>{consumer_name}</h3>"
                    f"<b>Score:</b> <span style='color:{color}; font-size:20px;'>{credit_score}</span> {status}</div>",
                    unsafe_allow_html=True)

    # === Account Scoring and Letter Tools ===
    st.subheader("📋 Account Analysis & Dispute Letter Builder")

    tradelines = report_data.get("tradelines", [])
    collections = report_data.get("collections", [])
    items = tradelines + collections

    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        balance = item.get("balance", item.get("amount", 0))
        status = item.get("status", "N/A")
        reported = item.get("last_reported", "N/A")

        score = 0
        if "charge" in status.lower(): score += 3
        if "late" in status.lower(): score += 2
        if balance and balance > 1000: score += 2
        if "collection" in item.get("remarks", "").lower(): score += 2

        st.markdown(f"### {creditor}")
st.markdown(f"**Status:** {status}  \n**Balance:** ${balance}  \n**Last Reported:** {reported}")
**Balance:** ${balance}  
**Last Reported:** {reported}")
        st.markdown(f"🔎 **Dispute Score:** `{score}/10`")

        bureau = st.selectbox(f"Bureau to dispute with", ["TransUnion", "Experian", "Equifax"], key=f"bureau_{i}")
        reason = st.selectbox(f"Dispute Reason", ["Not Mine", "Never Late", "Already Paid", "Wrong Balance", "Request Validation"], key=f"reason_{i}")
        if st.button(f"Generate Letter for {creditor}", key=f"gen_{i}"):
            st.success(f"Letter for {bureau} — Reason: {reason} generated for {creditor}. (PDF download coming next)")