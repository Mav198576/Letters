
import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime

# === INIT SESSION STATE ===
if "theme_color" not in st.session_state:
    st.session_state.theme_color = "#2c3e50"
if "font_size" not in st.session_state:
    st.session_state.font_size = "16px"
if "bg_color" not in st.session_state:
    st.session_state.bg_color = "#ffffff"
if "leads" not in st.session_state:
    st.session_state.leads = []
if "clients" not in st.session_state:
    st.session_state.clients = []
if "client_reports" not in st.session_state:
    st.session_state.client_reports = {}

# === STYLING ===
st.markdown(f'''
    <style>
        body {{
            background-color: {st.session_state.bg_color};
        }}
        .stApp {{
            font-size: {st.session_state.font_size};
            color: {st.session_state.theme_color};
        }}
    </style>
''', unsafe_allow_html=True)

# === SIDEBAR NAVIGATION ===
st.sidebar.title("📁 CRM Navigation")
tabs = [
    "📊 Dashboard", "📋 Leads", "👥 Clients", "🤖 Automations", "🧠 AI Disputer",
    "📈 Reports", "📄 Templates", "⚙️ Setup", "🛟 Support", "🎓 Training"
]
page = st.sidebar.radio("Go to", tabs)

# === DASHBOARD ===
if page == "📊 Dashboard":
    st.title("📊 Dashboard")
    st.metric("Total Leads", len(st.session_state.leads))
    st.metric("Total Clients", len(st.session_state.clients))

# === LEADS ===
elif page == "📋 Leads":
    st.title("📋 Leads")
    with st.form("lead_form", clear_on_submit=True):
        name = st.text_input("Lead Name")
        email = st.text_input("Email")
        notes = st.text_area("Notes")
        if st.form_submit_button("➕ Add Lead"):
            st.session_state.leads.append({"name": name, "email": email, "notes": notes})
            st.success(f"Lead '{name}' added.")

    st.subheader("📍 All Leads")
    for idx, lead in enumerate(st.session_state.leads):
        st.markdown(f"**Name:** {lead['name']}  \n📧 **Email:** {lead['email']}  \n🗒️ {lead['notes']}")  
📧 **Email:** {lead['email']}  
🗒️ {lead['notes']}")
        if st.button(f"Convert to Client", key=f"convert_{idx}"):
            st.session_state.clients.append({
                "name": lead['name'],
                "email": lead['email'],
                "score": 0
            })
            del st.session_state.leads[idx]
            st.success(f"Converted {lead['name']} to client.")
            st.experimental_rerun()
        st.markdown("---")

# === CLIENTS ===
elif page == "👥 Clients":
    st.title("👥 Clients")
    with st.form("client_form", clear_on_submit=True):
        cname = st.text_input("Client Name")
        cscore = st.number_input("Credit Score", min_value=300, max_value=850, step=1)
        cemail = st.text_input("Email")
        if st.form_submit_button("➕ Add Client"):
            st.session_state.clients.append({"name": cname, "score": cscore, "email": cemail})
            st.success(f"Client '{cname}' added.")

    st.subheader("📂 Client List")
    for client in st.session_state.clients:
        st.markdown(f"**{client['name']}**  
📧 {client['email']}  
📊 Score: {client['score']}")
        if st.button(f"📁 Upload Report for {client['name']}", key=f"upload_{client['name']}"):
            st.session_state["selected_client_for_upload"] = client['name']
            st.experimental_rerun()
        st.markdown("---")

    # Upload credit report
    if "selected_client_for_upload" in st.session_state:
        cname = st.session_state["selected_client_for_upload"]
        st.subheader(f"📤 Upload Credit Report for {cname}")
        uploaded_file = st.file_uploader("Upload JSON", type="json", key="client_report")
        if uploaded_file:
            content = json.load(uploaded_file)
            if cname not in st.session_state.client_reports:
                st.session_state.client_reports[cname] = []
            st.session_state.client_reports[cname].append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "report": content
            })
            st.success("Report uploaded.")
            del st.session_state["selected_client_for_upload"]
            st.experimental_rerun()

# === AI DISPUTER ===
elif page == "🧠 AI Disputer":
    st.title("🧠 AI Disputer")
    if not st.session_state.clients:
        st.info("No clients available.")
    else:
        selected = st.selectbox("Select Client", [c["name"] for c in st.session_state.clients])
        reports = st.session_state.client_reports.get(selected, [])
        if not reports:
            st.warning("No credit reports found for this client.")
        else:
            latest = reports[-1]
            st.markdown(f"🕒 Latest Upload: `{latest['date']}`")
            consumer_info = latest['report'].get("consumer_info", {})
            tradelines = latest['report'].get("tradelines", [])
            collections = latest['report'].get("collections", [])
            items = tradelines + collections

            st.markdown(f"**Client:** {consumer_info.get('name', selected)}")
            st.markdown(f"**Score:** {consumer_info.get('credit_score', 'N/A')}")

            for i, item in enumerate(items):
                name = item.get("creditor_name") or item.get("agency_name", "Unknown")
                score = 0
                if "charge" in item.get("status", "").lower(): score += 3
                if item.get("balance", 0) > 1000: score += 2
                if "collection" in item.get("remarks", "").lower(): score += 2
                if "late" in item.get("status", "").lower(): score += 1

                st.markdown(f"---
**{name}**  
Status: {item.get('status', 'N/A')}  
Balance: ${item.get('balance', 0)}  
Score Impact: **{score}**/10")

                bureau = st.selectbox(f"Choose Bureau for Letter", ["TransUnion", "Experian", "Equifax"], key=f"bureau_{i}")
                reason = st.selectbox(f"Suggested Reason", ["Not Mine", "Never Late", "Already Paid", "Wrong Balance", "Request Validation"], key=f"reason_{i}")
                if st.button(f"Generate Letter {i}"):
                    st.success(f"Generated letter for {name} via {bureau} - Reason: {reason}")

# === PLACEHOLDER TABS ===
elif page == "🤖 Automations":
    st.title("🤖 Automations")
    st.info("Coming soon.")

elif page == "📈 Reports":
    st.title("📈 Reports")
    st.info("Coming soon.")

elif page == "📄 Templates":
    st.title("📄 Templates")
    st.info("Coming soon.")

elif page == "⚙️ Setup":
    st.title("⚙️ Theme Customizer")
    color = st.color_picker("Primary Color", st.session_state.theme_color)
    bg = st.color_picker("Background Color", st.session_state.bg_color)
    font = st.selectbox("Font Size", ["14px", "16px", "18px", "20px"], index=["14px", "16px", "18px", "20px"].index(st.session_state.font_size))
    if st.button("Apply Theme"):
        st.session_state.theme_color = color
        st.session_state.bg_color = bg
        st.session_state.font_size = font
        st.experimental_rerun()

elif page == "🛟 Support":
    st.title("🛟 Support")
    st.info("Need help? Contact us or view documentation.")

elif page == "🎓 Training":
    st.title("🎓 Training")
    st.info("Training videos and onboarding tools coming soon.")
