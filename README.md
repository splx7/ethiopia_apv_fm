# 🌱 Ethiopia Smart APV Nexus Financial Model

**Production-Ready Financial Analysis Tool for 500 ha APV + Irrigation + Nexus Project**

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.0-FF4B4B.svg)](https://streamlit.io)

## 📊 Overview

Comprehensive 20-year financial model for a Smart Agrivoltaic (APV) Nexus project in Ethiopia, featuring:

- **2.5 MWp APV System** with elevated solar structures
- **4 MWh BESS** for energy storage and load balancing
- **500 ha integrated irrigation** with drip/sprinkler systems
- **Cold storage & processing facilities** for value-added agriculture
- **Minigrid distribution** for rural electrification

## ✨ Key Features

### Financial Modeling
- **Degradation Logic**: PV (0.7%/year), BESS (2.0%/year capacity fade + 0.1%/year efficiency)
- **Replacement CAPEX**: Component-specific lifetimes (inverters, batteries, pumps, processing equipment)
- **Inflation & Escalation**: Real vs. Nominal analysis with Ethiopian macro assumptions
- **IRR Separation**: Clear labels for Project IRR (pre-financing) and Equity IRR (post-debt)
- **Salvage & Decommissioning**: End-of-life value calculations (Year 20)

### Comprehensive CAPEX Breakdown (40+ Line Items)
1. **APV / Power Systems**: PV modules, structures, inverters, BESS, electrical infrastructure, minigrid
2. **Irrigation & Water**: Raw water intake, pumps, rising mains, on-farm distribution (drip/sprinkler)
3. **Agriculture & Nexus**: Cold storage, packhouse, processing equipment, farm machinery
4. **Development & Soft Costs**: Project development, ESIA, engineering, insurance, contingency

### Detailed OPEX Categories
- **Energy System**: PV O&M, BESS maintenance, security, insurance, land lease
- **Irrigation**: Pump maintenance, filter replacement, drip lateral replacement
- **Farm Production**: Labour, seeds, fertilizer, crop protection, packaging, logistics
- **Cold Storage & Processing**: Labour, consumables, equipment maintenance
- **Administration**: Management, office utilities

### Analysis Tools
- **Business Model Presets**: 7 financing scenarios (blended finance, PPP, commercial, cooperative)
- **Scenario Comparison**: Base / Pessimistic / Optimistic with varying degradation and escalation
- **Sensitivity Analysis**: Test impact of CAPEX, OPEX, energy prices, crop yields
- **Real-time Visualization**: Interactive charts for cash flows, DSCR, degradation curves

## 🚀 Installation & Usage

### Prerequisites
```bash
Python 3.9 or higher
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Locally
```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 🛠️ Technology Stack

- **Framework**: Streamlit 1.28.0
- **Data Processing**: Pandas 2.1.0, NumPy 1.24.3
- **Financial Calculations**: NumPy Financial 1.0.0
- **Visualization**: Matplotlib 3.7.2
- **Language**: Python 3.9+

## 📈 Model Structure

### Cash Flow Calculation
```
FCFF (Project) = Revenue - OPEX - CAPEX (initial + replacement)
FCFE (Equity)  = FCFF - Interest - Principal + New Debt
```

### Key Metrics
- Project IRR & NPV (pre-financing)
- Equity IRR & NPV (post-debt)
- Payback Period
- DSCR (Debt Service Coverage Ratio)
- Cumulative Cash Flows

## 📁 Project Structure

```
ethiopia_fm/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .streamlit/
│   └── config.toml       # Streamlit configuration
├── README.md             # This file
└── LICENSE               # License information
```

## 🔒 License & Copyright

**© 2025 All Rights Reserved**

This software and its source code are **proprietary and confidential**. 

### ⚠️ IMPORTANT DISCLAIMER

**UNAUTHORIZED USE, REPRODUCTION, OR DISTRIBUTION IS STRICTLY PROHIBITED.**

This financial model and all associated documentation are the exclusive property of ENVELOPS CO., LTD. No part of this software may be:

- Copied, reproduced, or distributed in any form
- Modified, adapted, or created derivative works from
- Reverse engineered, decompiled, or disassembled
- Used for commercial purposes without explicit written permission

**Permitted Use:**
- Authorized team members with explicit access rights
- Internal business analysis and decision-making only
- Non-commercial evaluation with prior written consent

**Enforcement:**
Unauthorized use will be prosecuted to the fullest extent of applicable copyright and intellectual property laws.

For licensing inquiries or permission requests, contact the repository owner.

---

## 📞 Support

For authorized users only. Contact the ENVELOPS CO., LTD (info@en-velops.com) for access and support.

## 🔐 Security Notice

This repository is **PRIVATE**. Do not share access credentials or repository links with unauthorized parties.

---

**Developed with ❤️ for sustainable agriculture and renewable energy integration in Ethiopia**
