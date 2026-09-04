import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition v2.8)")
st.write("Partner Stratégia: Dupla adókedvezmény, felezett hitelköltség és közös vagyonépítés.")

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
partner_mode = False
partner_income = 0
active_annual_gross = 0
start_sipp, start_aviva, start_trust = 15000, 15000, 0
monthly_sipp_user_net, monthly_aviva_total = 0, 0
working_years = 0
max_loan_limit = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti adatok")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)

    st.sidebar.header("👫 Családi Szövetség")
    partner_mode = st.sidebar.checkbox("Partner bevonása (Joint Strategy)", value=True)
    if partner_mode:
        partner_income = st.sidebar.number_input("Partner éves bruttó jövedelme (£)", value=35000)
    
    max_loan_limit = (active_annual_gross + partner_income) * 4.5
    
    st.sidebar.header("🏢 AVIVA (Workplace Pension)")
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=15000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    aviva_return = st.sidebar.slider("AVIVA várható éves hozama (%)", 1.0, 10.0, 4.5)
    multiplier = 2 if partner_mode else 1
    monthly_aviva_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100) * multiplier

    st.sidebar.header("🏹 Saját SIPP")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=0)
    monthly_sipp_user_net = st.sidebar.number_input("Havi saját befizetés (Nettó £)", value=200)
    working_years = st.sidebar.slider("Hány évig dolgozol még?", 0, int(75-current_age), 38)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
    
    st.sidebar.markdown("### 💰 Céges Cash-Flow & Extrakció")
    company_annual_revenue = st.sidebar.number_input("Cég éves nettó árbevétele (£)", value=120000)
    company_expenses = st.sidebar.number_input("Egyéb céges költségek (Éves £)", value=15000)
    
    director_salary = st.sidebar.number_input("Igazgatói éves bér (Optimalizált: £12,570)", value=12570)
    monthly_sipp_director = st.sidebar.number_input("Havi céges SIPP hozzájárulás (£)", value=3000)
    
    # Társasági adó alap számítás (Árbevétel - Költségek - Bér - Céges SIPP)
    annual_corporate_sipp = monthly_sipp_director * 12
    corporate_profit_before_tax = max(0, company_annual_revenue - company_expenses - director_salary - annual_corporate_sipp)
    
    # UK Corporation Tax sávok (19% - 25% marginal rate)
    if corporate_profit_before_tax <= 50000:
        corp_tax = corporate_profit_before_tax * 0.19
    elif corporate_profit_before_tax <= 250000:
        corp_tax = (50000 * 0.19) + ((corporate_profit_before_tax - 50000) * 0.265)
    else:
        corp_tax = corporate_profit_before_tax * 0.25
        
    retained_earnings = corporate_profit_before_tax - corp_tax
    
    # Osztalék politika a megmaradt profitból
    max_dividend_possible = retained_earnings
    annual_dividend_taken = st.sidebar.slider("Kivett éves osztalék (£)", 0, int(max_dividend_possible), int(max_dividend_possible * 0.7))
    
    st.sidebar.info(f"📊 Társasági adó: £{corp_tax:,.0f} | Cégben maradó profit: £{(retained_earnings - annual_dividend_taken):,.0f}")

    # Aktív éves bruttó meghatározása a meglévő logikák számára
    active_annual_gross = director_salary + annual_dividend_taken
    
    st.sidebar.header("👫 Családi Szövetség (Cégvezető)")
    partner_mode = st.sidebar.checkbox("Partner bevonása (Pl. Osztalék megosztás)", value=False)
    if partner_mode:
        partner_income = st.sidebar.number_input("Partner külön jövedelme / Osztaléka (£)", value=12570)
    
    max_loan_limit = (active_annual_gross + partner_income) * 4.5
    working_years = st.sidebar.slider("Hány évig fut még aktívan a cég?", 0, int(75-current_age), 20)

# --- SIPP & KIFIZETÉS ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP Meltdown & Kifizetés")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 58)
drawdown_start_age = st.sidebar.slider("Havi kifizetés kezdete", 57, 75, 72)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 8333)

state_p_monthly = (11502 / 12) * (2 if partner_mode else 1)
total_projected_gross = gross_sipp_meltdown + state_p_monthly

# Adósáv heatmap (Partner esetén dupla sávok)
threshold_20 = 4189 * (2 if partner_mode else 1)
threshold_40 = 10428 * (2 if partner_mode else 1)

if total_projected_gross <= threshold_20:
    st.sidebar.success("🟢 20%-os sáv (Basic Rate)")
elif total_projected_gross <= threshold_40:
    st.sidebar.info("🔵 40%-os sáv (Higher Rate)")
else:
    st.sidebar.error("🔴 45% + PA veszteség")

monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 3500)

st.sidebar.header("🏠 Ingatlanhitel")
target_house_value = st.sidebar.number_input("Tervezett ingatlanérték (£)", value=340000)
mortgage_interest = st.sidebar.slider("Hitel kamatláb (%)", 1.0, 8.0, 4.5)
mortgage_term = st.sidebar.slider("Hitel futamideje (év)", 5, 25, 15)

st.sidebar.header("📈 Ekonomiai Beállítások")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, st.session_state.market_return)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, st.session_state.inflation)
# --- ADÓKALKULÁTOR (Házastársi logikával) ---
def calculate_net_household(gross_m, partner_active):
    num_people = 2 if partner_active else 1
    gross_per_person_a = (gross_m / num_people) * 12
    
    pa = 12570
    if gross_per_person_a > 100000:
        pa = max(0, pa - (gross_per_person_a - 100000) / 2)
    
    taxable = max(0, gross_per_person_a - pa)
    tax = 0
    if taxable > 0:
        b20 = min(taxable, 37700); tax += b20 * 0.20
        if taxable > 37700:
            b40 = min(taxable - 37700, 125140 - 37700); tax += b40 * 0.40
        if taxable > 125140: tax += (taxable - 125140) * 0.45
            
    return ((gross_per_person_a - tax) * num_people) / 12

m_market_rate = ((1 + market_return/100) / (1 + inflation/100))**(1/12) - 1
if user_mode == "Órabéres alkalmazott":
    m_aviva_rate = ((1 + (aviva_return)/100) / (1 + inflation/100))**(1/12) - 1
else: m_aviva_rate = 0

# --- SZIMULÁCIÓ ---
ages, sipp_vals, aviva_vals, house_vals, isa_vals, holding_vals, mortgage_debt_vals = [], [], [], [], [], [], []
current_sipp, current_aviva, current_isa, current_holding, current_uk_house = start_sipp, start_aviva, 0, 0, 0
current_mortgage_debt, total_tax_paid, total_gross_drawdown, mortgage_payment = 0, 0, 0, 0
initial_mortgage_payment, sipp_at_retirement, final_pcls_val = 0, 0, 0
pcls_taken = False

if partner_mode:
    current_sipp *= 2
    current_aviva *= 2

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
            if age < drawdown_start_age: current_sipp += (monthly_sipp_user_net * 1.25 * multiplier)
        elif user_mode == "Céges igazgató / Vállalkozó":
            current_sipp += monthly_sipp_director

    if not pcls_taken and age >= pcls_age:
        total_p = current_sipp + current_aviva
        pcls_val = total_p * 0.25
        final_pcls_val = pcls_val
        ratio = current_sipp / total_p if total_p > 0 else 0.5
        current_sipp = max(0, current_sipp - (pcls_val * ratio))
        current_aviva = max(0, current_aviva - (pcls_val * (1 - ratio)))
        current_uk_house = target_house_value
        current_mortgage_debt = max(0, target_house_value - pcls_val)
        r, n = (mortgage_interest / 100) / 12, mortgage_term * 12
        if r > 0 and n > 0: mortgage_payment = current_mortgage_debt * (r * (1 + r)**n) / ((1 + r)**n - 1)
        elif n > 0: mortgage_payment = current_mortgage_debt / n
        initial_mortgage_payment = mortgage_payment
        pcls_taken = True
        
    adj_mortgage_payment = 0
    if current_mortgage_debt > 0:
        interest_m = current_mortgage_debt * (mortgage_interest / 100 / 12)
        principal_m = mortgage_payment - interest_m
        current_mortgage_debt = max(0, current_mortgage_debt - principal_m)
        adj_mortgage_payment = mortgage_payment / ((1 + (inflation/100))**(m/12))
        if current_mortgage_debt <= 0: current_mortgage_debt, mortgage_payment = 0, 0
    
    st_p_m = (11502 / 12 * (2 if partner_mode else 1)) if age >= 70 else 0
    if age >= drawdown_start_age:
        if sipp_at_retirement == 0: sipp_at_retirement = current_sipp + current_aviva
        total_pension = current_sipp + current_aviva
        if total_pension > 0.1:
            actual_gross = min(total_pension, gross_sipp_meltdown)
            total_net = calculate_net_household(actual_gross + st_p_m, partner_mode)
            total_tax_paid += ((actual_gross + st_p_m) - total_net)
            total_gross_drawdown += (actual_gross + st_p_m)
            ratio = current_sipp / total_pension if total_pension > 0 else 0.5
            current_sipp = max(0, current_sipp - (actual_gross * ratio))
            current_aviva = max(0, current_aviva - (actual_gross * (1 - ratio)))
            
            user_mortgage_share = adj_mortgage_payment / (2 if partner_mode else 1)
            net_after_essentials = total_net - adj_mortgage_payment - monthly_living_cost
            if net_after_essentials > 0:
                isa_limit = 1666 * (2 if partner_mode else 1)
                isa_in = min(net_after_essentials, isa_limit)
                current_isa += isa_in
                current_holding += (net_after_essentials - isa_in)
            else:
                shortfall = abs(net_after_essentials)
                if current_isa >= shortfall: current_isa -= shortfall
                else:
                    shortfall -= current_isa; current_isa = 0
                    current_holding = max(0, current_holding - shortfall)
        else:
            current_sipp, current_aviva = 0, 0
            net_state = calculate_net_household(st_p_m, partner_mode)
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
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='Saját SIPP (Közös)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=aviva_vals, name='AVIVA (Közös)', mode='lines', line=dict(color='#40E0D0', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(64,224,208,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=house_vals, name='Saját Ingatlan', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=isa_vals, name='ISA Vagyon (Közös)', mode='lines', line=dict(color='gold', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=holding_vals, name='Magyar Holding', mode='lines', line=dict(color='#C0C0C0', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(192,192,192,0.5)']])))
fig.add_trace(go.Scatter(x=ages, y=mortgage_debt_vals, name='Hitel tartozás', mode='lines', line=dict(color='firebrick', width=2, dash='dash')))

fig.update_layout(template="plotly_white", height=650, hovermode="x unified", hoverlabel=dict(bgcolor="rgba(255,255,255,0.9)", font_size=12, namelength=-1), legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
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

# --- STRATÉGIAI ELEMZÉS ---
st.markdown("### 🔍 Stratégiai Elemzés")
col_a, col_b = st.columns(2)
with col_a:
    months_left = (death_age - drawdown_start_age) * 12
    if months_left > 0:
        total_liquid = sipp_at_retirement
        max_sustainable = (total_liquid * m_market_rate) / (1 - (1 + m_market_rate)**-months_left) + (state_p_monthly)
        st.write(f"- 🏆 **Maximális fenntartható havi nettó:** £{max_sustainable:,.0f}")
        st.write(f"- 🛒 **Jelenleg tervezett havi nettó:** £{monthly_living_cost:,.0f}")
with col_b:
    st.write(f"- 🏰 **Maximális ingatlanérték:** £{max_loan_limit + final_pcls_val:,.0f}")
    st.write(f"- 🏠 **Havi hiteltörlesztő (összesen):** £{initial_mortgage_payment:,.0f}")
    if partner_mode:
        st.write(f"- ⚖️ **Te részed a törlesztőből:** £{initial_mortgage_payment/2:,.0f}")
