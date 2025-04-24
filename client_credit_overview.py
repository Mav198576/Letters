
import streamlit as st
import json

st.set_page_config(page_title="Client Overview", layout="centered")
st.title("📊 Client Credit Overview")

# Sample client info and score
client_data = {
    "name": "Jane Smith",
    "credit_score": 642
}

# Display client info
st.subheader("👤 Client Information")
st.markdown(f"**Name:** {client_data['name']}")
st.markdown(f"**Current Credit Score:** {client_data['credit_score']}")

# Display scoring system explanation
st.subheader("📘 How We Score Dispute Items")
st.markdown("""
We analyze your credit report and prioritize negative items based on their likelihood of successful removal and credit impact:

### 🔍 Scoring Breakdown:
- **Age of Item**
  - 🟢 Older than 12 months = +2 points
  - 🟡 Less than 12 months = +1 point

- **Account Type & Status**
  - 🔴 Charge-Off or Collection = +3 points
  - 🔶 Multiple Late Payments = +2 points
  - ⚠️ Balance exceeds limit = +2 points

- **Recency**
  - 🕒 Recently added collections = +1 point

### 🏁 Strategy
Items with higher scores are prioritized for dispute because:
- They often lack documentation
- They carry high credit impact
- They are legally challengeable under FCRA

This scoring helps us focus efforts where they can make the biggest difference.
""")

# Optional print button
st.markdown("""
    <button onclick="window.print()" style="
        background-color:#4CAF50;
        color:white;
        padding:10px 16px;
        font-size:16px;
        border:none;
        border-radius:6px;
        cursor:pointer;
        margin-top:20px;
    ">🖨️ Print This Page as PDF</button>
""", unsafe_allow_html=True)
