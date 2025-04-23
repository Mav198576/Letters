
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

    return f"""To Whom It May Concern,

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

st.set_page_config(page_title="Credit Dispute Chatbot", layout="centered")
st.title("🤖 AI Credit Dispute Chatbot")

if "messages" not in st.session_state:
    st.session_state.messages = []

# File upload trigger
if "credit_data" not in st.session_state:
    st.chat_message("assistant").write("Hi there! Please upload your JSON credit report to begin.")
    uploaded = st.file_uploader("Upload JSON Credit Report", type="json")
    if uploaded:
        data = json.load(uploaded)
        st.session_state["credit_data"] = data
        st.session_state.messages.append({"role": "assistant", "text": "Thanks! I’ve reviewed your report. Ask me what items to dispute or say 'generate letters'."})
else:
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["text"])

    prompt = st.chat_input("Ask me something about your credit report...")
    if prompt:
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "text": prompt})

        # Process question
        data = st.session_state["credit_data"]
        consumer_info = data["consumer_info"]
        recommendations = [score_item(i, "tradelines") for i in data.get("tradelines", [])]
        recommendations += [score_item(i, "collections") for i in data.get("collections", [])]
        recommendations = sorted(recommendations, key=lambda x: x["score"], reverse=True)

        if "dispute" in prompt.lower():
            response = f"I found {len(recommendations)} items you may want to dispute. The top one is: {recommendations[0]['creditor']} - {recommendations[0]['status']} (${recommendations[0]['balance']}) for reasons: {', '.join(recommendations[0]['reasons'])}."
        elif "letter" in prompt.lower():
            letters = [generate_dispute_letter(consumer_info, item) for item in recommendations]
            response = "Here’s a sample dispute letter:\n\n" + letters[0][:1000] + ("..." if len(letters[0]) > 1000 else "")
        else:
            response = "Try asking me: 'What items should I dispute?' or 'Can you generate letters?'"

        st.chat_message("assistant").write(response)
        st.session_state.messages.append({"role": "assistant", "text": response})
