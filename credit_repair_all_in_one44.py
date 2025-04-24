
import streamlit as st
import json
import os
import io
import smtplib
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="All-in-One Credit Repair System", layout="wide")

# === Session/Login ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

def login():
    st.title("🔐 Consultant Login")
    username = st.text_input("Enter your name to login")
    if st.button("Login"):
        if username.strip():
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.success(f"Welcome, {st.session_state.username}!")

if not st.session_state.logged_in:
    login()
    st.stop()

# === Dashboard Header ===
st.title(f"📊 {st.session_state.username}'s Dashboard")
st.markdown("Welcome to your all-in-one credit repair system. Select a tab to begin.")

# === Tabs ===
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📁 Manage Clients & Uploads", 
    "📈 Score Tracker", 
    "✉️ Dispute Letters", 
    "📄 View Full Report", 
    "📬 Send via Email"
])

BASE_DIR = Path("stored_reports")
BASE_DIR.mkdir(exist_ok=True)

# === Tab 1: Upload & Organize Reports ===
with tab1:
    st.subheader("📁 Upload Credit Report")
    consumer = st.text_input("Consumer Name", placeholder="e.g., Jane Smith")
    uploaded = st.file_uploader("Upload JSON Report", type="json", key="upload")

    if consumer and uploaded:
        c_key = consumer.replace(" ", "_")
        time_key = datetime.now().strftime("%Y-%m-%d_%H-%M")
        path = BASE_DIR / c_key / time_key
        path.mkdir(parents=True, exist_ok=True)
        file_path = path / f"report_{time_key}.json"
        with open(file_path, "w") as f:
            f.write(uploaded.read().decode("utf-8"))
        st.success(f"Report saved for {consumer} at {file_path}")

# === Tab 2: Score Tracker ===
with tab2:
    st.subheader("📈 Score History per Consumer")
    all_consumers = sorted([p.name for p in BASE_DIR.iterdir() if p.is_dir()])
    selected = st.selectbox("Select a Consumer", all_consumers)
    
    scores = []
    dates = []

    if selected:
        for rep in sorted((BASE_DIR / selected).glob("*/report_*.json")):
            with open(rep) as f:
                data = json.load(f)
            score = data.get("consumer_info", {}).get("credit_score", None)
            if score:
                date = rep.parent.name
                scores.append(score)
                dates.append(date)

        if scores:
            fig, ax = plt.subplots()
            ax.plot(dates, scores, marker='o')
            ax.set_title(f"{selected.replace('_', ' ')} Score Trend")
            ax.set_xlabel("Date")
            ax.set_ylabel("Score")
            st.pyplot(fig)
        else:
            st.info("No score history available.")

# === Tab 3: Dispute Letter Generator ===
with tab3:
    st.subheader("📄 Generate Dispute Letters")
    bureaus = {
        "TransUnion": "TransUnion Consumer Solutions\nP.O. Box 2000\nChester, PA 19016-2000",
        "Experian": "Experian\nP.O. Box 4500\nAllen, TX 75013",
        "Equifax": "Equifax Information Services LLC\nP.O. Box 740256\nAtlanta, GA 30374-0256"
    }
    templates = {
        "Not Mine": "I am writing to dispute the following information that appears on my credit report. The item is not mine and I request that it be removed immediately.",
        "Never Late": "This account was never late as reported. Please correct this error by removing the inaccurate payment history.",
        "Already Paid": "This account has already been paid in full. Please update your records to reflect a paid status.",
        "Wrong Balance / Status": "The balance or status on this account is incorrect. I request that it be corrected to reflect accurate information.",
        "Request Validation": "I am requesting full validation of this debt under the Fair Credit Reporting Act. If validation cannot be provided, please remove the account from my report."
    }

    c_name = st.selectbox("Select Consumer", all_consumers)
    if c_name:
        reports = list((BASE_DIR / c_name).glob("*/report_*.json"))
        report_options = [f"{r.parent.name} - {r.name}" for r in reports]
        selected_report = st.selectbox("Pick a report", report_options)
        
        if selected_report:
            sel_path = BASE_DIR / c_name / selected_report.split(" - ")[0] / selected_report.split(" - ")[1]
            with open(sel_path) as f:
                data = json.load(f)

            consumer_info = data.get("consumer_info", {"name": "Unknown", "address": "Unknown"})
            items = data.get("tradelines", []) + data.get("collections", [])

            reasons = {}
            for i, item in enumerate(items):
                name = item.get("creditor_name") or item.get("agency_name")
                reasons[i] = st.selectbox(f"Reason for {name}", list(templates.keys()), key=f"r{i}")

            if st.button("📄 Download All Letters (PDF)"):
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=letter)
                for i, item in enumerate(items):
                    reason = reasons[i]
                    body = templates[reason]
                    creditor = item.get("creditor_name") or item.get("agency_name")
                    balance = item.get("balance", item.get("amount", 0))
                    status = item.get("status", "N/A")

                    for bureau, address in bureaus.items():
                        y = 750
                        lines = [
                            consumer_info['name'],
                            consumer_info['address'],
                            "",
                            bureau,
                            *address.split("\n"),
                            "",
                            f"Date: {datetime.today().strftime('%B %d, %Y')}",
                            "",
                            f"Subject: Dispute of Account - {creditor}",
                            "",
                            "To Whom It May Concern,",
                            "",
                            f"Creditor: {creditor}",
                            f"Balance: ${balance}",
                            f"Status: {status}",
                            "",
                            body,
                            "",
                            "Under the Fair Credit Reporting Act (FCRA), I respectfully request that this item be investigated and removed if unverifiable.",
                            "",
                            "Sincerely,",
                            consumer_info['name']
                        ]
                        for line in lines:
                            c.drawString(40, y, line)
                            y -= 15
                            if y < 60:
                                c.showPage()
                                y = 750
                        c.showPage()
                c.save()
                buffer.seek(0)
                st.download_button("📥 Download Combined Dispute PDF", buffer, "dispute_letters.pdf", "application/pdf")

# === Tab 4: Full Report Viewer ===
with tab4:
    st.subheader("📄 View Complete Report")
    if c_name:
        report_path = BASE_DIR / c_name / selected_report.split(" - ")[0] / selected_report.split(" - ")[1]
        with open(report_path) as f:
            full_data = json.load(f)
        st.json(full_data)

# === Tab 5: Email PDF (Mock Setup) ===
with tab5:
    st.subheader("📬 Send Letters by Email")
    st.markdown("📧 *Feature coming soon: Configure SMTP to send PDF to bureau or consumer directly.*")
    st.text_input("Your Email")
    st.text_input("Recipient Email")
    st.text_input("Subject", value="Dispute Letter Submission")
    st.text_area("Message", value="Attached are dispute letters for review and processing.")
    st.file_uploader("Attach PDF", type="pdf")
    st.button("Send Email (Coming Soon)")
