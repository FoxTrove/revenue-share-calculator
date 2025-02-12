import streamlit as st

# Define a constant hourly rate for the service provider (hidden from the client)
SERVICE_PROVIDER_HOURLY_RATE = 60.0

def calculate_revenue_share_cap(
    total_contract, 
    num_payments, 
    monthly_payment, 
    expected_monthly_revenue, 
    revenue_threshold, 
    service_provider_hours, 
    minimum_guarantee_pct, 
    guarantee_due_months,  # Guarantee due term (months)
    monthly_rev_share_pct,
    base_risk_factor=0.5,
    threshold_multiplier=0.03,  # Sensitivity to revenue delay
    work_multiplier=0.2, 
    guarantee_risk_factor=0.5,
    revenue_share_risk_factor=0.15,
    deferred_payment_risk_factor=0.05  # Extra risk per extra deferred month
):
    """
    Calculates the Total Payment Cap (the adjusted total payment including risk) 
    and the Additional Revenue Share (Total Payment minus Contract Value).

    Risk factors are applied if full contract payment isn’t achieved “timely.”
    
    1. **Contract Payment Risk:**  
       base_multiplier = 1 + (unpaid_fraction * base_risk_factor)
       
    2. **Revenue Delay Risk:**  
       revenue_delay_multiplier = 1 + (delay_months * threshold_multiplier)  
       (Delay = (revenue_threshold / expected_monthly_revenue) - 1, minimum 0)
       
    3. **Work/Pay Deficit Risk:**  
       deficit_multiplier = 1 + (deficit_percentage * work_multiplier)  
       (Deficit percentage = (service provider's expected monthly earnings – monthly_payment) / expected monthly earnings)
       
    4. **Guarantee Risk:**  
       - First, compute the baseline guarantee percentage:  
         baseline_guarantee_pct = (monthly_payment × guarantee_due_months) / total_contract × 100.
       - If minimum guarantee is 100%, then guarantee_multiplier = 1.
       - If minimum guarantee is 0%, then guarantee_multiplier = 1 + guarantee_risk_factor × (guarantee_due_months/12).
       - Otherwise, if the minimum guarantee is greater than baseline:
             If (monthly_payment × guarantee_due_months) ≥ (total_contract × (minimum_guarantee_pct/100)), then guarantee_multiplier = 1.
             Else, let shortfall_ratio = (guaranteed_amount - actual_payments) / guaranteed_amount, and then:
             guarantee_multiplier = 1 + shortfall_ratio × guarantee_risk_factor × (guarantee_due_months/12).
       
    5. **Revenue Share Risk:**  
       rev_share_multiplier = 1 + ((1 - (monthly_rev_share_pct / 100)) × revenue_share_risk_factor)
       
    6. **Deferred Payment Risk:**  
       estimated_work_months = total_contract / (SERVICE_PROVIDER_HOURLY_RATE × service_provider_hours × 4).
       If total_paid ≥ total_contract, then deferred_payment_multiplier = 1.
       Else, extra_months = max(num_payments - estimated_work_months, 0) and
       deferred_payment_multiplier = 1 + (extra_months × deferred_payment_risk_factor)
       
    Final Multiplier = product of all multipliers.
    Total Payment = total_contract × Final Multiplier.
    Additional Revenue Share = Total Payment – total_contract.
    
    *Note:* If full payment is achieved on or before the estimated work duration, all extra risk is neutralized.
    """
    # Total paid from monthly payments
    total_paid = monthly_payment * num_payments

    # Estimated work duration (in months) based on service provider's capacity
    estimated_work_months = total_contract / (SERVICE_PROVIDER_HOURLY_RATE * service_provider_hours * 4)

    # 1. Contract Payment Risk
    unpaid_balance = max(total_contract - total_paid, 0)
    risk_from_contract = unpaid_balance / total_contract  # 0 if fully paid; up to 1 if nothing is paid
    base_multiplier = 1 + risk_from_contract * base_risk_factor

    # 2. Revenue Delay Risk
    if expected_monthly_revenue > 0:
        time_to_revenue_share = revenue_threshold / expected_monthly_revenue
    else:
        time_to_revenue_share = 0
    delay_months = max(time_to_revenue_share - 1, 0)  # revenue share kicks in after 1 month baseline
    revenue_delay_multiplier = 1 + delay_months * threshold_multiplier

    # 3. Work/Pay Deficit Risk
    expected_monthly_earnings = service_provider_hours * SERVICE_PROVIDER_HOURLY_RATE * 4
    pay_deficit = max(expected_monthly_earnings - monthly_payment, 0)
    deficit_percentage = pay_deficit / expected_monthly_earnings if expected_monthly_earnings > 0 else 0
    deficit_multiplier = 1 + deficit_percentage * work_multiplier

    # 4. Guarantee Risk
    # Compute baseline guarantee percentage: what percentage of the contract is covered by scheduled payments over the guarantee period.
    baseline_guarantee_pct = (monthly_payment * guarantee_due_months) / total_contract * 100

    if minimum_guarantee_pct >= 100:
        guarantee_multiplier = 1.0
    elif minimum_guarantee_pct <= 0:
        guarantee_multiplier = 1 + guarantee_risk_factor * (guarantee_due_months / 12)
    else:
        # Compute the "guaranteed amount" based on the client's promise:
        guaranteed_amount = total_contract * (minimum_guarantee_pct / 100)
        # Actual payments expected over the guarantee period:
        actual_payments = monthly_payment * guarantee_due_months
        if actual_payments >= guaranteed_amount:
            guarantee_multiplier = 1.0
        else:
            shortfall_ratio = (guaranteed_amount - actual_payments) / guaranteed_amount
            guarantee_multiplier = 1 + shortfall_ratio * guarantee_risk_factor * (guarantee_due_months / 12)

    # 5. Revenue Share Risk
    rev_share_decimal = monthly_rev_share_pct / 100.0
    rev_share_multiplier = 1 + (1 - rev_share_decimal) * revenue_share_risk_factor

    # 6. Deferred Payment Risk
    if total_paid >= total_contract:
        deferred_payment_multiplier = 1.0
    else:
        extra_months = max(num_payments - estimated_work_months, 0)
        deferred_payment_multiplier = 1 + extra_months * deferred_payment_risk_factor

    # Neutralize extra risk if full payment is achieved on or before the estimated work duration
    if total_paid >= total_contract and num_payments <= estimated_work_months:
        base_multiplier = revenue_delay_multiplier = deficit_multiplier = guarantee_multiplier = rev_share_multiplier = deferred_payment_multiplier = 1.0
        final_multiplier = 1.0
    else:
        final_multiplier = (base_multiplier *
                            revenue_delay_multiplier *
                            deficit_multiplier *
                            guarantee_multiplier *
                            rev_share_multiplier *
                            deferred_payment_multiplier)

    total_payment = total_contract * final_multiplier
    additional_revenue_share = total_payment - total_contract

    return (total_payment, final_multiplier, base_multiplier, 
            revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, 
            rev_share_multiplier, deferred_payment_multiplier, additional_revenue_share)

# ---------------- Streamlit App ----------------

st.title("Interactive Revenue Share Calculator")

st.markdown("### Input your values below:")

total_contract = st.number_input("Total contract value ($)", min_value=0.0, value=29000.0, step=100.0,
                                 help="The full contract value for the project.")
num_payments = st.number_input("Number of monthly payments", min_value=1, value=6, step=1,
                               help="The number of months over which payments will be made.")
monthly_payment = st.number_input("Monthly payment amount ($)", min_value=0.0, value=5000.0, step=100.0,
                                  help="The cash amount paid each month.")
expected_monthly_revenue = st.number_input("Expected monthly revenue ($)", min_value=0.0, value=10000.0, step=100.0,
                                           help="The revenue the company is expected to generate each month.")
revenue_threshold = st.number_input("Revenue threshold ($)", min_value=0.0, value=20000.0, step=100.0,
                                    help="The revenue level that triggers revenue share payments.")
service_provider_hours = st.number_input("Service provider hours per week", min_value=0.0, value=15.0, step=1.0,
                                         help="The number of hours per week the service provider will work on the project.")
minimum_guarantee_pct = st.number_input("Minimum guarantee (% of contract)", min_value=0.0, max_value=100.0, value=0.0, step=1.0,
                                        help="The percentage of the contract value that is guaranteed to be paid. Guarantees above the baseline (monthly payments cover a certain % of the contract) reduce risk.")
guarantee_due_months = st.number_input("Guarantee Due (months)", min_value=1, value=6, step=1,
                                       help="The number of months within which the guaranteed payment must be completed.")
monthly_rev_share_pct = st.number_input("Monthly revenue share (%)", min_value=0.0, max_value=100.0, value=20.0, step=1.0,
                                        help="The percentage of monthly revenue to be shared after the guarantee period.")

(total_payment, final_multiplier, base_multiplier, 
 revenue_delay_multiplier, deficit_multiplier, guarantee_multiplier, 
 rev_share_multiplier, deferred_payment_multiplier, additional_revenue_share) = calculate_revenue_share_cap(
    total_contract, 
    num_payments, 
    monthly_payment, 
    expected_monthly_revenue, 
    revenue_threshold, 
    service_provider_hours, 
    minimum_guarantee_pct, 
    guarantee_due_months,
    monthly_rev_share_pct
)

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
   Calculates the portion of the contract not paid upfront. Lower upfront cash increases risk.
2. **Revenue Delay Risk:**  
   Estimates the delay before revenue share kicks in (based on revenue threshold and expected revenue).
3. **Work/Pay Deficit Risk:**  
   Compares the service provider's expected monthly earnings (from service provider hours and the fixed hourly rate) with the monthly payment. A larger gap increases risk.
4. **Guarantee Risk:**  
   First, the tool calculates a baseline guarantee percentage (the % of the contract covered by scheduled payments over the guarantee period).  
   - If the minimum guarantee is 100%, no extra risk is added.  
   - If the minimum guarantee is below this baseline, the risk is fully active.  
   - If the minimum guarantee is above the baseline, each additional percentage point reduces risk.
5. **Revenue Share Risk:**  
   A lower monthly revenue share percentage increases risk.
6. **Deferred Payment Risk:**  
   Estimates how long the work should take (total contract divided by the service provider’s monthly capacity) and adds risk if the payment period extends beyond that.
   
These multipliers multiply together to form a Final Multiplier that adjusts the Contract Value into the Total Payment. The Additional Revenue Share is the extra amount above the Contract Value.
""")
