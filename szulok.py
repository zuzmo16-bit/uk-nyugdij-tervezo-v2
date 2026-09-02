import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- KONFIGURÁCIÓ ---
st.set_page_config(page_title="UK Master Wealth & Inheritance Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 UK Nyugdíj, Vagyon & Öröklési Stratégia (Post-2027 Rules)")
st.write("Ez a szimulátor már tartalmazza a 2024-es költségvetés szerinti öröklési adó módosításokat.")

# --- SIDEBAR: PROFIL ÉS IDŐTÁV ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio("Státusz:", ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó"))

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, 75-current_age, 36)
death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", 75, 100, 85)

# --- SIDEBAR: BEFIZETÉSEK ---
monthly_contribution_total = 0
active_annual_gross = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    
    st.sidebar.header("🗓️ Hétvégi pótlék")
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék összege (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    
    st.sidebar.header("🏹 Nyugdíj hozzájárulás")
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    
    base_a = hourly_rate * hours_per_week * 52
    weekend_a = weekend_bonus * weekends_per_year
    active_annual_gross = base_a + weekend_a
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
else:
    st.sidebar.header("🏢 Igazgatói befizetés")
    monthly_director_pension = st.sidebar.number_input("Havi céges nyugdíjbefizetés (£)", value=5000)
    monthly_contribution_total = monthly_director_pension
    active_annual_gross = 12570

# --- SIDEBAR: ÁLLAMI NYUGDÍJ ---
st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

# --- SIDEBAR: SIPP MÉRFÖLDKÖVEK ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés (Meltdown) kezdete", 57, 75, 70)
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó kivét a SIPP-ből (£)", 1000, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500)

st.sidebar.header("📈 Piac")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Vanguard hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
def calculate_net(sipp_m, state_m):
    total_gross_a = (sipp_m + state_m) * 12
    pa = 12570
    if total_gross_a > 100000:
        pa = max(0, pa - (total_gross_a - 100000) / 2)
    taxable = max(0, total_gross_a - pa)
    tax = 0
    if taxable > 0:
        b20 = min(taxable, 37700); tax += b20 * 0.20
        if taxable > 37700:
            b40 = min(taxable - 37700, 125140 - 37700); tax += b40 * 0.40
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

for m in range((death_age - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetés: Akkor is megy, ha már kivetted a 25%-ot, amíg dolgozol!
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 2. 25% Házvétel
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25
        current_sipp -= lump
        current_house = lump 
        pcls_taken = True
        
    # 3. Havi Meltdown
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_sipp_g = min(current_sipp, gross_monthly_withdrawal)
            net_income = calculate_net(actual_sipp_g, st_p_m)
            total_tax_paid += ((actual_sipp_g + st_p_m) - net_income)
            current_sipp -= actual_sipp_g
            if net_income >= monthly_living_cost:
                current_holdco += (net_income - monthly_living_cost)
            else:
                current_holdco = max(0, current_holdco - (monthly_living_cost - net_income))
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0
        else:
            net_income = calculate_net(0, st_p_m)
            current_holdco = max(0, current_holdco - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    holdco_vals.append(current_holdco)

# --- GRAFIKON (FADING STYLE) ---
fig = go.Figure()
# SIPP - SkyBlue
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (75%)', mode='lines', line=dict(color='#87CEEB', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.4)']])))
# INGATLAN - RoyalBlue
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan (25%)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
# HOLDCO - Gold
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo Vagyon', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)']])))

fig.update_layout(template="plotly_white", height=600, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- ÖRÖKLÉSI ADÓ (NEW 2027 RULES) ---
st.markdown("---")
st.header(f"⚰️ Öröklési kalkuláció {death_age} éves korban (Post-2027)")

final_sipp = sipp_vals[-1]
final_house = house_wealth[-1]
final_holdco = holdco_vals[-1]
# ÚJ SZABÁLY: A SIPP is a hagyaték része!
total_estate = final_sipp + final_house + final_holdco
threshold = 500000 # NRB + RNRB becslés
iht_tax = max(0, (total_estate - threshold) * 0.40)
net_inheritance = total_estate - iht_tax

# KPI Kijelzők
if sipp_emptied_age: emptied_str = f"{sipp_emptied_age:.1f} éves"
else: emptied_str = "Soha"

c1, c2, c3, c4 = st.columns(4)
c1.metric("Össz vagyon (Bruttó)", f"£{total_estate:,.0f}")
c2.metric("SIPP ürítési kor", emptied_str)
c3.error(f"Öröklési adó (HMRC): £{iht_tax:,.0f}")
c4.success(f"Nettó örökség: £{net_inheritance:,.0f}")

st.info(f"""
**Változások a 2027-es szabályok miatt:**
- Korábban a **£{final_sipp:,.0f}** SIPP vagyon adómentesen öröklődött volna.
- Az új szabályok szerint ez is beleszámít a hagyatékodba, így a HMRC **40% adót** vet ki rá a keret felett.
- Az összes kifizetett jövedelemadó az életed során: **£{total_tax_paid:,.0f}**.
""")
