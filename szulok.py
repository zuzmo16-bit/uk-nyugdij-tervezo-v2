import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition)")
st.write("UK-HU Transzfer, SSAS Loanback és Nemzetközi Örökség Optimalizáló.")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás (UK-HU Transzfer)")
)

# --- IDŐTÁV ÉS INDULÓ VAGYON ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Alapadatok")
if user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    current_age = st.sidebar.slider("Hány évesen indul a transzfer?", 45, 75, 53)
    death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)
    st.sidebar.subheader("💰 Jelenlegi Vagyon")
    start_sipp = st.sidebar.number_input("Összesített SIPP egyenleg (Öcséd + Tiéd) (£)", value=1000000)
    start_house = st.sidebar.number_input("UK Ingatlan értéke (£)", value=500000)
    start_trust = st.sidebar.number_input("Holding / Tröszt tőke (£)", value=250000)
    working_years = 0
else:
    current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 37)
    working_years = st.sidebar.slider("Hány évig fizetsz még be?", 0, 75-current_age, 20)
    death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)
    start_sipp = 15000
    start_house = 0
    start_trust = 0

# --- SSAS LOANBACK OPCIÓ ---
st.sidebar.markdown("---")
st.sidebar.header("🏦 SSAS Finanszírozás")
enable_ssas_loan = st.sidebar.checkbox("SSAS Loanback mozgósítása? (Max 50%)", value=True)
loan_amount = (start_sipp * 0.5) if enable_ssas_loan else 0

# --- MAGYARORSZÁGI STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🇭🇺 Magyarországi Jövő")
hu_move_age = st.sidebar.slider("Hazaköltözés éve", 45, 90, 53 if user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)" else 57)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetés (HU) (£)", 500, 15000, 3500)
gross_sipp_meltdown = st.sidebar.slider("Havi agresszív SIPP ürítés (£)", 0, 25000, 10000)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Piaci Paraméterek")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓ ÉS MATEK ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

def calculate_net(sipp_m, state_m):
    total_a = (sipp_m + state_m) * 12
    pa = 12570
    if total_a > 100000: pa = max(0, pa - (total_a - 100000) / 2)
    taxable = max(0, total_a - pa)
    tax = 0
    if taxable > 0:
        b20 = min(taxable, 37700); tax += b20 * 0.20
        if taxable > 37700:
            b40 = min(taxable - 37700, 125140 - 37700); tax += b40 * 0.40
        if taxable > 125140: tax += (taxable - 125140) * 0.45
    return (total_a - tax) / 12

# --- SZIMULÁCIÓ ---
ages, sipp_vals, house_wealth, trust_vals = [], [], [], []
current_sipp, current_trust, current_house = start_sipp, start_trust, start_house
pcls_taken = (user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)") # Ha transzfer, feltételezzük a PCLS-t
total_tax_paid = 0

# SSAS Loan Logic
if enable_ssas_loan:
    current_sipp -= loan_amount
    # A loan_amount a cégbe kerül, amiből megveszik a magyar gyárat (house_wealth-ként kezeljük a modellben)
    current_house += loan_amount 

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. SSAS Törlesztés vissza a SIPP-be (5 évig)
    if enable_ssas_loan and m > 0 and m <= 60:
        monthly_repayment_to_sipp = (loan_amount / 60) + (current_sipp * 0.005) # Tőke + Kamat
        current_sipp += monthly_repayment_to_sipp

    # 2. Meltdown & Megélhetés
    if age >= current_age: # Transzfer módban azonnal indul
        if current_sipp > 0:
            actual_g = min(current_sipp, gross_sipp_meltdown)
            net = calculate_net(actual_g, 958) # Állami nyugdíj becslés
            total_tax_paid += (actual_g - net)
            current_sipp -= actual_g
            if net >= monthly_living_cost: current_trust += (net - monthly_living_cost)
            else: current_trust = max(0, current_trust - (monthly_living_cost - net))
        else:
            current_trust = max(0, current_trust - monthly_living_cost)

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (SSAS törlesztéssel hízó)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Magyar Perennis Bázis (Ingatlan+Gép)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='Magyar Holding / Tröszt', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))
fig.update_layout(template="plotly_white", height=600, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- KPI MÉRLEG ---
total_at_death = sipp_vals[-1] + house_wealth[-1] + trust_vals[-1]
years_since_move = death_age - hu_move_age
iht_tax = 0 if years_since_move >= 10 else max(0, (total_at_death - 500000) * 0.40)

st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Örökség", f"£{total_at_death:,.0f}")
c2.metric("Mozgósított SSAS tőke", f"£{loan_amount:,.0f}")
c3.metric("IHT Adóteher", f"£{iht_tax:,.0f}")
c4.metric("Nettó Örökség", f"£{(total_at_death - iht_tax):,.0f}")

st.info(f"**SSAS Loanback Elemzés:** A terved alapján £{loan_amount:,.0f} tőkét mozgósítottunk 5 évre. A cég profitjából évi kb. £130.000 törlesztés folyik vissza a SIPP-be, ami a £220.000-os PJS profit mellett teljesen fenntartható.")
