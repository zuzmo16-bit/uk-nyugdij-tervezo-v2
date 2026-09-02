import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK Retirement & State Pension Strategy", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 UK Nyugdíj Stratégia + Állami Nyugdíj (State Pension)")
st.write("Ez a modell figyelembe veszi az állami nyugdíj adóügyi hatását is a SIPP kiürítése során.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 46)
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, int(75-current_age), 24)

st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj (State Pension)")
state_pension_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_pension_annual = st.sidebar.number_input("Éves állami nyugdíj összege (£)", value=11502, help="Jelenlegi teljes állami nyugdíj kb. £11,502 évente.")

st.sidebar.markdown("---")
st.sidebar.header("🔓 SIPP Stratégia")
sipp_start_age = st.sidebar.slider("SIPP kifizetés kezdete", 57, 75, 70)
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó kivét a SIPP-ből (£)", 1000, 25000, 3230)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 10000, 3500)

# --- ADÓKALKULÁTOR (Állami nyugdíjjal korrigálva) ---
def calculate_net(sipp_gross_m, state_p_m):
    # Az összes adóköteles jövedelem (SIPP + Állami nyugdíj)
    total_gross_a = (sipp_gross_m + state_p_m) * 12
    
    pa = 12570
    if total_gross_a > 100000:
        pa = max(0, pa - (total_gross_a - 100000) / 2)
    
    taxable = max(0, total_gross_a - pa)
    tax = 0
    if taxable > 0:
        band20 = min(taxable, 37700)
        tax += band20 * 0.20
        if taxable > 37700:
            band40 = min(taxable - 37700, 125140 - 37700)
            tax += band40 * 0.40
        if taxable > 125140:
            tax += (taxable - 125140) * 0.45
            
    # A nettó jövedelem: (Összes bruttó - összes adó)
    total_net_a = total_gross_a - tax
    # Minket a "zsebbe kerülő" havi nettó érdekel
    return total_net_a / 12

# --- SZIMULÁCIÓ ---
# (A korábbi piaci paraméterekkel...)
market_return = st.sidebar.slider("Vanguard hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Infláció (%)", 0.0, 8.0, 2.5)
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, holdco_vals = [], [], []
current_sipp, current_holdco = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # Befizetés
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_cont
        
    # Állami nyugdíj összege az adott hónapban
    current_state_p_m = (state_pension_annual / 12) if age >= state_pension_age else 0
    
    # SIPP kifizetés
    if age >= sipp_start_age:
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        if current_sipp > 0:
            actual_sipp_gross = min(current_sipp, gross_monthly_withdrawal)
            # Nettó számítás (SIPP + Állami)
            total_net_income = calculate_net(actual_sipp_gross, current_state_p_m)
            
            # Adó kiszámítása (összes jövedelem alapján)
            total_gross_m = actual_sipp_gross + current_state_p_m
            total_tax_paid += (total_gross_m - total_net_income)
            
            current_sipp -= actual_sipp_gross
            
            # Megélhetés levonása a teljes nettóból, maradék a HoldCo-ba
            if total_net_income >= monthly_living_cost:
                current_holdco += (total_net_income - monthly_living_cost)
            else:
                current_holdco = max(0, current_holdco - (monthly_living_cost - total_net_income))
            
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0
        else:
            # SIPP elfogyott, de az állami nyugdíj megmaradt!
            total_net_income = calculate_net(0, current_state_p_m)
            if total_net_income >= monthly_living_cost:
                current_holdco += (total_net_income - monthly_living_cost)
            else:
                current_holdco = max(0, current_holdco - (monthly_living_cost - total_net_income))

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS ---
st.subheader(f"📊 Szimuláció eredménye (Állami nyugdíj {state_pension_age} éves kortól)")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=600, hovermode="x unified")
fig.add_vline(x=state_pension_age, line_dash="dot", line_color="orange", annotation_text="Állami Nyugdíj START")
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
current_net = calculate_net(gross_monthly_withdrawal if current_age >= sipp_start_age else 0, (state_pension_annual/12) if current_age >= state_pension_age else 0)
c1.metric("Aktuális nettó jövedelem", f"£{current_net:,.0f}")
c2.metric("SIPP ürítési kor", f"{sipp_emptied_age:.1f if sipp_emptied_age else 'Soha'}")
c3.metric("Összes adó a HMRC-nek", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.warning(f"""
⚠️ **Figyelem az adócsapdára:** 
Amint eléred a(z) {state_pension_age} éves kort, az állami nyugdíjad (£{state_pension_annual/12:,.0f}/hó) elhasználja az adómentes kereted 91%-át. 
Ha továbbra is havi £{gross_monthly_withdrawal:,.0f}-ot veszel ki a SIPP-ből, az **összesített bruttó jövedelmed £{(gross_monthly_withdrawal + state_pension_annual/12):,.0f}** lesz. 
Ezzel már közelebb kerülsz a 40%-os sávhoz (£4,189/hó).
""")
