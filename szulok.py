import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- OLDAL KONFIGURÁCIÓ ---
st.set_page_config(page_title="Perennis Imperial Master", layout="wide", page_icon="🛡️")

st.title("🛡️ Perennis: A Birodalmi Vagyonkezelő (Full Edition)")
st.write("SIPP & AVIVA Meltdown, ISA megtakarítás és alkalmazotti adóoptimalizálás.")

# --- SIDEBAR: FELHASZNÁLÓI PROFIL ---
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Órabéres alkalmazott", "Céges igazgató / Vállalkozó", "Nemzetközi Kivonulás (UK-HU Transzfer)")
)

# --- IDŐTÁV & ÉLETHOSSZ ---
st.sidebar.markdown("---")
st.sidebar.header("📌 Időtáv & Élethossz")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 31)
death_age = st.sidebar.slider("Várható élethossz", 75, 100, 85)

# --- VÁLTOZÓK INICIALIZÁLÁSA ---
start_sipp = 15000
start_aviva = 0 # Új: AVIVA induló
start_trust = 0
start_house = 0
working_years = 0
monthly_sipp_total = 0
monthly_aviva_total = 0
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
    
    working_years = st.sidebar.slider("Hány évig dolgozol még (befizetés)?", 0, int(75-current_age), 36)
    
    active_annual_gross = (hourly_rate * hours_per_week * 52) + (weekend_bonus * weekends_per_year)
    # Az alkalmazotti befizetés az AVIVA-ba megy
    monthly_aviva_total = (active_annual_gross / 12) * ((ee_pct + er_pct) / 100)
    # A SIPP-be jelenleg 0 megy, hacsak nincs külön slider (user korábbi logikája szerint ez külön privát)
    start_aviva = st.sidebar.number_input("Jelenlegi AVIVA egyenleg (£)", value=5000)

elif user_mode == "Céges igazgató / Vállalkozó":
    st.sidebar.header("🏢 Vállalkozói adatok")
    monthly_sipp_total = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
    working_years = st.sidebar.slider("Hány évig fizetsz még be a SIPP-be?", 0, int(75-current_age), 20)
    active_annual_gross = 12570 

# --- SIPP & KIFIZETÉS STRATÉGIA ---
st.sidebar.markdown("---")
st.sidebar.header("🔑 SIPP & Kifizetés Stratégia")
pcls_age = st.sidebar.slider("Házvétel (25% PCLS) életkora", 57, 75, 57)
drawdown_start_age = st.sidebar.slider("Havi kifizetés (Meltdown) kezdete", 57, 75, 70)
gross_sipp_meltdown = st.sidebar.slider("Havi bruttó SIPP+AVIVA kivét (£)", 0, 25000, 5594)
monthly_living_cost = st.sidebar.slider("Havi nettó megélhetési igény (Zsebbe) (£)", 500, 15000, 500)

# --- ÁLLAMI NYUGDÍJ ---
st.sidebar.markdown("---")
st.sidebar.header("🏛️ Állami Nyugdíj")
state_p_age = st.sidebar.slider("Állami nyugdíjkorhatár", 67, 75, 70)
state_p_annual = st.sidebar.number_input("Éves állami nyugdíj (£)", value=11502)

# --- PIACI PARAMÉTEREK ---
st.sidebar.header("📈 Piaci Paraméterek")
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

real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

# --- SZIMULÁCIÓ ---
ages, sipp_vals, aviva_vals, hu_base_vals, uk_house_vals, trust_vals = [], [], [], [], [], []
current_sipp, current_aviva, current_trust, current_uk_house = start_sipp, start_aviva, start_trust, 0
pcls_taken, total_tax_paid = False, 0

for m in range(int((death_age - current_age) * 12) + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # Hozamok
    current_sipp *= (1 + m_rate)
    current_aviva *= (1 + m_rate)
    current_trust *= (1 + m_rate)
    current_uk_house *= (1 + (inflation / 100)) ** (1/12)

    # 1. Befizetések
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_sipp_total
        current_aviva += monthly_aviva_total

    # 2. 25% PCLS (Kombinált poolból)
    if not pcls_taken and age >= pcls_age:
        total_pension_pool = current_sipp + current_aviva
        pcls_val = total_pension_pool * 0.25
        # Arányosan vonjuk le mindkettőből
        ratio_sipp = current_sipp / total_pension_pool if total_pension_pool > 0 else 0.5
        current_sipp -= pcls_val * ratio_sipp
        current_aviva -= pcls_val * (1 - ratio_sipp)
        current_uk_house = pcls_val
        pcls_taken = True
        
    st_p_m = (state_p_annual / 12) if age >= state_p_age else 0
    
    # 4. Meltdown & Megélhetés & ISA (Trust/Holding néven a grafikonon)
    if age >= drawdown_start_age:
        total_pension_balance = current_sipp + current_aviva
        if total_pension_balance > 0:
            actual_gross = min(total_pension_balance, gross_sipp_meltdown)
            net_pension_income = calculate_net(actual_gross, st_p_m) - (st_p_m) # Csak a nyugdíjból jövő nettó
            total_net_all_sources = net_pension_income + st_p_m
            
            total_tax_paid += ((actual_gross + st_p_m) - total_net_all_sources)
            
            # Levonás a poolból arányosan
            ratio_sipp = current_sipp / total_pension_balance if total_pension_balance > 0 else 0.5
            current_sipp -= actual_gross * ratio_sipp
            current_aviva -= actual_gross * (1 - ratio_sipp)
            
            # Pénz elosztása: Megélhetés vs ISA
            # A user kérése: nettó jövedelem a zsebbe csak a megélhetésig, a többi ISA
            if total_net_all_sources >= monthly_living_cost:
                # A "zsebbe" csak a living cost megy, a többi a sárga vonalba (ISA)
                current_trust += (total_net_all_sources - monthly_living_cost)
            else:
                # Ha a nettó nem elég, az ISA-ból pótoljuk
                shortfall = monthly_living_cost - total_net_all_sources
                current_trust = max(0, current_trust - shortfall)
            
            if current_sipp <= 10: current_sipp = 0
            if current_aviva <= 10: current_aviva = 0
        else:
            # Ha elfogyott a nyugdíj, ISA + Állami marad
            current_net_state = calculate_net(0, st_p_m)
            current_trust = max(0, current_trust - (monthly_living_cost - current_net_state))

    sipp_vals.append(current_sipp)
    aviva_vals.append(current_aviva)
    uk_house_vals.append(current_uk_house)
    trust_vals.append(current_trust)

# --- VIZUALIZÁCIÓ ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg (Saját)', mode='lines', line=dict(color='#87CEEB', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(135,206,235,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=aviva_vals, name='AVIVA egyenleg (Workplace)', mode='lines', line=dict(color='#40E0D0', width=2), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(64,224,208,0.3)']])))
fig.add_trace(go.Scatter(x=ages, y=uk_house_vals, name='Ingatlan (PCLS-ből)', mode='lines', line=dict(color='royalblue', width=3), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(65,105,225,0.4)']])))

# Sárga vonal elnevezése profilonként
trust_label = "ISA Vagyon" if user_mode == "Órabéres alkalmazott" else "Perennis Vagyon (Holding)"
fig.add_trace(go.Scatter(x=ages, y=trust_vals, name=trust_label, mode='lines', line=dict(color='gold', width=4), fill='tozeroy', fillgradient=dict(type='vertical', colorscale=[[0, 'rgba(255,255,255,0)'], [1, 'rgba(255,215,0,0.5)']])))

fig.update_layout(template="plotly_white", height=650, hovermode="x unified", legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
st.plotly_chart(fig, use_container_width=True)

# --- STRATÉGIAI ELEMZÉS ---
total_at_death = sipp_vals[-1] + aviva_vals[-1] + uk_house_vals[-1] + trust_vals[-1]
iht_tax = max(0, (total_at_death - 500000) * 0.40) 

st.header(f"📜 Perennis Birodalmi Mérleg ({death_age} évesen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Bruttó Összvagyon", f"£{total_at_death:,.0f}")
c4.metric("Nettó Örökség", f"£{(total_at_death - iht_tax):,.0f}")

# Éves bruttó bér és havi befizetés megjelenítése
if user_mode == "Órabéres alkalmazott":
    c2.metric("Éves bruttó bér", f"£{active_annual_gross:,.0f}")
    c3.metric("Havi AVIVA befizetés", f"£{monthly_aviva_total:,.0f}")
else:
    c2.metric("Havi SIPP befizetés", f"£{monthly_sipp_total:,.0f}")

st.markdown("### 🔍 Stratégiai Elemzés")
col_a, col_b = st.columns(2)

with col_a:
    st.write("**Adóoptimalizálás:**")
    st_p_m = state_p_annual / 12
    proj_net_total = calculate_net(gross_sipp_meltdown, st_p_m)
    
    # Kiszámoljuk a zsebbe kapott és ISA-ba menő részt
    zsebbe = min(proj_net_total, monthly_living_cost)
    isa_ba = max(0, proj_net_total - monthly_living_cost)
    
    st.write(f"- A tervezett havi **£{gross_sipp_meltdown:,.0f}** kombinált nyugdíj kivét után a teljes nettó jövedelmed **£{proj_net_total:,.0f}** lesz.")
    st.write(f"- Ebből **£{zsebbe:,.0f}** fedezi a havi megélhetésedet (zsebbe), a fennmaradó **£{isa_ba:,.0f}** pedig az **ISA számládra** kerül befektetésre.")

with col_b:
    st.write("**Vagyonvédelem & 4% szabály:**")
    # A 4%-ot az ISA + Nyugdíj tőkére vetítjük
    idx_retire = int((drawdown_start_age-current_age)*12)
    check_val = max(trust_vals[-1], trust_vals[idx_retire] if idx_retire < len(trust_vals) else 0)
    withdrawal_rate = (monthly_living_cost * 12 / check_val) * 100 if check_val > 0 else 0
    
    if withdrawal_rate > 4.0:
        st.warning(f"⚠️ A havi költésed ({withdrawal_rate:.1f}%) meghaladja az Alkotmányos 4%-ot az elérhető tőkéhez képest.")
    else:
        st.success(f"✅ A megélhetési rátád ({withdrawal_rate:.1f}%) fenntartható örökséget biztosít.")
