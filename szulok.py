import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK HoldCo Investment Strategy", layout="wide", page_icon="📈")

st.title("📈 SIPP -> HoldCo Befektetési Stratégia")
st.write("A modell azt szimulálja, amikor a SIPP 25%-át a Holding cégbe fekteted be (Vanguard All-World), és onnan kapod vissza a törlesztést.")

# 🎛️ PARAMÉTEREK
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 75, 43)
working_years = st.sidebar.slider("Hány évig termel még a cég? (SIPP befizetés)", 0, 40, 14)
target_age = 100 

st.sidebar.markdown("---")
st.sidebar.header("🔓 SIPP & HoldCo Esemény")
lump_sum_age = st.sidebar.slider("SIPP 25% kivétel életkora", 57, 75, 57)
monthly_payout = st.sidebar.number_input("Havi kifizetés a Holdingból (£)", value=3000)

st.sidebar.markdown("---")
st.sidebar.header("💰 Pénzügyi Beállítások")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

st.sidebar.header("📈 Piaci Hozamok")
market_return = st.sidebar.slider("Vanguard All-World várható hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# Reálhozam számítás
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

# Szimuláció
ages = []
sipp_vals = []
holdco_vals = []
total_wealth = []

current_sipp = initial_sipp
current_holdco = 0
pcls_taken = False
director_loan_account = 0

total_months = (target_age - current_age) * 12

for m in range(total_months + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Piaci növekedés (SIPP és HoldCo is befektetve van)
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 2. Aktív évek befizetései
    if m <= (working_years * 12):
        current_sipp += monthly_cont
        
    # 3. A NAGY ESEMÉNY: SIPP 25% -> Holding (Vanguard)
    if age >= lump_sum_age and not pcls_taken:
        lump_sum_val = current_sipp * 0.25
        current_sipp -= lump_sum_val
        current_holdco += lump_sum_val # A Holding befekteti a pénzt
        director_loan_account = lump_sum_val # Ennyivel tartozik a cég neked
        pcls_taken = True

    # 4. Kifizetés: Törlesztés a Holdingból
    if pcls_taken:
        if current_holdco >= monthly_payout:
            current_holdco -= monthly_payout
            # A DLA (Director's Loan Account) fogy, amíg tart, addig adómentes
            director_loan_account = max(0, director_loan_account - monthly_payout)
        else:
            # Ha a Holding elfogy, a SIPP-ből vonjuk le a maradékot
            remainder = monthly_payout - current_holdco
            current_holdco = 0
            current_sipp = max(0, current_sipp - remainder)

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)
    total_wealth.append(current_sipp + current_holdco)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=total_wealth, name='Teljes Nettó Vagyon', line=dict(color='royalblue', width=4)))
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg (Vanguard)', line=dict(color='lightblue', dash='dash')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo egyenleg (Vanguard)', line=dict(color='gold', width=2)))

fig.update_layout(
    title=f"HoldCo Stratégia: {lump_sum_age} éves kortól havi £{monthly_payout} kifizetés",
    xaxis_title="Életkor",
    yaxis_title="Vagyon (£)",
    height=600,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# Összegző infó
st.markdown("### 📝 Stratégiai összefoglaló")
col1, col2, col3 = st.columns(3)
col1.metric("Kivett PCLS összeg", f"£{director_loan_account + (monthly_payout * (target_age-lump_sum_age)*12 if not pcls_taken else 0):,.0f}")
col2.metric("Holding kifutási ideje", f"{'Elfogy' if holdco_vals[-1] == 0 else 'Kitart 100 éves korig'}")
col3.metric("Végső örökség (100 év)", f"£{total_wealth[-1]:,.0f}")

st.info(f"""
**Hogyan működik ez a szimuláció?**
1. **SIPP fázis:** 57 éves korig a céged havi £{monthly_cont}-t tesz be adómentesen.
2. **Transfer:** {lump_sum_age} évesen a SIPP 25%-a átkerül a Holdingba. Ezt a cég **Vanguard All-World**-be fekteti.
3. **Repayment:** A cég havi £{monthly_payout}-t fizet neked. Ez a HMRC szemében **tagi kölcsön visszafizetése**, tehát nem jövedelemadó-köteles számodra, amíg a tőke tart.
4. **Hozam:** A Holdingban lévő pénz nem csak 'ül', hanem a piaci {market_return}%-kal növekszik, ami jelentősen kitolja azt az időt, amíg a Holdingból tudsz élni.
""")
