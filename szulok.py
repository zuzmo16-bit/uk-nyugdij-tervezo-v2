import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK Employee & Director Pension Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 UK Nyugdíj & Vagyon Stratégia: Alkalmazott vs. Igazgató")
st.write("Ez a modell kiszámolja a nyugdíjfelhalmozást alkalmazotti (órabéres) és igazgatói státuszban, majd szimulálja a vagyon kimentését.")

# 🎛️ FELHASZNÁLÓI PROFIL KIVÁLASZTÁSA
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

# BEFIZETÉSI LOGIKA MÓDOK SZERINT
monthly_contribution_total = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti adatok")
    hourly_rate = st.sidebar.number_input("Órabér (£)", value=15.0)
    hours_per_week = st.sidebar.number_input("Heti óraszám", value=40)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 5)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 3)
    
    # Bruttó bér számítás (52 hétre)
    annual_gross = hourly_rate * hours_per_week * 52
    monthly_gross_salary = annual_gross / 12
    # Összes havi befizetés a nyugdíjba (Munkavállaló + Munkáltató)
    monthly_contribution_total = monthly_gross_salary * ((ee_pct + er_pct) / 100)
    
    st.sidebar.info(f"Éves bruttó bér: £{annual_gross:,.0f}\nHavi nyugdíj befizetés: £{monthly_contribution_total:,.0f}")

else:
    st.sidebar.header("🏢 Igazgatói adatok")
    monthly_director_pension = st.sidebar.number_input("Havi CÉGES nyugdíjbefizetés (£)", value=5000)
    monthly_contribution_total = monthly_director_pension

# 🔓 KIFIZETÉSI STRATÉGIA (MELTDOWN)
st.sidebar.markdown("---")
st.sidebar.header("🔓 Stratégia Időzítése")
sipp_start_age = st.sidebar.slider("Hány évesen induljon a kifizetés?", 57, 75, 67)

st.sidebar.header("💶 Kifizetési Beállítások")
gross_monthly_withdrawal = st.sidebar.slider(
    "Havi bruttó kivét a SIPP-ből (£)", 
    min_value=1000, max_value=25000, value=4189,
    help="Havi £4,189-ig maradsz a 20%-os sávban."
)

monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 10000, 3000)

# 📈 PIACI BEÁLLÍTÁSOK
st.sidebar.markdown("---")
st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Várható éves hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR FÜGGVÉNY ---
def calculate_net(gross_m):
    gross_a = gross_m * 12
    pa = 12570
    if gross_a > 100000:
        pa = max(0, pa - (gross_a - 100000) / 2)
    
    taxable = max(0, gross_a - pa)
    tax = 0
    if taxable > 0:
        # 20% sáv
        band20 = min(taxable, 37700)
        tax += band20 * 0.20
        # 40% sáv
        if taxable > 37700:
            band40 = min(taxable - 37700, 125140 - 37700)
            tax += band40 * 0.40
        # 45% sáv
        if taxable > 125140:
            band45 = taxable - 125140
            tax += band45 * 0.45
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
    
    # 1. Befizetési fázis
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    # 2. Kifizetési fázis
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
            
            # Megélhetés levonása, maradék befektetése a privát alapba
            if net_income >= monthly_living_cost:
                current_private += (net_income - monthly_living_cost)
            else:
                current_private = max(0, current_private - (monthly_living_cost - net_income))
            
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0
        else:
            # SIPP elfogyott, privát tőkéből élünk tovább
            current_private = max(0, current_private - monthly_living_cost)

    sipp_vals.append(current_sipp)
    private_vals.append(current_private)

# --- VIZUALIZÁCIÓ ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 {user_mode} stratégia | SIPP ürítés: {emptied_text}")

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
c2.metric("Nettó havi jövedelem (kivét alatt)", f"£{calculate_net(gross_monthly_withdrawal):,.0f}")
c3.metric("Összes befizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{private_vals[-1]:,.0f}")

st.info(f"""
**Hogyan működik az alkalmazotti modell?**
- A program kiszámolja az éves bruttó béredet: **£{hourly_rate*hours_per_week*52:,.0f}**.
- A nyugdíjba havonta összesen **{ee_pct + er_pct}%** vándorol be, ami **£{monthly_contribution_total:,.0f}**.
- 57 éves korod után (vagy amikor beállítottad) elindul a 25% kimentése és a havi kifizetés, pont úgy, mint az igazgatói modellnél.
""")
