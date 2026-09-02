import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK SIPP Meltdown Strategy", layout="wide", page_icon="📉")

st.title("📉 SIPP-ből Holdingba: 20%-os Adósáv Optimalizáló")
st.write("Ez a modell a SIPP fokozatos kiürítését és a Holding (HoldCo) feltöltését szimulálja, ügyelve a 20%-os adólimitre.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 56, 43)
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, 40, 14)

st.sidebar.markdown("---")
st.sidebar.header("🔓 Kivételi Stratégia (57+ év)")

# Bruttó kivét csúszka (£4,189-ig)
gross_monthly = st.sidebar.slider(
    "Havi bruttó kivét a SIPP-ből (£)", 
    min_value=500, 
    max_value=4189, 
    value=4189,
    help="£4,189 felett már 40% adót kellene fizetned. Maradjunk ez alatt."
)

# Nettó számítás a menübe
personal_allowance_monthly = 1047.50 
if gross_monthly <= personal_allowance_monthly:
    net_monthly = gross_monthly
else:
    taxable = gross_monthly - personal_allowance_monthly
    net_monthly = personal_allowance_monthly + (taxable * 0.8)

st.sidebar.info(f"**Nettó érték a kezedbe:** £{net_monthly:,.2f} / hó\n\n(Ez kerül át havonta a Holdingba)")

st.sidebar.markdown("---")
st.sidebar.header("💰 SIPP és Piac")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

market_return = st.sidebar.slider("Vanguard All-World hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# --- MATEMATIKAI ALAPOK ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

# --- SZIMULÁCIÓ ---
ages = []
sipp_vals = []
holdco_vals = []
total_tax_paid = 0

current_sipp = initial_sipp
current_holdco = 0
pcls_taken = False
sipp_emptied_age = None

target_age = 100
total_months = (target_age - current_age) * 12

for m in range(total_months + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Piaci hozam hozzáadása
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 2. Befizetési szakasz (57 éves korig)
    if age < 57 and m <= (working_years * 12):
        current_sipp += monthly_cont
        
    # 3. Transzfer szakasz (57 éves kortól)
    if age >= 57:
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly)
            
            if actual_gross <= personal_allowance_monthly:
                tax = 0
            else:
                tax = (actual_gross - personal_allowance_monthly) * 0.20
            
            total_tax_paid += tax
            net_to_holdco = actual_gross - tax
            
            current_sipp -= actual_gross
            current_holdco += net_to_holdco
            
            if current_sipp <= 0.01: # Közelítsük a nullát
                sipp_emptied_age = age
                current_sipp = 0

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS JAVÍTÁSA ---
# Kiszámoljuk a szöveget előre, hogy elkerüljük a ValueError-t
if sipp_emptied_age:
    emptied_text = f"{sipp_emptied_age:.1f} éves"
else:
    emptied_text = "több mint 100 éves"

st.markdown(f"### 📊 SIPP Ürítési Terv: {emptied_text} korra fogy el a SIPP")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo Vanguard portfólió', line=dict(color='gold', width=4)))

fig.update_layout(
    title=f"SIPP likvidálás havi £{gross_monthly} bruttó kivéttel",
    xaxis_title="Életkor",
    yaxis_title="Vagyon (£)",
    height=600,
    hovermode="x unified"
)
fig.add_vline(x=75, line_dash="dash", line_color="red", annotation_text="Cél: 75 év")

st.plotly_chart(fig, use_container_width=True)

# Biztonságos indexelés a KPI-khez
idx_75 = int((75 - current_age) * 12)
if idx_75 >= len(holdco_vals): idx_75 = -1

c1, c2, c3, c4 = st.columns(4)
c1.metric("HoldCo vagyon 75 évesen", f"£{holdco_vals[idx_75]:,.0f}")
c2.metric("SIPP ürítési életkor", emptied_text)
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("HoldCo vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.success(f"""
**A stratégia lényege:**
- A SIPP-ben maradó pénz havonta kamatozik, miközben folyamatosan csapolod.
- A kivételt megállítottuk **£{gross_monthly}**-nál, így csak 20%-os adót fizetsz.
- A Holdingba kerülő nettó **£{net_monthly:,.0f}** azonnal a Vanguardba kerül.
""")

if sipp_emptied_age and sipp_emptied_age > 75:
    st.warning("⚠️ Ezzel a havi összeggel nem érsz a SIPP végére 75 éves korodig. Emelned kellene a havi kivétet, vagy lejjebb vinni a piaci hozam elvárást.")
