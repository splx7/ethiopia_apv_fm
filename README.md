# Ethiopia Smart APV Nexus Financial Model

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ethiopia-apv-fm.streamlit.app)

**Repository**: https://github.com/splx7/ethiopia_apv_fm

## 🌱 Overview

Production-ready web-based financial model for the **Ethiopia Smart APV Nexus Project**, featuring advanced technical degradation modeling, equipment replacement scheduling, and comprehensive inflation/escalation analysis over a 20-year horizon.

**Key Features:**
- ✅ 7 business model scenarios (Models A-G)
- ✅ PV & BESS degradation modeling
- ✅ Equipment replacement CAPEX tracking
- ✅ Nominal/Real inflation analysis modes
- ✅ Scenario sensitivity comparison
- ✅ Interactive Streamlit UI with Material Design

## 🚀 Quick Start

### Local Installation

```bash
# Clone repository
git clone https://github.com/splx7/ethiopia_apv_fm.git
cd ethiopia_apv_fm

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Docker (Alternative)

```bash
docker build -t ethiopia-apv-model .
docker run -p 8501:8501 ethiopia-apv-model
```

## 📊 Technical Specifications

- **Project Scope**: 2.5 MWp APV + 4 MWh BESS + 500 ha irrigation
- **Analysis Period**: 20 years (Year 0 = construction, Years 1-20 = operations)
- **Currency**: Real USD with optional nominal analysis
- **Default Discount Rate**: 12% (nominal) / 8% (real)

## 🔧 Advanced Features

### 1. Technical Degradation
- PV annual degradation: 0.5%/year (configurable)
- BESS capacity fade: 2%/year (configurable)
- Automatic replacement scheduling

### 2. Equipment Replacement
- PV Inverters (Year 12, 15% of PV CAPEX)
- Irrigation Pumps (Year 10, 30% of irrigation CAPEX)
- BESS Replacement (Year 10, 70% of initial cost)
- Cold Storage & Processing Overhauls (Year 12)
- Residual Value (Year 20, 10% of total CAPEX)

### 3. Inflation/Escalation
- **Nominal Mode**: Costs and revenues escalate annually
  - Wage escalation: 7%/year
  - Material escalation: 5%/year
  - Energy tariff escalation: 5%/year
  - Crop price escalation: 4%/year
  
- **Real Mode**: Constant prices (original methodology)

### 4. Scenario Analysis
- Base Case (current parameters)
- Pessimistic (worse degradation, higher inflation)
- Optimistic (better degradation, lower inflation)

## 📋 Business Models

| Model | Description | Equity | Debt | Interest | Risk |
|-------|-------------|--------|------|----------|------|
| **Model E** (Default) | Blended Finance | 30% | 70% | 5% | Medium |
| **Model A** | Fully Private SPC | 30% | 70% | 16% | Medium-High |
| **Model B** | APV Only (Energy Sales) | 40% | 60% | 16% | Low-Medium |
| **Model C** | PPP Hybrid | 25% | 75% | 10% | Low-Medium |
| **Model D** | Grant-Funded Pilot | 0% | 0% | 0% | Low |
| **Model F** | Cooperative + Anchor | 20% | 80% | 5% | Low |
| **Model G** | Joint SPC (Coop+Private) | 30% | 70% | 6% | Medium |

## 📖 Documentation

- **Walkthrough**: See `walkthrough.md` for comprehensive feature guide
- **Implementation Plan**: See `implementation_plan.md` for technical details
- **Feasibility Study**: Based on Ethiopia Smart APV Nexus Chapter VIII

## 🛠️ Technology Stack

- **Frontend**: Streamlit 1.28+
- **Computation**: pandas, numpy
- **Financial Calculations**: numpy-financial
- **Visualization**: matplotlib
- **Design**: Google Material Design theme

## 📝 Usage

1. **Select Business Model** from sidebar (Model E recommended for baseline)
2. **Adjust Parameters** in expandable sections:
   - Technical specs (APV, BESS, irrigation)
   - CAPEX & OPEX components
   - Revenue parameters (energy, crops, processing)
   - Financing structure
   - **NEW**: Degradation parameters
   - **NEW**: Equipment replacement schedule
   - **NEW**: Inflation/escalation rates
3. **Review KPIs** in main dashboard
4. **Analyze Cash Flows** in detail table
5. **Explore Charts** (Revenue vs OPEX, Cash Flows, DSCR, Degradation Curves)
6. **Run Sensitivity Analysis** to test parameter variations
7. **Compare Scenarios** (Base/Pessimistic/Optimistic)

## ⚙️ Configuration

All parameters are editable through the Streamlit UI. Key defaults:

### Technical
- APV Capacity: 2.5 MWp
- BESS Capacity: 4 MWh
- Irrigated Area: 470 ha
- PV Degradation: 0.5%/year
- BESS Degradation: 2%/year

### Financial
- Equity Share: 30% (Model E)
- Debt Interest: 5% (Model E, concessional)
- Debt Tenor: 15 years
- Grace Period: 3 years
- Tax Rate: 30% (5-year holiday)

### Economic (Nominal Mode)
- General Inflation: 10%/year
- Wage Escalation: 7%/year
- Material Escalation: 5%/year
- Energy Tariff Escalation: 5%/year
- Crop Price Escalation: 4%/year

## 🔒 Alpha Version - Internal Testing

**Current Status**: Alpha v2.0 (Enhanced with Advanced Features)

**Testing Checklist**:
- [ ] All 7 business models functional
- [ ] Degradation calculations verified
- [ ] Replacement CAPEX scheduling correct
- [ ] Nominal/Real modes produce expected results
- [ ] Scenario comparison working
- [ ] Export functionality tested
- [ ] UI responsive across devices

## 📞 Support & Feedback

For internal testing feedback, please contact the development team.

## 📄 License

Internal use only - Ethiopia Smart APV Nexus Project

---

**Version**: 2.0 (Advanced Features)  
**Last Updated**: 2025-12-03  
**Status**: Alpha Testing
