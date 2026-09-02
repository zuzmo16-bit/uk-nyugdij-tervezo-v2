import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK Retirement & Tax Strategy", layout="wide", page_icon="🛡️")

st.title("🛡️ UK Nyugdíj & Privát Vagyonkezelő Szimulátor")
st.warning("Figyelem: A Director's Loan (tagi kölcsön) bonyolult adózási kérdéseket vethet fel. Ez a modell a tőke mozgását és a hozamokat szimulálja, de mindenképpen konzultálj brit adótanácsadóval!")

# 🎛️ BEÁLLÍTÁSOK
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 75, 43)
working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be? (Céges befizetés)", 0, 40, 14)
target_age = 100 

st.sidebar.markdown("---")
st.sidebar.header("🔓 SIPP Stratégia (57+ év)")
lump_sum_age = st.sidebar.slider("25% Tax-Free kifizetés életkora", 57, 75, 57)
monthly_income_target = st.sidebar.number_input("Havi cél jövedelem (nettó £)", value=3000, step=100)

st.sidebar.markdown("---")
st.sidebar.header("🏦 Pénzügyi Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_pension_cont = st.sidebar.number_input("Havi céges befizetés (Gross) (£)", value=5000)
annual_return = st.sidebar.slider("Várható éves piaci hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# Matematikai alapok (Reálhozam)
real_annual_rate = ((1 + (annual_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_annual_rate) ** (1/12) - 1

# Szimulációs tömbök
ages = []
total_wealth = []
sipp_bal = []
private_bal = [] # Ez a 'Privát Befektetési Alap', ahol a 25% kamatozik

# Kezdőértékek
current_sipp = initial_sipp
current_private = 0
pcls_taken = False

for m in range((target_age - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Hozamok
    current_sipp *= (1 + m_rate)
    current_private *= (1 + m_rate)
    
    # 2. Befizetés (amíg dolgozol)
    if m <= (working_years * 12):
        current_sipp += monthly_pension_cont
        
    # 3. 25% Tax-Free Lump Sum (Ezt kiveszed és félreteszed befektetésbe)
    if age >= lump_sum_age and not pcls_taken:
        amount = current_sipp * 0.25
        current_sipp -= amount
        current_private += amount # Átkerül a privát portfólióba
        pcls_taken = True

    # 4. Jövedelem kifizetése (Drawdown)
    if age >= lump_sum_age:
        # Először a privát portfóliót (25%-ot) éljük fel, mert az már adózott pénz
        if current_private >= monthly_income_target:
            current_private -= monthly_income_target
        else:
            remainder = monthly_income_target - current_private
            current_private = 0
            current_sipp = max(0, current_sipp - remainder)

    sipp_bal.append(current_sipp)
    private_bal.append(current_private)
    total_wealth.append(current_sipp + current_private)

# --- GRAFIKON ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=total_wealth, name='Összesített Vagyon (Reálérték)', line=dict(color='royalblue', width=4)))
fig.add_trace(go.Scatter(x=ages, y=sipp_bal, name='SIPP (Adóköteles rész)', line=dict(color='lightblue', dash='dash')))
fig.add_trace(go.Scatter(x=ages, y=private_bal, name='Privát Alap (A 25% hozamaival)', line=dict(color='orange', dash='dot')))

fig.update_layout(
    title="Vagyonfelépítés és Felélés (Inflációval korrigálva)",
    xaxis_title="Életkor",
    yaxis_title="Vagyon (£)",
    height=600,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

# KPI blokk
st.markdown("### 📊 Mérföldkövek")
col1, col2 = st.columns(2)
col1.metric("SIPP értéke a kifizetéskor", f"£{max(sipp_bal + private_bal):,.0f}")
col2.metric("Örökség 100 évesen", f"£{total_wealth[-1]:,.0f}")

st.info(f"""
**Hogyan működik ez a modell adózási szempontból?**
1. **SIPP Befizetés:** A céged levonja a profitból (Corporation Tax megtakarítás).
2. **57 évesen:** Kiveszed a 25%-ot. Ez a HMRC szerint adómentes. Nem kölcsönként, hanem **magánvagyonként** kezeled.
3. **Kifizetés:** A havi £{monthly_income_target}-ot először ebből a magánvagyonból fedezed. Mivel ez már a te pénzed, nincs jövedelemadó rajta.
4. **SIPP Maradék:** Amíg a magánpénzedből élsz, a SIPP-ed (75%) tovább termeli a hozamot adómentes környezetben.
""")
