import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Planner", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő")
st.write("SIPP Meltdown, Trösztépítés és Nemzetközi Adóoptimalizálás (UK-HU transzfer).")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás / Örökség Optimalizáló")
)

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")

# Induló adatok kezelése profilok szerint
if user_mode == "Nemzetközi Kivonulás / Örökség Optimalizáló":
    current_age = st.sidebar.slider("Hány éves kortól induljon a szimuláció?", 18, 90, 63)
    death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", current_age + 1, 100, 85)
    
    st.sidebar.markdown("---")
    st.sidebar.header("💰 Meglévő Vagyon (Induló értékek)")
    start_sipp = st.sidebar.number_input("Meglévő Brit SIPP egyenleg (£)", value=1000000)
    start_house = st.sidebar.number_input("Meglévő Ingatlan értéke (£)", value=500000)
    start_trust = st.sidebar.number_input("Meglévő Brit Holding/Tröszt vagyon (£)", value=250000)
    working_years = 0 # Ebben a módban feltételezzük a kifizetési fázist
else:
    current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
    working_years = st.sidebar.slider("Hány évig fizetsz még be (befizetés)?", 0, 75-current_age, 36)
    death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", 75, 100, 85)
    start_sipp = 15000
    start_house = 0
    start_trust = 0

# --- MAGYARORSZÁGI STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🇭🇺 Nemzetközi Stratégia")
enable_hu_move = st.sidebar.checkbox("Hazaköltözés Magyarországra?", value=(user_mode == "Nemzetközi Kivonulás / Örökség Optimalizáló"))
if enable_hu_move:
    hu_move_age = st.sidebar.slider("Hazaköltözés életkora", 18, 90, current_age if user_mode == "Nemzetközi Kivonulás / Örökség Optimalizáló" else 63)
else:
    hu_move_age = 999

# --- BEFIZETÉSEK ---
monthly_contribution_total = 0
if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti adatok")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours = st.sidebar.number_input("Heti óra", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£)", value=53.70)
    ee_pct = st.sidebar.slider("Saját 4% (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói 4% (%)", 0, 20, 4)
    active_annual_gross = (hourly_rate * hours * 52) + (weekend_bonus * 26)
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    monthly_contribution_total = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

# --- SIPP STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP & Kifizetés Stratégia")
if user_mode != "Nemzetközi Kivonulás / Örökség Optimalizáló":
    pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
    drawdown_start_age = st.sidebar.slider("SIPP Meltdown kezdete", 57, 75, 57)
else:
    pcls_age = current_age # Ebben a módban feltételezzük, hogy már elérhető vagy kivettük
    drawdown_start_age = current_age

gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó SIPP kivét (Meltdown) (£)", 0, 25000, 8333 if user_mode != "Nemzetközi Kivonulás / Örökség Optimalizáló" else 10000)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500)

st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

st.sidebar.header("📈 Piaci Paraméterek")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
def calculate_net(sipp_m, state_m):
    total_gross_a = (sipp_m + state_m) * 12
    pa = 12570
    if total_gross_a > 100000: pa = max(0, pa - (total_gross_a - 100000) / 2)
    taxable = max(0, total_gross_a - pa)
    tax = 0
    if taxable > 0:
        b20 = min(taxable, 37700); tax += b20 * 0.20
        if taxable > 37700:
            b40 = min(taxable - 37700, 125140 - 37700); tax += b40 * 0.40
        if taxable > 125140: tax += (taxable - 125140) * 0.45
    return (total_gross_a - tax) / 12

# --- SZIMULÁCIÓ ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, house_wealth, trust_vals = [], [], [], []
current_sipp, current_trust, current_house = start_sipp, start_trust, start_house
pcls_taken, total_tax_paid = (user_mode == "Nemzetközi Kivonulás / Örökség Optimalizáló"), 0

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetés (Csak ha nem az Optimizer módban vagyunk)
    if user_mode != "Nemzetközi Kivonulás / Örökség Optimalizáló":
        if m <= (working_years * 12) and age <= 75:
            current_sipp += monthly_contribution_total
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 2. 25% Kivét (Optimizer módban ez átugorható, ha már be van állítva indulónak)
    if user_mode != "Nemzetközi Kivonulás / Örökség Optimalizáló":
        if age >= pcls_age and not pcls_taken:
            lump = current_sipp * 0.25; current_sipp -= lump; current_house = lump; pcls_taken = True
        
    # 3. Kifizetés & Transzfer
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_sipp_g = min(current_sipp, gross_monthly_withdrawal)
            net_income = calculate_net(actual_sipp_g, st_p_m)
            total_tax_paid += ((actual_sipp_g + st_p_m) - net_income)
            current_sipp -= actual_sipp_g
            if net_income >= monthly_living_cost: current_trust += (net_income - monthly_living_cost)
            else: current_trust = max(0, current_trust - (monthly_living_cost - net_income))
        else:
            net_income = calculate_net(0, st_p_m)
            current_trust = max(0, current_trust - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Bentmaradó)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan (Perennis bázis)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='Perennis Vagyon (Holding)', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))
fig.update_layout(template="plotly_white", height=600, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- KALKULÁCIÓK ---
total_gross_at_death = sipp_vals[-1] + house_wealth[-1] + trust_vals[-1]

if enable_hu_move:
    years_since_move = death_age - hu_move_age
    iht_tax = 0 if years_since_move >= 10 else max(0, (total_gross_at_death - 500000) * 0.40)
else:
    iht_tax = max(0, (total_gross_at_death - 500000) * 0.40)

idx_retire = int((drawdown_start_age-current_age)*12)
check_val = max(trust_vals[-1], trust_vals[idx_retire] if idx_retire < len(trust_vals) else 0)
withdrawal_rate_trust = (monthly_living_cost * 12 / check_val) * 100 if check_val > 0 else 0

st.markdown("---")
st.header(f"📜 Perennis Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Várható Bruttó Vagyon", f"£{total_gross_at_death:,.0f}")
c2.metric("Tröszt kifizetési ráta", f"{withdrawal_rate_trust:.1f}%")
c3.metric("IHT Adóteher", f"£{iht_tax:,.0f}")
c4.metric("Nettó örökség", f"£{(total_gross_at_death - iht_tax):,.0f}")

if withdrawal_rate_trust > 4.0:
    st.warning(f"⚠️ **ALKOTMÁNYELLENES:** A megélhetési rátád ({withdrawal_rate_trust:.1f}%) meghaladja a 4%-os korlátot!")
else:
    st.success(f"✅ **ALKOTMÁNYOS:** A tőkemegőrzés biztosított.")
