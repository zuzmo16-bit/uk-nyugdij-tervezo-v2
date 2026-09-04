import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition)")
st.write("SIPP & AVIVA Meltdown, SSAS Loanback, ISA és Nemzetközi Adóoptimalizálás.")

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
    current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 31)
death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)

# --- INICIALIZÁLÁS ---
start_sipp = 0
start_aviva = 0
start_trust = 0
start_house = 0
working_years = 0
monthly_sipp_user_net = 0
monthly_aviva_total = 0
monthly_sipp_director = 0
active_annual_gross = 0

# --- PROFIL SPECIFIKUS ADATOK ---
if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    
    st.sidebar.header("🏢 AVIVA (Workplace Pension)")
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=5000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    aviva_return = st.sidebar.slider("AVIVA várható éves hozama (%)", 1.0, 10.0, 4.5)
    
    st.sidebar.header("🏹 Saját SIPP (Vanguard)")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=0)
    monthly_sipp_user_net = st.sidebar.number_input("Havi saját befizetés a SIPP-be (Nettó £)", value=100)
    
    working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, int(75-current_age), 36)
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)
    monthly_aviva_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
    monthly_sipp_director = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
    working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, int(75-current_age), 20)
    start_trust = st.sidebar.number_input("Holding tőke (£)", value=0)
    aviva_return = 0

elif user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    st.sidebar.subheader("💰 Jelenlegi Vagyon")
    start_sipp = st.sidebar.number_input("Összesített SIPP egyenleg (£)", value=1000000)
    start_house = st.sidebar.number_input("UK Ingatlan értéke (£)", value=500000)
    start_trust = st.sidebar.number_input("Holding / Tröszt tőke (£)", value=250000)
    working_years = 0
    aviva_return = 0

# --- SIPP & KIFIZETÉS STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP & Kifizetés Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés (Meltdown) kezdete", 57, 75, 70 if user_mode != "Nemzetközi Kivonulás (UK-HU Transzfer)" else current_age)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 3500)

# --- ÁLLAMI NYUGDÍJ ---
st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 70)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Ekonomiai Beállítások")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- HAZAKÖLTÖZÉS ---
st.sidebar.markdown("---")
st.sidebar.header("🇭🇺 Nemzetközi Stratégia")
enable_hu_move = st.sidebar.checkbox("Hazaköltözés Magyarországra?", value=(user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)"))
hu_move_age = st.sidebar.slider("Hazaköltözés életkora", 18, 90, 63 if not enable_hu_move else current_age)

# --- SSAS LOANBACK (Csak nemzetközi módban) ---
enable_ssas_loan = False
loan_amount = 0
if user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    st.sidebar.markdown("---")
    st.sidebar.header("🏦 SSAS Finanszírozás")
    enable_ssas_loan = st.sidebar.checkbox("SSAS Loanback mozgósítása? (Max 50%)", value=True)
    loan_amount = (start_sipp * 0.5) if enable_ssas_loan else 0

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

real_market_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_market_rate = (1 + real_market_rate) ** (1/12) - 1

if user_mode == "Órabéres alkalmazott":
    real_aviva_rate = ((1 + (aviva_return / 100)) / (1 + (inflation / 100))) - 1
    m_aviva_rate = (1 + real_aviva_rate) ** (1/12) - 1
else:
    m_aviva_rate = 0

# --- SZIMULÁCIÓ ---
ages, sipp_vals, aviva_vals, hu_base_vals, uk_house_vals, trust_vals = [], [], [], [], [], []
current_sipp, current_aviva, current_trust, current_uk_house, current_hu_base = start_sipp, start_aviva, start_trust, 0, 0
loan_balance = loan_amount
pcls_taken, total_tax_paid, total_gross_income_drawdown = (user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)"), 0, 0

if enable_ssas_loan:
    current_sipp -= loan_amount
    current_hu_base = loan_amount 

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_market_rate)
    current_aviva *= (1 + m_aviva_rate)
    current_trust *= (1 + m_market_rate)
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)
    current_hu_base *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetések
    if m <= (working_years * 12) and age <= 75:
        current_aviva += monthly_aviva_total
        if user_mode == "Órabéres alkalmazott":
            current_sipp += (monthly_sipp_user_net * 1.25)
        elif user_mode == "Céges igazgató / Vállalkozó":
            current_sipp += monthly_sipp_director

    # 2. SSAS Törlesztés
    if enable_ssas_loan and loan_balance > 0 and m <= 60:
        repayment = loan_amount / 60
        interest = loan_balance * 0.005 
        current_sipp += (repayment + interest)
        loan_balance -= repayment

    # 3. 25% PCLS (Kombinált)
    if not pcls_taken and age >= pcls_age:
        total_p = current_sipp + current_aviva
        pcls_val = total_p * 0.25
        ratio = current_sipp / total_p if total_p > 0 else 0.5
        current_sipp -= pcls_val * ratio
        current_aviva -= pcls_val * (1 - ratio)
        current_uk_house = pcls_val
        pcls_taken = True
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 4. Meltdown & Megélhetés
    if age >= drawdown_start_age:
        total_pension = current_sipp + current_aviva
        if total_pension > 0:
            actual_gross = min(total_pension, gross_sipp_meltdown)
            total_net = calculate_net(actual_gross, st_p_m)
            
            # Adó és Bruttó gyűjtése
            tax_this_month = ((actual_gross + st_p_m) - total_net)
            total_tax_paid += tax_this_month
            total_gross_income_drawdown += (actual_gross + st_p_m)
            
            # Levonás arányosan
            ratio = current_sipp / total_pension if total_pension > 0 else 0.5
            current_sipp -= actual_gross * ratio
            current_aviva -= actual_gross * (1 - ratio)
            
            if total_net >= monthly_living_cost:
                current_trust += (total_net - monthly_living_cost)
            else:
                shortfall = monthly_living_cost - total_net
                current_trust = max(0, current_trust - shortfall)
        else:
            net_state = calculate_net(0, st_p_m)
            total_gross_income_drawdown += st_p_m
            total_tax_paid += (st_p_m - net_state)
            current_trust = max(0, current_trust - (monthly_living_cost - net_state))

    sipp_vals.append(current_sipp + loan_balance)
    aviva_vals.append(current_aviva)
    hu_base_vals.append(current_hu_base)
    uk_house_vals.append(current_uk_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Saját + Hitel)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
if user_mode == "Órabéres alkalmazott":
    fig.add_trace(go.Scatter(x=ages, y=aviva_vals, name='AVIVA (Workplace)', mode='lines', line=dict(color='#40E0D0', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(64,224,208,0.3)']])))

fig.add_trace(go.Scatter(x=ages, y=hu_base_vals, name='Magyar Perennis Bázis', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=uk_house_vals, name='Saját Ingatlan', mode='lines', line=dict(color='teal', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(0,128,128,0.4)']])))

trust_label = "ISA Vagyon" if user_mode == "Órabéres alkalmazott" else "Perennis Vagyon (Holding)"
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name=trust_label, mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))

fig.update_layout(template="plotly_white", height=650, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- ANALITIKAI MÉRLEG ---
st.markdown("---")
total_at_death = sipp_vals[-1] + aviva_vals[-1] + hu_base_vals[-1] + uk_house_vals[-1] + trust_vals[-1]
years_kint = death_age - hu_move_age
iht_tax = 0 if (enable_hu_move and years_kint >= 10) else max(0, (total_at_death - 500000) * 0.40)

st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")
c2.metric("Összes kifizetett adó (HMRC)", f"£{total_tax_paid:,.0f}")

# Effektív adókulcs számítása a havi folyósítástól
eff_tax_rate = (total_tax_paid / total_gross_income_drawdown * 100) if total_gross_income_drawdown > 0 else 0
c3.metric("Effektív adókulcs", f"{eff_tax_rate:.1f}%")

c4.metric("Nettó Örökség", f"£{(total_at_death - iht_tax):,.0f}")

st.markdown("### 🔍 Stratégiai Elemzés")
col_a, col_b = st.columns(2)
with col_a:
    st_p_m = state_p_annual / 12
    proj_net = calculate_net(gross_sipp_meltdown, st_p_m)
    zsebbe = min(proj_net, monthly_living_cost)
    isa_ba = max(0, proj_net - monthly_living_cost)
    st.write(f"**Jövedelem-megosztás a nyugdíj alatt:**")
    st.write(f"- Tervezett havi nettó: £{proj_net:,.0f}")
    st.write(f"- Ebből **£{zsebbe:,.0f}** megy megélhetésre, a maradék **£{isa_ba:,.0f}** az **{trust_label}** számlára.")
    st.write(f"- A kifizetési szakaszban a HMRC-nek összesen **£{total_tax_paid:,.0f}** jövedelemadót fizetsz ki.")

with col_b:
    idx_ret = int((drawdown_start_age-current_age)*12)
    val_at_ret = trust_vals[idx_ret] if idx_ret < len(trust_vals) else trust_vals[-1]
    w_rate = (monthly_living_cost * 12 / max(1, val_at_ret)) * 100
    if w_rate > 4.0: st.warning(f"⚠️ A {w_rate:.1f}%-os kivételi ráta magasabb az Alkotmányos 4%-nál.")
    else: st.success(f"✅ A {w_rate:.1f}%-os kivételi ráta fenntartható.")
