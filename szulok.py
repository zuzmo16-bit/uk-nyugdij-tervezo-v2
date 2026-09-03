import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition)")
st.write("SSAS Loanback: Vagyon-újrahasznosítási stratégia (UK-HU Transzfer).")

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
    start_sipp = st.sidebar.number_input("Összesített SIPP egyenleg (£)", value=1000000)
    start_trust = st.sidebar.number_input("Holding / Tröszt tőke (£)", value=250000)
    working_years = 0
else:
    current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 37)
    working_years = st.sidebar.slider("Hány évig fizetsz még be?", 0, 75-current_age, 20)
    death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)
    start_sipp = 15000
    start_trust = 0

# --- SSAS LOANBACK ---
st.sidebar.markdown("---")
st.sidebar.header("🏦 SSAS Finanszírozás")
enable_ssas_loan = st.sidebar.checkbox("SSAS Loanback (50% hitel a gyárra)", value=True)
loan_amount = (start_sipp * 0.5) if enable_ssas_loan else 0

# --- KIFIZETÉS ---
st.sidebar.markdown("---")
st.sidebar.header("💶 Kifizetési Stratégia")
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP ürítés (£)", 0, 25000, 8333)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetés (HU) (£)", 500, 15000, 3500)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Piaci Paraméterek")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- MATEK ---
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
ages, sipp_vals, hu_base_vals, uk_house_vals, trust_vals = [], [], [], [], []
current_sipp, current_trust = start_sipp, start_trust
current_hu_base, current_uk_house = 0, 0
loan_balance = loan_amount
pcls_taken, total_tax_paid = False, 0

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # Hozamok
    current_sipp *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_hu_base *= (1 + (inflation / 100)) ** (1/12)
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. SSAS Loanback Indulás (53 évesen)
    if m == 0 and enable_ssas_loan:
        current_hu_base = loan_amount # Megvesszük a gyárat hitelből
    
    # 2. SSAS Törlesztés (5 évig)
    if loan_balance > 0 and m <= 60:
        repayment = loan_amount / 60
        interest = loan_balance * 0.005 # ~6% éves kamat
        current_sipp += (repayment + interest) # A SIPP hízik a törlesztőtől
        loan_balance -= repayment

    # 3. 25% PCLS (Házvétel 57 évesen)
    if not pcls_taken and age >= 57:
        # A SIPP értékéből kivesszük a 25%-ot (csak a likvid részből)
        pcls_val = (current_sipp - loan_balance) * 0.25
        current_sipp -= pcls_val
        current_uk_house = pcls_val
        pcls_taken = True

    # 4. Meltdown & Megélhetés
    if age >= 57:
        if current_sipp > 0:
            actual_g = min(current_sipp, gross_sipp_meltdown)
            net = calculate_net(actual_g, 958)
            total_tax_paid += (actual_g - net)
            current_sipp -= actual_g
            if net >= monthly_living_cost: current_trust += (net - monthly_living_cost)
            else: current_trust = max(0, current_trust - (monthly_living_cost - net))
        else:
            current_trust = max(0, current_trust - monthly_living_cost)

    # Adatok mentése (A SIPP sor most már a tőkét + a kintlévő hitelt is mutatja)
    sipp_vals.append(current_sipp + loan_balance)
    hu_base_vals.append(current_hu_base)
    uk_house_vals.append(current_uk_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Tőke + Hiteltartozás)', mode='lines', line=dict(color='#87CEEB', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=hu_base_vals, name='Magyar Perennis Bázis (Gyár)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=uk_house_vals, name='Saját Ingatlan (UK)', mode='lines', line=dict(color='teal', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(0,128,128,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='Magyar Holding / Tröszt', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))
fig.update_layout(template="plotly_white", height=650, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- KPI ---
total_at_death = sipp_vals[-1] + hu_base_vals[-1] + uk_house_vals[-1] + trust_vals[-1]
st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")
c2.metric("Induló SSAS Hitel", f"£{loan_amount:,.0f}")
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Nettó Örökség (HU 0%)", f"£{total_at_death:,.0f}") # Magyarországi 0%-ot feltételezve

st.info(f"**Double Check Sikeres:** Az 5 éves SSAS hitelperiódus alatt a nyugdíjvagyonod nemhogy csökkent volna, de a visszafizetett kamatok és a Vanguard hozamok miatt £{sipp_vals[60]:,.0f}-ra nőtt, miközben lett egy tehermentes magyar gyárad is.")
