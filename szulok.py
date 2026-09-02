import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK SIPP-to-HoldCo Strategy", layout="wide", page_icon="🏦")

st.title("🏦 SIPP, Holding és Életmód Tervező")
st.write("Ebben a verzióban már te állíthatod be, pontosan mikor induljon el a vagyon átmentése a Holdingba.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 43)

# 1. Befizetési időtartam
max_working_years = 75 - current_age
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, max_working_years, min(14, max_working_years))

st.sidebar.markdown("---")
st.sidebar.header("🔓 SIPP Stratégia Időzítése")

# 2. ÚJ CSÚSZKA: Mikor induljon a SIPP felbontása?
sipp_start_age = st.sidebar.slider(
    "Hány évesen induljon a transzfer? (PCLS + Kifizetés)", 
    min_value=max(57, current_age), # Brit törvények szerint min. 57 (régebben 55)
    max_value=75, 
    value=max(57, current_age)
)

st.sidebar.markdown("---")
st.sidebar.header("💶 Kifizetési Beállítások")

# 3. Mennyit veszünk ki havonta (Bruttó)
gross_monthly = st.sidebar.slider(
    "Havi bruttó kivét a SIPP-ből (£)", 
    min_value=500, max_value=4189, value=4189,
    help="£4,189-ig maradsz a 20%-os adósávban."
)

# Nettó számítás (havi)
pa_monthly = 1047.50 
taxable = max(0, gross_monthly - pa_monthly)
net_monthly_total = pa_monthly + (taxable * 0.8)

# 4. Mennyit költesz el belőle?
monthly_living_cost = st.sidebar.slider(
    "Havi megélhetési igény (Zsebbe) (£)", 
    min_value=500, max_value=10000, value=2500
)

# HoldCo-ba jutó rész kalkulációja
to_holdco_theoretical = max(0, net_monthly_total - monthly_living_cost)

st.sidebar.info(f"""
**Tervezett elosztás ({sipp_start_age} éves kortól):**
- 💰 Nettó jövedelem: £{net_monthly_total:,.0f}
- 🛒 Ebből megélhetés: £{monthly_living_cost:,.0f}
- 📈 Ebből Holdingba megy: £{to_holdco_theoretical:,.0f}
""")

st.sidebar.markdown("---")
st.sidebar.header("📈 Piaci Beállítások")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
market_return = st.sidebar.slider("Vanguard All-World hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# --- SZIMULÁCIÓS LOGIKA ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, holdco_vals = [], [], []
current_sipp, current_holdco = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Hozamok
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 2. Befizetések (amíg tart a cég/munka és 75 év alatt van)
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_cont
        
    # 3. Transzfer és Kifizetés (A beállított kezdőkortól!)
    if age >= sipp_start_age:
        # 25% Tax-Free Lump Sum egyszeri átrakása
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        # Havi SIPP kiürítés (Meltdown)
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly)
            tax = max(0, actual_gross - pa_monthly) * 0.20
            total_tax_paid += tax
            net_from_sipp = actual_gross - tax
            current_sipp -= actual_gross
            
            # Megélhetés vs. Holding feltöltés
            if net_from_sipp >= monthly_living_cost:
                current_holdco += (net_from_sipp - monthly_living_cost)
            else:
                # Ha a SIPP nettó nem elég, a Holdingból pótoljuk
                shortfall = monthly_living_cost - net_from_sipp
                current_holdco = max(0, current_holdco - shortfall)
            
            if current_sipp <= 0.1: 
                sipp_emptied_age = age
                current_sipp = 0
        else:
            # SIPP elfogyott, a teljes megélhetés a Holdingot terheli
            current_holdco = max(0, current_holdco - monthly_living_cost)

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- VIZUALIZÁCIÓ ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 Stratégia: {sipp_start_age} éves kezdés | SIPP ürítés: {emptied_text}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Adóköteles)', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=550, hovermode="x unified")

# Jelöljük a kezdő életkort és a 75-ös határt
fig.add_vline(x=sipp_start_age, line_dash="dot", line_color="green", annotation_text="START")
fig.add_vline(x=75, line_dash="dash", line_color="red")

st.plotly_chart(fig, use_container_width=True)

# KPI-k
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"HoldCo vagyon {sipp_start_age} évesen", f"£{holdco_vals[int((sipp_start_age-current_age)*12)]:,.0f}")
c2.metric("SIPP ürítési kor", emptied_text)
c3.metric("Összes befizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.success(f"""
**Mi történik a modellben?**
- **{sipp_start_age} éves korig:** A SIPP-ed zavartalanul hízik a befizetésekből és a Vanguard hozamaiból.
- **{sipp_start_age} évesen:** Egyetlen gombnyomással átrakod a SIPP-ed 25%-át a Holdingba (adómentesen).
- **Utána:** Megkezded a havi £{gross_monthly:,.0f} bruttó kivétet, amiből fenntartod az életmódodat, a maradékot pedig a Holdingba pumpálod.
""")
