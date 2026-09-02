import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- KONFIGURÁCIÓ ---
st.set_page_config(page_title="UK SIPP Split Strategy", layout="wide", page_icon="🏠")

st.title("🏠 UK SIPP: Házvétel 57 évesen & Munka folytatása")
st.write("Ez a modell lehetővé teszi a 25% kivételét (pl. házra) anélkül, hogy leállítaná a nyugdíjbefizetéseket.")

# --- SIDEBAR ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 31)
working_years = st.sidebar.slider("Hány évig dolgozol még összesen?", 0, int(75-current_age), 39)

st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Mérföldkövek")

# 1. ESSEMÉNY: A 25% adómentes kivétele (pl. Házvásárlás)
pcls_age = st.sidebar.slider("Hány évesen veszed ki a 25%-ot (Házvétel)?", 57, 75, 57)

# 2. ESEMÉNY: Mikor hagyod abba a munkát és kezded el a kifizetést?
drawdown_start_age = st.sidebar.slider("Hány évesen induljon a havi járadék (Meltdown)?", 57, 75, 70)

st.sidebar.markdown("---")
st.sidebar.header("👷 Alkalmazotti bér")
hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
hours_per_week = st.sidebar.number_input("Heti óraszám", value=40)
ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)

active_annual_gross = (hourly_rate * hours_per_week * 52) + (53.70 * 26) # Alap + Hétvégi pótlék
monthly_contribution = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)

st.sidebar.markdown("---")
st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
def calculate_net(sipp_m, state_m):
    total_gross_a = (sipp_m + state_m) * 12
    pa = 12570
    if total_gross_a > 100000:
        pa = max(0, pa - (total_gross_a - 100000) / 2)
    taxable = max(0, total_gross_a - pa)
    tax = 0
    if taxable > 0:
        b20 = min(taxable, 37700)
        tax += b20 * 0.20
        if taxable > 37700:
            b40 = min(taxable - 37700, 125140 - 37700)
            tax += b40 * 0.40
        if taxable > 125140:
            tax += (taxable - 125140) * 0.45
    return (total_gross_a - tax) / 12

# --- SZIMULÁCIÓ ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, house_wealth, holdco_vals = [], [], [], []
current_sipp, current_holdco, current_house = initial_sipp, 0, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12) # A ház értéke csak az inflációval nő

    # BEFIZETÉS: Folyamatos, amíg tart a munka (független a 25%-tól!)
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution
        
    # 25% KIVÉTELE (PCLS)
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25
        current_sipp -= lump
        current_house = lump # Ez a "Ház értéke"
        pcls_taken = True
        
    # HAVI KIFIZETÉS (Drawdown)
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_sipp_g = min(current_sipp, 4189) # Tegyük fel havi 4k kivétet ürítésre
            net_income = calculate_net(actual_sipp_g, 0)
            total_tax_paid += (actual_sipp_g - net_income)
            current_sipp -= actual_sipp_g
            # Itt most mindent a HoldCo-ba teszünk, hogy lássuk a vagyont
            current_holdco += net_income
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS ---
emptied_str = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 Stratégia: Házvétel {pcls_age} évesen | Nyugdíjba vonulás {drawdown_start_age} évesen")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Bentmaradó 75%)', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan értéke (25%)', fill='tonexty', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo / Későbbi vagyon', line=dict(color='gold', width=4)))

fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=600, hovermode="x unified")
fig.add_vline(x=pcls_age, line_dash="dot", line_color="orange", annotation_text="HÁZVÉTEL")
fig.add_vline(x=drawdown_start_age, line_dash="dash", line_color="green", annotation_text="NYUGDÍJ")
st.plotly_chart(fig, use_container_width=True)

st.success(f"""
**Hogy működik a terved a számok alapján?**
1. **{pcls_age} évesen:** Kivettél £{house_wealth[int((pcls_age-current_age)*12)]:,.0f} összeget adómentesen. Ebből veszed meg a házat.
2. **Folytatás:** Mivel nem vettél ki adóköteles részt, a befizetéseid (havi £{monthly_contribution:,.0f}) zavartalanul mennek tovább a SIPP-be.
3. **{drawdown_start_age} évesen:** Leteszed a munkát, és elkezded a SIPP maradékának kiürítését.
4. **Eredmény:** A grafikonon látszik, hogy a SIPP (kék) 57 évesen beesik egy kicsit, de utána **tovább hízik** egészen {drawdown_start_age} éves korodig!
""")
