
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

tab = st.selectbox("Navigation", ["Dashboard", "Leads", "Clients"])

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
