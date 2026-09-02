import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="UK SIPP Aggressive Meltdown", layout="wide", page_icon="🚀")

st.title("🚀 Aggresszív SIPP-ből Holdingba Átmentés")
st.write("Ha a SIPP túl nagyra nő, a 20%-os adósáv nem elég az ürítéshez. Itt modellezheted a 40-45%-os adó mellett történő kimentést.")

# --- SIDEBAR / MENÜ ---
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 74, 46)

# 1. Befizetési időtartam
max_working_years = 75 - current_age
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, max_working_years, 24)

st.sidebar.markdown("---")
st.sidebar.header("🔓 Stratégia Időzítése")
sipp_start_age = st.sidebar.slider("Hány évesen induljon a transzfer?", 57, 75, 70)

st.sidebar.markdown("---")
st.sidebar.header("💶 Kifizetési Beállítások (Aggresszív)")

# MEGEMELT LIMIT: Akár havi £20,000-et is kivehetsz, hogy ürüljön a SIPP
gross_monthly = st.sidebar.slider(
    "Havi bruttó kivét a SIPP-ből (£)", 
    min_value=1000, max_value=25000, value=12000,
    help="Figyelem! Havi ~£4,189 felett 40%, ~£10,400 felett 45% az adó!"
)

# PONTOS BRIT ADÓKALKULÁTOR (Éves szinteken számolva, majd visszabontva)
def calculate_net(gross_m):
    gross_a = gross_m * 12
    # Personal Allowance (PA) kezelése (£100k felett csökken)
    pa = 12570
    if gross_a > 100000:
        reduction = (gross_a - 100000) / 2
        pa = max(0, pa - reduction)
    
    taxable = max(0, gross_a - pa)
    tax = 0
    
    # 20% sáv (£37,700-ig a PA felett)
    band20 = min(taxable, 37700)
    tax += band20 * 0.20
    
    # 40% sáv (£37,700 - £125,140 között)
    if taxable > 37700:
        band40 = min(taxable - 37700, 125140 - 37700)
        tax += band40 * 0.40
        
    # 45% sáv (£125,140 felett)
    if taxable > 125140:
        band45 = taxable - 125140
        tax += band45 * 0.45
        
    return (gross_a - tax) / 12

net_monthly_total = calculate_net(gross_monthly)

# Megélhetés
monthly_living_cost = st.sidebar.slider("Havi megélhetési igény (£)", 500, 10000, 3500)
to_holdco_theoretical = max(0, net_monthly_total - monthly_living_cost)

st.sidebar.warning(f"""
**Adózási hatás:**
- Bruttó: £{gross_monthly:,.0f}
- Nettó: £{net_monthly_total:,.0f}
- **Effektív adókulcs: {((gross_monthly-net_monthly_total)/gross_monthly)*100:.1f}%**
""")

st.sidebar.markdown("---")
st.sidebar.header("📈 Piaci Paraméterek")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=15000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)
market_return = st.sidebar.slider("Vanguard hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Infláció (%)", 0.0, 8.0, 2.5)

# --- SZIMULÁCIÓ ---
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

ages, sipp_vals, holdco_vals = [], [], []
current_sipp, current_holdco = initial_sipp, 0
pcls_taken, sipp_emptied_age = False, None
total_tax_paid = 0

for m in range((100 - current_age) * 12 + 1):
    age = current_age + (m / 12)
    ages.append(age)
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    if m <= (working_years * 12) and age <= 75:
        current_sipp += monthly_cont
        
    if age >= sipp_start_age:
        if not pcls_taken:
            lump_sum = current_sipp * 0.25
            current_sipp -= lump_sum
            current_holdco += lump_sum
            pcls_taken = True
        
        if current_sipp > 0:
            actual_gross = min(current_sipp, gross_monthly)
            net_from_sipp = calculate_net(actual_gross)
            total_tax_paid += (actual_gross - net_from_sipp)
            current_sipp -= actual_gross
            
            if net_from_sipp >= monthly_living_cost:
                current_holdco += (net_from_sipp - monthly_living_cost)
            else:
                current_holdco = max(0, current_holdco - (monthly_living_cost - net_from_sipp))
            
            if current_sipp <= 100: 
                sipp_emptied_age = age
                current_sipp = 0
        else:
            current_holdco = max(0, current_holdco - monthly_living_cost)

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- VIZUALIZÁCIÓ ---
emptied_text = f"{sipp_emptied_age:.1f} éves" if sipp_emptied_age else "Soha"
st.subheader(f"📊 Aggresszív Stratégia: SIPP ürítés: {emptied_text}")

fig = go.Figure()
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP (Adóköteles)', fill='tozeroy', line=dict(color='lightblue')))
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='HoldCo (Vanguard)', line=dict(color='gold', width=4)))
fig.update_layout(xaxis_title="Életkor", yaxis_title="Vagyon (£)", height=550, hovermode="x unified")
fig.add_vline(x=sipp_start_age, line_dash="dot", line_color="green", annotation_text="Kezdés")
fig.add_vline(x=75, line_dash="dash", line_color="red")
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("SIPP csúcsérték", f"£{max(sipp_vals):,.0f}")
c2.metric("SIPP ürítési kor", emptied_text)
c3.metric("Összes kifizetett adó", f"£{total_tax_paid:,.0f}")
c4.metric("Vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.info(f"""
**Szakértői elemzés:**
Mivel a SIPP-ed {sipp_start_age} évesen eléri a több millió fontot, a havi £4,189-os kivétel nem elegendő az ürítéshez. 
Ahhoz, hogy a pénzt átmentsd a Holdingba, **be kell állítanod egy magasabb (pl. havi £12,000 - £15,000) bruttó kivételt.**
Igen, ilyenkor az állam elviszi a pénz közel 40%-át adóban, de ez az egyetlen módja, hogy a tőke ne a SIPP-ben ragadjon, hanem átkerüljön a te kontrollod alatt lévő Holdingba.
""")
