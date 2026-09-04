import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Master Edition)")
st.write("Javított hitel- és ISA-dinamika számítás az alkalmazotti profilhoz.")

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
start_sipp, start_aviva, start_trust, start_house = 15000, 5000, 0, 0
working_years, monthly_sipp_user_net, monthly_aviva_total, monthly_sipp_director = 0, 0, 0, 0, 0
active_annual_gross, partner_income = 0, 0

# --- PROFIL SPECIFIKUS ADATOK ---
if user_mode == "Órabéres alkalmazott":
    st.sidebar.header("👷 Alkalmazotti bér")
    hourly_rate = st.sidebar.number_input("Alap órabér (£)", value=19.14)
    hours_per_week = st.sidebar.number_input("Heti alap óraszám", value=40)
    weekend_bonus = st.sidebar.number_input("Hétvégi pótlék (£ / alkalom)", value=53.70)
    weekends_per_year = st.sidebar.slider("Hétvégék száma egy évben", 0, 52, 26)
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)

    st.sidebar.header("👫 Jelzáloghitel (Affordability)")
    mortgage_type = st.sidebar.radio("Hitel konstrukció", ("Solo Mortgage", "Joint Mortgage"))
    partner_income = st.sidebar.number_input("Partner éves bruttó jövedelme (£)", value=30000) if mortgage_type == "Joint Mortgage" else 0
    
    st.sidebar.header("🏢 AVIVA (Workplace Pension)")
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=5000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 4)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 4)
    aviva_return = st.sidebar.slider("AVIVA várható éves hozama (%)", 1.0, 10.0, 4.5)
    
    st.sidebar.header("🏹 Saját SIPP (Vanguard)")
    start_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
    monthly_sipp_user_net = st.sidebar.number_input("Havi saját befizetés (Nettó £)", value=100)
    
    st.sidebar.header("🏠 Ingatlanhitel Paraméterek")
    target_house_value = st.sidebar.number_input("Tervezett ingatlanérték (£)", value=340000)
    mortgage_interest = st.sidebar.slider("Hitel kamatláb (%)", 1.0, 8.0, 4.5)
    mortgage_term = st.sidebar.slider("Hitel futamideje (év)", 5, 25, 18)

    working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, int(75-current_age), 36)
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

# --- SIPP STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP & Kifizetés Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés (Meltdown) kezdete", 57, 75, 72)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 8333)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 3500)

# --- ÁLLAMI NYUGDÍJ ---
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 70)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Ekonomiai Beállítások")
market_return = st.sidebar.slider("Vanguard éves hozam (%)", 1.0, 15.0, 7.5)
inflation = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

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

m_market_rate = ( (1 + market_return/100) / (1 + inflation/100) )**(1/12) - 1
if user_mode == "Órabéres alkalmazott":
    m_aviva_rate = ( (1 + aviva_return/100) / (1 + inflation/100) )**(1/12) - 1
else: m_aviva_rate = 0

# --- SZIMULÁCIÓ ---
ages, sipp_vals, aviva_vals, uk_house_vals, trust_vals, mortgage_debt_vals = [], [], [], [], [], []
current_sipp, current_aviva, current_trust, current_uk_house = start_sipp, start_aviva, start_trust, 0
current_mortgage_debt = 0
pcls_taken, total_tax_paid, total_gross_income_drawdown = False, 0, 0
mortgage_payment = 0
final_pcls_val = 0

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_market_rate)
    current_aviva *= (1 + m_aviva_rate)
    current_trust *= (1 + m_market_rate) # Az ISA is kamatozik!
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetési szakasz (Munka + Hitel hatása az ISA-ra)
    if m <= (working_years * 12):
        current_aviva += monthly_aviva_total
        if user_mode == "Órabéres alkalmazott":
            current_sipp += (monthly_sipp_user_net * 1.25)
            # Fizetés utáni ISA megtakarítás számítás (ha már van hitel és még dolgozik)
            if age < drawdown_start_age:
                # Egyszerűsített havi megtakarítási modell aktív korra
                salary_net = calculate_net(active_annual_gross / 12, 0)
                living_now = 2500 / ((1 + (inflation/100))**(m/12)) # Mai értéken £2500 a jelenlegi living cost
                surplus = salary_net - living_now - (mortgage_payment / ((1 + (inflation/100))**(m/12)))
                if surplus > 0: current_trust += surplus

    # 2. Házvétel (PCLS)
    if not pcls_taken and age >= pcls_age:
        total_p = current_sipp + current_aviva
        pcls_val = total_p * 0.25
        final_pcls_val = pcls_val
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
        
    # 3. Hitel törlesztés
    adj_mortgage_payment = 0
    if current_mortgage_debt > 0:
        interest_m = current_mortgage_debt * (mortgage_interest / 100 / 12)
        principal_m = mortgage_payment - interest_m
        current_mortgage_debt -= principal_m
        adj_mortgage_payment = mortgage_payment / ((1 + (inflation/100))**(m/12)) # Reálértékben a törlesztő
        if current_mortgage_debt < 0: current_mortgage_debt, mortgage_payment = 0, 0
    
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 4. Meltdown & Megélhetés
    if age >= drawdown_start_age:
        total_pension = current_sipp + current_aviva
        if total_pension > 0:
            actual_gross = min(total_pension, gross_sipp_meltdown)
            total_net = calculate_net(actual_gross, st_p_m)
            total_tax_paid += ((actual_gross + st_p_m) - total_net)
            total_gross_income_drawdown += (actual_gross + st_p_m)
            
            ratio = current_sipp / total_pension if total_pension > 0 else 0.5
            current_sipp -= actual_gross * ratio
            current_aviva -= actual_gross * (1 - ratio)
            
            net_after_mortgage = total_net - adj_mortgage_payment
            if net_after_mortgage >= monthly_living_cost:
                current_trust += (net_after_mortgage - monthly_living_cost)
            else:
                current_trust = max(0, current_trust - (monthly_living_cost - net_after_mortgage))
        else:
            net_state = calculate_net(0, st_p_m)
            current_trust = max(0, current_trust - (monthly_living_cost + adj_mortgage_payment - net_state))

    sipp_vals.append(current_sipp)
    aviva_vals.append(current_aviva)
    uk_house_vals.append(current_uk_house)
    trust_vals.append(current_trust)
    mortgage_debt_vals.append(current_mortgage_debt)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='Saját SIPP', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
if user_mode == "Órabéres alkalmazott":
    fig.add_trace(go.Scatter(x=ages, y=aviva_vals, name='AVIVA (Workplace)', mode='lines', line=dict(color='#40E0D0', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(64,224,208,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=uk_house_vals, name='Saját Ingatlan', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))
if max(mortgage_debt_vals) > 0:
    fig.add_trace(go.Scatter(x=ages, y=mortgage_debt_vals, name='Jelzálog tartozás', mode='lines', line=dict(color='firebrick', width=2, dash='dash')))
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name='ISA Vagyon', mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))

fig.update_layout(template="plotly_white", height=650, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- KPI MÉRLEG ---
st.markdown("---")
total_at_death = sipp_vals[-1] + aviva_vals[-1] + uk_house_vals[-1] + trust_vals[-1] - mortgage_debt_vals[-1]
st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")
c2.metric("Összes kifizetett adó (HMRC)", f"£{total_tax_paid:,.0f}")
eff_rate = (total_tax_paid / total_gross_income_drawdown * 100) if total_gross_income_drawdown > 0 else 0
c3.metric("Effektív adókulcs", f"{eff_rate:.1f}%")
c4.metric("Nettó Örökség", f"£{(total_at_death - max(0, (total_at_death-500000)*0.4)):,.0f}")

with st.expander("🔍 Stratégiai Elemzés és Hitel Adatok"):
    st.write(f"- 🏠 **Hitelkeret (4.5x jövedelem):** £{(active_annual_gross + partner_income)*4.5:,.0f}")
    st.write(f"- 💸 **Havi törlesztő (induló):** £{mortgage_payment:,.0f}")
    st.write(f"- 🕒 **Hitel kifutása:** {pcls_age + mortgage_term} éves korra.")
    st.info("Az ISA vagyon azért fogy el gyorsan a végén, mert a SIPP kiürülése után a teljes havi £3,500-at ebből kell fedezni.")
