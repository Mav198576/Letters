
import streamlit as st
import pandas as pd
import random
import uuid
from datetime import datetime

st.set_page_config(page_title="AI Credit Disputer", layout="wide")

# --- Sample Fake Data ---
leads_data = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Lead {i}",
        "email": f"lead{i}@example.com",
        "source": random.choice(["Facebook", "Website", "Referral"]),
        "status": random.choice(["New", "Hot", "Follow-Up"]),
        "added": datetime.now().strftime("%Y-%m-%d")
    } for i in range(1, 11)
]

clients_data = [
    {
        "id": str(uuid.uuid4()),
        "name": f"Client {i}",
        "email": f"client{i}@example.com",
        "score": random.randint(580, 750),
        "joined": datetime.now().strftime("%Y-%m-%d")
    } for i in range(1, 11)
]

# --- UI Tabs ---
st.title("AI Credit Disputer CRM")


tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Leads", "Clients", "Dispute Tools"])
with tab2:
    st.header("📇 Leads")
    search_leads = st.text_input("🔍 Search Leads", placeholder="Name or email", key="leads_tab2_search")
    status_filter = st.selectbox("Status Filter", ["All", "New", "Hot", "Follow-Up"])
    
    def filter_leads(leads, search_text, status_filter):
        today = datetime.now()
        filtered = []
        for lead in leads:
            if search_text.lower() in lead["name"].lower() or search_text.lower() in lead["email"].lower():
                if status_filter == "All" or lead["status"] == status_filter:
                    lead["inactive"] = (today - datetime.strptime(lead["added"], "%Y-%m-%d")).days > 30
                    filtered.append(lead)
        return filtered

    filtered_leads = filter_leads(leads_data, search_leads, status_filter)

    for lead in filtered_leads:
        st.markdown(f"**{lead['name']}** — {lead['email']} | Source: {lead['source']} | Status: {lead['status']}")
        if lead.get("inactive"):
            st.warning("⚠️ Inactive for 30+ days")
        st.markdown("---")

with tab3:
    st.header("👥 Clients")
    st.subheader("📈 Client Credit Score Summary")

    score_data = [c["score"] for c in clients_data]
    score_df = pd.DataFrame(score_data, columns=["Credit Score"])

    st.line_chart(score_df[["Credit Score"]])

    search_clients = st.text_input("🔍 Search Clients", placeholder="Name or email", key="clients_tab3_search_final")
    
    def filter_clients(clients, search_text):
        return [c for c in clients if search_text.lower() in c["name"].lower() or search_text.lower() in c["email"].lower()]

    filtered_clients = filter_clients(clients_data, search_clients)

    for client in filtered_clients:
        st.markdown(f"**{client['name']}** — {client['email']} | Score: {client['score']}")
        st.markdown("---")


import json

# --- Upload & Dispute Letter Generator ---

# --- Scoring Breakdown ---
def score_tradeline(item):
    score = 0
    breakdown = []

    if "charge" in item["status"].lower():
        score += 3
        breakdown.append("+3 Charge-Off")
    if "collection" in item["status"].lower():
        score -= 2
        breakdown.append("-2 Collection")
    if item.get("balance", 0) > 1000:
        score -= 1
        breakdown.append("-1 High Balance")
    if "late" in item["status"].lower():
        score -= 1
        breakdown.append("-1 Late")
    if "closed" in item["status"].lower():
        score += 1
        breakdown.append("+1 Closed Account")

    return score, breakdown

# Add scoring breakdown to Dispute Tools tab

# --- Phase 5: Store Reports and Show Upload Timeline ---
import os

REPORT_DIR = "uploaded_reports"
os.makedirs(REPORT_DIR, exist_ok=True)


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def generate_dispute_letter_pdf(consumer_name, tradelines, bureau_name, agency_name="Your Agency", logo_path=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if logo_path:
        try:
            c.drawImage(logo_path, 50, height - 80, width=100, preserveAspectRatio=True)
        except Exception as e:
            print("Logo error:", e)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 100, agency_name)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, f"To: {bureau_name}")
    c.drawString(50, height - 140, f"From: {consumer_name}")
    c.drawString(50, height - 160, "Re: Dispute of inaccurate items")

    y = height - 200
    for i, item in enumerate(tradelines, 1):
        text = f"{i}. {item['creditor_name']} - {item['status']}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 100

    c.drawString(50, y - 30, "Please investigate and remove any inaccurate information.")
    c.drawString(50, y - 60, "Sincerely,")
    c.drawString(50, y - 80, consumer_name)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

# Add PDF button in Dispute Tools section
with tab4:
    st.header("📤 Upload Credit Report")

    uploaded_file = st.file_uploader("Upload JSON credit report", type="json")
    logo_path = st.text_input("Optional Logo Path (for PDF)")
    agency_name = st.text_input("Agency Name", value="Your Agency")

    if uploaded_file:
        try:
            report_data = json.load(uploaded_file)
            consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown Consumer")
            tradelines = report_data.get("tradelines", [])
            bureau = st.selectbox("Select Bureau", ["TransUnion", "Equifax", "Experian"])

            for i, item in enumerate(tradelines, 1):
                score, breakdown = score_tradeline(item)
                with st.expander(f"{i}. {item['creditor_name']}"):
                    st.markdown(f"- **Status:** {item['status']}")
                    st.markdown(f"- **Balance:** ${item['balance']}")
                    st.markdown(f"- **Last Reported:** {item['last_reported']}")
                    st.markdown(f"**Score Impact:** `{score}`")
                    st.markdown("**Breakdown:** " + ", ".join(breakdown))

            if st.button("🖨️ Generate PDF Letter"):
                pdf_file = generate_dispute_letter_pdf(consumer_name, tradelines, bureau, agency_name, logo_path)
                st.download_button("📄 Download PDF", data=pdf_file, file_name="dispute_letter.pdf")
        except Exception as e:
            st.error(f"Could not process report: {e}")

from datetime import timedelta
import numpy as np

# --- Enhanced Dashboard UI ---

with tab1:
    st.header("📊 Dashboard Overview")

    col1, col2 = st.columns(2)
    col1.metric("Total Leads", len(leads_data))
    col2.metric("Total Clients", len(clients_data))
    st.subheader("⚡ Quick Actions")
    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("📤 Upload Report"):
            st.session_state["jump_to_dispute_tools"] = True
    with colB:
        if st.button("➕ Add Lead"):
            st.info("Feature coming soon!")
    with colC:
        st.download_button("📄 Download Template", "Name, Email\nJohn Doe, john@example.com", file_name="lead_template.csv")


    st.subheader("🗓️ Today's Date")
    st.write(datetime.today().strftime("%A, %B %d, %Y"))

    st.subheader("📈 Client Credit Score Summary")

    score_data = [c["score"] for c in clients_data]
    score_df = pd.DataFrame(score_data, columns=["Credit Score"])

    st.line_chart(score_df[["Credit Score"]])

    search_clients = st.text_input("🔍 Search Clients", placeholder="Name or email", key="clients_tab3_search_final")
    
    def filter_clients(clients, search_text):
        return [c for c in clients if search_text.lower() in c["name"].lower() or search_text.lower() in c["email"].lower()]

    filtered_clients = filter_clients(clients_data, search_clients)

    for client in filtered_clients:
        st.markdown(f"**{client['name']}** — {client['email']} | Score: {client['score']}")
        st.markdown("---")


import json

# --- Upload & Dispute Letter Generator ---

# --- Scoring Breakdown ---
def score_tradeline(item):
    score = 0
    breakdown = []

    if "charge" in item["status"].lower():
        score += 3
        breakdown.append("+3 Charge-Off")
    if "collection" in item["status"].lower():
        score -= 2
        breakdown.append("-2 Collection")
    if item.get("balance", 0) > 1000:
        score -= 1
        breakdown.append("-1 High Balance")
    if "late" in item["status"].lower():
        score -= 1
        breakdown.append("-1 Late")
    if "closed" in item["status"].lower():
        score += 1
        breakdown.append("+1 Closed Account")

    return score, breakdown

# Add scoring breakdown to Dispute Tools tab

# --- Phase 5: Store Reports and Show Upload Timeline ---
import os

REPORT_DIR = "uploaded_reports"
os.makedirs(REPORT_DIR, exist_ok=True)


from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def generate_dispute_letter_pdf(consumer_name, tradelines, bureau_name, agency_name="Your Agency", logo_path=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if logo_path:
        try:
            c.drawImage(logo_path, 50, height - 80, width=100, preserveAspectRatio=True)
        except Exception as e:
            print("Logo error:", e)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 100, agency_name)
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, f"To: {bureau_name}")
    c.drawString(50, height - 140, f"From: {consumer_name}")
    c.drawString(50, height - 160, "Re: Dispute of inaccurate items")

    y = height - 200
    for i, item in enumerate(tradelines, 1):
        text = f"{i}. {item['creditor_name']} - {item['status']}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 100

    c.drawString(50, y - 30, "Please investigate and remove any inaccurate information.")
    c.drawString(50, y - 60, "Sincerely,")
    c.drawString(50, y - 80, consumer_name)
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer

# Add PDF button in Dispute Tools section
with tab4:
    st.header("📤 Upload Credit Report")

    uploaded_file = st.file_uploader("Upload JSON credit report", type="json")
    logo_path = st.text_input("Optional Logo Path (for PDF)")
    agency_name = st.text_input("Agency Name", value="Your Agency")

    if uploaded_file:
        try:
            report_data = json.load(uploaded_file)
            consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown Consumer")
            tradelines = report_data.get("tradelines", [])
            bureau = st.selectbox("Select Bureau", ["TransUnion", "Equifax", "Experian"])

            for i, item in enumerate(tradelines, 1):
                score, breakdown = score_tradeline(item)
                with st.expander(f"{i}. {item['creditor_name']}"):
                    st.markdown(f"- **Status:** {item['status']}")
                    st.markdown(f"- **Balance:** ${item['balance']}")
                    st.markdown(f"- **Last Reported:** {item['last_reported']}")
                    st.markdown(f"**Score Impact:** `{score}`")
                    st.markdown("**Breakdown:** " + ", ".join(breakdown))

            if st.button("🖨️ Generate PDF Letter"):
                pdf_file = generate_dispute_letter_pdf(consumer_name, tradelines, bureau, agency_name, logo_path)
                st.download_button("📄 Download PDF", data=pdf_file, file_name="dispute_letter.pdf")
        except Exception as e:
            st.error(f"Could not process report: {e}")