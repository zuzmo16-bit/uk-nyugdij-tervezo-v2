import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK Employee & Director Pension Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 UK Nyugdíj & Vagyon Stratégia")

# 🎛️ FELHASZNÁLÓI PROFIL
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó")
)

st.sidebar.markdown("---")
st.sidebar.header("📌 Életkor és Időtáv")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 46)
target_age = 100 
max_work = 75 - current_age
working_years = st.sidebar.slider("Hány évig dolgozol még (befizetési fázis)?", 0, max_work, 20)

# BEFIZETÉSI LOGIKA
monthly_contribution_total = 0
total_annual_gross = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alapbér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=15.0)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=37)
    
    st.sidebar.header("🗓️ Hétvégi pótlék")
    # Itt az egyben megadható pótlék összeg
    weekend_bonus_per_event = st.sidebar.number_input("Hétvégi pótlék összege (£ / hétvége)", value=180.0, help="Az egy hétvége alatt keresett összes extra bruttó összeg.")
    weekends_per_year = st.sidebar.slider("Hány hétvégét dolgozol egy évben?", 0, 52, 26)
    
    st.sidebar.header("🏹 Nyugdíj hozzájárulás")
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 5)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 3)
    
    # Éves bruttó kiszámítása
    base_annual = hourly_rate * hours_per_week * 52
    weekend_annual = weekend_bonus_per_event * weekends_per_year
    total_annual_gross = base_annual + weekend_annual
    
    monthly_gross_salary = total_annual_gross / 12
    monthly_contribution_total = monthly_gross_salary * ((ee_pct + er_pct) / 100)
    
    st.sidebar.info(f"Havi átlagos bruttó: £{monthly_gross_salary:,.0f}")

else:
    st.sidebar.header("🏢 Igazgatói adatok")
    monthly_director_pension = st.sidebar.number_input("Havi CÉGES nyugdíjbefizetés (£)", value=5000)
    monthly_contribution_total = monthly_director_pension

# 🔓 KIFIZETÉSI STRATÉGIA
st.sidebar.markdown("---")
st.sidebar.header("🔓 Stratégia Időzítése")
sipp_start_age = st.sidebar.slider("Hány évesen induljon a kifizetés?", 57, 75, 67)

st.sidebar.header("💶 Kifizetési Beállítások")
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó kivét a SIPP-ből (£)", 1000, 25000, 4189)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 10000, 3000)

# 📈 PIACI BEÁLLÍTÁSOK
st.sidebar.markdown("---")
st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Várható éves hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
def calculate_net(gross_m):
    gross_a = gross_m * 12
    pa = 12570
    if gross_a > 100000:
        pa = max(0, pa - (gross_a - 100000) / 2)
    taxable = max(0, gross_a - pa)
    tax = 0
    if taxable > 0:
        band20 = min(taxable, 37700)
        tax += band20 * 0.20
        if taxable > 37700:
            band40 = min(taxable - 37700, 125140 - 37700)
            tax += band40 * 0.40
        if taxable > 125140:
            tax += (taxable - 125140) * 0.45
    return (gross_a - tax) / 12

# --- SZIMULÁCIÓ ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, private_vals = [], [], []
current_sipp, current_private = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((target_age - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_private *= (1 + m_rate)
    
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    if age >= sipp_start_age:
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_private += lump_sum
            pcls_taken = True
        
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly_withdrawal)
            net_income = calculate_net(actual_gross)
            total_tax_paid += (actual_gross - net_income)
            current_sipp -= actual_gross
            
            if net_income >= monthly_living_cost:
                current_private += (net_income - monthly_living_cost)
            else:
                current_private = max(0, current_private - (monthly_living_cost - net_income))
            
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0
        else:
            current_private = max(0, current_private - monthly_living_cost)

    sipp_vals.append(current_sipp)
    private_vals.append(current_private)

# --- VIZUALIZÁCIÓ ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 {user_mode} | SIPP ürítés: {emptied_text}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=private_vals, name='Privát/HoldCo vagyon', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=600, hovermode="x unified")
fig.add_vline(x=sipp_start_age, line_dash="dot", line_color="green", annotation_text="Kezdés")
fig.add_vline(x=75, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)

# KPI-K
c1, c2, c3, c4 = st.columns(4)
c1.metric("SIPP csúcsérték", f"£{max(sipp_vals):,.0f}")
c2.metric("Éves bruttó bér (aktív)", f"£{total_annual_gross:,.0f}")
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{private_vals[-1]:,.0f}")
