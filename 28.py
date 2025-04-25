
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

tab = st.selectbox("Navigation", ["Dashboard", "Leads", "Clients", "Dispute Tools"])

# --- Dashboard Charts ---

# --- Tab Routing with Filters and Alerts ---

if tab == "Dashboard":
    st.header("📊 Dashboard Overview")
    st.metric("Total Leads", len(leads_data))
    st.metric("Total Clients", len(clients_data))

    # Lead source breakdown
    source_df = pd.DataFrame([l["source"] for l in leads_data], columns=["Source"])
    source_counts = source_df["Source"].value_counts().reset_index()
    source_counts.columns = ["Source", "Count"]
    st.bar_chart(source_counts.set_index("Source"))

    # Client score trend
    score_df = pd.DataFrame([c["score"] for c in clients_data], columns=["Credit Score"])
    st.line_chart(score_df)

elif tab == "Leads":
    st.header("📇 Leads")
    search_leads = st.text_input("🔍 Search Leads", placeholder="Name or email")
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

elif tab == "Clients":
    st.header("👥 Clients")
    search_clients = st.text_input("🔍 Search Clients", placeholder="Name or email")
    
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

if tab == "Dispute Tools":
    st.header("📤 Upload Credit Report")

    uploaded_file = st.file_uploader("Upload JSON credit report", type="json")
    if uploaded_file:
        try:
            report_data = json.load(uploaded_file)
            consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown Consumer").replace(" ", "_")
            upload_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{consumer_name}_{upload_date}.json"
            file_path = os.path.join(REPORT_DIR, filename)

            with open(file_path, "w") as f:
                json.dump(report_data, f)
            st.success(f"Report saved as: {filename}")

            # Display current report
            st.markdown(f"### Consumer: **{report_data.get('consumer_info', {}).get('name', 'Unknown')}**")
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

        except Exception as e:
            st.error(f"Could not process report: {e}")

    # Show timeline of all stored reports
    st.subheader("📚 Stored Credit Reports")
    files = sorted(os.listdir(REPORT_DIR), reverse=True)
    for file in files:
        if file.endswith(".json"):
            with st.expander(file):
                with open(os.path.join(REPORT_DIR, file), "r") as f:
                    data = json.load(f)
                name = data.get("consumer_info", {}).get("name", "Unknown")
                tradelines = data.get("tradelines", [])
                st.markdown(f"**Name:** {name}")
                st.markdown(f"**Tradelines:** {len(tradelines)}")
                if st.button(f"View {file}", key=file):
                    st.session_state["selected_report"] = file
