import streamlit as st

st.set_page_config(page_title="Merch Income Calculator", layout="centered")

# ---------------- AMAZON BASE COSTS ----------------
AMAZON_COST = {
    "T-Shirt": 9.10,     # Example Amazon base cost
    "Hoodie": 25.75      # Example Amazon base cost
}

# ---------------- PAYONEER SETTINGS ----------------
DEFAULT_PAYONEER_PERCENT = 2.0     # 2% receiving fee
DEFAULT_USD_TO_INR = 83.0          # Editable live rate


def calculate_income(product, sell_price, tax_percent, payoneer_percent, usd_to_inr):
    amazon_deduction = AMAZON_COST[product]
    royalty_before_tax = sell_price - amazon_deduction
    tax_deduction = royalty_before_tax * (tax_percent / 100)
    royalty_after_tax = royalty_before_tax - tax_deduction
    payoneer_fee = royalty_after_tax * (payoneer_percent / 100)
    final_usd = royalty_after_tax - payoneer_fee
    final_inr = final_usd * usd_to_inr

    return {
        "Amazon Deduction": amazon_deduction,
        "Royalty Before Tax": royalty_before_tax,
        "Tax Deducted": tax_deduction,
        "Royalty After Tax": royalty_after_tax,
        "Payoneer Fee": payoneer_fee,
        "Final USD": final_usd,
        "Final INR": final_inr
    }


# ---------------- STREAMLIT UI ----------------
st.title("🧮 Merch by Amazon Income Calculator")
st.write("Calculate your final earnings after Amazon costs, taxes, and Payoneer deductions.")

# Section 1 — Product Type
product = st.selectbox("Select Product", ["T-Shirt", "Hoodie"])

# Section 2 — Selling Price
sell_price = st.number_input(
    "Enter Selling Price (USD)",
    min_value=1.0,
    step=0.50,
    value=19.99
)

# Section 3 — Tax Deduction
tax_percent = st.selectbox(
    "Select Tax Rate",
    [15, 30],
    index=0,
    help="15% = With W-8BEN | 30% = Without W-8BEN"
)

# Section 4 — Payoneer Settings
payoneer_percent = st.number_input(
    "Payoneer Fee (%)",
    min_value=0.0,
    value=DEFAULT_PAYONEER_PERCENT,
    step=0.1
)

usd_to_inr = st.number_input(
    "USD to INR Conversion Rate",
    min_value=50.0,
    value=DEFAULT_USD_TO_INR,
    step=0.5
)

# Calculate Button
if st.button("Calculate Income"):
    result = calculate_income(product, sell_price, tax_percent, payoneer_percent, usd_to_inr)

    st.subheader("📊 Final Breakdown")
    st.write(f"**Amazon Deduction:** ${result['Amazon Deduction']:.2f}")
    st.write(f"**Royalty Before Tax:** ${result['Royalty Before Tax']:.2f}")
    st.write(f"**Tax Deducted ({tax_percent}%):** ${result['Tax Deducted']:.2f}")
    st.write(f"**Royalty After Tax:** ${result['Royalty After Tax']:.2f}")
    st.write(f"**Payoneer Fee ({payoneer_percent}%):** ${result['Payoneer Fee']:.2f}")
    st.write(f"### 💵 Final USD You Receive: **${result['Final USD']:.2f}**")
    st.write(f"### 🇮🇳 Final INR in Your Bank: **₹{result['Final INR']:.2f}**")


st.markdown("---")
st.caption("Made for POD creators — change the values any time.")
