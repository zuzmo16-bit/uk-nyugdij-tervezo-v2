import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="UK Universal Pension & Wealth Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 Komplett UK Nyugdíj, Vagyon & Adóoptimalizáló")
st.write("Ez a szimulátor a legteljesebb verzió: kezeli a vállalkozói és alkalmazotti létet, a 25%-os házvásárlást és az állami nyugdíjat is.")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó")
)

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
max_work = 75 - current_age
working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, max_work, 36)

# --- SIDEBAR: SIPP MÉRFÖLDKÖVEK ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Mérföldkövek")
pcls_age = st.sidebar.slider("Hány évesen veszed ki a 25%-ot (pl. Házvétel)?", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Hány évesen induljon a havi járadék (Meltdown)?", 57, 75, 70)

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
    
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    
    # Éves bruttó és havi befizetés
    base_a = hourly_rate * hours_per_week * 52
    weekend_a = weekend_bonus * weekends_per_year
    active_annual_gross = base_a + weekend_a
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
    st.sidebar.info(f"Éves bruttó: £{active_annual_gross:,.0f}")

else:
    st.sidebar.header("🏢 Igazgatói befizetés")
    monthly_director_pension = st.sidebar.number_input("Havi céges nyugdíjbefizetés (£)", value=5000)
    monthly_contribution_total = monthly_director_pension
    active_annual_gross = 12570 # Minimálbérként kezelve adózáshoz

# --- SIDEBAR: ÁLLAMI NYUGDÍJ ---
st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj (State Pension)")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 70)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

# --- SIDEBAR: KIFIZETÉS ÉS PIAC ---
st.sidebar.markdown("---")
st.sidebar.header("💶 Kifizetés & Életmód")
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó kivét a SIPP-ből (£)", 1000, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500)

st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR (BRIT SZABÁLYOK) ---
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
    current_house *= (1 + (inflation / 100)) ** (1/12) # Ház inflációkövető

    # 1. BEFIZETÉS: Amíg tart a munka (75 éves korig)
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    # 2. ÁLLAMI NYUGDÍJ
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 3. 25% TAX-FREE KIVÉTEL (Házvétel)
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25
        current_sipp -= lump
        current_house = lump 
        pcls_taken = True
        
    # 4. HAVI JÁRADÉK (Drawdown)
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_sipp_g = min(current_sipp, gross_monthly_withdrawal)
            net_income = calculate_net(actual_sipp_g, st_p_m)
            total_tax_paid += ((actual_sipp_g + st_p_m) - net_income)
            current_sipp -= actual_sipp_g
            
            # Megélhetés kezelése
            if net_income >= monthly_living_cost:
                current_holdco += (net_income - monthly_living_cost)
            else:
                current_holdco = max(0, current_holdco - (monthly_living_cost - net_income))
            
            if current_sipp <= 100:
                sipp_emptied_age = age
                current_sipp = 0
        else:
            # SIPP elfogyott, Állami nyugdíj + HoldCo marad
            net_income = calculate_net(0, st_p_m)
            current_holdco = max(0, current_holdco - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS ---
if sipp_emptied_age:
    emptied_str = f"{sipp_emptied_age:.1f} éves"
else:
    emptied_str = "Soha"

st.subheader(f"📊 {user_mode} | Házvétel: {pcls_age} év | Nyugdíj: {drawdown_start_age} év | SIPP ürítés: {emptied_str}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg (75%)', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan értéke (25%)', fill='tonexty', line=dict(color='orange')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo / Maradék vagyon', line=dict(color='gold', width=4)))

fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=650, hovermode="x unified", template="plotly_white")
fig.add_vline(x=pcls_age, line_dash="dot", line_color="orange", annotation_text="Házvétel")
fig.add_vline(x=state_p_age, line_dash="dash", line_color="gray", annotation_text="Állami Nyugdíj")
fig.add_vline(x=drawdown_start_age, line_dash="dash", line_color="green", annotation_text="Nyugdíj kezdete")
st.plotly_chart(fig, use_container_width=True)

# --- KPI-K ---
c1, c2, c3, c4 = st.columns(4)
# Tervezett havi nettó számítása
proj_net = calculate_net(gross_monthly_withdrawal, (state_p_annual/12))
c1.metric("Várható havi nettó (nyugdíj alatt)", f"£{proj_net:,.0f}")
c2.metric("SIPP ürítési kor", emptied_str)
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Örökség 100 évesen", f"£{(holdco_vals[-1] + house_wealth[-1]):,.0f}")

st.info(f"""
**Hogy működik ez a stratégia?**
- **Aktív szakasz:** Havi **£{monthly_contribution_total:,.0f}** befizetés megy a SIPP-be (céges/egyéni+munkáltatói).
- **Házvétel ({pcls_age} év):** A SIPP aktuális értékének 25%-át (£{house_wealth[int((pcls_age-current_age)*12)]:,.0f}) adómentesen kiveszed. A SIPP 75%-a bent marad és **tovább kamatozik**.
- **Munka folytatása:** {pcls_age} és {drawdown_start_age} év között **továbbra is fizetsz be**, így a SIPP egyenleged újra növekedésnek indul.
- **Nyugdíj ({drawdown_start_age} év):** Elindul a havi £{gross_monthly_withdrawal:,.0f} bruttó kivét + az állami nyugdíj.
""")
