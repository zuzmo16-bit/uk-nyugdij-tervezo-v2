import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK SIPP to HoldCo & Living", layout="wide", page_icon="🏡")

st.title("🏡 SIPP, Holding és Megélhetési Tervező")
st.write("Javított verzió: A befizetések most már 75 éves korig is tarthatnak.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 43)

# Kiszámoljuk, max hány évig fizethet még (75 éves korig)
max_working_years = 75 - current_age
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, max_working_years, min(14, max_working_years))

st.sidebar.markdown("---")
st.sidebar.header("🔓 Kivételi és Megélhetési Stratégia")

# 1. Mennyit veszünk ki a SIPP-ből?
gross_monthly = st.sidebar.slider(
    "Havi bruttó kivét a SIPP-ből (£)", 
    min_value=500, max_value=4189, value=4189,
    help="A 20%-os adósáv teteje."
)

# Nettó számítás
pa_monthly = 1047.50 
taxable = max(0, gross_monthly - pa_monthly)
net_monthly_total = pa_monthly + (taxable * 0.8)

# 2. Mennyit költesz el ebből?
monthly_living_cost = st.sidebar.slider(
    "Havi megélhetési igény (Zsebbe) (£)", 
    min_value=500, max_value=5000, value=2500
)

# HoldCo-ba jutó elméleti rész (amíg tart a SIPP)
to_holdco_theoretical = max(0, net_monthly_total - monthly_living_cost)

st.sidebar.success(f"""
**Pénz elosztása (havi):**
- łą Nettó jövedelem: £{net_monthly_total:,.0f}
- 🛒 Megélhetés: £{monthly_living_cost:,.0f}
- 📈 Holdingba megy: £{to_holdco_theoretical:,.0f}
""")

st.sidebar.markdown("---")
st.sidebar.header("💰 Vagyon és Hozam")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
market_return = st.sidebar.slider("Vanguard All-World hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható infláció (%)", 0.0, 8.0, 2.5)

# --- MATEMATIKA ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, holdco_vals = [], [], []
current_sipp, current_holdco = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Piaci hozam hozzáadása (Mindenre)
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 2. BEFIZETÉSI SZAKASZ (Javítva: 75 éves korig tartatjuk, ha a csúszka engedi)
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_cont
        
    # 3. KIFIZETÉSI SZAKASZ (57 éves kortól)
    if age >= 57:
        # A) 25% Tax-Free Lump Sum (Csak egyszer)
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        # B) SIPP Ürítés és Megélhetés
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly)
            tax = max(0, actual_gross - pa_monthly) * 0.20
            total_tax_paid += tax
            net_from_sipp = actual_gross - tax
            current_sipp -= actual_gross
            
            # Pénz elosztása: Előbb eszünk, a maradék megy a cégbe
            if net_from_sipp >= monthly_living_cost:
                current_holdco += (net_from_sipp - monthly_living_cost)
            else:
                shortfall = monthly_living_cost - net_from_sipp
                current_holdco = max(0, current_holdco - shortfall)
            
            if current_sipp <= 0.1: 
                sipp_emptied_age = age
                current_sipp = 0
        else:
            # SIPP elfogyott, Holdingból élünk
            current_holdco = max(0, current_holdco - monthly_living_cost)

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 Állapot: SIPP ürítés: {emptied_text} | Holding: {'Kitart' if holdco_vals[-1] > 0 else 'Elfogy'}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=500, hovermode="x unified")
fig.add_vline(x=75, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("HoldCo vagyon 75 évesen", f"£{holdco_vals[int((75-current_age)*12)]:,.0f}")
c2.metric("SIPP ürítési kor", emptied_text)
c3.metric("Összes befizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Örökség 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.info(f"""
**Megjegyzés a befizetésekről:** 
A modell most már engedi a SIPP befizetést egészen 75 éves korig. 
Figyelem: Ha 57 éves korod után is fizetsz be, miközben már veszel ki adóköteles jövedelmet, a HMRC az **MPAA** szabály miatt évi £10,000-ra korlátozhatja a befizetési keretedet.
""")
