import streamlit as st
import numpy as np
import plotly.graph_objects as go

# Oldal konfiguráció
st.set_page_config(page_title="SIPP to HoldCo Transfer Strategy", layout="wide", page_icon="🏦")

st.title("🏦 SIPP-ből Holdingba (HoldCo) Átmentési Stratégia")
st.write("A cél: 57 és 75 éves kor között a teljes SIPP vagyont átmozgatni a Holding társaságba a lehető legoptimálisabb adózás mellett.")

# 🎛️ PARAMÉTEREK
st.sidebar.header("📌 Alapadatok")
current_age = st.sidebar.slider("Jelenlegi életkor", 18, 56, 43)
working_years = st.sidebar.slider("Hány évig fizet még a cég a SIPP-be?", 0, 40, 14)
target_age = 100 

st.sidebar.markdown("---")
st.sidebar.header("💰 SIPP és Befizetések")
initial_sipp = st.sidebar.number_input("Jelenlegi SIPP egyenleg (£)", value=11000)
monthly_cont = st.sidebar.number_input("Havi céges SIPP befizetés (£)", value=5000)

st.sidebar.header("📈 Piaci Hozamok (Vanguard)")
market_return = st.sidebar.slider("Várható éves hozam (%)", 1.0, 12.0, 7.5)
inflation = st.sidebar.slider("Várható éves infláció (%)", 0.0, 8.0, 2.5)

# Matek
real_rate = ((1 + (market_return / 100)) / (1 + (inflation / 100))) - 1
m_rate = (1 + real_rate) ** (1/12) - 1

# Szimuláció
ages = []
sipp_vals = []
holdco_vals = []
total_tax_paid = 0

current_sipp = initial_sipp
current_holdco = 0
pcls_taken = False

# Idővonal (hónapokban)
total_months = (target_age - current_age) * 12

for m in range(total_months + 1):
    age = current_age + (m / 12)
    ages.append(age)
    
    # 1. Hozamok (SIPP és HoldCo is pörög a Vanguardban)
    current_sipp *= (1 + m_rate)
    current_holdco *= (1 + m_rate)
    
    # 2. Befizetési szakasz (57 éves korig vagy amíg tart a munka)
    if age < 57 and m <= (working_years * 12):
        current_sipp += monthly_cont
        
    # 3. A NAGY TRANSZFER (57-75 éves kor között)
    if 57 <= age < 75:
        # A) Első lépés: 57 évesen a 25% PCLS kivétele
        if not pcls_taken:
            lump_sum_tax_free = current_sipp * 0.25
            current_sipp -= lump_sum_tax_free
            current_holdco += lump_sum_tax_free
            pcls_taken = True
        
        # B) Második lépés: A maradék 75% kiszívása havi adagokban
        # Kiszámoljuk, mennyi kell havonta, hogy 75 évesre 0 legyen (annuitás szerűen)
        months_left = (75 - age) * 12
        if months_left > 0:
            raw_withdrawal = current_sipp / months_left
            
            # ADÓZÁS (Brit sávos jövedelemadó - havi szintekre bontva)
            # Personal Allowance: ~£1047/hó (0%)
            # Basic Rate: £1047 - £4189 (20%)
            # Higher Rate: £4189+ (40%)
            
            taxable = raw_withdrawal
            monthly_tax = 0
            
            if taxable > 4189:
                monthly_tax += (taxable - 4189) * 0.40
                taxable = 4189
            if taxable > 1047:
                monthly_tax += (taxable - 1047) * 0.20
            
            total_tax_paid += monthly_tax
            net_transfer = raw_withdrawal - monthly_tax
            
            # SIPP csökken, Holding nő a nettóval
            current_sipp -= raw_withdrawal
            current_holdco += net_transfer

    sipp_vals.append(current_sipp)
    holdco_vals.append(current_holdco)

# --- VIZUALIZÁCIÓ ---
st.markdown("### 📊 Az átmentési stratégia látványterve")

fig = go.Figure()
# SIPP vonal - el kell fogynia 75-re
fig.add_trace(go.Scatter(x=ages, y=sipp_vals, name='SIPP egyenleg (Ürítés alatt)', fill='tozeroy', line=dict(color='lightblue')))
# HoldCo vonal - felépül a SIPP-ből
fig.add_trace(go.Scatter(x=ages, y=holdco_vals, name='Holding (HoldCo) vagyon', line=dict(color='gold', width=4)))

fig.update_layout(
    title="SIPP likvidálás és HoldCo feltöltés (57-75 év között)",
    xaxis_title="Életkor",
    yaxis_title="Vagyon (£)",
    xaxis=dict(range=[current_age, 85]), # 85-ig nézzük, hogy látszódjon a végeredmény
    height=600
)
st.plotly_chart(fig, use_container_width=True)

# KPI blokk
c1, c2, c3 = st.columns(3)
c1.metric("Várható HoldCo vagyon 75 évesen", f"£{holdco_vals[int((75-current_age)*12)]:,.0f}")
c2.metric("Összesen kifizetett jövedelemadó", f"£{total_tax_paid:,.0f}", delta_color="inverse")
c3.metric("Holding vagyon 100 évesen", f"£{holdco_vals[-1]:,.0f}")

st.info(f"""
**Hogyan optimalizáltuk az átvitelt?**
1. **57 évesen:** A SIPP negyedét (£{holdco_vals[int((57.1-current_age)*12)] if pcls_taken else 0:,.0f}) adómentesen átmozgattuk.
2. **57-75 év között:** A maradékot havi részletekben vettük ki. 
3. **Adózás:** A modell figyelembe vette, hogy ha túl gyorsan veszed ki (havi £4,189 felett), akkor 40% adót fizetsz. Ezt levontuk, és csak a 'tiszta' pénzt tetted be a Holdingba.
4. **Vanguard hatás:** Mivel a Holdingban a pénz azonnal befektetésre kerül, a 75 éves kori egyenleged jóval magasabb, mint amit összesen kivettél a SIPP-ből!
""")
