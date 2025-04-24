
# --- Global Safe Defaults for AI Disputer CRM ---

try:
    user
except NameError:
    user = {"email": "guest@example.com", "is_admin": True}

try:
    consumer_key
except NameError:
    consumer_key = "guest"

import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="AI Credit Disputer", layout="wide")
st.title("📄 AI Credit Disputer")

storage_dir = Path("stored_reports")
log_path = Path("letter_logs.json")
storage_dir.mkdir(exist_ok=True)

# Load letter log
if log_path.exists():
    with open(log_path) as f:
        letter_log = json.load(f)
else:
    letter_log = {}

uploaded_file = st.file_uploader("Upload your credit report", type="json")

if uploaded_file:
    report_data = json.load(uploaded_file)
    consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown")
    credit_score = report_data.get("consumer_info", {}).get("credit_score", 0)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    today = datetime.now().strftime("%Y-%m-%d")

    consumer_key = consumer_name.replace(" ", "_")
    consumer_dir = storage_dir / consumer_key
    save_path = consumer_dir / timestamp
    save_path.mkdir(parents=True, exist_ok=True)
    with open(save_path / "report.json", "w") as f:
        json.dump(report_data, f, indent=2)

    # === Save score history ===
    score_history_path = consumer_dir / "score_history.json"
    if score_history_path.exists():
        with open(score_history_path) as f:
            history = json.load(f)
    else:
        history = []

    history.append({"date": today, "score": credit_score})
    with open(score_history_path, "w") as f:
        json.dump(history, f, indent=2)

    st.success(f"Report uploaded for {consumer_name} on {timestamp}")

    # === Score Display + Graph ===
    st.subheader("📈 Credit Score Overview")
    score_color = "#e74c3c" if credit_score < 580 else "#f39c12" if credit_score < 670 else "#2ecc71"
    st.markdown(f"<div style='padding:10px; border-left: 6px solid {score_color};'><h3>{consumer_name}</h3>"
                f"<b>Score:</b> <span style='color:{score_color}; font-size:20px;'>{credit_score}</span></div>",
                unsafe_allow_html=True)

    if len(history) > 1:
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        st.line_chart(df.set_index("date")["score"])

    # === Account Section ===
    st.subheader("📋 Select Accounts to Dispute")
    selected_accounts = []
    items = report_data.get("tradelines", []) + report_data.get("collections", [])

    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        balance = item.get("balance", item.get("amount", 0))
        status = item.get("status", "N/A")
        reported = item.get("last_reported", "N/A")

        score = 0
        breakdown = []
        if "charge" in status.lower():
            score += 3
            breakdown.append("+3 Charge-off")
        if "late" in status.lower():
            score += 2
            breakdown.append("+2 Late payments")
        if balance and balance > 1000:
            score += 2
            breakdown.append("+2 High balance")
        if "collection" in item.get("remarks", "").lower():
            score += 2
            breakdown.append("+2 Collection remark")
        if not breakdown:
            breakdown.append("0 – No indicators")

        with st.container():
            st.markdown(f"### {creditor}")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""**Status:** {status}  
**Balance:** ${balance}  
**Last Reported:** {reported}""")
                st.markdown(f"🧠 **Dispute Score:** `{score}/10`")
                with st.expander("🔍 Score Breakdown"):
                    for line in breakdown:
                        st.markdown(f"- {line}")
            with col2:
                selected = st.checkbox("Include in Letter", key=f"check_{i}")
                if selected:
                    selected_accounts.append({
                        "creditor": creditor,
                        "status": status,
                        "balance": balance,
                        "reported": reported,
                        "index": i
                    })

    if selected_accounts:
        bureau = st.selectbox("Select Bureau", ["TransUnion", "Experian", "Equifax"])
        reason = st.selectbox("Dispute Reason", ["Not Mine", "Never Late", "Already Paid", "Wrong Balance", "Request Validation"])

        if st.button("📄 Generate Multi-Item Letter PDF"):
            buffer = BytesIO()
            c = canvas.Canvas(buffer)
            c.setFont("Helvetica", 12)
            c.drawString(50, 800, f"{bureau}")
            c.drawString(50, 780, f"Consumer: {consumer_name}")
            c.drawString(50, 760, "Subject: Dispute Letter - Multiple Accounts")
            c.drawString(50, 740, f"Dear {bureau},")
            c.drawString(50, 720, "I am writing to dispute the following accounts:")

            y = 700
            log_entries = []
            for item in selected_accounts:
                c.drawString(60, y, f"• {item['creditor']} — {item['status']} — ${item['balance']} — {item['reported']}")
                log_entries.append({
                    "creditor": item['creditor'],
                    "bureau": bureau,
                    "reason": reason,
                    "date": today
                })
                y -= 20
                if y < 100:
                    c.showPage()
                    c.setFont("Helvetica", 12)
                    y = 800

            c.drawString(50, y-20, f"Dispute Reason: {reason}")
            c.drawString(50, y-40, "Under the FCRA, please investigate and correct these items.")
            c.drawString(50, y-60, f"Thank you,")
            c.drawString(50, y-80, f"{consumer_name}")
            c.save()
            buffer.seek(0)

            st.download_button("📥 Download Combined PDF", data=buffer, file_name=f"{consumer_key}_bulk_dispute_letter.pdf", mime="application/pdf")

            # Save letter log
            if consumer_key not in letter_log:
                letter_log[consumer_key] = []
            letter_log[consumer_key].extend(log_entries)
            with open(log_path, "w") as f:
                json.dump(letter_log, f, indent=2)

# === View Letter History ===
st.sidebar.title("📑 Letter History")
if letter_log:
    for person, entries in letter_log.items():
        with st.sidebar.expander(person.replace("_", " ")):
            for e in entries:
                st.markdown(f"- {e['date']} | **{e['creditor']}** | {e['bureau']} | {e['reason']}")
else:
    st.sidebar.info("No letters generated yet.")

# --- Phase 3: Add-on to AI Disputer All-in-One ---

import fitz  # PyMuPDF for PDF parsing

# Add PDF upload for conversion to JSON (mock example)
st.sidebar.header("📄 PDF Report Import (Beta)")
pdf_file = st.sidebar.file_uploader("Upload Credit Report (PDF)", type="pdf", key="pdf_report")
if pdf_file:
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()

    # Demo extraction logic (real app would parse structure properly)
    st.sidebar.success("PDF text extracted!")
    st.sidebar.write(text[:500] + "...")  # preview

    # Convert into basic JSON-like structure (mock)
    extracted = {
        "consumer_info": {
            "name": "Extracted User",
            "credit_score": 620
        },
        "tradelines": [
            {
                "creditor_name": "Mock Creditor 1",
                "status": "Charge-off",
                "balance": 1540,
                "last_reported": "2024-12-01",
                "remarks": "collection"
            },
            {
                "creditor_name": "Mock Creditor 2",
                "status": "Late",
                "balance": 980,
                "last_reported": "2024-10-15",
                "remarks": ""
            }
        ]
    }

    if st.sidebar.button("Import Extracted Data"):
        with open("temp_pdf_report.json", "w") as f:
            json.dump(extracted, f, indent=2)
        st.session_state["imported_json"] = extracted
        st.sidebar.success("Imported as structured JSON!")

# Inject AI-generated dispute sequence example
st.sidebar.header("🧠 AI Dispute Sequence (Demo)")
if "imported_json" in st.session_state:
    imported_data = st.session_state["imported_json"]
    for i, item in enumerate(imported_data["tradelines"]):
        creditor = item.get("creditor_name")
        with st.sidebar.expander(f"{creditor} – Sequence"):
            st.markdown("**Round 1 – Validation Letter**")
            st.markdown(f"Dear {creditor}, I request validation of this debt...")

            st.markdown("**Round 2 – Escalation**")
            st.markdown(f"I still have not received proper validation for {creditor}...")

            st.markdown("**Round 3 – Legal Reference**")
            st.markdown(f"Under the FCRA and FDCPA, continued reporting without validation is unlawful...")

# --- Branding + Dashboard View ---

# Branding controls
st.sidebar.header("🎨 Branding Options")
agency_name = st.sidebar.text_input("Agency Name", value="My Credit Agency")
primary_color = st.sidebar.color_picker("Primary Color", value="#2c3e50")
logo_url = st.sidebar.text_input("Logo URL (optional)")

# Custom header display
st.markdown(f"<h2 style='color:{primary_color};'>{agency_name}</h2>", unsafe_allow_html=True)
if logo_url:
    st.image(logo_url, width=150)

# === Dashboard View ===
st.sidebar.title("📊 Dashboard")
all_clients = [f.name for f in storage_dir.iterdir() if f.is_dir()]
total_reports = sum(len(list((storage_dir / client).glob("*/*.json"))) for client in all_clients)
st.sidebar.metric("Total Reports", total_reports)

# Display recent uploads
recent_uploads = []
for client in all_clients:
    client_path = storage_dir / client
    folders = sorted(client_path.glob("*"), reverse=True)
    if folders:
        latest = folders[0]
        json_file = latest / "report.json"
        if json_file.exists():
            with open(json_file) as f:
                r = json.load(f)
                recent_uploads.append({
                    "client": client.replace("_", " "),
                    "score": r.get("consumer_info", {}).get("credit_score", "N/A"),
                    "date": latest.name
                })

if recent_uploads:
    st.sidebar.markdown("**Recent Reports:**")
    for r in recent_uploads[:5]:
        st.sidebar.markdown(f"- {r['date']} | {r['client']} | Score: {r['score']}")

# --- Phase 5: To-Do List, Calendar, and 45-Day Recheck ---

# ========== TO-DO LIST ==========
st.sidebar.header("✅ To-Do List")
todo_path = Path("todo.json")

# Load tasks
if todo_path.exists():
    with open(todo_path) as f:
        todos = json.load(f)
else:
    todos = []

new_task = st.sidebar.text_input("New Task")
if st.sidebar.button("Add Task"):
    if new_task:
        todos.append({"task": new_task, "done": False})
        with open(todo_path, "w") as f:
            json.dump(todos, f, indent=2)

for i, t in enumerate(todos):
    checked = st.sidebar.checkbox(t["task"], value=t["done"], key=f"todo_{i}")
    todos[i]["done"] = checked
with open(todo_path, "w") as f:
    json.dump(todos, f, indent=2)

# ========== CALENDAR ==========
st.sidebar.header("🗓️ Calendar Preview")
today = datetime.today()
st.sidebar.markdown(f"**Today:** {today.strftime('%A, %B %d, %Y')}")

# ========== 45-DAY REPORT CHECK ==========
st.sidebar.header("⏱️ 45-Day Report Reminders")

due_clients = []
for client in storage_dir.iterdir():
    if not client.is_dir():
        continue
    folders = sorted(client.glob("*"), reverse=True)
    if folders:
        try:
            last_date = datetime.strptime(folders[0].name, "%Y-%m-%d_%H-%M")
            days_since = (today - last_date).days
            if days_since >= 45:
                due_clients.append((client.name.replace("_", " "), days_since))
        except:
            continue

if due_clients:
    st.sidebar.markdown("### Ready to Recheck:")
    for name, days in due_clients:
        st.sidebar.markdown(f"- **{name}** ({days} days ago)")
else:
    st.sidebar.info("No clients due yet.")

# --- Phase 6: Full Client Portal with Login ---

# ========== USER LOGIN SYSTEM ==========
user_db_path = Path("users.json")
if user_db_path.exists():
    with open(user_db_path) as f:
        user_db = json.load(f)
else:
    user_db = {
        "admin@example.com": {
            "password": "admin123",
            "is_admin": True
        }
    }

# login removed
    st.session_state["user"] = None

def login_user(email, password):
    if email in user_db and user_db[email]["password"] == password:
        st.session_state["user"] = {"email": email, "is_admin": user_db[email].get("is_admin", False)}
        return True
    return False

def register_user(email, password):
    if email not in user_db:
        user_db[email] = {"password": password, "is_admin": False}
        with open(user_db_path, "w") as f:
            json.dump(user_db, f, indent=2)
        return True
    return False

# login removed
    st.sidebar.header("🔐 Login or Register")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")
    if st.sidebar.button("Login"):
        if login_user(email, password):
            st.success("Logged in!")
        else:
            st.error("Invalid credentials.")
    if st.sidebar.button("Register"):
        if register_user(email, password):
            st.success("Account created!")
        else:
            st.warning("Email already exists.")
    st.stop()

user = st.session_state["user"]


# ========== PORTAL VIEW ==========
if user.get("is_admin", False):
    st.markdown("## 🧑‍💼 Admin Portal")
    st.write("Access to all client reports, scores, and letters.")
else:
    st.markdown("## 🙋 Client Portal")
    st.write("Your reports, scores, and letter tools below.")

# --- Phase 7: Role Access + Branded PDFs + Mock Email Reminders ---

# Load client branding from local storage (simulate database)
branding_path = Path("branding.json")
if branding_path.exists():
    with open(branding_path) as f:
        branding_data = json.load(f)
else:
    branding_data = {}

# Let client save their branding info
if not user.get("is_admin", False):
    st.sidebar.header("🎨 Your Branding")
    agency_brand = st.sidebar.text_input("Your Agency Name", value=branding_data.get(user["email"], {}).get("name", ""))
    agency_logo = st.sidebar.text_input("Logo URL", value=branding_data.get(user["email"], {}).get("logo", ""))
    if st.sidebar.button("Save Branding"):
        branding_data[user["email"]] = {"name": agency_brand, "logo": agency_logo}
        with open(branding_path, "w") as f:
            json.dump(branding_data, f, indent=2)
        st.sidebar.success("Branding saved!")

# Filter client data by login identity
if not user.get("is_admin", False):
    consumer_key = user["email"].replace("@", "_").replace(".", "_")
    user_storage_dir = storage_dir / consumer_key
    user_storage_dir.mkdir(exist_ok=True)
    storage_dir = user_storage_dir  # override global path for this session

# PDF branding override
client_brand_name = branding_data.get(user["email"], {}).get("name", "")
client_logo = branding_data.get(user["email"], {}).get("logo", "")

# Modify PDF generator (inject branding into previous letter section)
# Locate the previous canvas drawing section and include header
# This override will replace the start of letter writing

if selected_accounts:
    if st.button("📄 Generate Multi-Item Letter PDF"):
        buffer = BytesIO()
        c = canvas.Canvas(buffer)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 820, client_brand_name or agency_name)
        if client_logo:
            try:
                import requests
                from PIL import Image
                from io import BytesIO as PILBytes
                response = requests.get(client_logo)
                img = Image.open(PILBytes(response.content))
                c.drawInlineImage(img, 400, 760, width=140, preserveAspectRatio=True)
            except:
                c.setFont("Helvetica", 8)
                c.drawString(400, 760, "(Logo failed to load)")
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, f"{bureau}")
        c.drawString(50, 780, f"Consumer: {consumer_name}")
        c.drawString(50, 760, "Subject: Dispute Letter - Multiple Accounts")
        c.drawString(50, 740, f"Dear {bureau},")
        c.drawString(50, 720, "I am writing to dispute the following accounts:")

        y = 700
        log_entries = []
        for item in selected_accounts:
            c.drawString(60, y, f"• {item['creditor']} — {item['status']} — ${item['balance']} — {item['reported']}")
            log_entries.append({
                "creditor": item['creditor'],
                "bureau": bureau,
                "reason": reason,
                "date": today
            })
            y -= 20
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800

        c.drawString(50, y-20, f"Dispute Reason: {reason}")
        c.drawString(50, y-40, "Under the FCRA, please investigate and correct these items.")
        c.drawString(50, y-60, f"Thank you,")
        c.drawString(50, y-80, f"{consumer_name}")
        c.save()
        buffer.seek(0)

        st.download_button("📥 Download Branded PDF", data=buffer, file_name=f"{consumer_key}_bulk_dispute_letter.pdf", mime="application/pdf")

        # Save letter log
        if consumer_key not in letter_log:
            letter_log[consumer_key] = []
        letter_log[consumer_key].extend(log_entries)
        with open(log_path, "w") as f:
            json.dump(letter_log, f, indent=2)

# --- 45-day Reminder Mock Email Log ---
email_log_path = Path("email_log.json")
if email_log_path.exists():
    with open(email_log_path) as f:
        email_log = json.load(f)
else:
    email_log = []

if user.get("is_admin", False):
    st.subheader("📧 Mock Email Log")
    new_reminders = []
    for client in due_clients:
        email = client[0].replace(" ", "_").replace("_at_", "@")
        reminder_entry = {"to": email, "subject": "Time to upload new credit report!", "date": today.strftime("%Y-%m-%d")}
        if reminder_entry not in email_log:
            new_reminders.append(reminder_entry)

    if new_reminders:
        email_log.extend(new_reminders)
        with open(email_log_path, "w") as f:
            json.dump(email_log, f, indent=2)

    for e in email_log[-10:]:
        st.markdown(f"- To: **{e['to']}** | Subject: *{e['subject']}* | Date: {e['date']}")

# --- Phase 8: SMTP Email + Zapier Webhook + Analytics ---

import smtplib
from email.message import EmailMessage
import requests

# ========== SMTP CONFIG ==========
st.sidebar.header("✉️ SMTP Email Settings (Admin)")
smtp_host = st.sidebar.text_input("SMTP Server", value="smtp.gmail.com")
smtp_port = st.sidebar.number_input("Port", value=587)
smtp_user = st.sidebar.text_input("Email Username", value="", type="default")
smtp_pass = st.sidebar.text_input("Email Password", value="", type="password")

# ========== SEND REAL EMAILS ==========
def send_email(to_email, subject, body):
    try:
        msg = EmailMessage()
        msg["From"] = smtp_user
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

if user.get("is_admin", False) and st.sidebar.button("📧 Send All Due Reminders"):
    for client, days in due_clients:
        to_email = client.replace(" ", "_") + "@demo.com"
        subject = "Time to upload your new credit report"
        body = f"Hi {client}, it’s been {days} days since your last upload. Please log in and upload your updated report."
        send_email(to_email, subject, body)
    st.success("Reminders sent!")

# ========== ZAPIER TRIGGER ==========
zapier_url = st.sidebar.text_input("Zapier Webhook URL (optional)")
def trigger_zapier(event, payload):
    if zapier_url:
        try:
            requests.post(zapier_url, json={"event": event, "payload": payload})
        except Exception as e:
            st.warning(f"Zapier trigger failed: {e}")

# Trigger when user uploads a file
if uploaded_file:
    trigger_zapier("report_uploaded", {"user": user["email"], "score": credit_score})

# Trigger when PDF letter is downloaded
if selected_accounts and st.button("Trigger Zapier for Letter"):
    trigger_zapier("letter_generated", {"user": user["email"], "creditors": [x["creditor"] for x in selected_accounts]})
    st.success("Zapier event sent!")

# ========== CLIENT ANALYTICS ==========
if not user.get("is_admin", False):
    st.subheader("📊 Your Score Trends")
    history_file = storage_dir / "score_history.json"
    if history_file.exists():
        with open(history_file) as f:
            hist = json.load(f)
        df = pd.DataFrame(hist)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        st.line_chart(df.set_index("date")["score"])

    letter_count = len(letter_log.get(consumer_key, []))
    st.metric("Total Letters Sent", letter_count)

    # Optional basic stat: letters per dispute score
    scores = [3 if "charge" in l["reason"].lower() else 2 for l in letter_log.get(consumer_key, [])]
    if scores:
        avg_score = round(sum(scores) / len(scores), 2)
        st.metric("Avg Dispute Weight", avg_score)

# --- Phase 9: Success Tracking, Preview/Download, Custom Status Tags ---

# Custom status field storage
status_file = Path("dispute_statuses.json")
if status_file.exists():
    with open(status_file) as f:
        custom_statuses = json.load(f)
else:
    custom_statuses = {}

# Add custom statuses (admin only)
if user.get("is_admin", False):
    st.sidebar.header("⚙️ Custom Dispute Statuses")
    new_status = st.sidebar.text_input("Add New Status")
    if st.sidebar.button("Add Status"):
        if new_status not in custom_statuses:
            custom_statuses[new_status] = {}
            with open(status_file, "w") as f:
                json.dump(custom_statuses, f, indent=2)
            st.sidebar.success("Status added.")

# Show status options on each account (if user is client)
account_status_data = {}

st.subheader("📌 Account Status Tracker")
if uploaded_file or "imported_json" in st.session_state:
    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        status_key = f"{consumer_key}_{creditor}_{i}"

        current_status = custom_statuses.get(status_key, {}).get("status", "Not Set")
        st.markdown(f"**{creditor}** — Current Status: `{current_status}`")

        if custom_statuses:
            chosen = st.selectbox("Update Status", list(custom_statuses.keys()), key=f"statusbox_{i}")
            if st.button(f"Update Status for {creditor}", key=f"updatestatus_{i}"):
                custom_statuses[status_key] = {
                    "status": chosen,
                    "date": datetime.today().strftime("%Y-%m-%d")
                }
                with open(status_file, "w") as f:
                    json.dump(custom_statuses, f, indent=2)
                st.success(f"{creditor} updated to: {chosen}")

# Dispute result effectiveness
if not user.get("is_admin", False):
    st.subheader("✅ Dispute Effectiveness")
    status_stats = {}
    for k, v in custom_statuses.items():
        if k.startswith(consumer_key):
            s = v["status"]
            status_stats[s] = status_stats.get(s, 0) + 1
    if status_stats:
        for s, count in status_stats.items():
            st.markdown(f"- **{s}**: {count} account(s)")

# Secure preview of uploaded JSON reports (client only)
if not user.get("is_admin", False):
    st.subheader("🔍 View Uploaded Credit Reports")
    client_path = Path("stored_reports") / consumer_key
    report_files = list(client_path.glob("**/report.json"))
    if report_files:
        for file in sorted(report_files, reverse=True):
            with open(file) as f:
                report_data = json.load(f)
            with st.expander(f"Report: {file.parent.name}"):
                st.json(report_data)
                st.download_button("Download JSON", data=json.dumps(report_data, indent=2),
                                   file_name=f"{file.parent.name}_report.json", mime="application/json")

# --- Phase 10: Mobile UI, Drag-and-Drop Upload, Client Messaging ---

# ========== DRAG-AND-DROP REPORT UPLOAD ==========
st.subheader("📂 Upload Credit Report")
uploaded_drag = st.file_uploader("Drop your JSON or PDF file here", type=["json", "pdf"], label_visibility="collapsed")

if uploaded_drag and uploaded_drag.name.endswith(".json"):
    report_data = json.load(uploaded_drag)
    st.success("JSON report uploaded successfully.")
    st.session_state["report_data"] = report_data

elif uploaded_drag and uploaded_drag.name.endswith(".pdf"):
    text = ""
    with fitz.open(stream=uploaded_drag.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    st.session_state["report_data"] = {
        "consumer_info": {"name": "Parsed PDF", "credit_score": 630},
        "tradelines": [{"creditor_name": "PDF Creditor", "status": "Late", "balance": 890, "last_reported": "2024-11-10"}]
    }
    st.success("PDF parsed and report structure created.")

# Use parsed report if present
if "report_data" in st.session_state:
    report_data = st.session_state["report_data"]
    consumer_name = report_data.get("consumer_info", {}).get("name", "Unknown")
    credit_score = report_data.get("consumer_info", {}).get("credit_score", 0)
    tradelines = report_data.get("tradelines", [])
    st.markdown(f"**Consumer:** {consumer_name} — **Score:** {credit_score}")
    for item in tradelines:
        st.markdown(f"- {item['creditor_name']} | {item['status']} | ${item['balance']}")

# ========== MOBILE UI OPTIMIZATION ==========
st.markdown("""
<style>
    @media (max-width: 768px) {
        .block-container {
            padding: 1rem !important;
        }
        .css-1cpxqw2 {
            flex-direction: column !important;
        }
        .css-1d391kg {
            flex-direction: column !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ========== CLIENT MESSAGE CENTER ==========
message_file = Path("messages.json")
if message_file.exists():
    with open(message_file) as f:
        all_messages = json.load(f)
else:
    all_messages = []

if not user.get("is_admin", False):
    st.subheader("💬 Send Message to Admin")
    msg = st.text_area("Your Message")
    if st.button("Send Message"):
        all_messages.append({
            "from": user["email"],
            "to": "admin",
            "text": msg,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        with open(message_file, "w") as f:
            json.dump(all_messages, f, indent=2)
        st.success("Message sent.")

if user.get("is_admin", False):
    st.subheader("📥 Client Messages")
    for m in reversed(all_messages[-10:]):
        st.markdown(f"**{m['from']}** on {m['date']}")
        st.markdown(f"> {m['text']}")
        st.markdown("---")

# --- Phase 11: Client Progress Bar Tracker ---

from streamlit.components.v1 import html

if not user.get("is_admin", False):
    st.subheader("📈 Dispute Progress Tracker")

    total_accounts = len(items)
    resolved_statuses = ["Removed", "Resolved", "Verified Deleted"]
    active_statuses = ["Pending", "In Dispute", "Escalated", "Round 1", "Round 2", "Round 3"]

    resolved_count = 0
    active_count = 0

    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        status_key = f"{consumer_key}_{creditor}_{i}"
        status_obj = custom_statuses.get(status_key, {})
        status = status_obj.get("status", "")

        if status in resolved_statuses:
            resolved_count += 1
        elif status in active_statuses:
            active_count += 1

    percent_resolved = int((resolved_count / total_accounts) * 100) if total_accounts > 0 else 0

    # Progress bar color
    color = "#e74c3c" if percent_resolved < 25 else "#f1c40f" if percent_resolved < 75 else "#2ecc71"
    st.markdown(f"<div style='margin:10px 0; font-weight:bold;'>Progress: {percent_resolved}% Resolved</div>", unsafe_allow_html=True)
    html(f"""
    <div style='width:100%; background:#eee; border-radius:5px;'>
      <div style='width:{percent_resolved}%; background:{color}; height:20px; border-radius:5px;'></div>
    </div>
    """, height=30)

    # Status breakdown
    st.markdown("#### Account Status Breakdown")
    for s in resolved_statuses + active_statuses:
        count = sum(1 for k, v in custom_statuses.items() if k.startswith(consumer_key) and v.get("status") == s)
        if count > 0:
            st.markdown(f"- **{s}**: {count}")

# --- Phase 12: Timeline, Score Comparison, AI Dispute Priority ---

import plotly.graph_objects as go

# ========== Score Change Comparison ==========
if not user.get("is_admin", False):
    st.subheader("📉 Score Improvement")

    score_file = storage_dir / "score_history.json"
    if score_file.exists():
        with open(score_file) as f:
            history = json.load(f)

        if len(history) >= 2:
            first = history[0]["score"]
            latest = history[-1]["score"]
            change = latest - first
            st.metric("Score Change", f"{change:+} points", delta_color="normal")

            # Plot line chart
            df = pd.DataFrame(history)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")
            st.line_chart(df.set_index("date")["score"])
        else:
            st.info("Not enough uploads to compare scores.")

# ========== Dispute Timeline ==========
if not user.get("is_admin", False):
    st.subheader("🕒 Dispute Round Timeline")

    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        status_key = f"{consumer_key}_{creditor}_{i}"
        status_history = [v for k, v in custom_statuses.items() if k == status_key]

        if status_history:
            timeline = [status_history[0]["status"]]
            dates = [status_history[0].get("date", "N/A")]

            fig = go.Figure(go.Scatter(
                x=dates,
                y=timeline,
                mode="lines+markers",
                name=creditor,
                line=dict(shape="hv", color="blue")
            ))
            fig.update_layout(title=creditor, height=200)
            st.plotly_chart(fig, use_container_width=True)

# ========== AI-Based Dispute Priority ==========
if not user.get("is_admin", False):
    st.subheader("🤖 AI Dispute Priority Suggestion")

    ranked = []
    for i, item in enumerate(items):
        creditor = item.get("creditor_name") or item.get("agency_name", "Unknown")
        score = 0
        status = item.get("status", "").lower()
        remarks = item.get("remarks", "").lower()
        balance = item.get("balance", item.get("amount", 0))

        if "charge" in status:
            score += 3
        if "late" in status:
            score += 2
        if "collection" in remarks:
            score += 2
        if balance and balance > 1000:
            score += 1

        ranked.append((creditor, score))

    ranked.sort(key=lambda x: x[1], reverse=True)
    st.markdown("### 🔝 Suggested Dispute Targets")
    for cred, score in ranked[:5]:
        st.markdown(f"- **{cred}** — Priority Score: `{score}/10`")

# --- Phase 13: Admin Analytics + CSV Export + SaaS Prep ---

import csv

if user.get("is_admin", False):
    st.subheader("📊 Admin Analytics Overview")

    user_dirs = [d for d in storage_dir.parent.iterdir() if d.is_dir()]
    total_users = len(user_dirs)
    total_reports = sum(len(list(d.glob("**/report.json"))) for d in user_dirs)
    total_letters = sum(len(letter_log.get(d.name, [])) for d in user_dirs)

    st.metric("Total Users", total_users)
    st.metric("Reports Uploaded", total_reports)
    st.metric("Dispute Letters Generated", total_letters)

    # Cross-user score trend view
    st.markdown("### 📈 Global Score Trends")
    all_scores = []
    for user_dir in user_dirs:
        score_path = user_dir / "score_history.json"
        if score_path.exists():
            with open(score_path) as f:
                data = json.load(f)
            for row in data:
                all_scores.append({
                    "email": user_dir.name.replace("_", "@").replace("dot", "."),
                    "date": row["date"],
                    "score": row["score"]
                })

    if all_scores:
        df = pd.DataFrame(all_scores)
        df["date"] = pd.to_datetime(df["date"])
        st.line_chart(df.pivot_table(index="date", columns="email", values="score"))

    # Export to CSV
    st.markdown("### 📤 Export User Activity Log")

    activity_rows = []
    for user_dir in user_dirs:
        history_path = user_dir / "score_history.json"
        letters = letter_log.get(user_dir.name, [])
        if history_path.exists():
            with open(history_path) as f:
                scores = json.load(f)
                for s in scores:
                    activity_rows.append({
                        "user": user_dir.name,
                        "date": s["date"],
                        "score": s["score"],
                        "letters_generated": len(letters)
                    })

    if activity_rows:
        csv_file = "user_activity_log.csv"
        with open(csv_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=activity_rows[0].keys())
            writer.writeheader()
            writer.writerows(activity_rows)

        with open(csv_file, "rb") as f:
            st.download_button("📥 Download CSV", f, file_name=csv_file, mime="text/csv")

# Prep for SaaS structure
st.sidebar.markdown("### ⚙️ SaaS Mode Settings (Prep)")
demo_mode = st.sidebar.checkbox("Enable Demo Mode")
if demo_mode:
    st.sidebar.info("Demo mode enabled: limited data visibility and testing features.")

# --- Phase 14: Top Tab UI, Logo Upload, Dashboard Enhancements ---

import streamlit.components.v1 as components

# Logo uploader
st.sidebar.header("🖼️ Upload Logo")
uploaded_logo = st.sidebar.file_uploader("Upload your logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
logo_path = None
if uploaded_logo:
    logo_path = f"logos/{user['email'].replace('@', '_at_')}_logo.png"
    Path("logos").mkdir(exist_ok=True)
    with open(logo_path, "wb") as f:
        f.write(uploaded_logo.read())

# Dashboard style with logo + metrics
st.markdown("""
<style>
.css-1v0mbdj.eknhn3m10 {margin-top: -50px;}
.css-1aumxhk {
    background: #f9f9f9;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
</style>
""", unsafe_allow_html=True)

# Top tab nav layout
tab_options = ["Dashboard", "Dispute Manager", "Reports", "Messages", "Settings"]
selected_tab = st.selectbox("📁 Navigate", tab_options, key="tabnav")

# Display uploaded logo (if available)
if logo_path and Path(logo_path).exists():
    st.image(logo_path, width=150)

# === DASHBOARD OVERVIEW ===
if selected_tab == "Dashboard":
    st.title("📊 Dashboard Overview")

    # Calendar preview
    st.subheader("🗓️ Calendar")
    today = datetime.today()
    st.markdown(f"**Today:** {today.strftime('%A, %B %d, %Y')}")

    # Active clients metric
    clients = [p.name for p in storage_dir.iterdir() if p.is_dir()]
    st.metric("Active Clients", len(clients))

    # Reports due for refresh
    st.subheader("⏱️ Reports Due (45+ days)")
    due_list = []
    for c in clients:
        folders = sorted((storage_dir / c).glob("*"), reverse=True)
        if folders:
            try:
                last = datetime.strptime(folders[0].name, "%Y-%m-%d_%H-%M")
                if (today - last).days >= 45:
                    due_list.append((c.replace("_", " "), (today - last).days))
            except:
                continue

    if due_list:
        for name, days in due_list:
            st.markdown(f"- **{name}** ({days} days ago)")
    else:
        st.success("No clients are due for refresh.")

# Additional tabs (placeholder for rest of app)
elif selected_tab == "Dispute Manager":
    st.title("🧾 Dispute Manager")
    st.info("Manage disputes here (move core tools into this view).")

elif selected_tab == "Reports":
    st.title("📂 Report Viewer")
    st.info("Show uploaded JSON and parsed PDFs here.")

elif selected_tab == "Messages":
    st.title("💬 Client Messages")
    st.info("Inbox and communication hub.")

elif selected_tab == "Settings":
    st.title("⚙️ Settings")
    st.info("User, brand, and app configuration.")

# --- Phase 15: Polished Tab Views ---

# Dispute Manager (core functionality moved here)
if selected_tab == "Dispute Manager":
    st.title("🧾 Dispute Manager")
    st.write("Upload a credit report, select accounts, and generate dispute letters.")

    st.subheader("📤 Upload or Drag-and-Drop Credit Report")
    uploaded = st.file_uploader("Upload credit report (JSON or PDF)", type=["json", "pdf"])

    if uploaded:
        if uploaded.name.endswith(".json"):
            report_data = json.load(uploaded)
        elif uploaded.name.endswith(".pdf"):
            text = ""
            with fitz.open(stream=uploaded.read(), filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
            report_data = {
                "consumer_info": {"name": "PDF Parse", "credit_score": 620},
                "tradelines": [{"creditor_name": "PDF Creditor", "status": "Late", "balance": 750, "last_reported": "2024-11-01"}]
            }
        st.success("Report loaded!")
        consumer = report_data.get("consumer_info", {}).get("name", "Unknown")
        score = report_data.get("consumer_info", {}).get("credit_score", "N/A")
        st.markdown(f"**Consumer:** {consumer} | **Score:** {score}")

        st.subheader("🧠 Account Disputes")
        tradelines = report_data.get("tradelines", [])
        for item in tradelines:
            with st.expander(f"{item['creditor_name']} — {item['status']}"):
                st.markdown(f"- **Balance:** ${item['balance']}")
                st.markdown(f"- **Last Reported:** {item['last_reported']}")

# Report viewer
elif selected_tab == "Reports":
    st.title("📂 Uploaded Reports")
    client_key = user["email"].replace("@", "_at_")
    user_folder = Path("stored_reports") / client_key
    if user_folder.exists():
        report_files = list(user_folder.glob("**/report.json"))
        for file in sorted(report_files, reverse=True):
            with open(file) as f:
                data = json.load(f)
            with st.expander(f"{file.parent.name} — {data.get('consumer_info', {}).get('name', '')}"):
                st.json(data)
                st.download_button("Download JSON", data=json.dumps(data, indent=2),
                                   file_name=f"{file.parent.name}_report.json", mime="application/json")
    else:
        st.info("No reports uploaded yet.")

# Messages view
elif selected_tab == "Messages":
    st.title("💬 Messages")
    if not user.get("is_admin", False):
        st.subheader("Send a Message")
        msg = st.text_area("Type your message:")
        if st.button("Send"):
            all_messages.append({
                "from": user["email"],
                "to": "admin",
                "text": msg,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
            with open("messages.json", "w") as f:
                json.dump(all_messages, f, indent=2)
            st.success("Message sent!")
    else:
        st.subheader("Inbox")
        if all_messages:
            for m in reversed(all_messages[-10:]):
                st.markdown(f"**{m['from']}** at {m['date']}")
                st.markdown(f"> {m['text']}")
                st.markdown("---")
        else:
            st.info("No messages yet.")

# Settings view
elif selected_tab == "Settings":
    st.title("⚙️ User Settings")

    st.markdown(f"**Email:** {user['email']}")
    st.markdown("**Branding Options**")
    agency_name = st.text_input("Agency Name", value=branding_data.get(user["email"], {}).get("name", ""))
    color_theme = st.color_picker("Theme Color", value="#2c3e50")
    new_logo = st.file_uploader("Upload New Logo", type=["png", "jpg"])

    if st.button("Save Settings"):
        branding_data[user["email"]] = {
            "name": agency_name,
            "color": color_theme,
            "logo": branding_data.get(user["email"], {}).get("logo", "")
        }
        if new_logo:
            logo_path = f"logos/{user['email'].replace('@', '_at_')}_logo.png"
            with open(logo_path, "wb") as f:
                f.write(new_logo.read())
            branding_data[user["email"]]["logo"] = logo_path
        with open("branding.json", "w") as f:
            json.dump(branding_data, f, indent=2)
        st.success("Settings saved!")

# --- Phase 16: No Login, Top Tabs, Leads/Clients Views ---

# Replacing login with default public session
user = {"email": "guest@example.com", "is_admin": True}
consumer_key = "guest"

# Apply compact tab layout
tab_style = """
<style>
    .stSelectbox > div > div {
        font-size: 14px !important;
        padding: 6px 8px !important;
    }
</style>
"""
st.markdown(tab_style, unsafe_allow_html=True)

# Compact top tab selection
tab_options = ["Dashboard", "Leads", "Clients", "Dispute Manager", "Reports", "Messages", "Settings"]
selected_tab = st.selectbox("🧭 Navigate", tab_options, key="topnav")

# === NEW: Leads tab ===
if selected_tab == "Leads":
    st.title("📇 Leads")
    st.info("Add and manage new prospects here.")
    st.dataframe(pd.DataFrame(columns=["Name", "Email", "Source", "Date Added"]))

# === NEW: Clients tab ===
elif selected_tab == "Clients":
    st.title("👥 Clients")
    st.info("List of active or onboarded credit repair clients.")
    st.dataframe(pd.DataFrame(columns=["Client", "Last Upload", "Status", "Score"]))

# --- Phase 17: Editable CRM Leads + Clients ---

import uuid

# CRM file storage paths
leads_file = Path("crm_leads.json")
clients_file = Path("crm_clients.json")

# Load or initialize
if leads_file.exists():
    leads_data = json.load(open(leads_file))
else:
    leads_data = []

if clients_file.exists():
    clients_data = json.load(open(clients_file))
else:
    clients_data = []

# === LEADS VIEW ===
if selected_tab == "Leads":
    st.title("📇 Leads CRM")
    with st.form("add_lead"):
        col1, col2 = st.columns(2)
        with col1:
            lead_name = st.text_input("Lead Name")
            lead_email = st.text_input("Email")
        with col2:
            lead_source = st.selectbox("Source", ["Facebook", "Referral", "Website", "Other"])
            submitted = st.form_submit_button("Add Lead")
        if submitted and lead_name and lead_email:
            leads_data.append({
                "id": str(uuid.uuid4()),
                "name": lead_name,
                "email": lead_email,
                "source": lead_source,
                "status": "New",
                "added": datetime.now().strftime("%Y-%m-%d")
            })
            with open(leads_file, "w") as f:
                json.dump(leads_data, f, indent=2)
            st.success("Lead added!")

    st.markdown("### Current Leads")
    for lead in leads_data:
        with st.expander(f"{lead['name']} ({lead['email']})"):
            st.markdown(f"- **Source:** {lead['source']}")
            st.markdown(f"- **Status:** {lead['status']}")
            st.markdown(f"- **Date Added:** {lead['added']}")
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Convert", key=f"convert_{lead['id']}"):
                    clients_data.append({
                        "id": lead["id"],
                        "name": lead["name"],
                        "email": lead["email"],
                        "status": "Active",
                        "joined": datetime.now().strftime("%Y-%m-%d")
                    })
                    leads_data = [l for l in leads_data if l["id"] != lead["id"]]
                    with open(leads_file, "w") as f:
                        json.dump(leads_data, f, indent=2)
                    with open(clients_file, "w") as f:
                        json.dump(clients_data, f, indent=2)
                    st.success(f"{lead['name']} converted to client!")

# === CLIENTS VIEW ===
elif selected_tab == "Clients":
    st.title("👥 Clients CRM")
    st.markdown("### Current Clients")
    for client in clients_data:
        with st.expander(f"{client['name']} ({client['email']})"):
            st.markdown(f"- **Status:** {client['status']}")
            st.markdown(f"- **Joined:** {client['joined']}")

# --- Phase 18: Custom Lead Stages, CSV Upload, and Zapier Integration ---

# Load tag/stage config
stage_options = ["New", "Hot", "Follow-Up", "No Response", "Converted"]
tag_options = ["Credit", "Student Loan", "Real Estate", "Bankruptcy", "Auto Loan"]

# Custom upload via CSV
if selected_tab == "Leads":
    st.markdown("### 📥 Bulk Upload Leads via CSV")
    csv_upload = st.file_uploader("Upload CSV file with columns: name, email, source", type="csv", key="csvleads")
    if csv_upload:
        df = pd.read_csv(csv_upload)
        count = 0
        for _, row in df.iterrows():
            if "name" in row and "email" in row:
                leads_data.append({
                    "id": str(uuid.uuid4()),
                    "name": row["name"],
                    "email": row["email"],
                    "source": row.get("source", "CSV Import"),
                    "status": "New",
                    "added": datetime.now().strftime("%Y-%m-%d")
                })
                count += 1
        with open(leads_file, "w") as f:
            json.dump(leads_data, f, indent=2)
        st.success(f"{count} leads uploaded from CSV!")

    # Display editable lead list with stages and tags
    st.markdown("### 📝 Lead Management")
    for lead in leads_data:
        with st.expander(f"{lead['name']} ({lead['email']})"):
            lead["status"] = st.selectbox("Status", stage_options, index=stage_options.index(lead.get("status", "New")), key=f"stage_{lead['id']}")
            tags = st.multiselect("Tags", tag_options, default=lead.get("tags", []), key=f"tags_{lead['id']}")
            lead["tags"] = tags
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("Convert", key=f"convert_{lead['id']}"):
                    clients_data.append({
                        "id": lead["id"],
                        "name": lead["name"],
                        "email": lead["email"],
                        "status": "Active",
                        "joined": datetime.now().strftime("%Y-%m-%d")
                    })
                    leads_data = [l for l in leads_data if l["id"] != lead["id"]]
                    with open(clients_file, "w") as f:
                        json.dump(clients_data, f, indent=2)
                    st.success(f"{lead['name']} converted to client.")
            with open(leads_file, "w") as f:
                json.dump(leads_data, f, indent=2)

# === ZAPIER WEBHOOK ENDPOINT ===
if "zapier_leads" not in st.session_state:
    st.session_state["zapier_leads"] = []

def capture_zapier_lead(payload):
    new_lead = {
        "id": str(uuid.uuid4()),
        "name": payload.get("name", "Zapier Lead"),
        "email": payload.get("email", "noemail@example.com"),
        "source": payload.get("source", "Zapier"),
        "status": "New",
        "added": datetime.now().strftime("%Y-%m-%d")
    }
    leads_data.append(new_lead)
    with open(leads_file, "w") as f:
        json.dump(leads_data, f, indent=2)
    st.session_state["zapier_leads"].append(new_lead)

# Simulate Zapier JSON input (admin only testing)
if selected_tab == "Leads" and user.get("is_admin", False):
    with st.expander("🧪 Simulate Zapier Lead Capture"):
        zap_name = st.text_input("Zapier Name")
        zap_email = st.text_input("Zapier Email")
        zap_source = st.text_input("Zapier Source", value="Web Form")
        if st.button("Add Zapier Lead"):
            capture_zapier_lead({"name": zap_name, "email": zap_email, "source": zap_source})
            st.success("Zapier lead added.")
