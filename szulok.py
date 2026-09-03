import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Planner", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő")
st.write("A SIPP ürítése és a Tröszt (Perennis tőke) felépítése az Alkotmány 4%-os szabálya mellett.")

# --- SIDEBAR: PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio("Státusz:", ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó"))

st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, 75-current_age, 36)
death_age = st.sidebar.slider("Várható élethossz (Halálozási kor)", 75, 100, 85)

# --- BEFIZETÉSEK ---
if user_mode == "Órabéres alkalmazott":
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours = st.sidebar.number_input("Heti óra", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£)", value=53.70)
    ee_pct = st.sidebar.slider("Saját 4% (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói 4% (%)", 0, 20, 4)
    active_annual_gross = (hourly_rate * hours * 52) + (weekend_bonus * 26)
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
else:
    monthly_contribution_total = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

st.sidebar.markdown("---")
st.sidebar.header("🔑 Birodalmi Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("SIPP Meltdown (Kiürítés) kezdete", 57, 75, 57)

# AGRESSZÍV KIÜRÍTÉS (Ezt toljuk a Trösztbe)
gross_monthly_withdrawal = st.sidebar.slider("Agresszív havi bruttó SIPP kivét (£)", 1000, 25000, 10000, 
                                             help="A cél a SIPP gyors kiürítése a Tröszt javára.")

# ALKOTMÁNYOS MEGÉLHETÉS (Ezt vesszük ki a Trösztből/SIPP-ből élni)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500,
                                         help="Ezt a költést mérjük a 4%-os szabályhoz.")

st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
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
current_sipp, current_trust, current_house = initial_sipp, 0, 0
pcls_taken, total_tax_paid = False, 0

for m in range((death_age - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetés (Aktív kor)
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_contribution_total
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 2. Házvétel (25% azonnal a Trösztbe, majd Ingatlanba)
    if age >= pcls_age and not pcls_taken:
        lump = current_sipp * 0.25
        current_sipp -= lump
        current_house = lump 
        pcls_taken = True
        
    # 3. Meltdown és Tröszt építés
    if age >= drawdown_start_age:
        if current_sipp > 0:
            # SIPP agresszív csapolása
            actual_sipp_g = min(current_sipp, gross_monthly_withdrawal)
            net_income = calculate_net(actual_sipp_g, st_p_m)
            total_tax_paid += ((actual_sipp_g + st_p_m) - net_income)
            current_sipp -= actual_sipp_g
            
            # Előbb a megélhetés, a maradék megy a Trösztbe/Holdingba
            if net_income >= monthly_living_cost:
                current_trust += (net_income - monthly_living_cost)
            else:
                shortfall = monthly_living_cost - net_income
                current_trust = max(0, current_trust - shortfall)
            
            if current_sipp <= 100: current_sipp = 0
        else:
            # Ha elfogyott a SIPP, minden a Trösztből jön
            net_income = calculate_net(0, st_p_m)
            current_trust = max(0, current_trust - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp)
    house_wealth.append(current_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Ürítés alatt)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=house_wealth, name='Ingatlan (Perennis bázis)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='Perennis Tröszt Vagyon', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', 
                         fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))

fig.update_layout(template="plotly_white", height=600, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- ALKOTMÁNYOSSÁGI VIZSGÁLAT (4% SZABÁLY A TRÖSZTRE) ---
annual_living_total = monthly_living_cost * 12
final_trust_val = trust_vals[-1]
idx_retire = int((drawdown_start_age-current_age)*12)
if idx_retire < len(trust_vals):
    current_trust_at_retirement = trust_vals[idx_retire]
else:
    current_trust_at_retirement = 0

check_val = max(final_trust_val, current_trust_at_retirement)
withdrawal_rate_trust = (annual_living_total / check_val) * 100 if check_val > 0 else 0

st.markdown("---")
st.header(f"📜 Perennis Alkotmányos Mérleg")

# JAVÍTOTT KPI RÉSZ: Mindenhol st.metric-et használunk a TypeError elkerülésére
c1, c2, c3, c4 = st.columns(4)
total_gross_at_death = sipp_vals[-1] + house_wealth[-1] + trust_vals[-1]
iht_tax = max(0, (total_gross_at_death - 500000) * 0.40)

c1.metric("Össz vagyon halálkor", f"£{total_gross_at_death:,.0f}")
c2.metric("Tröszt kifizetési ráta", f"{withdrawal_rate_trust:.1f}%")
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Nettó örökség (Post-2027)", f"£{(total_gross_at_death - iht_tax):,.0f}")

# Alkotmányos figyelmeztetések a KPI-k alatt
if withdrawal_rate_trust > 4.0:
    st.warning(f"⚠️ **ALKOTMÁNYELLENES:** A havi £{monthly_living_cost:,.0f} költésed a Tröszt tőkéjének {withdrawal_rate_trust:.1f}%-a. Ez veszélyezteti a tőkemegőrzés szabályát!")
else:
    st.success(f"✅ **ALKOTMÁNYOS:** A megélhetési rátád ({withdrawal_rate_trust:.1f}%) biztosítja a birodalom halhatatlanságát.")

st.info(f"**Stratégiai elemzés:** A SIPP-et havi £{gross_monthly_withdrawal:,.0f} bruttóval ürítjük. Az adózott pénzt a Trösztbe mentjük, ahol a vagyon immár a Perennis Alkotmány 4%-os védelme alatt áll.")
