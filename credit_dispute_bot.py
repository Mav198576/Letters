
import streamlit as st
import json
from datetime import datetime

def months_since(date_str):
    report_date = datetime.strptime(date_str, "%Y-%m-%d")
    today = datetime.today()
    return (today.year - report_date.year) * 12 + (today.month - report_date.month)

def score_item(item, category):
    score = 0
    reasons = []
    months_old = months_since(item["last_reported"])

    if months_old > 12:
        score += 2
        reasons.append("Older than 12 months")
    else:
        score += 1
        reasons.append("Recent negative reporting")

    if category == "tradelines":
        if item["balance"] > item.get("credit_limit", 1):
            score += 2
            reasons.append("Balance exceeds limit")
        if "charge" in item["status"].lower() or "off" in item["status"].lower():
            score += 3
            reasons.append("Account charged off")
        if "late" in item["status"].lower():
            score += 2
            reasons.append("Multiple late payments")

    if category == "collections":
        score += 3
        reasons.append("Collection account")
        if months_old < 6:
            score += 1
            reasons.append("Recently added")

    return {
        "category": category,
        "creditor": item.get("creditor_name") or item.get("agency_name"),
        "status": item["status"],
        "balance": item.get("balance", item.get("amount")),
        "score": score,
        "reasons": reasons
    }

def generate_dispute_letter(consumer_info, item):
    name = consumer_info["name"]
    address = consumer_info["address"]
    creditor = item["creditor"]
    reasons_text = ", ".join(item["reasons"])
    account_status = item["status"]
    balance = item["balance"]

    return f"""
To Whom It May Concern,

My name is {name}, and I am writing to formally dispute an item on my credit report. I have reviewed the information on my report and have identified the following account that I believe is inaccurate or requires further verification:

Creditor: {creditor}  
Status: {account_status}  
Reported Balance: ${balance}  

Reason for Dispute: {reasons_text}.

Under the Fair Credit Reporting Act (FCRA), I am requesting that you conduct a thorough investigation and provide verification of this account. If you cannot verify the accuracy, I respectfully request that the item be deleted from my credit file.

Please mail me a copy of the results of your investigation to the address listed below:

{address}

Thank you for your time and attention to this matter.

Sincerely,  
{name}
"""

# Streamlit UI
st.set_page_config(page_title="AI Credit Dispute Bot", layout="centered")
st.title("📄 AI Credit Dispute Bot")
st.write("Upload your JSON credit report and receive smart dispute suggestions and personalized letters.")

uploaded_file = st.file_uploader("Upload Credit Report (JSON)", type="json")

if uploaded_file:
    data = json.load(uploaded_file)
    consumer_info = data["consumer_info"]
    recommendations = []

    for item in data.get("tradelines", []):
        recommendations.append(score_item(item, "tradelines"))
    for item in data.get("collections", []):
        recommendations.append(score_item(item, "collections"))

    recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)
    
    st.subheader("Top Items to Dispute")
    for i, item in enumerate(recommendations, start=1):
        st.markdown(f"**{i}. {item['creditor']}**")
        st.write(f"- Status: {item['status']}")
        st.write(f"- Balance: ${item['balance']}")
        st.write(f"- Reasons: {', '.join(item['reasons'])}")

    st.subheader("Dispute Letters")
    for letter in [generate_dispute_letter(consumer_info, item) for item in recommendations]:
        with st.expander("📨 View Letter"):
            st.text_area("Dispute Letter", letter, height=300)
