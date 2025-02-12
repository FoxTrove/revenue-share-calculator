import streamlit as st

def calculate_revenue_share_cap(
    total_contract, 
    num_payments, 
    monthly_payment, 
    expected_monthly_revenue, 
    revenue_threshold, 
    weekly_work_hours, 
    hourly_rate, 
    minimum_guarantee_pct, 
    guarantee_due_months,  # When the guarantee is due
    monthly_rev_share_pct,
    base_risk_factor=0.7,
    threshold_multiplier=0.03,  # Increased from 0.01 to 0.03 for higher sensitivity to delay
    work_multiplier=0.2, 
    guarantee_risk_factor=0.5,
    revenue_share_risk_factor=0.15
):
    """
    Calculates the Revenue Share Cap using several risk factors.
    
    1. **Contract Payment Risk:**  
       Unpaid portion of the contract increases risk.
       base_multiplier = 1 + (unpaid_fraction × base_risk_factor)
    
    2. **Revenue Delay Risk:**  
       Delay (beyond a 1‑month baseline) until revenue share payments start.
       revenue_delay_multiplier = 1 + (delay_months × threshold_multiplier)
    
    3. **Work/Pay Deficit Risk:**  
       The gap between expected monthly earnings (weekly_work_hours × hourly_rate × 4)
       and the monthly payment.
       deficit_multiplier = 1 + (deficit_percentage × work_multiplier)
    
    4. **Guarantee Risk:**  
       A lower minimum guarantee (or a longer wait for it) increases risk.
       guarantee_multiplier = 1 + ((1 – guarantee_pct_decimal) × guarantee_risk_factor × (guarantee_due_months / 12))
    
    5. **Revenue Share Risk:**  
       A lower monthly revenue share percentage increases risk.
       rev_share_multiplier = 1 + ((1 – rev_share_decimal) × revenue_share_risk_factor)
    
    The Final Multiplier is the product of these five multipliers, and:
      Revenue Share Cap = total_contract × Final Multiplier
    """
    # 1. Contract Payment Risk
    total_paid = monthly_payment * num_payments
    unpaid_balance = max(total_contract - total_paid, 0)
    risk_from_contract = unpaid_balance / total_contract  # 0 if fully paid; 1 if nothing paid
    base_multiplier = 1 + risk_from_contract * base_risk_factor

    # 2. Revenue Delay Risk
    if expected_monthly_revenue > 0:
        time_to_revenue_share = revenue_threshold / expected_monthly_revenue
    else:
        time_to_revenue_share = 0
    delay_months = max(time_to_revenue_share - 1, 0)  # baseline: revenue shares start after 1 month
    revenue_delay_multiplier = 1 + delay_months * threshold_multiplier

    # 3. Work/Pay Deficit Risk
    expected_monthly_earnings = weekly_work_hours * hourly_rate * 4  # approx. 4 weeks/month
    pay_deficit = max(expected_monthly_earnings - monthly_payment, 0)
    deficit_percentage = pay_deficit / expected_monthly_earnings if expected_monthly_earnings > 0 else 0
    deficit_multiplier = 1 + deficit_percentage * work_multiplier

    # 4. Guarantee Risk
    guarantee_decimal = minimum_guarantee_pct / 100.0  # 1.0 means full guarantee (no extra risk)
    guarantee_multiplier = 1 + (1 - guarantee_decimal) * guarantee_risk_factor * (guarantee_due_months / 12)

    # 5. Revenue Share Risk
    rev_share_decimal = monthly_rev_share_pct / 100.0  # 1.0 means full monthly revenue share (minimal risk)
    rev_share_multiplier = 1 + (1 - rev_share_decimal) * revenue_share_risk_factor

    # Final Multiplier and Revenue Share Cap
    final_multiplier = (
        base_multiplier *
        revenue_delay_multiplier *
        deficit_multiplier *
        guarantee_multiplier *
        rev_share_multiplier
    )
    revenue_share_cap = total_contract * final_multiplier

    return (revenue_share_cap, final_multiplier, base_multiplier, 
            revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, rev_share_multiplier)

# ---------------- Streamlit App ----------------

st.title("Interactive Revenue Share Calculator")

st.markdown("### Input your values below:")

total_contract = st.number_input("Total contract value ($)", min_value=0.0, value=29000.0, step=100.0)
num_payments = st.number_input("Number of monthly payments", min_value=1, value=12, step=1)
monthly_payment = st.number_input("Monthly payment amount ($)", min_value=0.0, value=2000.0, step=100.0)
expected_monthly_revenue = st.number_input("Expected monthly revenue ($)", min_value=0.0, value=10000.0, step=100.0)
revenue_threshold = st.number_input("Revenue threshold ($)", min_value=0.0, value=500000.0, step=100.0)
weekly_work_hours = st.number_input("Hours per week you'll work", min_value=0.0, value=15.0, step=1.0)
hourly_rate = st.number_input("Your hourly rate ($)", min_value=0.0, value=60.0, step=1.0)
minimum_guarantee_pct = st.number_input("Minimum guarantee (% of contract)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
guarantee_due_months = st.number_input("Guarantee Due (months)", min_value=1, value=12, step=1)
monthly_rev_share_pct = st.number_input("Monthly revenue share (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

cap, final_multiplier, base_multiplier, revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, rev_share_multiplier = calculate_revenue_share_cap(
    total_contract, 
    num_payments, 
    monthly_payment, 
    expected_monthly_revenue, 
    revenue_threshold, 
    weekly_work_hours, 
    hourly_rate, 
    minimum_guarantee_pct, 
    guarantee_due_months,
    monthly_rev_share_pct
)

st.markdown("---")
st.write(f"### Revenue Share Cap: ${cap:,.2f}")
st.write(f"Final Multiplier: {final_multiplier:.2f}")

st.markdown("---")
st.write("#### Multipliers Breakdown:")
st.write(f"- **Base Multiplier (Contract Payment Risk):** {base_multiplier:.2f}")
st.write(f"- **Revenue Delay Multiplier:** {revenue_delay_multiplier:.2f}")
st.write(f"- **Deficit Multiplier (Work/Pay Deficit):** {deficit_multiplier:.2f}")
st.write(f"- **Guarantee Multiplier:** {guarantee_multiplier:.2f}")
st.write(f"- **Revenue Share Multiplier:** {rev_share_multiplier:.2f}")

st.markdown("---")
st.markdown("""
**How It Works:**  
1. **Contract Payment Risk:**  
   Determines the unpaid portion of the contract (monthly payment × number of payments) and applies a base multiplier (default factor = 0.7).  
2. **Revenue Delay Risk:**  
   Calculates how long (in months) until revenue share payments begin (revenue threshold ÷ expected monthly revenue, minus 1 month baseline). With the updated multiplier (0.03), a high threshold dramatically increases risk.
3. **Work/Pay Deficit Risk:**  
   Compares expected monthly earnings (weekly hours × hourly rate × 4) with your monthly payment; a larger shortfall increases risk modestly (multiplier factor = 0.2).
4. **Guarantee Risk:**  
   A lower minimum guarantee or a longer wait for the guarantee (in months) increases risk (multiplier factor = 0.5).
5. **Revenue Share Risk:**  
   A lower monthly revenue share percentage increases risk (multiplier factor = 0.15).
   
These factors multiply together to yield a final multiplier that adjusts the contract value to produce your Revenue Share Cap.
""")
