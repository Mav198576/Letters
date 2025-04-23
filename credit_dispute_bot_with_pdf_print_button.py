
import streamlit as st
import json
import os
import io
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

st.set_page_config(page_title="Credit Dispute Chatbot", layout="centered")
st.title("🤖 AI Credit Dispute Chatbot with Monthly Archive & PDF Export")

BASE_DIR = Path("storage")
current_month = datetime.now().strftime("%Y-%m")
month_folder = BASE_DIR / current_month
month_folder.mkdir(parents=True, exist_ok=True)

def save_file(filename, content):
    file_path = month_folder / filename
    with open(file_path, "w") as f:
        f.write(content)
    return file_path

def save_pdf(filename, letters):
    pdf_path = month_folder / filename
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    for letter_text in letters:
        lines = letter_text.split("\n")
        y = height - 40
        for line in lines:
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line.strip())
            y -= 14
        c.showPage()
    c.save()
    buffer.seek(0)
    with open(pdf_path, "wb") as f:
        f.write(buffer.read())
    return pdf_path

def months_available():
    return sorted([folder.name for folder in BASE_DIR.glob("*") if folder.is_dir()])

def load_text_file(filepath):
    with open(filepath, "r") as f:
        return f.read()

st.subheader("📤 Upload a Credit Report (JSON format)")
uploaded_file = st.file_uploader("Upload JSON", type="json")

if uploaded_file:
    data = json.load(uploaded_file)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"report_{timestamp}.json"
    save_file(filename, json.dumps(data, indent=2))
    st.success(f"✅ Credit report uploaded and saved.")

    consumer_info = data.get("consumer_info", {"name": "Unknown", "address": "Unknown"})
    letters = []
    for item in data.get("tradelines", []) + data.get("collections", []):
        letter = f"""To Whom It May Concern,

My name is {consumer_info['name']}, and I am writing to formally dispute an item on my credit report.

Creditor: {item.get('creditor_name') or item.get('agency_name')}
Status: {item.get('status')}
Balance: ${item.get('balance', 0)}

Under the Fair Credit Reporting Act (FCRA), I am requesting an investigation of this account.
Please mail the results to:

{consumer_info['address']}

Sincerely,
{consumer_info['name']}
"""
        letters.append(letter)

    all_letters_txt = "\n\n---\n\n".join(letters)
    txt_filename = f"letters_{timestamp}.txt"
    save_file(txt_filename, all_letters_txt)

    pdf_filename = f"letters_{timestamp}.pdf"
    pdf_path = save_pdf(pdf_filename, letters)

    st.download_button("📄 Download All Letters (TXT)", data=all_letters_txt,
                       file_name=txt_filename, mime="text/plain")
    with open(pdf_path, "rb") as pdf_file:
        st.download_button("🖨️ Download All Letters (PDF)", data=pdf_file.read(),
                           file_name=pdf_filename, mime="application/pdf")

st.subheader("📁 View Stored Reports & Letters by Month")
month_selected = st.selectbox("Select a month:", months_available())

if month_selected:
    files = list((BASE_DIR / month_selected).glob("*"))
    for f in files:
        if f.suffix == ".json":
            st.markdown(f"📄 **Report:** `{f.name}`")
            st.download_button("Download Report", load_text_file(f), file_name=f.name)
        elif f.suffix == ".txt":
            st.markdown(f"📝 **Letters (TXT):** `{f.name}`")
            st.download_button("Download Letters", load_text_file(f), file_name=f.name)
        elif f.suffix == ".pdf":
            st.markdown(f"🖨️ **Letters (PDF):** `{f.name}`")
            with open(f, "rb") as pdf:
                st.download_button("Download PDF", data=pdf.read(), file_name=f.name, mime="application/pdf")


# Optional browser-based print/export to PDF
st.markdown("""
    <button onclick="window.print()" style="
        background-color:#4CAF50;
        color:white;
        padding:10px 16px;
        font-size:16px;
        border:none;
        border-radius:6px;
        cursor:pointer;
        margin:20px 0;
    ">🖨️ Print This Page as PDF</button>
""", unsafe_allow_html=True)
