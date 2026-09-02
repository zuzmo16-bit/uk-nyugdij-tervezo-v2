import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="UK Wealth & Inheritance Planner", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 UK Nyugdíj, Vagyon & Öröklési Stratégia")

# --- SIDEBAR ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio("Státusz:", ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó"))

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
working_years = st.sidebar.slider("Hány évig fizetsz be?", 0, 75-current_age, 36)
# ÚJ: Halálozási életkor
death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", 75, 100, 85)

st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Mérföldkövek")
pcls_age = st.sidebar.slider("Házvétel (25%) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Nyugdíj (Meltdown) kezdete", 57, 75, 70)

# --- BEFIZETÉSEK & KIFIZETÉSEK (Rövidítve a korábbiak alapján) ---
if user_mode == "Órabéres alkalmazott":
    hourly_rate = st.sidebar.number_input("Órabér (£)", value=19.14)
    hours = st.sidebar.number_input("Heti óra", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£)", value=53.70)
    ee_er = st.sidebar.slider("Összes nyugdíj hozzájárulás (%)", 0, 40, 8)
    monthly_contribution_total = ((hourly_rate * hours * 52) + (weekend_bonus * 26)) / 12 * (ee_er / 100)
else:
    monthly_contribution_total = st.sidebar.number_input("Havi céges nyugdíj (£)", value=5000)

state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó SIPP kivét (£)", 1000, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetés (£)", 500, 15000, 3500)

market_return = st.sidebar.slider("Vanguard hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Infláció (%)", 0.0, 8.0, 2.5)

# --- ADÓKALKULÁTOR ---
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
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, house_wealth, holdco_vals = [], [], [], []
current_sipp, current_holdco, current_house = 15000, 0, 0
pcls_taken = False

for m in range((death_age - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12)
    if m <= (working_years * 12) and age <= 75: current_sipp += monthly_contribution_total
    st_p_m = (state_p_annual / 12) if age >= 71 else 0 # 71 éves korhatár
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25; current_sipp -= lump; current_house = lump; pcls_taken = True
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_g = min(current_sipp, gross_monthly_withdrawal)
            net = calculate_net(actual_g, st_p_m)
            current_sipp -= actual_g
            if net >= monthly_living_cost: current_holdco += (net - monthly_living_cost)
            else: current_holdco = max(0, current_holdco - (monthly_living_cost - net))
        else:
            net = calculate_net(0, st_p_m)
            current_holdco = max(0, current_holdco - (monthly_living_cost - net))
    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    holdco_vals.append(current_holdco)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (IHT Mentes)', mode='lines', line=dict(color='#87CEEB', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.4)'] ])))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan (IHT Köteles*)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)'] ])))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (IHT Köteles)', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)'] ])))
fig.update_layout(template="plotly_white", height=600, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- ÖRÖKLÉSI KALKULÁTOR ---
st.markdown("---")
st.header(f"⚰️ Örökségi mérleg {death_age} évesen")

final_sipp = sipp_vals[-1]
final_house = house_wealth[-1]
final_holdco = holdco_vals[-1]
taxable_estate = final_house + final_holdco
# IHT Matek: £500k keret (Nil Rate + Residence Nil Rate)
threshold = 500000
iht_tax = max(0, (taxable_estate - threshold) * 0.40)
net_inheritance = final_sipp + (taxable_estate - iht_tax)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Teljes Bruttó Vagyon", f"£{final_sipp + taxable_estate:,.0f}")
c2.metric("SIPP (Adómentes örökség)", f"£{final_sipp:,.0f}")
c3.error(f"Öröklési adó (HMRC): £{iht_tax:,.0f}")
c4.success(f"Nettó örökség a gyerekeknek: £{net_inheritance:,.0f}")

st.info(f"""
**Öröklési elemzés:**
- A **SIPP egyenleged (£{final_sipp:,.0f})** kívül esik a hagyatékon, így a gyerekek ezt 100%-ban megkapják adómentesen (ha 75 év alatt halsz meg) vagy jövedelemadóval (75 felett).
- A **Ház és a HoldCo (£{taxable_estate:,.0f})** beleszámít az adóköteles vagyonba. 
- Az első **£500,000** adómentes, a felette lévő részre a HMRC **40% adót** vetett ki, ami **£{iht_tax:,.0f}**.
- Ha az adó túl magas, érdemes lehet több pénzt a SIPP-ben hagyni a HoldCo helyett!
""")
