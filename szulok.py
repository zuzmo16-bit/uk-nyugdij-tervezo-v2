import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Full Edition)")
st.write("SIPP Meltdown, Trösztépítés, Alkalmazotti és Vállalkozói adóoptimalizálás.")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás (UK-HU Transzfer)")
)

# --- IDŐTÁV & ÉLETHOSSZ (MINDEN PROFILHOZ) ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 37)
death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)

# --- PROFIL SPECIFIKUS BEÁLLÍTÁSOK ---
start_sipp = 15000
start_trust = 0
start_house = 0
working_years = 0
monthly_contribution_total = 0
active_annual_gross = 0

if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    
    st.sidebar.header("🏹 Nyugdíj hozzájárulás")
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    
    working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, 75-current_age, 20)
    
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)
    monthly_contribution_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    monthly_contribution_total = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
    working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, 75-current_age, 20)
    active_annual_gross = 12570 # Feltételezett alapbér

elif user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    st.sidebar.subheader("💰 Jelenlegi Vagyon")
    start_sipp = st.sidebar.number_input("Összesített SIPP egyenleg (£)", value=1000000)
    start_trust = st.sidebar.number_input("Holding / Tröszt tőke (£)", value=250000)
    # Ez a profil azonnal a kifizetésre fókuszál
    working_years = 0

# --- SIPP STRATÉGIA (VISSZAÁLLÍTVA) ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP & Kifizetés Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés (Meltdown) kezdete", 57, 75, 67 if user_mode != "Nemzetközi Kivonulás (UK-HU Transzfer)" else 53)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP kivét (£)", 0, 25000, 8333)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (£)", 500, 15000, 3500)

# --- ÁLLAMI NYUGDÍJ ---
st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 71)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Piaci Paraméterek")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# --- SSAS LOANBACK (Csak nemzetközi módban) ---
enable_ssas_loan = False
loan_amount = 0
if user_mode == "Nemzetközi Kivonulás (UK-HU Transzfer)":
    st.sidebar.markdown("---")
    st.sidebar.header("🏦 SSAS Finanszírozás")
    enable_ssas_loan = st.sidebar.checkbox("SSAS Loanback mozgósítása? (Max 50%)", value=True)
    loan_amount = (start_sipp * 0.5) if enable_ssas_loan else 0

# --- ADÓ ÉS MATEK ---
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

real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

# --- SZIMULÁCIÓ ---
ages, sipp_vals, hu_base_vals, uk_house_vals, trust_vals = [], [], [], [], []
current_sipp, current_trust, current_uk_house, current_hu_base = start_sipp, start_trust, 0, 0
loan_balance = loan_amount
pcls_taken, total_tax_paid = False, 0

if enable_ssas_loan:
    current_sipp -= loan_amount
    current_hu_base = loan_amount 

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_hu_base *= (1 + (inflation / 100)) ** (1/12)
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetések (amíg aktív)
    if user_mode != "Nemzetközi Kivonulás (UK-HU Transzfer)":
        if m <= (working_years * 12) and age <= 75:
            current_sipp += monthly_contribution_total

    # 2. SSAS Törlesztés vissza a SIPP-be
    if enable_ssas_loan and loan_balance > 0 and m <= 60:
        repayment = loan_amount / 60
        interest = loan_balance * 0.005 
        current_sipp += (repayment + interest)
        loan_balance -= repayment

    # 3. 25% PCLS (Házvétel)
    if not pcls_taken and age >= pcls_age:
        pcls_val = (current_sipp - loan_balance) * 0.25
        current_sipp -= pcls_val
        current_uk_house = pcls_val
        pcls_taken = True
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 4. Meltdown & Megélhetés
    if age >= drawdown_start_age:
        if current_sipp > 0:
            actual_g = min(current_sipp, gross_sipp_meltdown)
            net_income = calculate_net(actual_g, st_p_m)
            total_tax_paid += ((actual_g + st_p_m) - net_income)
            current_sipp -= actual_g
            if net_income >= monthly_living_cost: current_trust += (net_income - monthly_living_cost)
            else: current_trust = max(0, current_trust - (monthly_living_cost - net_income))
            if current_sipp <= 100: current_sipp = 0
        else:
            net_income = calculate_net(0, st_p_m)
            current_trust = max(0, current_trust - (monthly_living_cost - net_income))

    sipp_vals.append(current_sipp + loan_balance)
    hu_base_vals.append(current_hu_base)
    uk_house_vals.append(current_uk_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ (FADING GRADIENTS) ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Bentmaradó 75%)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=hu_base_vals, name='Magyar Perennis Bázis (Hitelből)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=uk_house_vals, name='Saját Ingatlan (PCLS-ből)', mode='lines', line=dict(color='teal', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(0,128,128,0.4)']])))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='Perennis Vagyon (Holding)', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))
fig.update_layout(template="plotly_white", height=650, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- ANALITIKAI MÉRLEG (PROFIL SPECIFIKUS) ---
st.markdown("---")
total_at_death = sipp_vals[-1] + hu_base_vals[-1] + uk_house_vals[-1] + trust_vals[-1]
iht_tax = max(0, (total_at_death - 500000) * 0.40) # Post-2027 rules

st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")

# Profil specifikus KPI-k
if user_mode == "Órabéres alkalmazott":
    c2.metric("Éves bruttó bér", f"£{active_annual_gross:,.0f}")
    c3.metric("Havi SIPP befizetés", f"£{monthly_contribution_total:,.0f}")
elif user_mode == "Céges igazgató / Vállalkozó":
    total_corp_tax_saved = (monthly_contribution_total * working_years * 12) * 0.25
    c2.metric("Megspórolt CT adó", f"£{total_corp_tax_saved:,.0f}")
    c3.metric("Összes befizetett adó", f"£{total_tax_paid:,.0f}")
else:
    c2.metric("Mozgósított SSAS hitel", f"£{loan_amount:,.0f}")
    c3.metric("Kifizetett IHT (Becsült)", f"£{iht_tax:,.0f}")

c4.metric("Nettó Örökség", f"£{(total_at_death - iht_tax):,.0f}")

# --- ELEMZÉSI SZÖVEGEK ---
st.markdown("### 🔍 Stratégiai Elemzés")
col_a, col_b = st.columns(2)

with col_a:
    st.write("**Adóoptimalizálás:**")
    if user_mode == "Órabéres alkalmazott":
        st.write(f"- A te 4%-od és a munkáltatód 4%-a évente £{monthly_contribution_total*12:,.0f} tőkét épít adómentesen.")
    elif user_mode == "Céges igazgató / Vállalkozó":
        st.write(f"- A havi £{monthly_contribution_total:,.0f} céges befizetés közvetlenül csökkenti a Perennis Joinery Studio társasági adóját.")
    st.write(f"- A tervezett havi £{gross_sipp_meltdown:,.0f} SIPP kivét után a nettó jövedelmed £{calculate_net(gross_sipp_meltdown, state_p_annual/12):,.0f} lesz.")

with col_b:
    st.write("**Vagyonvédelem & 4% szabály:**")
    idx_retire = int((drawdown_start_age-current_age)*12)
    check_val = max(trust_vals[-1], trust_vals[idx_retire] if idx_retire < len(trust_vals) else 0)
    withdrawal_rate = (monthly_living_cost * 12 / check_val) * 100 if check_val > 0 else 0
    
    if withdrawal_rate > 4.0:
        st.warning(f"⚠️ A megélhetési rátád ({withdrawal_rate:.1f}%) magasabb az Alkotmányos 4%-nál. A tőke fogyhat.")
    else:
        st.success(f"✅ A megélhetési rátád ({withdrawal_rate:.1f}%) biztonságos, a birodalom fenntartható.")
