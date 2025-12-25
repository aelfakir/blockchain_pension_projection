import streamlit as st
import pandas as pd
import hashlib
import datetime
from dataclasses import dataclass

# 1. Define the Data Structures FIRST
@dataclass
class PensionRecord:
    year: int
    salary: float
    accrual_rate: float
    cpi_index: float

    def calculate_unit(self):
        return (self.salary * self.accrual_rate) * (1 + self.cpi_index)

@dataclass
class Block:
    index: int
    record: PensionRecord
    prev_hash: str
    timestamp: str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def hash_block(self):
        block_string = f"{self.index}{self.record}{self.prev_hash}{self.timestamp}"
        return hashlib.sha256(block_string.encode()).hexdigest()

# 2. Initialize Streamlit Page Configuration
st.set_page_config(page_title="CARE Blockchain Pension", layout="wide")

# 3. Initialize Blockchain in Session State (if not already there)
if "chain" not in st.session_state:
    genesis_record = PensionRecord(2023, 0.0, 0.0, 0.0)
    st.session_state.chain = [Block(0, genesis_record, "0")]

# 4. Sidebar for User Inputs
with st.sidebar:
    st.header("1. Log Contribution")
    year = st.number_input("Year", value=2025)
    salary = st.number_input("Annual Salary (£)", min_value=0.0, step=1000.0)
    accrual_denom = st.selectbox("Accrual Rate (1/x)", [49, 57, 60], index=0)
    cpi = st.slider("Inflation Revaluation (%)", -2.0, 10.0, 2.0) / 100

    if st.button("Secure Year in Blockchain"):
        accrual_rate = 1 / accrual_denom
        new_record = PensionRecord(year, salary, accrual_rate, cpi)
        prev_hash = st.session_state.chain[-1].hash_block()
        new_block = Block(len(st.session_state.chain), new_record, prev_hash)
        st.session_state.chain.append(new_block)
        st.success(f"Year {year} locked!")

    st.divider()
    
    st.header("2. Retirement Settings")
    npa = st.number_input("Normal Pension Age (NPA)", value=67, min_value=50)
    retire_age = st.number_input("Planned Retirement Age", value=67, min_value=50)
    reduction_rate = st.number_input("Annual Reduction % (if early)", value=4.0, step=0.5) / 100

# 5. Calculations (Define total_pension_raw before it's displayed)
total_pension_raw = sum(b.record.calculate_unit() for b in st.session_state.chain[1:])

if retire_age < npa:
    years_early = npa - retire_age
    total_reduction = years_early * reduction_rate
    final_pension = total_pension_raw * (1 - total_reduction)
    status_msg = f"⚠️ Early Retirement: {total_reduction:.0%} total reduction applied ({years_early} years early)."
else:
    final_pension = total_pension_raw
    status_msg = "✅ Retirement at or after NPA: 100% of accrued pension awarded."

# 6. Main UI Display
st.title("🛡️ CARE Pension Blockchain")

st.subheader("Financial Projection")
c1, c2, c3 = st.columns(3)
c1.metric("Accrued Base Pension", f"£{total_pension_raw:,.2f}")
c2.metric("Adjustment Factor", f"{(final_pension/max(total_pension_raw, 1)):.0%}")
c3.metric("Final Annual Payout", f"£{final_pension:,.2f}")

st.info(status_msg)

# Display the Ledger Table
st.subheader("Verified Blockchain Ledger")
df_data = []
for block in st.session_state.chain[1:]:
    unit = block.record.calculate_unit()
    df_data.append({
        "Year": block.record.year,
        "Salary": f"£{block.record.salary:,.2f}",
        "Accrual": f"1/{int(1/block.record.accrual_rate)}",
        "Inflation": f"{block.record.cpi_index:.1%}",
        "Pension Earned": f"£{unit:,.2f}",
        "Block Hash": block.hash_block()[:15] + "..."
    })

if df_data:
    st.table(pd.DataFrame(df_data))
else:
    st.write("No contributions logged yet. Add your first year in the sidebar.")
