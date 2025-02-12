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
    threshold_multiplier=0.03,  # Sensitivity to revenue delay
    work_multiplier=0.2, 
    guarantee_risk_factor=0.5,
    revenue_share_risk_factor=0.15,
    deferred_payment_risk_factor=0.05  # Extra risk per extra deferred month
):
    """
    Calculates the Total Payment Cap using several risk factors.
    
    Factors:
    1. **Contract Payment Risk:**  
       base_multiplier = 1 + (unpaid_fraction × base_risk_factor)
       
    2. **Revenue Delay Risk:**  
       revenue_delay_multiplier = 1 + (delay_months × threshold_multiplier)
       (Delay = (revenue_threshold / expected_monthly_revenue) - 1, minimum 0)
       
    3. **Work/Pay Deficit Risk:**  
       deficit_multiplier = 1 + (deficit_percentage × work_multiplier)
       (Deficit percentage = (expected monthly earnings – monthly_payment) / expected monthly earnings)
       
    4. **Guarantee Risk:**  
       guarantee_multiplier = 1 + ((1 – (minimum_guarantee_pct / 100)) × guarantee_risk_factor × (guarantee_due_months / 12))
       
    5. **Revenue Share Risk:**  
       rev_share_multiplier = 1 + ((1 – (monthly_rev_share_pct / 100)) × revenue_share_risk_factor)
       
    6. **Deferred Payment Risk:**  
       estimated_work_months = total_contract / (hourly_rate × weekly_work_hours × 4)
       extra_months = max(num_payments - estimated_work_months, 0)
       deferred_payment_multiplier = 1 + (extra_months × deferred_payment_risk_factor)
       
    The Final Multiplier is the product of these factors, and:
      Total Payment = total_contract × Final Multiplier
      
    *Note:* The “Additional Revenue Share” is then:
      Total Payment – total_contract
    """
    # Calculate total paid upfront.
    total_paid = monthly_payment * num_payments

    # 1. Contract Payment Risk
    unpaid_balance = max(total_contract - total_paid, 0)
    risk_from_contract = unpaid_balance / total_contract  # 0 if fully paid; up to 1 if nothing paid
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
    rev_share_decimal = monthly_rev_share_pct / 100.0  # 1.0 means full revenue share (minimal risk)
    rev_share_multiplier = 1 + (1 - rev_share_decimal) * revenue_share_risk_factor

    # 6. Deferred Payment Risk
    estimated_work_months = total_contract / (hourly_rate * weekly_work_hours * 4)
    extra_months = max(num_payments - estimated_work_months, 0)
    deferred_payment_multiplier = 1 + extra_months * deferred_payment_risk_factor

    # Final Multiplier and Total Payment
    final_multiplier = (base_multiplier *
                        revenue_delay_multiplier *
                        deficit_multiplier *
                        guarantee_multiplier *
                        rev_share_multiplier *
                        deferred_payment_multiplier)
    total_payment = total_contract * final_multiplier

    return (total_payment, final_multiplier, base_multiplier, 
            revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, 
            rev_share_multiplier, deferred_payment_multiplier)

# ---------------- Streamlit App ----------------

st.title("Interactive Revenue Share Calculator")

st.markdown("### Input your values below:")

total_contract = st.number_input("Total contract value ($)", min_value=0.0, value=29000.0, step=100.0)
num_payments = st.number_input("Number of monthly payments", min_value=1, value=12, step=1)
monthly_payment = st.number_input("Monthly payment amount ($)", min_value=0.0, value=2000.0, step=100.0)
expected_monthly_revenue = st.number_input("Expected monthly revenue ($)", min_value=0.0, value=10000.0, step=100.0)
revenue_threshold = st.number_input("Revenue threshold ($)", min_value=0.0, value=20000.0, step=100.0)
weekly_work_hours = st.number_input("Hours per week you'll work", min_value=0.0, value=15.0, step=1.0)
hourly_rate = st.number_input("Your hourly rate ($)", min_value=0.0, value=60.0, step=1.0)
minimum_guarantee_pct = st.number_input("Minimum guarantee (% of contract)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
guarantee_due_months = st.number_input("Guarantee Due (months)", min_value=1, value=12, step=1)
monthly_rev_share_pct = st.number_input("Monthly revenue share (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0)

(total_payment, final_multiplier, base_multiplier, 
 revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, 
 rev_share_multiplier, deferred_payment_multiplier) = calculate_revenue_share_cap(
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

# Calculate the additional revenue share (i.e. the extra beyond the base contract)
additional_revenue_share = total_payment - total_contract

st.markdown("---")
st.write(f"### Total Payment: ${total_payment:,.2f}")
st.write(f"### Contract Value: ${total_contract:,.2f}")
st.write(f"### Additional Revenue Share: ${additional_revenue_share:,.2f}")
st.write(f"Final Multiplier: {final_multiplier:.2f}")

st.markdown("---")
st.write("#### Multipliers Breakdown:")
st.write(f"- **Base Multiplier (Contract Payment Risk):** {base_multiplier:.2f}")
st.write(f"- **Revenue Delay Multiplier:** {revenue_delay_multiplier:.2f}")
st.write(f"- **Deficit Multiplier (Work/Pay Deficit):** {deficit_multiplier:.2f}")
st.write(f"- **Guarantee Multiplier:** {guarantee_multiplier:.2f}")
st.write(f"- **Revenue Share Multiplier:** {rev_share_multiplier:.2f}")
st.write(f"- **Deferred Payment Multiplier:** {deferred_payment_multiplier:.2f}")

st.markdown("---")
st.markdown("""
**How It Works:**  
1. **Contract Payment Risk:**  
   The app calculates how much of the contract is paid upfront. Less cash upfront increases risk.
2. **Revenue Delay Risk:**  
   It estimates the delay (based on revenue threshold and expected revenue) before revenue share payments begin.
3. **Work/Pay Deficit Risk:**  
   It compares your expected monthly earnings (from work hours and hourly rate) with your monthly payment. A larger gap increases risk.
4. **Guarantee Risk:**  
   A lower minimum guarantee or a longer wait for the guarantee adds risk.
5. **Revenue Share Risk:**  
   A lower monthly revenue share percentage increases risk.
6. **Deferred Payment Risk:**  
   It estimates how long the work should take (using your hourly rate and work hours) and adds risk if payments extend beyond that period.
   
The multipliers are multiplied together to form a Final Multiplier, which adjusts the Contract Value into the Total Payment. The Additional Revenue Share is the extra amount over the Contract Value.
""")
