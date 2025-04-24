
import streamlit as st
import json

st.set_page_config(page_title="Client Credit Report Viewer", layout="wide")
st.title("📄 Full Credit Report Viewer")

# Simulated uploaded credit report data
try:
    uploaded_file = st.file_uploader("Upload a JSON Credit Report", type="json")

    if uploaded_file:
        data = json.load(uploaded_file)
        consumer_info = data.get("consumer_info", {})
        tradelines = data.get("tradelines", [])
        collections = data.get("collections", [])
        inquiries = data.get("inquiries", [])
        public_records = data.get("public_records", [])

        st.subheader("👤 Consumer Information")
        st.json(consumer_info)

        # Full tradelines
        st.subheader("🏦 Tradelines")
        for t in tradelines:
            is_negative = any(x in t.get("status", "").lower() for x in ["charge", "late", "off", "delinquent"])
            style = "background-color: #ffe6e6;" if is_negative else "background-color: #f4f4f4;"
            st.markdown(f"<div style='{style} padding: 10px; border-radius: 6px;'>"
                        f"<strong>{t.get('creditor_name')}</strong><br>"
                        f"Status: {t.get('status')}<br>"
                        f"Balance: ${t.get('balance')}<br>"
                        f"Reported: {t.get('last_reported', 'N/A')}<br>"
                        f"Remarks: {t.get('remarks', 'None')}</div><br>", unsafe_allow_html=True)

        # Collections
        st.subheader("🧾 Collection Accounts")
        for c in collections:
            st.markdown(f"<div style='background-color: #ffe6e6; padding: 10px; border-radius: 6px;'>"
                        f"<strong>{c.get('agency_name')}</strong><br>"
                        f"Original Creditor: {c.get('original_creditor', 'N/A')}<br>"
                        f"Status: {c.get('status')}<br>"
                        f"Balance: ${c.get('amount')}<br>"
                        f"Reported: {c.get('last_reported', 'N/A')}<br>"
                        f"Remarks: {c.get('remarks', 'None')}</div><br>", unsafe_allow_html=True)

        # Inquiries
        if inquiries:
            st.subheader("🔍 Credit Inquiries")
            for i in inquiries:
                st.markdown(f"**{i.get('business_name')}** - {i.get('inquiry_type')} on {i.get('date')}")

        # Public Records
        if public_records:
            st.subheader("⚖️ Public Records")
            st.json(public_records)

except Exception as e:
    st.error(f"Failed to process report: {e}")
