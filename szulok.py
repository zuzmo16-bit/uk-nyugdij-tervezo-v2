import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition v2)")
st.write("Vizuális adósáv-elemzéssel, hitelképességi kontrollal és stressz-teszt funkciókkal.")

# --- SESSION STATE A STRESSZ-TESZTEKHEZ ---
if 'market_return' not in st.session_state: st.session_state.market_return = 7.5
if 'inflation' not in st.session_state: st.session_state.inflation = 2.5
if 'death_age' not in st.session_state: st.session_state.death_age = 85

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás (UK-HU Transzfer)")
)

# --- IDŐTÁV & ÉLETHOSSZ ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
death_age = st.sidebar.slider("Várható élethossz", 75, 100, st.session_state.death_age)

# --- PROFIL SPECIFIKUS ADATOK ---
partner_income = 0
active_annual_gross = 0
start_sipp, start_aviva, start_trust = 15000, 15000, 0
monthly_aviva_total = 0
working_years = 0
est_deposit = 0
max_loan_allowed = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)

    st.sidebar.header("👫 Affordability (Hitelképesség)")
    mortgage_type = st.sidebar.radio("Hitel konstrukció", ("Solo Mortgage", "Joint Mortgage"))
    partner_income = st.sidebar.number_input("Partner éves bruttó jövedelme (£)", value=25000) if mortgage_type == "Joint Mortgage" else 0
    
    max_loan_allowed = (active_annual_gross + partner_income) * 4.5
    
    st.sidebar.header("🏢 AVIVA (Workplace Pension)")
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=15000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    aviva_return = st.sidebar.slider("AVIVA várható éves hozama (%)", 1.0, 10.0, 4.5)
    monthly_aviva_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)

    working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, int(75-current_age), 36)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
    monthly_sipp_director = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
    working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, int(75-current_age), 20)
    active_annual_gross = 12570 

# --- SIPP & KIFIZETÉS STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Meltdown & Adósávok")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés kezdete", 57, 75, 72)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 8333)

# FIX: unsafe_allow_human_readable eltávolítva
if gross_sipp_meltdown <= 4189:
    st.sidebar.markdown(f'<div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745;"><b>🟢 20%-os sáv (Basic Rate)</b><br>Adóoptimalizált zóna.</div>', unsafe_allow_html=True)
elif gross_sipp_meltdown <= 8333:
    st.sidebar.markdown(f'<div style="background-color: #d1ecf1; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff;"><b>🔵 40%-os sáv (Higher Rate)</b><br>Vigyázat, a jövedelmed fele adózhat!</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown(f'<div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545;"><b>🔴 45%-os sáv + PA veszteség</b><br>Aggresszív kimentés, extra magas adóteher!</div>', unsafe_allow_html=True)

monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 3500)

# --- INGATLANHITEL KONTROLL ---
if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("🏠 Ingatlanhitel Paraméterek")
    target_house_value = st.sidebar.number_input("Tervezett ingatlanérték (£)", value=340000)
    
    years_to_pcls = pcls_age - current_age
    est_sipp_at_pcls = start_sipp * (1.05**years_to_pcls)
    est_aviva_at_pcls = (start_aviva + monthly_aviva_total*12*years_to_pcls) * (1.03**years_to_pcls)
    est_deposit = (est_sipp_at_pcls + est_aviva_at_pcls) * 0.25
    max_house_allowed = max_loan_allowed + est_deposit
    
    if target_house_value > max_house_allowed:
        st.sidebar.error(f"❌ Túl drága ingatlan! A jövedelmed és önerőd alapján a max: £{max_house_allowed:,.0f}")
    else:
        st.sidebar.success(f"✅ Hitelképes vagy £{max_house_allowed:,.0f} értékig.")
    
    mortgage_interest = st.sidebar.slider("Hitel kamatláb (%)", 1.0, 8.0, 4.5)
    mortgage_term = st.sidebar.slider("Hitel futamideje (év)", 5, 25, 18)

# --- EKONOMIAI ÉS STRESSZ ---
st.sidebar.header("📈 Ekonomiai Beállítások")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, st.session_state.market_return)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, st.session_state.inflation)

st.sidebar.markdown("---")
st.sidebar.header("☢️ Stressz-Teszt")
c_s1, c_s2 = st.sidebar.columns(2)
if c_s1.button("Válság (3%)"): st.session_state.market_return = 3.0; st.rerun()
if c_s2.button("Infláció (5%)"): st.session_state.inflation = 5.0; st.rerun()

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
m_market_rate = ((1 + market_return/100) / (1 + inflation/100))**(1/12) - 1
m_aviva_rate = ((1 + (4.5 if user_mode != "Órabéres alkalmazott" else aviva_return)/100) / (1 + inflation/100))**(1/12) - 1

ages, sipp_vals, aviva_vals, house_vals, isa_vals, holding_vals, mortgage_debt_vals = [], [], [], [], [], [], []
current_sipp, current_aviva, current_isa, current_holding, current_uk_house = start_sipp, start_aviva, 0, 0, 0
current_mortgage_debt, total_tax_paid, total_gross_drawdown, mortgage_payment = 0, 0, 0, 0
pcls_taken = False

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_market_rate)
    current_aviva *= (1 + m_aviva_rate)
    current_isa *= (1 + m_market_rate)
    current_holding *= (1 + m_market_rate)
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)

    if m <= (working_years * 12):
        current_aviva += monthly_aviva_total
        if user_mode == "Órabéres alkalmazott" and age < drawdown_start_age: current_sipp += (100 * 1.25)
        elif user_mode == "Céges igazgató / Vállalkozó": current_sipp += 5000

    if not pcls_taken and age >= pcls_age:
        total_p = current_sipp + current_aviva
        pcls_val = total_p * 0.25
        ratio = current_sipp / total_p if total_p > 0 else 0.5
        current_sipp -= pcls_val * ratio
        current_aviva -= pcls_val * (1 - ratio)
        if user_mode == "Órabéres alkalmazott":
            current_uk_house = target_house_value
            current_mortgage_debt = max(0, target_house_value - pcls_val)
            r = (mortgage_interest / 100) / 12
            n = mortgage_term * 12
            mortgage_payment = current_mortgage_debt * (r * (1 + r)**n) / ((1 + r)**n - 1) if r > 0 else current_mortgage_debt / n
        pcls_taken = True
        
    adj_mortgage_payment = 0
    if current_mortgage_debt > 0:
        interest_m = current_mortgage_debt * (mortgage_interest / 100 / 12)
        principal_m = mortgage_payment - interest_m
        current_mortgage_debt -= principal_m
        adj_mortgage_payment = mortgage_payment / ((1 + (inflation/100))**(m/12))
        if current_mortgage_debt < 0: current_mortgage_debt, mortgage_payment = 0, 0
    
    st_p_m = (11502 / 12) if age >= 70 else 0
    if age >= drawdown_start_age:
        total_pension = current_sipp + current_aviva
        if total_pension > 0:
            actual_gross = min(total_pension, gross_sipp_meltdown)
            total_net = calculate_net(actual_gross, st_p_m)
            total_tax_paid += ((actual_gross + st_p_m) - total_net)
            total_gross_drawdown += (actual_gross + st_p_m)
            ratio = current_sipp / total_pension if total_pension > 0 else 0.5
            current_sipp -= actual_gross * ratio
            current_aviva -= actual_gross * (1 - ratio)
            net_after_essentials = total_net - adj_mortgage_payment - monthly_living_cost
            if net_after_essentials > 0:
                isa_in = min(net_after_essentials, 1666)
                current_isa += isa_in
                current_holding += (net_after_essentials - isa_in)
            else:
                shortfall = abs(net_after_essentials)
                if current_holding >= shortfall: current_holding -= shortfall
                else: 
                    shortfall -= current_holding; current_holding = 0
                    current_isa = max(0, current_isa - shortfall)
        else:
            net_state = calculate_net(0, st_p_m)
            shortfall = abs(net_state - adj_mortgage_payment - monthly_living_cost)
            if current_holding >= shortfall: current_holding -= shortfall
            else:
                shortfall -= current_holding; current_holding = 0
                current_isa = max(0, current_isa - shortfall)

    sipp_vals.append(current_sipp)
    aviva_vals.append(current_aviva)
    house_vals.append(current_uk_house)
    isa_vals.append(current_isa)
    holding_vals.append(current_holding)
    mortgage_debt_vals.append(current_mortgage_debt)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='Saját SIPP', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=aviva_vals, name='AVIVA', mode='lines', line=dict(color='#40E0D0', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(64,224,208,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=house_vals, name='Saját Ingatlan', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=isa_vals, name='ISA Vagyon', mode='lines', line=dict(color='gold', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=holding_vals, name='Holding', mode='lines', line=dict(color='#C0C0C0', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(192,192,192,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=mortgage_debt_vals, name='Hitel tartozás', mode='lines', line=dict(color='firebrick', width=2, dash='dash')))

fig.update_layout(template="plotly_white", height=650, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- KPI MÉRLEG ---
total_at_death = sipp_vals[-1] + aviva_vals[-1] + house_vals[-1] + isa_vals[-1] + holding_vals[-1] - mortgage_debt_vals[-1]
st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Összvagyon (Bruttó)", f"£{total_at_death + max(0, (total_at_death-500000)*0.4):,.0f}")
c2.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
eff_rate = (total_tax_paid / total_gross_drawdown * 100) if total_gross_drawdown > 0 else 0
c3.metric("Effektív adókulcs", f"{eff_rate:.1f}%")
c4.metric("Nettó Örökség", f"£{total_at_death - max(0, (total_at_death-500000)*0.4):,.0f}")
