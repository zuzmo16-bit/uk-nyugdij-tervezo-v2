import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK SIPP to HoldCo & Living", layout="wide", page_icon="🏡")

st.title("🏡 SIPP, Holding és Megélhetési Tervező")
st.write("Ez a szimulátor kettéválasztja a SIPP-ből kivett összeget: egy részét elköltöd a mindennapokra, a maradékot pedig befekteted a Holdingba.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 56, 43)
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, 40, 14)

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
    min_value=500, max_value=5000, value=2500,
    help="Ennyit költesz el havonta élelemre, lakásra, életre."
)

# HoldCo-ba jutó rész
to_holdco = max(0, net_monthly_total - monthly_living_cost)

st.sidebar.success(f"""
**Pénz elosztása (havi):**
- łą Nettó jövedelem: £{net_monthly_total:,.0f}
- 🛒 Megélhetés: £{monthly_living_cost:,.0f}
- 📈 Holdingba megy: £{to_holdco:,.0f}
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

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    if age < 57 and m <= (working_years * 12):
        current_sipp += monthly_cont
        
    if age >= 57:
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        # 1. SIPP Ürítés
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly)
            tax = max(0, actual_gross - pa_monthly) * 0.20
            net_from_sipp = actual_gross - tax
            current_sipp -= actual_gross
            
            # Ha a SIPP nettója több mint a megélhetés, a maradék megy a HoldCo-ba
            if net_from_sipp >= monthly_living_cost:
                current_holdco += (net_from_sipp - monthly_living_cost)
            else:
                # Ha a SIPP nem elég a megélhetésre, a Holdingból pótoljuk
                shortfall = monthly_living_cost - net_from_sipp
                current_holdco = max(0, current_holdco - shortfall)
            
            if current_sipp <= 0.1: sipp_emptied_age = age
        else:
            # 2. Ha elfogyott a SIPP, minden a Holdingból megy
            current_holdco = max(0, current_holdco - monthly_living_cost)

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- MEGJELENÍTÉS ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 SIPP ürítés: {emptied_text} | Holding sorsa: {'Kitart' if holdco_vals[-1] > 0 else 'Elfogy'}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Adóköteles)', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=500)
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3 = st.columns(3)
c1.metric("HoldCo vagyon 75 évesen", f"£{holdco_vals[int((75-current_age)*12)]:,.0f}")
c2.metric("Havi elkölthető (Nettó)", f"£{monthly_living_cost:,.0f}")
c3.metric("Örökség 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.info(f"""
**Hogy néz ki az életed 57 évesen?**
1. A SIPP-ből kiveszed a bruttó £{gross_monthly:,.0f}-ot. 
2. Ebből £{monthly_living_cost:,.0f}-ot elköltesz **megélhetésre** (utazás, számlák, étel).
3. A maradék £{to_holdco:,.0f}-ot pedig félreteszed a **Holdingba**, hogy a jövőben is legyen mihez nyúlni.
4. Ha 75 éves korodra elfogy a SIPP, a Holdingban felgyülemlett pénz fogja fizetni a havi £{monthly_living_cost:,.0f} költségedet tovább.
""")
