import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="UK Wealth & Pension Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 Komplett UK Nyugdíj & Vagyon Stratégia")
st.write("Ez a szimulátor ötvözi az alkalmazotti és cégvezetői létet az állami nyugdíjjal és az adóoptimalizált kifizetéssel.")

# --- SIDEBAR / MENÜ ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó")
)

st.sidebar.markdown("---")
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 46)
max_work = 75 - current_age
working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, max_work, 20)

# --- BEFIZETÉSI LOGIKA ---
monthly_contribution_total = 0
active_annual_gross = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=15.0)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=37)
    
    st.sidebar.header("🗓️ Hétvégi pótlék")
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék összege (£ / alkalom)", value=180.0)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 5)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 3)
    
    # Bruttó számítás
    base_a = hourly_rate * hours_per_week * 52
    weekend_a = weekend_bonus * weekends_per_year
    active_annual_gross = base_a + weekend_a
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
    st.sidebar.info(f"Éves bruttó: £{active_annual_gross:,.0f}")

else:
    st.sidebar.header("🏢 Igazgatói befizetés")
    monthly_director_pension = st.sidebar.number_input("Havi céges nyugdíjbefizetés (£)", value=5000)
    monthly_contribution_total = monthly_director_pension
    active_annual_gross = 12570 # Feltételezett minimálbér igazgatóknak

st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj (State Pension)")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

st.sidebar.markdown("---")
st.sidebar.header("🔓 SIPP Stratégia")
sipp_start_age = st.sidebar.slider("SIPP kifizetés kezdete", 57, 75, 67)
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó kivét a SIPP-ből (£)", 1000, 25000, 3500)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 10000, 3000)

st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
def calculate_net(sipp_m, state_m):
    total_gross_a = (sipp_m + state_m) * 12
    pa = 12570
    # PA Tapering £100k felett
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

ages, sipp_vals, holdco_vals = [], [], []
current_sipp, current_holdco = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 1. Befizetés
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    # 2. Állami nyugdíj
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 3. SIPP Kifizetés
    if age >= sipp_start_age:
        if not pcls_taken:
            lump = current_sipp * 0.25
            current_sipp -= lump
            current_holdco += lump
            pcls_taken = True
        
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
            # SIPP elfogyott, csak állami nyugdíj + HoldCo marad
            net_income = calculate_net(0, st_p_m)
            current_holdco = max(0, current_holdco - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS JAVÍTÁSA ---
# A hiba elkerülése: előre formázzuk a szöveget
if sipp_emptied_age:
    emptied_str = f"{sipp_emptied_age:.1f} éves"
else:
    emptied_str = "Soha"

st.subheader(f"📊 {user_mode} stratégia | SIPP ürítés: {emptied_str}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=600, hovermode="x unified")
fig.add_vline(x=state_p_age, line_dash="dot", line_color="orange", annotation_text="Állami Nyugdíj")
st.plotly_chart(fig, use_container_width=True)

# KPI-K
c1, c2, c3, c4 = st.columns(4)
# Aktuális nettó számítása a kijelzőhöz
cur_st_p = (state_p_annual/12) if current_age >= state_p_age else 0
cur_sipp_g = gross_monthly_withdrawal if current_age >= sipp_start_age else 0
cur_net = calculate_net(cur_sipp_g, cur_st_p)

c1.metric("Várható havi nettó", f"£{cur_net:,.0f}")
c2.metric("SIPP ürítési kor", emptied_str)
c3.metric("Összes adó a HMRC-nek", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.info(f"""
**Összegzés:**
- Jelenleg **£{active_annual_gross:,.0f}** éves bruttó bérrel számolunk az aktív években.
- A SIPP-be havi **£{monthly_contribution_total:,.0f}** érkezik (céges + saját).
- Az állami nyugdíj {state_p_age} évesen belépve havi **£{state_p_annual/12:,.0f}** adóköteles jövedelmet ad hozzá a keretedhez.
""")
