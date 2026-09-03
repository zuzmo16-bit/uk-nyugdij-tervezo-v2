import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Wealth & Inheritance Planner", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Dinasztia Vagyontervezője")
st.write("A 'Birodalmi Útmutató' alapján kalibrált szimulátor (2027-es IHT szabályokkal).")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio("Státusz:", ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó"))

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, 75-current_age, 36)
death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", 75, 100, 85)

# --- SIDEBAR: BEFIZETÉSEK ---
monthly_contribution_total = 0
if user_mode == "Órabéres alkalmazott":
    hourly_rate = st.sidebar.number_input("Órabér (£)", value=19.14)
    hours = st.sidebar.number_input("Heti óra", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£)", value=53.70)
    ee_er = st.sidebar.slider("Összes nyugdíj hozzájárulás (%)", 0, 40, 8)
    monthly_contribution_total = ((hourly_rate * hours * 52) + (weekend_bonus * 26)) / 12 * (ee_er / 100)
else:
    monthly_contribution_total = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Mérföldkövek")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Kifizetés (Meltdown) kezdete", 57, 75, 70)
gross_monthly_withdrawal = st.sidebar.slider("Havi bruttó SIPP kivét (£)", 1000, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500)

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

    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    # FIX: Állami nyugdíj szinkronizálva a csúszkával
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25
        current_sipp -= lump
        current_house = lump 
        pcls_taken = True
        
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

# --- GRAFIKON (MASTER DESIGN) ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Post-2027 IHT Köteles)', mode='lines', line=dict(color='#87CEEB', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan (Perennis bázis)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo / Tröszt Vagyon', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)']])))

fig.update_layout(template="plotly_white", height=600, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- ÖRÖKLÉSI KALKULÁCIÓ ---
st.markdown("---")
final_sipp = sipp_vals[-1]
final_house = house_wealth[-1]
final_holdco = holdco_vals[-1]
total_estate = final_sipp + final_house + final_holdco
threshold = 500000
iht_tax = max(0, (total_estate - threshold) * 0.40)
net_inheritance = total_estate - iht_tax

# Alkotmányos 4% szabály ellenőrzés
total_capital_at_retirement = sipp_vals[int((drawdown_start_age-current_age)*12)] + holdco_vals[int((drawdown_start_age-current_age)*12)]
annual_drawdown = gross_monthly_withdrawal * 12
withdrawal_rate = (annual_drawdown / total_capital_at_retirement) * 100 if total_capital_at_retirement > 0 else 0

st.header(f"⚰️ Örökségi mérleg {death_age} évesen")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Össz vagyon (Bruttó)", f"£{total_estate:,.0f}")
c2.metric("Várható havi nettó", f"£{calculate_net(gross_monthly_withdrawal, state_p_annual/12):,.0f}")
c3.error(f"HMRC Jussa (IHT): £{iht_tax:,.0f}")
c4.success(f"Nettó örökség: £{net_inheritance:,.0f}")

# --- SAFETY CHECK: ALKOTMÁNYOSSÁGI VIZSGÁLAT ---
if withdrawal_rate > 4.0:
    st.warning(f"⚠️ **Alkotmányos figyelmeztetés:** A havi kivéted ({withdrawal_rate:.1f}%) meghaladja a tervedben rögzített 4%-os korlátot! Ez veszélyezteti a tőke örökkévalóságát.")
else:
    st.success(f"✅ **Alkotmányos fegyelem:** A kivételi rátád ({withdrawal_rate:.1f}%) belül van a 4%-os biztonsági korláton.")

st.info(f"**Megjegyzés:** A szimuláció a 2027 áprilisától érvényes szabályokkal számol, ahol a SIPP (£{final_sipp:,.0f}) már nem adómentes örökség. Az összes kifizetett jövedelemadó az életed alatt: £{total_tax_paid:,.0f}.")
