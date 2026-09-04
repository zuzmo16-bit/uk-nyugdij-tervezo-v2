import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition v2.4)")
st.write("Javított 3-színű adó-heatmap és prioritásos vagyonfelélési stratégia.")

# --- SESSION STATE ---
if 'market_return' not in st.session_state: st.session_state.market_return = 7.5
if 'inflation' not in st.session_state: st.session_state.inflation = 2.5

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás (UK-HU Transzfer)")
)

# --- IDŐTÁV & ÉLETHOSSZ ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
if user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    current_age = st.sidebar.slider("Hány évesen indul a transzfer?", 45, 75, 53)
else:
    current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 34)
death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)

# --- BEÁLLÍTÁSOK INICIALIZÁLÁSA ---
partner_income = 0
active_annual_gross = 0
start_sipp, start_aviva, start_trust = 15000, 15000, 0
monthly_sipp_user_net = 0
monthly_aviva_total = 0
working_years = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)

    st.sidebar.header("👫 Affordability")
    mortgage_type = st.sidebar.radio("Hitel konstrukció", ("Solo Mortgage", "Joint Mortgage"))
    partner_income = st.sidebar.number_input("Partner éves bruttó jövedelme (£)", value=25000) if mortgage_type == "Joint Mortgage" else 0
    max_loan_allowed = (active_annual_gross + partner_income) * 4.5
    
    st.sidebar.header("🏢 AVIVA (Workplace Pension)")
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=15000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    aviva_return = st.sidebar.slider("AVIVA várható éves hozama (%)", 1.0, 10.0, 4.5)
    monthly_aviva_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)

    st.sidebar.header("🏹 Saját SIPP")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=0)
    monthly_sipp_user_net = st.sidebar.number_input("Havi saját befizetés (Nettó £)", value=200)
    working_years = st.sidebar.slider("Hány évig dolgozol még?", 0, int(75-current_age), 38)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
    monthly_sipp_director = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
    working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, int(75-current_age), 20)
    active_annual_gross = 12570 

# --- SIPP & KIFIZETÉS STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Meltdown & Kifizetés")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 58)
drawdown_start_age = st.sidebar.slider("Havi kifizetés kezdete", 57, 75, 72)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 4189)

# --- JAVÍTOTT ADÓ-HEATMAP (3 SZÍN) ---
state_p_monthly = 11502 / 12
total_projected_gross = gross_sipp_meltdown + state_p_monthly

if total_projected_gross <= 4189:
    st.sidebar.markdown('<div style="background-color: #d4edda; padding: 10px; border-radius: 5px; border-left: 5px solid #28a745; color: #155724;"><b>🟢 20%-os sáv (Basic Rate)</b><br>Optimális adózás.</div>', unsafe_allow_html=True)
elif total_projected_gross <= 10428:
    st.sidebar.markdown('<div style="background-color: #d1ecf1; padding: 10px; border-radius: 5px; border-left: 5px solid #007bff; color: #0c5460;"><b>🔵 40%-os sáv (Higher Rate)</b><br>Vigyázat, a jövedelem fele az államé lehet!</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div style="background-color: #f8d7da; padding: 10px; border-radius: 5px; border-left: 5px solid #dc3545; color: #721c24;"><b>🔴 45% + Personal Allowance veszteség</b><br>Kritikus adóteher (akár 60% effektív)!</div>', unsafe_allow_html=True)

monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 3300)

st.sidebar.header("🏠 Ingatlanhitel")
target_house_value = st.sidebar.number_input("Tervezett ingatlanérték (£)", value=340000)
mortgage_interest = st.sidebar.slider("Hitel kamatláb (%)", 1.0, 8.0, 4.5)
mortgage_term = st.sidebar.slider("Hitel futamideje (év)", 5, 25, 15)

st.sidebar.header("📈 Ekonomiai Beállítások")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, st.session_state.market_return)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, st.session_state.inflation)

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

m_market_rate = ((1 + market_return/100) / (1 + inflation/100))**(1/12) - 1
if user_mode == "Órabéres alkalmazott":
    m_aviva_rate = ((1 + (4.5 if user_mode != "Órabéres alkalmazott" else aviva_return)/100) / (1 + inflation/100))**(1/12) - 1
else: m_aviva_rate = 0

# --- SZIMULÁCIÓ ---
ages, sipp_vals, aviva_vals, house_vals, isa_vals, holding_vals, mortgage_debt_vals = [], [], [], [], [], [], []
current_sipp, current_aviva, current_isa, current_holding, current_uk_house = start_sipp, start_aviva, 0, 0, 0
current_mortgage_debt, total_tax_paid, total_gross_drawdown, mortgage_payment = 0, 0, 0, 0
pcls_taken = False
sipp_at_retirement = 0

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
        if user_mode == "Órabéres alkalmazott":
            if age < drawdown_start_age: current_sipp += (monthly_sipp_user_net * 1.25)
        elif user_mode == "Céges igazgató / Vállalkozó":
            current_sipp += 5000

    if not pcls_taken and age >= pcls_age:
        total_p = current_sipp + current_aviva
        pcls_val = total_p * 0.25
        ratio = current_sipp / total_p if total_p > 0 else 0.5
        current_sipp -= pcls_val * ratio
        current_aviva -= pcls_val * (1 - ratio)
        current_uk_house = target_house_value
        current_mortgage_debt = max(0, target_house_value - pcls_val)
        r, n = (mortgage_interest / 100) / 12, mortgage_term * 12
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
        if sipp_at_retirement == 0: sipp_at_retirement = current_sipp + current_aviva
        total_pension = current_sipp + current_aviva
        if total_pension > 0:
            actual_gross = min(total_pension, gross_sipp_meltdown)
            total_net = calculate_net(actual_gross, st_p_m)
            total_tax_paid += ((actual_gross + st_p_m) - total_net)
            total_gross_drawdown += (actual_gross + st_p_m)
            ratio = current_sipp / total_pension if total_pension > 0 else 0.5
            current_sipp -= actual_gross * ratio
            current_aviva -= actual_gross * (1 - ratio)
            
            # Maradvány kezelés: Hitel -> Living -> ISA (£1666/hó) -> Holding
            net_after_essentials = total_net - adj_mortgage_payment - monthly_living_cost
            if net_after_essentials > 0:
                isa_in = min(net_after_essentials, 1666)
                current_isa += isa_in
                current_holding += (net_after_essentials - isa_in)
            else:
                # HIÁNY: ISA ürül először (prioritásos felélés)!
                shortfall = abs(net_after_essentials)
                if current_isa >= shortfall: current_isa -= shortfall
                else:
                    shortfall -= current_isa; current_isa = 0
                    current_holding = max(0, current_holding - shortfall)
        else:
            net_state = calculate_net(0, st_p_m)
            total_gross_drawdown += st_p_m
            total_tax_paid += (st_p_m - net_state)
            shortfall = abs(net_state - adj_mortgage_payment - monthly_living_cost)
            if current_isa >= shortfall: current_isa -= shortfall
            else:
                shortfall -= current_isa; current_isa = 0
                current_holding = max(0, current_holding - shortfall)

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
fig.add_trace(go.Scatter(x=ages, y=isa_vals, name='ISA Vagyon (Elsőbbségi felélés)', mode='lines', line=dict(color='gold', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=holding_vals, name='Magyar Holding (Birodalmi tőke)', mode='lines', line=dict(color='#C0C0C0', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(192,192,192,0.5)']])))
fig.add_trace(go.Scatter(x=ages, y=mortgage_debt_vals, name='Hitel tartozás', mode='lines', line=dict(color='firebrick', width=2, dash='dash')))
fig.update_layout(template="plotly_white", height=650, hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- KPI MÉRLEG ---
st.markdown("---")
total_at_death = sipp_vals[-1] + aviva_vals[-1] + house_vals[-1] + isa_vals[-1] + holding_vals[-1] - mortgage_debt_vals[-1]
st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")
c2.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
eff_rate = (total_tax_paid / total_gross_drawdown * 100) if total_gross_drawdown > 0 else 0
c3.metric("Effektív adókulcs", f"{eff_rate:.1f}%")
c4.metric("Nettó Örökség", f"£{(total_at_death - max(0, (total_at_death-500000)*0.4)):,.0f}")

# --- STRATÉGIAI ELEMZÉS SZAKASZ (FIXÁLVA) ---
st.markdown("### 🔍 Stratégiai Elemzés")
col_a, col_b = st.columns(2)

with col_a:
    st.write("**Megélhetés és Fenntarthatóság:**")
    months_left = (death_age - drawdown_start_age) * 12
    if months_left > 0:
        total_liquid = sipp_at_retirement # közelítés
        max_sustainable = (total_liquid * m_market_rate) / (1 - (1 + m_market_rate)**-months_left) + (11502/12)
        st.write(f"- 🏆 **Maximális fenntartható havi nettó:** £{max_sustainable:,.0f}")
        st.write(f"- 🛒 **Jelenleg tervezett havi nettó:** £{monthly_living_cost:,.0f}")
        if monthly_living_cost > max_sustainable:
            st.error(f"⚠️ A tervezett költésed magasabb a fenntarthatónál!")
        else:
            st.success(f"✅ A terved fenntartható.")

with col_b:
    st.write("**Hitel és Adó információk:**")
    if user_mode == "Órabéres alkalmazott":
        st.write(f"- 🏠 **Havi hiteltörlesztő (induló):** £{mortgage_payment:,.0f}")
    proj_net = calculate_net(gross_sipp_meltdown, 11502/12)
    isa_ba = max(0, proj_net - adj_mortgage_payment - monthly_living_cost)
    st.write(f"- 💰 **Tervezett havi teljes nettó:** £{proj_net:,.0f}")
    st.write(f"- 📈 **Ebből ISA/Holdingba kerül:** £{isa_ba:,.0f}")
