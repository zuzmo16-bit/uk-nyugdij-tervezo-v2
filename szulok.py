import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK Örökség & Nyugdíj Tervező", layout="wide", page_icon="🇬🇧")

st.title("🇬🇧 Komplett UK Nyugdíj, Örökség & Vállalkozói Adóoptimalizáló")
st.write("Ez a szimulátor a SIPP (nyugdíj) és ISA (adómentes megtakarítás) kombinációját modellezi, figyelembe véve a brit adószabályokat.")

# 🎛️ STRATÉGIA KIVÁLASZTÁSA
st.sidebar.markdown("## ⚙️ Felhasználói Profil")
user_mode = st.sidebar.radio(
    "Válaszd ki a státuszodat:",
    ("Sima alkalmazott (Szülők mintája)", "Céges igazgató / Vállalkozó")
)

st.sidebar.markdown("---")
st.sidebar.header("📌 Életkor és Időtáv")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 90, 43 if user_mode == "Céges igazgató / Vállalkozó" else 66)
working_years = st.sidebar.slider("Hány évig dolgozol / működik még a cég?", 0, 50, 14 if user_mode == "Céges igazgató / Vállalkozó" else 2)
target_age = 100 

# 💰 RUGALMAS KIFIZETÉSI BEÁLLÍTÁSOK
st.sidebar.markdown("---")
st.sidebar.header("🔓 Nyugdíj Kifizetési Stratégia")

# 1. Egyszeri adómentes rész (PCLS - Pension Commencement Lump Sum)
st.sidebar.subheader("💵 Adómentes kifizetés (25% Lump Sum)")
enable_lump_sum = st.sidebar.checkbox("Szeretnék élni az adómentes kivéttel", value=True)
if enable_lump_sum:
    lump_sum_age = st.sidebar.slider("Kivétel életkora (év)", 57, 75, 57, help="A brit törvények szerint jelenleg 57 éves kortól lehet hozzáférni a SIPP-hez.")
    lump_sum_pct = st.sidebar.slider("Kivenni kívánt arány (%)", 1, 25, 25, help="A SIPP egyenleged max 25%-a vehető ki adómentesen.")
else:
    lump_sum_age = 999
    lump_sum_pct = 0

# 2. Havi rendszeres kivétel (Drawdown)
st.sidebar.subheader("💶 Rendszeres havi járadék")
enable_monthly_drawdown = st.sidebar.checkbox("Szeretnék havi járadékot (Income)", value=False)
if enable_monthly_drawdown:
    drawdown_start_age = st.sidebar.slider("Járadék kezdő életkora", 57, 99, 67)
    monthly_drawdown_amount = st.sidebar.number_input("Havi kivétel összege (£/hó)", value=1000, step=100)
else:
    drawdown_start_age = 999
    monthly_drawdown_amount = 0

# VÁLTOZÓK INICIALIZÁLÁSA
monthly_wpp = 0
sipp_monthly_gross = 0
monthly_director_corporate = 0
initial_balance = 0

if user_mode == "Sima alkalmazott (Szülők mintája)":
    st.sidebar.header("🏢 Workplace Pension (WPP)")
    initial_balance = st.sidebar.number_input("Jelenlegi nyugdíj egyenleg (£)", value=0)
    gross_salary = st.sidebar.number_input("Havi bruttó fizetés (£)", value=1000)
    ee_pct = st.sidebar.slider("Saját hozzájárulás (%)", 0, 20, 5)
    er_pct = st.sidebar.slider("Munkáltatói hozzájárulás (%)", 0, 20, 3)
    
    st.sidebar.header("🏹 Vanguard SIPP megtakarítás")
    net_monthly_input = st.sidebar.number_input("Havi extra megtakarítás zsebből (£)", value=100)
    
    monthly_wpp = gross_salary * ((ee_pct + er_pct) / 100)
    sipp_monthly_gross = net_monthly_input * 1.25 # 20% tax relief visszapótlása
else:
    st.sidebar.header("🏢 Igazgatói alapbeállítások")
    initial_balance = st.sidebar.number_input("Induló nyugdíj egyenleg (£)", value=11000)
    monthly_director_corporate = st.sidebar.number_input("Havi CÉGES nyugdíjbefizetés (£)", value=4000, help="100%-ban leírható a társasági adóból.")
    net_monthly_input = st.sidebar.number_input("Havi magán (ISA) megtakarítás (£)", value=0)

st.sidebar.header("📈 Piaci Beállítások")
nominal_return = st.sidebar.slider("Éves piaci hozam (%)", 1.0, 12.0, 7.0)
inflation_rate = st.sidebar.slider("Éves infláció (%)", 0.0, 8.0, 2.5)

# Matematikai számítások
annual_real_return = ((1 + (nominal_return / 100)) / (1 + (inflation_rate / 100))) - 1
monthly_rate = (1 + annual_real_return) ** (1/12) - 1

# Idősoros listák
ins_ages = []
ins_payout_real = []
hybrid_wealth_trajectory = []
sipp_trajectory = []
isa_trajectory = []

# Szimulációs állapot
sim_sipp_balance = initial_balance
sim_isa_balance = 0
working_months = working_years * 12
total_months = (target_age - current_age) * 12
pcls_taken = False
final_pcls_amount = 0
gold_cross_age = None

# SZIMULÁCIÓ FUTTATÁSA
for m in range(total_months + 1):
    age_at_m = current_age + (m / 12)
    ins_ages.append(age_at_m)
    
    # Életbiztosítás reálértéke (példa fix £30k-val)
    real_payout = 30000 / ((1 + (inflation_rate/100)) ** (m / 12))
    ins_payout_real.append(real_payout)
    
    # 1. HOZAMOK HOZZÁADÁSA
    sim_sipp_balance *= (1 + monthly_rate)
    sim_isa_balance *= (1 + monthly_rate)
    
    # 2. BEFIZETÉSEK (csak amíg dolgozik)
    if m <= working_months:
        if user_mode == "Sima alkalmazott (Szülők mintája)":
            sim_sipp_balance += (monthly_wpp + sipp_monthly_gross)
        else:
            sim_sipp_balance += monthly_director_corporate
            sim_isa_balance += net_monthly_input
            
    # 3. %-OS ADÓMENTES KIFIZETÉS (PCLS)
    if enable_lump_sum and age_at_m >= lump_sum_age and not pcls_taken:
        lump_sum_value = sim_sipp_balance * (lump_sum_pct / 100)
        sim_sipp_balance -= lump_sum_value
        sim_isa_balance += lump_sum_value  # Átkerül az adómentes ISA-ba
        pcls_taken = True
        final_pcls_amount = lump_sum_value

    # 4. HAVI KIFIZETÉSEK (Drawdown)
    if enable_monthly_drawdown and age_at_m >= drawdown_start_age:
        # Először az ISA-ból költünk (mert az adómentes), utána a SIPP-ből
        if sim_isa_balance >= monthly_drawdown_amount:
            sim_isa_balance -= monthly_drawdown_amount
        else:
            rem = monthly_drawdown_amount - sim_isa_balance
            sim_isa_balance = 0
            sim_sipp_balance = max(0, sim_sipp_balance - rem)

    # Adatok mentése
    current_total = sim_sipp_balance + sim_isa_balance
    hybrid_wealth_trajectory.append(current_total)
    sipp_trajectory.append(sim_sipp_balance)
    isa_trajectory.append(sim_isa_balance)
    
    # Aranykereszt figyelés
    if gold_cross_age is None and current_total >= real_payout:
        gold_cross_age = age_at_m

# --- MEGJELENÍTÉS ---

# KPI-k
st.markdown("### 📊 Eredmények Összegzése")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Várható vagyon 100 évesen", f"£{hybrid_wealth_trajectory[-1]:,.0f}")
c2.metric("SIPP egyenleg (Nyugdíj)", f"£{sim_sipp_balance:,.0f}")
c3.metric("ISA egyenleg (Adómentes)", f"£{sim_isa_balance:,.0f}")
if gold_cross_age:
    c4.success(f"⭐ Önellátó: {gold_cross_age:.1f} év")
else:
    c4.warning("Nincs 'Aranykereszt'")

if pcls_taken:
    st.info(f"ℹ️ **PCLS (Tax-free lump sum) esemény:** {lump_sum_age} évesen £{final_pcls_amount:,.0f} összeget csoportosítottál át az adómentes keretbe.")

if user_mode == "Céges igazgató / Vállalkozó":
    total_corp_tax_saved = (monthly_director_corporate * working_months) * 0.25
    st.success(f"💰 **Adómegtakarítás:** A céged kb. £{total_corp_tax_saved:,.2f} Társasági Adót (Corporation Tax) spórol meg ezzel a stratégiával.")

# GRAFIKON
st.markdown("---")
st.header("📈 Vagyon Alakulása vs. Biztosítás")

fig = go.Figure()

# Összesített vagyon
fig.add_trace(go.Scatter(
    x=ins_ages, y=hybrid_wealth_trajectory,
    mode='lines', name='Teljes nettó vagyon (Reálérték)',
    line=dict(color='royalblue', width=4)
))

# SIPP rész
fig.add_trace(go.Scatter(
    x=ins_ages, y=sipp_trajectory,
    mode='lines', name='Ebből SIPP (Adóköteles)',
    line=dict(color='lightblue', width=2, dash='dot')
))

# ISA rész
fig.add_trace(go.Scatter(
    x=ins_ages, y=isa_trajectory,
    mode='lines', name='Ebből ISA (Adómentes)',
    line=dict(color='lightgreen', width=2, dash='dot')
))

# Biztosítás
fig.add_trace(go.Scatter(
    x=ins_ages, y=ins_payout_real,
    mode='lines', name='Életbiztosítás értéke (£30k reálérték)',
    line=dict(color='firebrick', width=2, dash='dash')
))

fig.update_layout(
    xaxis_title="Életkor",
    yaxis_title="Vagyon (£)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    height=600,
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True)

st.write("""
**Magyarázat:**
- **SIPP (Nyugdíj):** Itt gyűlik a pénz adókedvezménnyel, de a kivétel (a 25% felett) jövedelemadó-köteles.
- **ISA (Adómentes):** Ide kerül az egyszeri 25%-os kifizetésed. Innen bármikor adómentesen vehetsz ki pénzt.
- **Aranykereszt:** Az a pont, ahol a saját felépített vagyonod reálértéke meghaladja a biztosítási összeget. Innentől a családod öröksége akkor is biztosított, ha már nincs életbiztosításod.
""")
