
import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="AI Credit Disputer", layout="wide")
st.title("📄 AI Credit Disputer")

# Create storage path
storage_dir = Path("stored_reports")
storage_dir.mkdir(exist_ok=True)

# Upload JSON credit report
st.subheader("📤 Upload Credit Report (JSON)")
uploaded_file = st.file_uploader("Upload your credit report", type="json")

if uploaded_file:
    report_data = json.load(uploaded_file)
    consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown")
    credit_score = report_data.get("consumer_info", {}).get("credit_score", 0)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # Store the report
    consumer_key = consumer_name.replace(" ", "_")
    save_path = storage_dir / consumer_key / timestamp
    save_path.mkdir(parents=True, exist_ok=True)
    with open(save_path / "report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    st.success(f"Report uploaded for {consumer_name} at {timestamp}")

    # === Credit Score Display ===
    st.subheader("📈 Credit Score Overview")
    score_color = "#e74c3c" if credit_score < 580 else "#f39c12" if credit_score < 670 else "#2ecc71"
    score_status = "Poor" if credit_score < 580 else "Fair" if credit_score < 670 else "Good"
    st.markdown(f"<div style='padding:10px; border-left: 6px solid {score_color};'><h3>{consumer_name}</h3>"
                f"<b>Score:</b> <span style='color:{score_color}; font-size:20px;'>{credit_score}</span> — {score_status}</div>",
                unsafe_allow_html=True)

    # === Account Breakdown and Letter Generator ===
    st.subheader("📋 Account Analysis & Letter Generator")

    tradelines = report_data.get("tradelines", [])
    collections = report_data.get("collections", [])
    items = tradelines + collections

    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        balance = item.get("balance", item.get("amount", 0))
        status = item.get("status", "N/A")
        reported = item.get("last_reported", "N/A")

score = 0
        breakdown = []

        if "charge" in status.lower():
            score += 3
            breakdown.append("+3 Charge-off or Charged status")
        if "late" in status.lower():
            score += 2
            breakdown.append("+2 Late payment history")
        if balance and balance > 1000:
            score += 2
            breakdown.append("+2 High balance over $1000")
        if "collection" in item.get("remarks", "").lower():
            score += 2
            breakdown.append("+2 Collection remarks present")
        if not breakdown:
            breakdown.append("0 – No dispute indicators found")

        st.markdown(f"### {creditor}")
        st.markdown(f"""**Status:** {status}  
**Balance:** ${balance}  
**Last Reported:** {reported}""")
        st.markdown(f"🧠 **Dispute Score:** `{score}/10`")
        with st.expander("🔍 Score Breakdown"):
            for line in breakdown:
                st.markdown(f"- {line}")
        st.markdown(f"### {creditor}")
        st.markdown(f"""**Status:** {status}  
**Balance:** ${balance}  
**Last Reported:** {reported}""")
        st.markdown(f"🧠 **Dispute Score:** `{score}/10`")

        bureau = st.selectbox("Select Bureau", ["TransUnion", "Experian", "Equifax"], key=f"bureau_{i}")
        reason = st.selectbox("Select Dispute Reason", ["Not Mine", "Never Late", "Already Paid", "Wrong Balance", "Request Validation"], key=f"reason_{i}")
        if st.button(f"Generate Letter for {creditor}", key=f"btn_{i}"):
            st.success(f"Letter generated for {bureau} with reason: {reason}")


        # === PDF Letter Generation ===
        if st.button(f"📄 Download Letter PDF for {creditor}", key=f"pdf_{i}"):
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            c.setFont("Helvetica", 12)
            c.drawString(50, 800, f"{bureau}")
            c.drawString(50, 780, f"Consumer: {consumer_name}")
            c.drawString(50, 760, f"Subject: Dispute Letter")
            c.drawString(50, 740, f"Dear {bureau},")
            c.drawString(50, 720, f"I am writing to dispute the following account from my credit report.")
            c.drawString(50, 700, f"Creditor: {creditor}")
            c.drawString(50, 680, f"Status: {status}")
            c.drawString(50, 660, f"Balance: ${balance}")
            c.drawString(50, 640, f"Dispute Reason: {reason}")
            c.drawString(50, 620, "Under the FCRA, please investigate and correct this item.")
            c.drawString(50, 600, f"Thank you,")
            c.drawString(50, 580, f"{consumer_name}")
            c.save()
            buffer.seek(0)
            st.download_button("📥 Download PDF", data=buffer, file_name=f"{consumer_key}_{creditor}_dispute_letter.pdf", mime="application/pdf")