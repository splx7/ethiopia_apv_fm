"""
Ethiopia Smart APV Nexus Financial Model
=========================================
A production-ready web-based financial model application for the Ethiopia Smart APV Nexus Project.
Replicates Chapter VIII "Financial and Economic Analysis" from the feasibility study.

Technology: Python 3 + Streamlit
Analysis: 20-year horizon, real USD, 10% discount rate
Scope: 2.5 MWp APV + 4 MWh BESS + 500 ha irrigation
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy_financial as npf

# ============================================================
# 1. DATA STRUCTURES AND DEFAULT ASSUMPTIONS
# ============================================================

@dataclass
class TechnicalConfig:
    """Technical configuration parameters for APV site"""
    apv_capacity_mwp: float = 2.5
    bess_capacity_mwh: float = 4.0
    bess_pcs_mw: float = 1.2
    total_area_ha: float = 500.0
    irrigated_area_ha: float = 470.0
    apv_footprint_m2: float = 48200.0
    
    # Energy generation and use (MWh/year)
    pv_generation_mwh: float = 5408.0
    internal_load_mwh: float = 3689.0
    surplus_energy_mwh: float = 2461.3
    
    # Crop production
    crop_revenue_area_ha: float = 404.6
    crop_yield_ton_per_ha: float = 2.47  # ~1,000 tons total
    
    # Post-harvest split
    share_fresh: float = 0.30
    share_storage: float = 0.30
    share_processed: float = 0.40


@dataclass
class CapexInputs:
    """CAPEX breakdown inputs (USD)"""
    # APV system
    apv_capacity_kwp: float = 2500
    apv_unit_cost: float = 900  # USD/kWp
    
    # BESS
    bess_capacity_kwh: float = 4000
    bess_unit_cost: float = 350  # USD/kWh
    
    # Irrigation
    irrigation_area_ha: float = 470
    irrigation_unit_cost: float = 2175  # USD/ha
    
    # Other systems (lump sum)
    cold_storage_processing: float = 300000
    electrical_infra_ems: float = 300000
    civil_works: float = 350000
    
    # Percentages
    engineering_pct: float = 0.05  # % of direct CAPEX
    contingency_pct: float = 0.10  # % of (direct + engineering)
    
    def calculate_total(self) -> Dict[str, float]:
        """Calculate total CAPEX breakdown"""
        apv = self.apv_capacity_kwp * self.apv_unit_cost
        bess = self.bess_capacity_kwh * self.bess_unit_cost
        irrigation = self.irrigation_area_ha * self.irrigation_unit_cost
        
        direct_capex = (apv + bess + irrigation + 
                       self.cold_storage_processing + 
                       self.electrical_infra_ems + 
                       self.civil_works)
        
        engineering = direct_capex * self.engineering_pct
        subtotal = direct_capex + engineering
        contingency = subtotal * self.contingency_pct
        total = subtotal + contingency
        
        return {
            'APV System': apv,
            'BESS': bess,
            'Irrigation System': irrigation,
            'Cold Storage & Processing': self.cold_storage_processing,
            'Electrical Infra & EMS': self.electrical_infra_ems,
            'Civil Works': self.civil_works,
            'Engineering & Design': engineering,
            'Contingency': contingency,
            'Total CAPEX': total
        }


@dataclass
class OpexInputs:
    """Annual OPEX inputs (USD/year)"""
    apv_om: float = 40000
    bess_om: float = 15000
    irrigation_om: float = 40000
    cold_storage_processing_om: float = 25000
    staff_admin: float = 30000
    
    def calculate_total(self) -> float:
        """Calculate total annual OPEX"""
        return (self.apv_om + self.bess_om + self.irrigation_om + 
                self.cold_storage_processing_om + self.staff_admin)


@dataclass
class RevenueInputs:
    """Revenue parameters"""
    # Energy
    surplus_energy_mwh: float = 2461.3
    energy_tariff: float = 0.10  # USD/kWh
    
    # Crop production
    crop_area_ha: float = 404.6
    crop_yield_ton_per_ha: float = 2.47
    
    # Post-harvest shares
    share_fresh: float = 0.30
    share_storage: float = 0.30
    share_processed: float = 0.40
    
    # Prices and costs (USD/kg)
    price_fresh: float = 1.20
    cost_fresh: float = 0.30
    price_storage: float = 1.40
    cost_storage: float = 0.40
    price_processed: float = 2.00
    cost_processed: float = 0.90
    
    # Additional value-added
    other_value_added: float = 40000  # USD/year
    
    def calculate_revenues(self) -> Dict[str, float]:
        """Calculate annual revenues by category"""
        # Energy revenue
        energy_rev = self.surplus_energy_mwh * 1000 * self.energy_tariff
        
        # Crop production
        total_tons = self.crop_area_ha * self.crop_yield_ton_per_ha
        
        tons_fresh = total_tons * self.share_fresh
        tons_storage = total_tons * self.share_storage
        tons_processed = total_tons * self.share_processed
        
        # Net revenues per segment (tons to kg)
        rev_fresh = (tons_fresh * 1000) * (self.price_fresh - self.cost_fresh)
        rev_storage = (tons_storage * 1000) * (self.price_storage - self.cost_storage)
        rev_processed = (tons_processed * 1000) * (self.price_processed - self.cost_processed)
        
        crop_total = rev_fresh + rev_storage + rev_processed
        
        return {
            'Energy Revenue': energy_rev,
            'Fresh Crop Sales': rev_fresh,
            'Stored Crop Sales': rev_storage,
            'Processed Products': rev_processed,
            'Other Value-Added': self.other_value_added,
            'Total Revenue': energy_rev + crop_total + self.other_value_added
        }


@dataclass
class FinancingInputs:
    """Financing structure parameters"""
    equity_share: float = 0.30
    debt_share: float = 0.70
    debt_interest_rate: float = 0.05  # 5% real
    debt_tenor_years: int = 15
    debt_grace_years: int = 3
    corporate_tax_rate: float = 0.30
    tax_holiday_years: int = 5
    discount_rate: float = 0.10
    asset_life_years: int = 20
    salvage_value_pct: float = 0.0
    public_capex_share: float = 0.0  # For PPP models


@dataclass
class DegradationInputs:
    """Technical degradation parameters for PV and BESS"""
    # PV degradation
    pv_annual_degradation_pct: float = 0.005  # 0.5%/year
    pv_useful_lifetime_years: int = 25
    
    # BESS degradation
    bess_annual_degradation_pct: float = 0.02  # 2%/year
    bess_min_soh_pct: float = 0.70  # 70% minimum SOH
    bess_replacement_year: int = 10
    bess_replacement_cost_pct: float = 0.70  # 70% of initial BESS CAPEX
    
    def get_pv_capacity_factor(self, year: int) -> float:
        """Get PV capacity degradation factor for given year (1-indexed)"""
        if year == 0:
            return 1.0
        return (1 - self.pv_annual_degradation_pct) ** (year - 1)
    
    def get_bess_capacity_factor(self, year: int) -> float:
        """Get BESS capacity degradation factor for given year (1-indexed)"""
        if year == 0:
            return 1.0
        
        # Calculate years since last replacement/initial
        years_since_install = year if year < self.bess_replacement_year else (year - self.bess_replacement_year)
        
        factor = (1 - self.bess_annual_degradation_pct) ** (years_since_install - 1) if years_since_install > 0 else 1.0
        return max(factor, self.bess_min_soh_pct)


@dataclass
class ReplacementCapexInputs:
    """Major equipment replacement and overhaul costs"""
    # PV inverters
    inverter_replacement_year: int = 12
    inverter_replacement_cost_pct: float = 0.15  # 15% of PV CAPEX
    
    # Irrigation pumps
    pump_replacement_year: int = 10
    pump_replacement_cost_pct: float = 0.30  # 30% of irrigation CAPEX
    
    # Cold storage
    cold_storage_overhaul_year: int = 12
    cold_storage_overhaul_cost_pct: float = 0.25  # 25% of cold storage CAPEX
    
    # Processing line
    processing_overhaul_year: int = 12
    processing_overhaul_cost_pct: float = 0.25  # 25% of processing CAPEX
    
    # Residual value at end of project
    residual_value_pct: float = 0.10  # 10% of total initial CAPEX
    
    def calculate_year_capex(self, year: int, pv_capex: float, irrigation_capex: float, 
                            cold_storage_capex: float, bess_capex: float, 
                            bess_replacement_cost_pct: float, bess_replacement_year: int,
                            total_initial_capex: float) -> float:
        """Calculate replacement/overhaul CAPEX for a given year"""
        capex = 0.0
        
        # Inverter replacement
        if year == self.inverter_replacement_year:
            capex += pv_capex * self.inverter_replacement_cost_pct
        
        # Pump replacement
        if year == self.pump_replacement_year:
            capex += irrigation_capex * self.pump_replacement_cost_pct
        
        # Cold storage overhaul
        if year == self.cold_storage_overhaul_year:
            capex += cold_storage_capex * self.cold_storage_overhaul_cost_pct
        
        # Processing overhaul (using portion of cold storage CAPEX as proxy)
        if year == self.processing_overhaul_year and year != self.cold_storage_overhaul_year:
            capex += cold_storage_capex * 0.5 * self.processing_overhaul_cost_pct
        
        # BESS replacement
        if year == bess_replacement_year:
            capex += bess_capex * bess_replacement_cost_pct
        
        # Residual value at year 20 (negative CAPEX = cash inflow)
        if year == 20:
            capex -= total_initial_capex * self.residual_value_pct
        
        return capex


@dataclass
class InflationInputs:
    """Inflation and price escalation parameters for Ethiopia"""
    # Analysis mode
    use_nominal_cashflows: bool = True
    
    # General macro
    general_inflation_pct: float = 0.10  # 10%/year
    discount_rate_nominal_pct: float = 0.12  # 12%/year nominal
    discount_rate_real_pct: float = 0.08  # 8%/year real
    
    # Cost-side escalation
    wage_escalation_pct: float = 0.07  # 7%/year
    om_material_escalation_pct: float = 0.05  # 5%/year
    land_lease_escalation_pct: float = 0.03  # 3%/year
    
    # Revenue-side escalation
    electricity_tariff_escalation_pct: float = 0.05  # 5%/year
    crop_price_escalation_pct: float = 0.04  # 4%/year
    processed_product_price_escalation_pct: float = 0.04  # 4%/year
    
    def get_escalation_factor(self, base_rate: float, year: int) -> float:
        """Get escalation factor for given year (1-indexed)"""
        if not self.use_nominal_cashflows or year == 0:
            return 1.0
        return (1 + base_rate) ** (year - 1)
    
    def get_discount_rate(self) -> float:
        """Get appropriate discount rate based on analysis mode"""
        return self.discount_rate_nominal_pct if self.use_nominal_cashflows else self.discount_rate_real_pct


# Business model presets
BUSINESS_MODELS = {
    'Model E (Blended Finance - Default)': {
        'equity_share': 0.30,
        'debt_share': 0.70,
        'debt_interest_rate': 0.05,
        'debt_tenor_years': 15,
        'debt_grace_years': 3,
        'revenue_share_spc': 1.0,
        'description': 'Reference blended-finance case with concessional debt',
        'risk_level': 'Medium',
        'capex_scope': 'Full system',
    },
    'Model A (Fully Private SPC)': {
        'equity_share': 0.30,
        'debt_share': 0.70,
        'debt_interest_rate': 0.16,
        'debt_tenor_years': 10,
        'debt_grace_years': 2,
        'revenue_share_spc': 1.0,
        'description': 'Fully private with commercial debt',
        'risk_level': 'Medium-High',
        'capex_scope': 'Full system',
    },
    'Model B (APV Only - Energy Sales)': {
        'equity_share': 0.40,
        'debt_share': 0.60,
        'debt_interest_rate': 0.16,
        'debt_tenor_years': 10,
        'debt_grace_years': 2,
        'revenue_share_spc': 0.35,  # Energy only
        'description': 'SPC owns APV+BESS only, sells energy',
        'risk_level': 'Low-Medium',
        'capex_scope': 'APV + BESS only',
    },
    'Model C (PPP Hybrid)': {
        'equity_share': 0.25,
        'debt_share': 0.75,
        'debt_interest_rate': 0.10,
        'debt_tenor_years': 15,
        'debt_grace_years': 3,
        'revenue_share_spc': 0.65,  # Partial crop revenue
        'description': 'Public-private partnership with blended finance',
        'risk_level': 'Low-Medium',
        'capex_scope': '60% of full system (40% public)',
        'public_capex_share': 0.40,
    },
    'Model D (Grant-Funded Pilot)': {
        'equity_share': 0.0,
        'debt_share': 0.0,
        'debt_interest_rate': 0.0,
        'debt_tenor_years': 0,
        'debt_grace_years': 0,
        'revenue_share_spc': 1.0,
        'description': 'Fully grant-funded demonstration project',
        'risk_level': 'Low (donor-funded)',
        'capex_scope': 'Full system (grant)',
    },
    'Model F (Cooperative + Anchor Buyer)': {
        'equity_share': 0.20,
        'debt_share': 0.80,
        'debt_interest_rate': 0.05,
        'debt_tenor_years': 15,
        'debt_grace_years': 3,
        'revenue_share_spc': 0.25,  # Most revenue to coop
        'description': 'Cooperative ownership with soft loans',
        'risk_level': 'Low',
        'capex_scope': 'Full system',
    },
    'Model G (Joint SPC - Coop + Private)': {
        'equity_share': 0.30,
        'debt_share': 0.70,
        'debt_interest_rate': 0.06,
        'debt_tenor_years': 15,
        'debt_grace_years': 3,
        'revenue_share_spc': 1.0,
        'description': 'Joint venture SPC (15% coop + 15% private)',
        'risk_level': 'Medium',
        'capex_scope': 'Full system',
    },
}


# ============================================================
# 2. FINANCIAL CALCULATION FUNCTIONS
# ============================================================

def build_debt_schedule(total_capex: float, financing: FinancingInputs, 
                       public_capex_share: float = 0.0) -> pd.DataFrame:
    """
    Build debt repayment schedule
    
    Args:
        total_capex: Total project CAPEX
        financing: Financing parameters
        public_capex_share: Share of CAPEX covered by public/grant funds
        
    Returns:
        DataFrame with annual debt schedule
    """
    # Adjust CAPEX for public share
    spc_capex = total_capex * (1 - public_capex_share)
    debt_amount = spc_capex * financing.debt_share
    
    years = financing.asset_life_years + 1  # 0-20
    schedule = pd.DataFrame({
        'Year': range(years),
        'Beginning_Balance': 0.0,
        'Interest': 0.0,
        'Principal': 0.0,
        'Total_Payment': 0.0,
        'Ending_Balance': 0.0,
    })
    
    if debt_amount == 0 or financing.debt_tenor_years == 0:
        return schedule
    
    # Year 0: draw down debt
    schedule.loc[0, 'Ending_Balance'] = debt_amount
    
    # Calculate annual principal payment after grace period
    repayment_years = financing.debt_tenor_years - financing.debt_grace_years
    if repayment_years > 0:
        annual_principal = debt_amount / repayment_years
    else:
        annual_principal = 0
    
    # Build schedule
    for year in range(1, years):
        schedule.loc[year, 'Beginning_Balance'] = schedule.loc[year-1, 'Ending_Balance']
        
        if year > financing.debt_tenor_years:
            # Debt fully repaid
            continue
            
        balance = schedule.loc[year, 'Beginning_Balance']
        interest = balance * financing.debt_interest_rate
        
        if year <= financing.debt_grace_years:
            # Grace period: interest only
            principal = 0
        else:
            # Repayment period
            principal = min(annual_principal, balance)
        
        schedule.loc[year, 'Interest'] = interest
        schedule.loc[year, 'Principal'] = principal
        schedule.loc[year, 'Total_Payment'] = interest + principal
        schedule.loc[year, 'Ending_Balance'] = balance - principal
    
    return schedule


def calculate_cashflows(capex_breakdown: Dict[str, float],
                       opex_inputs: OpexInputs,
                       revenue_inputs: RevenueInputs,
                       financing: FinancingInputs,
                       degradation: DegradationInputs = None,
                       replacement: ReplacementCapexInputs = None,
                       inflation: InflationInputs = None,
                       public_capex_share: float = 0.0,
                       revenue_share_spc: float = 1.0,
                       pv_generation_base: float = 5408.0) -> pd.DataFrame:
    """
    Calculate annual cash flows and financial metrics with degradation, escalation, and replacement CAPEX
    
    Args:
        capex_breakdown: CAPEX components
        opex_inputs: Operating expense parameters
        revenue_inputs: Revenue parameters
        financing: Financing structure
        degradation: Degradation parameters (optional, defaults applied if None)
        replacement: Replacement CAPEX parameters (optional, defaults applied if None)
        inflation: Inflation/escalation parameters (optional, defaults applied if None)
        public_capex_share: Share of CAPEX from public sources
        revenue_share_spc: Share of revenues retained by SPC
        pv_generation_base: Base year PV generation (MWh)
        
    Returns:
        DataFrame with annual cash flows
    """
    # Apply defaults if not provided
    if degradation is None:
        degradation = DegradationInputs()
    if replacement is None:
        replacement = ReplacementCapexInputs()
    if inflation is None:
        inflation = InflationInputs()
    
    total_capex = capex_breakdown['Total CAPEX']
    spc_capex = total_capex * (1 - public_capex_share)
    
    # Build debt schedule
    debt_schedule = build_debt_schedule(total_capex, financing, public_capex_share)
    
    # Get base year revenues and OPEX (for escalation)
    revenues_base = revenue_inputs.calculate_revenues()
    opex_base = opex_inputs.calculate_total()
    
    # Extract component CAPEX values for replacement calculations
    pv_capex = capex_breakdown['APV System']
    bess_capex = capex_breakdown['BESS']
    irrigation_capex = capex_breakdown['Irrigation System']
    cold_storage_capex = capex_breakdown['Cold Storage & Processing']
    
    # Initialize cash flow DataFrame with additional columns
    years = financing.asset_life_years + 1
    cf = pd.DataFrame({
        'Year': range(years),
        'PV_Energy_MWh': 0.0,
        'BESS_Capacity_MWh': 0.0,
        'Revenue': 0.0,
        'OPEX': 0.0,
        'Replacement_CAPEX': 0.0,
        'EBITDA': 0.0,
        'Depreciation': 0.0,
        'EBIT': 0.0,
        'Interest': 0.0,
        'Taxable_Income': 0.0,
        'Tax': 0.0,
        'Net_Income': 0.0,
        'Debt_Principal': 0.0,
        'FCFF': 0.0,
        'FCFE': 0.0,
        'DSCR': 0.0,
    })
    
    # Year 0: CAPEX investment
    equity_investment = spc_capex * financing.equity_share
    cf.loc[0, 'FCFF'] = -spc_capex
    cf.loc[0, 'FCFE'] = -equity_investment
    cf.loc[0, 'PV_Energy_MWh'] = pv_generation_base
    cf.loc[0, 'BESS_Capacity_MWh'] = revenue_inputs.surplus_energy_mwh / 1000  # Convert MWh
    
    # Operating years (1-20)
    annual_depreciation = spc_capex / financing.asset_life_years
    
    for year in range(1, years):
        # ===== DEGRADATION =====
        # PV energy degradation
        pv_factor = degradation.get_pv_capacity_factor(year)
        pv_energy_year = pv_generation_base * pv_factor
        cf.loc[year, 'PV_Energy_MWh'] = pv_energy_year
        
        # BESS capacity degradation
        bess_factor = degradation.get_bess_capacity_factor(year)
        bess_capacity_year = 4.0 * bess_factor  # Base 4 MWh
        cf.loc[year, 'BESS_Capacity_MWh'] = bess_capacity_year
        
        # Calculate degraded surplus energy (proportional to PV output)
        surplus_energy_year = revenue_inputs.surplus_energy_mwh * pv_factor
        
        # ===== REVENUES (with escalation) =====
        # Energy revenue
        tariff_esc_factor = inflation.get_escalation_factor(
            inflation.electricity_tariff_escalation_pct, year)
        energy_rev = surplus_energy_year * 1000 * revenue_inputs.energy_tariff * tariff_esc_factor
        
        # Crop revenues (also affected by degraded irrigation water availability ~ PV output)
        crop_esc_factor = inflation.get_escalation_factor(
            inflation.crop_price_escalation_pct, year)
        processed_esc_factor = inflation.get_escalation_factor(
            inflation.processed_product_price_escalation_pct, year)
        
        # Scale crop production with slight degradation (assume 90% linked to water, water linked to PV)
        crop_production_factor = 0.1 + 0.9 * pv_factor  # Min 10% even if PV fails
        
        # Calculate base crop revenues
        total_tons = revenue_inputs.crop_area_ha * revenue_inputs.crop_yield_ton_per_ha * crop_production_factor
        tons_fresh = total_tons * revenue_inputs.share_fresh
        tons_storage = total_tons * revenue_inputs.share_storage
        tons_processed = total_tons * revenue_inputs.share_processed
        
        rev_fresh = (tons_fresh * 1000) * (revenue_inputs.price_fresh - revenue_inputs.cost_fresh) * crop_esc_factor
        rev_storage = (tons_storage * 1000) * (revenue_inputs.price_storage - revenue_inputs.cost_storage) * crop_esc_factor
        rev_processed = (tons_processed * 1000) * (revenue_inputs.price_processed - revenue_inputs.cost_processed) * processed_esc_factor
        
        # Other value-added
        other_va = revenue_inputs.other_value_added * crop_esc_factor
        
        total_revenue = (energy_rev + rev_fresh + rev_storage + rev_processed + other_va) * revenue_share_spc
        cf.loc[year, 'Revenue'] = total_revenue
        
        # ===== OPEX (with escalation) =====
        # Categorize OPEX by escalation type
        # Labour-related (staff): wage escalation
        wage_esc_factor = inflation.get_escalation_factor(inflation.wage_escalation_pct, year)
        staff_opex = opex_inputs.staff_admin * wage_esc_factor
        
        # Materials/O&M: material escalation
        material_esc_factor = inflation.get_escalation_factor(inflation.om_material_escalation_pct, year)
        om_opex = (opex_inputs.apv_om + opex_inputs.bess_om + opex_inputs.irrigation_om + 
                  opex_inputs.cold_storage_processing_om) * material_esc_factor
        
        total_opex = staff_opex + om_opex
        cf.loc[year, 'OPEX'] = total_opex
        
        # ===== REPLACEMENT CAPEX =====
        repl_capex = replacement.calculate_year_capex(
            year, pv_capex, irrigation_capex, cold_storage_capex, bess_capex,
            degradation.bess_replacement_cost_pct, degradation.bess_replacement_year,
            total_capex
        )
        cf.loc[year, 'Replacement_CAPEX'] = repl_capex
        
        # ===== FINANCIAL CALCULATIONS =====
        cf.loc[year, 'EBITDA'] = total_revenue - total_opex
        
        # Depreciation and EBIT
        cf.loc[year, 'Depreciation'] = annual_depreciation
        cf.loc[year, 'EBIT'] = cf.loc[year, 'EBITDA'] - annual_depreciation
        
        # Interest
        cf.loc[year, 'Interest'] = debt_schedule.loc[year, 'Interest']
        cf.loc[year, 'Debt_Principal'] = debt_schedule.loc[year, 'Principal']
        
        # Tax
        taxable_income = max(0, cf.loc[year, 'EBIT'] - cf.loc[year, 'Interest'])
        cf.loc[year, 'Taxable_Income'] = taxable_income
        
        if year <= financing.tax_holiday_years:
            cf.loc[year, 'Tax'] = 0
        else:
            cf.loc[year, 'Tax'] = taxable_income * financing.corporate_tax_rate
        
        # Net income
        cf.loc[year, 'Net_Income'] = (cf.loc[year, 'EBIT'] - 
                                      cf.loc[year, 'Interest'] - 
                                      cf.loc[year, 'Tax'])
        
        # Cash flows (subtract replacement CAPEX)
        cf.loc[year, 'FCFF'] = (cf.loc[year, 'EBITDA'] - 
                               cf.loc[year, 'Tax'] - 
                               repl_capex)
        
        cf.loc[year, 'FCFE'] = (cf.loc[year, 'FCFF'] - 
                               cf.loc[year, 'Interest'] - 
                               cf.loc[year, 'Debt_Principal'])
        
        # DSCR
        debt_service = cf.loc[year, 'Interest'] + cf.loc[year, 'Debt_Principal']
        if debt_service > 0:
            cf.loc[year, 'DSCR'] = (cf.loc[year, 'EBITDA'] - cf.loc[year, 'Tax']) / debt_service
    
    return cf


def compute_kpis(cashflows: pd.DataFrame, discount_rate: float = 0.10, 
                inflation: InflationInputs = None) -> Dict[str, float]:
    """
    Compute key performance indicators
    
    Args:
        cashflows: DataFrame with annual cash flows
        discount_rate: Discount rate for NPV (deprecated if inflation provided)
        inflation: Inflation parameters (uses appropriate nominal/real discount rate)
        
    Returns:
        Dictionary of KPIs
    """
    # Use inflation-appropriate discount rate if provided
    if inflation is not None:
        effective_discount_rate = inflation.get_discount_rate()
        analysis_mode = 'Nominal' if inflation.use_nominal_cashflows else 'Real'
    else:
        effective_discount_rate = discount_rate
        analysis_mode = 'Real'
    
    fcff = cashflows['FCFF'].values
    fcfe = cashflows['FCFE'].values
    
    # IRRs
    try:
        project_irr = npf.irr(fcff)
    except:
        project_irr = np.nan
    
    try:
        equity_irr = npf.irr(fcfe)
    except:
        equity_irr = np.nan
    
    # NPVs
    npv_project = npf.npv(effective_discount_rate, fcff)
    npv_equity = npf.npv(effective_discount_rate, fcfe)
    
    # Payback periods
    cum_fcff = np.cumsum(fcff)
    cum_fcfe = np.cumsum(fcfe)
    
    payback_project = np.where(cum_fcff >= 0)[0]
    payback_project = payback_project[0] if len(payback_project) > 0 else np.nan
    
    payback_equity = np.where(cum_fcfe >= 0)[0]
    payback_equity = payback_equity[0] if len(payback_equity) > 0 else np.nan
    
    # DSCR statistics
    dscr_values = cashflows.loc[cashflows['DSCR'] > 0, 'DSCR']
    min_dscr = dscr_values.min() if len(dscr_values) > 0 else np.nan
    avg_dscr = dscr_values.mean() if len(dscr_values) > 0 else np.nan
    
    return {
        'Project IRR': project_irr,
        'Equity IRR': equity_irr,
        'NPV': npv_project,
        'Equity NPV': npv_equity,
        'Payback Period (years)': payback_project,
        'Equity Payback (years)': payback_equity,
        'Min DSCR': min_dscr,
        'Avg DSCR': avg_dscr,
        'Discount Rate': effective_discount_rate,
        'Analysis Mode': analysis_mode,
    }




def calculate_scenario_comparison(base_inputs: Dict,
                                 capex_breakdown: Dict[str, float],
                                 opex_inputs: OpexInputs,
                                 revenue_inputs: RevenueInputs,
                                 financing: FinancingInputs,
                                 degradation: DegradationInputs,
                                 replacement: ReplacementCapexInputs,
                                 inflation: InflationInputs,
                                 public_capex_share: float = 0.0,
                                 revenue_share_spc: float = 1.0,
                                 pv_generation_base: float = 5408.0) -> pd.DataFrame:
    """
    Run scenario comparison: Base / Pessimistic / Optimistic
    
    Args:
        base_inputs: Dict with all base case parameters
        Other args: Base case input objects
        
    Returns:
        DataFrame comparing KPIs across scenarios
    """
    scenarios = {
        'Base Case': {
            'degradation': degradation,
            'inflation': inflation,
        },
        'Pessimistic': {
            'degradation': DegradationInputs(
                pv_annual_degradation_pct=degradation.pv_annual_degradation_pct * 1.4,  # Worse degradation
                bess_annual_degradation_pct=degradation.bess_annual_degradation_pct * 1.3,
                bess_replacement_year=degradation.bess_replacement_year - 2,  # Earlier replacement
            ),
            'inflation': InflationInputs(
                use_nominal_cashflows=inflation.use_nominal_cashflows,
                general_inflation_pct=inflation.general_inflation_pct * 1.2,  # Higher inflation
                discount_rate_nominal_pct=inflation.discount_rate_nominal_pct * 1.15,
                discount_rate_real_pct=inflation.discount_rate_real_pct,
                wage_escalation_pct=inflation.wage_escalation_pct * 1.3,  # Faster cost escalation
                om_material_escalation_pct=inflation.om_material_escalation_pct * 1.4,
                electricity_tariff_escalation_pct=inflation.electricity_tariff_escalation_pct * 0.7,  # Slower revenue growth
                crop_price_escalation_pct=inflation.crop_price_escalation_pct * 0.6,
            ),
        },
        'Optimistic': {
            'degradation': DegradationInputs(
                pv_annual_degradation_pct=degradation.pv_annual_degradation_pct * 0.6,  # Better degradation
                bess_annual_degradation_pct=degradation.bess_annual_degradation_pct * 0.7,
                bess_replacement_year=degradation.bess_replacement_year + 2,  # Later replacement
            ),
            'inflation': InflationInputs(
                use_nominal_cashflows=inflation.use_nominal_cashflows,
                general_inflation_pct=inflation.general_inflation_pct * 0.8,  # Lower inflation
                discount_rate_nominal_pct=inflation.discount_rate_nominal_pct * 0.9,
                discount_rate_real_pct=inflation.discount_rate_real_pct,
                wage_escalation_pct=inflation.wage_escalation_pct * 0.9,  # Slower cost escalation
                om_material_escalation_pct=inflation.om_material_escalation_pct * 0.8,
                electricity_tariff_escalation_pct=inflation.electricity_tariff_escalation_pct * 1.2,  # Faster revenue growth
                crop_price_escalation_pct=inflation.crop_price_escalation_pct * 1.3,
            ),
        },
    }
    
    results = []
    for scenario_name, scenario_params in scenarios.items():
        # Run cash flow model
        cf = calculate_cashflows(
            capex_breakdown, opex_inputs, revenue_inputs, financing,
            scenario_params['degradation'], replacement, scenario_params['inflation'],
            public_capex_share, revenue_share_spc, pv_generation_base
        )
        
        # Compute KPIs
        kpis = compute_kpis(cf, inflation=scenario_params['inflation'])
        
        results.append({
            'Scenario': scenario_name,
            'Project IRR': f"{kpis['Project IRR']*100:.2f}%" if not np.isnan(kpis['Project IRR']) else "N/A",
            'Equity IRR': f"{kpis['Equity IRR']*100:.2f}%" if not np.isnan(kpis['Equity IRR']) else "N/A",
            'NPV ($M)': f"${kpis['NPV']/1e6:.2f}M",
            'Payback (years)': f"{kpis['Payback Period (years)']}" if not np.isnan(kpis['Payback Period (years)']) else "N/A",
            'Min DSCR': f"{kpis['Min DSCR']:.2f}" if not np.isnan(kpis['Min DSCR']) else "N/A",
        })
    
    return pd.DataFrame(results)


def run_sensitivity_analysis(base_capex: Dict[str, float],
                            base_opex: OpexInputs,
                            base_revenue: RevenueInputs,
                            base_financing: FinancingInputs,
                            parameter: str,
                            variations: List[float],
                            degradation: DegradationInputs = None,
                            replacement: ReplacementCapexInputs = None,
                            inflation: InflationInputs = None,
                            public_capex_share: float = 0.0,
                            revenue_share_spc: float = 1.0,
                            pv_generation_base: float = 5408.0) -> pd.DataFrame:
    """
    Run sensitivity analysis on a single parameter
    
    Args:
        base_*: Base case inputs
        parameter: Parameter to vary
        variations: List of variation percentages (e.g., [-0.2, -0.1, 0, 0.1, 0.2])
        degradation: Degradation parameters
        replacement: Replacement CAPEX parameters
        inflation: Inflation parameters
        public_capex_share: Public CAPEX share
        revenue_share_spc: SPC revenue share
        pv_generation_base: Base PV generation
        
    Returns:
        DataFrame with sensitivity results
    """
    # Apply defaults
    if degradation is None:
        degradation = DegradationInputs()
    if replacement is None:
        replacement = ReplacementCapexInputs()
    if inflation is None:
        inflation = InflationInputs()
    
    results = []
    
    for var in variations:
        # Copy base inputs
        capex = base_capex.copy()
        opex = OpexInputs(**base_opex.__dict__)
        revenue = RevenueInputs(**base_revenue.__dict__)
        financing = FinancingInputs(**base_financing.__dict__)
        
        # Apply variation
        if parameter == 'CAPEX':
            capex['Total CAPEX'] *= (1 + var)
        elif parameter == 'OPEX':
            opex.apv_om *= (1 + var)
            opex.bess_om *= (1 + var)
            opex.irrigation_om *= (1 + var)
            opex.cold_storage_processing_om *= (1 + var)
            opex.staff_admin *= (1 + var)
        elif parameter == 'Crop Yield':
            revenue.crop_yield_ton_per_ha *= (1 + var)
        elif parameter == 'Crop Prices':
            revenue.price_fresh *= (1 + var)
            revenue.price_storage *= (1 + var)
            revenue.price_processed *= (1 + var)
        elif parameter == 'Energy Tariff':
            revenue.energy_tariff *= (1 + var)
        elif parameter == 'Interest Rate':
            financing.debt_interest_rate *= (1 + var)
        
        # Calculate cash flows and KPIs
        cf = calculate_cashflows(capex, opex, revenue, financing, 
                                degradation, replacement, inflation,
                                public_capex_share, revenue_share_spc, pv_generation_base)
        kpis = compute_kpis(cf, inflation=inflation)
        
        results.append({
            'Variation': f"{var*100:+.0f}%",
            'Variation_Value': var,
            'Project IRR': kpis['Project IRR'],
            'Equity IRR': kpis['Equity IRR'],
            'NPV': kpis['NPV'],
        })
    
    return pd.DataFrame(results)


# ============================================================
# 3. STREAMLIT UI
# ============================================================

def main():
    """Main Streamlit application"""
    
    # Page configuration
    st.set_page_config(
        page_title="Ethiopia Smart APV Nexus Financial Model",
        page_icon="🌱",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for Google Material Design theme
    st.markdown("""
        <style>
        .main {
            background-color: #fafafa;
        }
        .stMetric {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1976D2;
        }
        h2 {
            color: #424242;
            border-bottom: 2px solid #1976D2;
            padding-bottom: 10px;
        }
        h3 {
            color: #757575;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Logo and Title
    col_logo, col_title = st.columns([1, 4])
    
    with col_logo:
        try:
            st.image("assets/logo_icon.png", width=100)
        except:
            pass  # If logo not found, continue without it
    
    with col_title:
        st.title("🌱 Ethiopia Smart APV Nexus Financial Model")
        st.markdown("**Production-Ready Financial Analysis Tool** | 2.5 MWp APV + 4 MWh BESS + 500 ha Irrigation")
    
    st.markdown("---")
    
    # ============================================================
    # SIDEBAR: Model Selection and Inputs
    # ============================================================
    
    with st.sidebar:
        st.header("⚙️ Model Configuration")
        
        # Business model selection
        st.subheader("1. Business Model")
        selected_model = st.selectbox(
            "Select Business Model",
            options=list(BUSINESS_MODELS.keys()),
            index=0,  # Default to Model E
            help="Pre-configured financing and revenue structures"
        )
        
        model_config = BUSINESS_MODELS[selected_model]
        
        # Display model description
        st.info(f"**{model_config['description']}**\n\n"
               f"Risk Level: {model_config['risk_level']}\n\n"
               f"CAPEX Scope: {model_config['capex_scope']}")
        
        st.markdown("---")
        
        # Technical parameters
        st.subheader("2. Technical Parameters")
        with st.expander("APV & BESS Configuration", expanded=False):
            apv_capacity = st.number_input("APV Capacity (MWp)", value=2.5, step=0.1)
            bess_capacity = st.number_input("BESS Capacity (MWh)", value=4.0, step=0.5)
            pv_generation = st.number_input("Annual PV Generation (MWh)", value=5408.0, step=100.0)
            surplus_energy = st.number_input("Annual Surplus Energy (MWh)", value=2461.3, step=10.0)
        
        with st.expander("Crop Production", expanded=False):
            crop_area = st.number_input("Crop Revenue Area (ha)", value=404.6, step=10.0)
            crop_yield = st.number_input("Crop Yield (tons/ha)", value=2.47, step=0.1)
        
        st.markdown("---")
        
        # CAPEX inputs
        st.subheader("3. CAPEX Inputs")
        with st.expander("CAPEX Components", expanded=False):
            apv_unit_cost = st.number_input("APV Unit Cost (USD/kWp)", value=900, step=50)
            bess_unit_cost = st.number_input("BESS Unit Cost (USD/kWh)", value=350, step=25)
            irr_unit_cost = st.number_input("Irrigation Unit Cost (USD/ha)", value=2175, step=100)
            cold_storage_capex = st.number_input("Cold Storage CAPEX (USD)", value=300000, step=10000)
            electrical_capex = st.number_input("Electrical Infra (USD)", value=300000, step=10000)
            civil_capex = st.number_input("Civil Works (USD)", value=350000, step=10000)
        
        # OPEX inputs
        st.subheader("4. OPEX Inputs (Annual)")
        with st.expander("Operating Expenses", expanded=False):
            apv_om = st.number_input("APV O&M (USD/year)", value=40000, step=1000)
            bess_om = st.number_input("BESS O&M (USD/year)", value=15000, step=1000)
            irr_om = st.number_input("Irrigation O&M (USD/year)", value=40000, step=1000)
            storage_om = st.number_input("Cold Storage O&M (USD/year)", value=25000, step=1000)
            staff_cost = st.number_input("Staff & Admin (USD/year)", value=30000, step=1000)
        
        # Revenue inputs
        st.subheader("5. Revenue Parameters")
        with st.expander("Energy Revenue", expanded=False):
            energy_tariff = st.number_input("Energy Tariff (USD/kWh)", value=0.10, step=0.01, format="%.3f")
        
        with st.expander("Crop Revenue", expanded=False):
            st.markdown("**Post-Harvest Shares**")
            share_fresh = st.slider("Fresh Sales (%)", 0, 100, 30) / 100
            share_storage = st.slider("Stored Sales (%)", 0, 100, 30) / 100
            share_processed = st.slider("Processed (%)", 0, 100, 40) / 100
            
            st.markdown("**Prices (USD/kg)**")
            price_fresh = st.number_input("Fresh Price", value=1.20, step=0.05, format="%.2f")
            price_storage = st.number_input("Storage Price", value=1.40, step=0.05, format="%.2f")
            price_processed = st.number_input("Processed Price", value=2.00, step=0.10, format="%.2f")
            
            st.markdown("**Costs (USD/kg)**")
            cost_fresh = st.number_input("Fresh Cost", value=0.30, step=0.05, format="%.2f")
            cost_storage = st.number_input("Storage Cost", value=0.40, step=0.05, format="%.2f")
            cost_processed = st.number_input("Processed Cost", value=0.90, step=0.05, format="%.2f")
            
            other_va = st.number_input("Other Value-Added (USD/year)", value=40000, step=5000)
        
        # Financing inputs
        st.subheader("6. Financing Structure")
        with st.expander("Financing Parameters", expanded=True):
            equity_share = st.slider("Equity Share (%)", 0, 100, 
                                     int(model_config['equity_share']*100)) / 100
            debt_share = 1 - equity_share
            st.write(f"Debt Share: {debt_share*100:.0f}%")
            
            interest_rate = st.number_input("Debt Interest Rate (% p.a.)", 
                                           value=model_config['debt_interest_rate']*100, 
                                           step=0.5, format="%.2f") / 100
            tenor_years = st.number_input("Debt Tenor (years)", 
                                         value=model_config['debt_tenor_years'], 
                                         step=1)
            grace_years = st.number_input("Grace Period (years)", 
                                         value=model_config['debt_grace_years'], 
                                         step=1)
            
            tax_rate = st.slider("Corporate Tax Rate (%)", 0, 50, 30) / 100
            tax_holiday = st.number_input("Tax Holiday (years)", value=5, step=1)
            
            discount_rate = st.number_input("Discount Rate for NPV (%)", value=10.0, step=0.5) / 100
            
            # Model-specific parameters
            public_capex = model_config.get('public_capex_share', 0.0)
            if public_capex > 0:
                public_capex = st.slider("Public CAPEX Share (%)", 0, 100, 
                                        int(public_capex*100)) / 100
            
            revenue_share = model_config.get('revenue_share_spc', 1.0)
            if revenue_share < 1.0:
                revenue_share = st.slider("SPC Revenue Share (%)", 0, 100, 
                                         int(revenue_share*100)) / 100
        
        st.markdown("---")
        
        # NEW: Technical Degradation inputs
        st.subheader("7. Technical Degradation & Lifetime")
        with st.expander("PV System Degradation", expanded=False):
            pv_degradation = st.number_input(
                "PV Annual Degradation (% /year)", 
                value=0.5, 
                step=0.1, 
                format="%.1f",
                help="Typical crystalline-silicon PV degradation: 0.3–0.7%/year. Accounts for gradual power output loss."
            ) / 100
            pv_lifetime = st.number_input(
                "PV Useful Lifetime (years)", 
                value=25, 
                step=1,
                help="Expected operational lifetime of PV modules (typically 25-30 years)"
            )
        
        with st.expander("BESS Degradation & Replacement", expanded=False):
            bess_degradation = st.number_input(
                "BESS Annual Degradation (%/year)", 
                value=2.0, 
                step=0.1, 
                format="%.1f",
                help="Lithium-ion battery capacity fade: ~2%/year for daily cycling"
            ) / 100
            bess_min_soh = st.slider(
                "Min Acceptable SOH (%)", 
                50, 100, 70,
                help="Minimum State of Health before replacement required (typically 70-80%)"
            ) / 100
            bess_replacement_year = st.number_input(
                "BESS Replacement Year", 
                value=10, 
                min_value=1, 
                max_value=20, 
                step=1,
                help="Year when BESS is replaced (typically 8-12 years)"
            )
            bess_replacement_cost_pct = st.slider(
                "BESS Replacement Cost (% of initial)", 
                30, 100, 70,
                help="Expected cost of replacement as % of initial CAPEX (typically 60-80% due to price declines)"
            ) / 100
        
        st.markdown("---")
        
        # NEW: Replacement CAPEX inputs
        st.subheader("8. Equipment Replacement & Overhaul")
        with st.expander("Major Equipment Replacement", expanded=False):
            st.markdown("**PV Inverters**")
            inverter_repl_year = st.number_input(
                "Inverter Replacement Year", 
                value=12, 
                min_value=1, 
                max_value=20, 
                step=1,
                help="Inverters typically need replacement after 10-15 years"
            )
            inverter_repl_cost_pct = st.slider(
                "Cost (% of PV CAPEX)", 
                5, 30, 15,
                help="Inverters typically 10-20% of total PV system cost"
            ) / 100
            
            st.markdown("**Irrigation Pumps**")
            pump_repl_year = st.number_input(
                "Pump Replacement Year", 
                value=10, 
                min_value=1, 
                max_value=20, 
                step=1,
                help="Irrigation pumps typically need replacement every 8-12 years"
            )
            pump_repl_cost_pct = st.slider(
                "Cost (% of Irrigation CAPEX)", 
                10, 50, 30,
                help="Pumps and motors are major cost component of irrigation system"
            ) / 100
            
            st.markdown("**Cold Storage & Processing Overhaul**")
            cold_storage_overhaul_year = st.number_input(
                "Cold Storage Overhaul Year", 
                value=12, 
                min_value=1, 
                max_value=20, 
                step=1
            )
            cold_storage_overhaul_pct = st.slider(
                "Overhaul Cost (% of initial)", 
                10, 40, 25
            ) / 100
            
            processing_overhaul_year = st.number_input(
                "Processing Line Overhaul Year", 
                value=12, 
                min_value=1, 
                max_value=20, 
                step=1
            )
            processing_overhaul_pct = st.slider(
                "Processing Overhaul Cost (%)", 
                10, 40, 25
            ) / 100
            
            st.markdown("**Residual Value**")
            residual_value_pct = st.slider(
                "Residual Value at Year 20 (% of total CAPEX)", 
                0, 30, 10,
                help="Salvage/scrap value of equipment at end of project (typically 5-15%)"
            ) / 100
        
        st.markdown("---")
        
        # NEW: Inflation & Escalation inputs
        st.subheader("9. Macro-Economics & Escalation (Ethiopia)")
        
        st.markdown("**Analysis Mode**")
        use_nominal = st.toggle(
            "Use Nominal Cash Flows", 
            value=True,
            help="When ON: apply inflation/escalation (nominal terms). When OFF: real terms (constant prices)"
        )
        
        if use_nominal:
            st.info("💡 **Nominal Analysis**: Revenues and costs escalate with inflation. Use nominal discount rate.")
        else:
            st.info("💡 **Real Analysis**: Constant prices. Use real discount rate.")
        
        with st.expander("General Macro Parameters", expanded=False):
            general_inflation = st.number_input(
                "General Inflation (%/year)", 
                value=10.0, 
                step=0.5, 
                format="%.1f",
                help="Ethiopia's recent inflation trend (2020-2024): ~10-30%/year"
            ) / 100
            
            if use_nominal:
                discount_rate_nominal = st.number_input(
                    "Nominal Discount Rate (%/year)", 
                    value=12.0, 
                    step=0.5, 
                    format="%.1f",
                    help="Nominal WACC including inflation (typically real rate + inflation)"
                ) / 100
            else:
                discount_rate_real = st.number_input(
                    "Real Discount Rate (%/year)", 
                    value=8.0, 
                    step=0.5, 
                    format="%.1f",
                    help="Real discount rate (inflation-adjusted)"
                ) / 100
        
        with st.expander("Cost-Side Escalation", expanded=False):
            wage_esc = st.number_input(
                "Wage Escalation (%/year)", 
                value=7.0, 
                step=0.5, 
                format="%.1f",
                help="Annual wage growth (typically general inflation - 2 to + 3%)"
            ) / 100
            material_esc = st.number_input(
                "O&M Material Escalation (%/year)", 
                value=5.0, 
                step=0.5, 
                format="%.1f",
                help="Spare parts, farm inputs, fuel escalation"
            ) / 100
            land_esc = st.number_input(
                "Land Lease Escalation (%/year)", 
                value=3.0, 
                step=0.5, 
                format="%.1f",
                help="Land rental price escalation (if applicable)"
            ) / 100
        
        with st.expander("Revenue-Side Escalation", expanded=False):
            tariff_esc = st.number_input(
                "Electricity Tariff Escalation (%/year)", 
                value=5.0, 
                step=0.5, 
                format="%.1f",
                help="Ethiopian Power Corporation tariff adjustment history: ~3-7%/year"
            ) / 100
            crop_price_esc = st.number_input(
                "Crop Price Escalation (%/year)", 
                value=4.0, 
                step=0.5, 
                format="%.1f",
                help="Agricultural commodity price trends"
            ) / 100
            processed_esc = st.number_input(
                "Processed Product Price Escalation (%/year)", 
                value=4.0, 
                step=0.5, 
                format="%.1f",
                help="Value-added product price escalation"
            ) / 100
    
    # ============================================================
    # MAIN AREA: Calculations and Outputs
    # ============================================================
    
    # Build input objects
    capex_inputs = CapexInputs(
        apv_capacity_kwp=apv_capacity * 1000,
        apv_unit_cost=apv_unit_cost,
        bess_capacity_kwh=bess_capacity * 1000,
        bess_unit_cost=bess_unit_cost,
        irrigation_area_ha=470,
        irrigation_unit_cost=irr_unit_cost,
        cold_storage_processing=cold_storage_capex,
        electrical_infra_ems=electrical_capex,
        civil_works=civil_capex,
    )
    
    opex_inputs = OpexInputs(
        apv_om=apv_om,
        bess_om=bess_om,
        irrigation_om=irr_om,
        cold_storage_processing_om=storage_om,
        staff_admin=staff_cost,
    )
    
    revenue_inputs = RevenueInputs(
        surplus_energy_mwh=surplus_energy,
        energy_tariff=energy_tariff,
        crop_area_ha=crop_area,
        crop_yield_ton_per_ha=crop_yield,
        share_fresh=share_fresh,
        share_storage=share_storage,
        share_processed=share_processed,
        price_fresh=price_fresh,
        cost_fresh=cost_fresh,
        price_storage=price_storage,
        cost_storage=cost_storage,
        price_processed=price_processed,
        cost_processed=cost_processed,
        other_value_added=other_va,
    )
    
    financing_inputs = FinancingInputs(
        equity_share=equity_share,
        debt_share=debt_share,
        debt_interest_rate=interest_rate,
        debt_tenor_years=int(tenor_years),
        debt_grace_years=int(grace_years),
        corporate_tax_rate=tax_rate,
        tax_holiday_years=int(tax_holiday),
        discount_rate=discount_rate,
    )
    
    # NEW: Build degradation inputs
    degradation_inputs = DegradationInputs(
        pv_annual_degradation_pct=pv_degradation,
        pv_useful_lifetime_years=int(pv_lifetime),
        bess_annual_degradation_pct=bess_degradation,
        bess_min_soh_pct=bess_min_soh,
        bess_replacement_year= int(bess_replacement_year),
        bess_replacement_cost_pct=bess_replacement_cost_pct,
    )
    
    # NEW: Build replacement CAPEX inputs
    replacement_inputs = ReplacementCapexInputs(
        inverter_replacement_year=int(inverter_repl_year),
        inverter_replacement_cost_pct=inverter_repl_cost_pct,
        pump_replacement_year=int(pump_repl_year),
        pump_replacement_cost_pct=pump_repl_cost_pct,
        cold_storage_overhaul_year=int(cold_storage_overhaul_year),
        cold_storage_overhaul_cost_pct=cold_storage_overhaul_pct,
        processing_overhaul_year=int(processing_overhaul_year),
        processing_overhaul_cost_pct=processing_overhaul_pct,
        residual_value_pct=residual_value_pct,
    )
    
    # NEW: Build inflation inputs
    inflation_inputs = InflationInputs(
        use_nominal_cashflows=use_nominal,
        general_inflation_pct=general_inflation,
        discount_rate_nominal_pct=discount_rate_nominal if use_nominal else 0.12,
        discount_rate_real_pct=discount_rate_real if not use_nominal else 0.08,
        wage_escalation_pct=wage_esc,
        om_material_escalation_pct=material_esc,
        land_lease_escalation_pct=land_esc,
        electricity_tariff_escalation_pct=tariff_esc,
        crop_price_escalation_pct=crop_price_esc,
        processed_product_price_escalation_pct=processed_esc,
    )
    
    # Calculate with new parameters
    capex_breakdown = capex_inputs.calculate_total()
    revenues_breakdown = revenue_inputs.calculate_revenues()
    cashflows = calculate_cashflows(
        capex_breakdown, opex_inputs, revenue_inputs, financing_inputs,
        degradation_inputs, replacement_inputs, inflation_inputs,
        public_capex, revenue_share, pv_generation
    )
    kpis = compute_kpis(cashflows, inflation=inflation_inputs)
    
    # ============================================================
    # Display Results
    # ============================================================
    
    # Key metrics at top
    st.header("📊 Key Performance Indicators")
    
    # Display analysis mode
    analysis_mode = kpis.get('Analysis Mode', 'Real')
    discount_rate_used = kpis.get('Discount Rate', 0.10)
    
    if analysis_mode == 'Nominal':
        st.info(f"📊 **Analysis Mode: Nominal** (with inflation & escalation) | Discount Rate: {discount_rate_used*100:.1f}%")
    else:
        st.info(f"📊 **Analysis Mode: Real** (constant prices) | Discount Rate: {discount_rate_used*100:.1f}%")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Project IRR", f"{kpis['Project IRR']*100:.2f}%" if not np.isnan(kpis['Project IRR']) else "N/A")
        st.metric("NPV", f"${kpis['NPV']/1e6:.2f}M")
    
    with col2:
        st.metric("Equity IRR", f"{kpis['Equity IRR']*100:.2f}%" if not np.isnan(kpis['Equity IRR']) else "N/A")
        st.metric("Equity NPV", f"${kpis['Equity NPV']/1e6:.2f}M")
    
    with col3:
        st.metric("Payback Period", f"{kpis['Payback Period (years)']} years" 
                 if not np.isnan(kpis['Payback Period (years)']) else "N/A")
        st.metric("Min DSCR", f"{kpis['Min DSCR']:.2f}" if not np.isnan(kpis['Min DSCR']) else "N/A")
    
    with col4:
        st.metric("Total CAPEX", f"${capex_breakdown['Total CAPEX']/1e6:.2f}M")
        total_opex = opex_inputs.calculate_total()
        st.metric("Annual OPEX (Year 1)", f"${total_opex/1e3:.0f}k")
    
    st.markdown("---")
    
    # Assumptions Summary
    st.header("📋 Model Assumptions Summary")
    
    tab1, tab2, tab3 = st.tabs(["CAPEX Breakdown", "Revenue Breakdown", "Financing Structure"])
    
    with tab1:
        capex_df = pd.DataFrame({
            'Component': list(capex_breakdown.keys()),
            'Amount (USD)': [f"${v:,.0f}" for v in capex_breakdown.values()],
            'Share (%)': [f"{v/capex_breakdown['Total CAPEX']*100:.1f}%" 
                         for v in capex_breakdown.values()]
        })
        st.dataframe(capex_df, use_container_width=True, hide_index=True)
        
        # Pie chart
        fig, ax = plt.subplots(figsize=(8, 6))
        colors = plt.cm.Set3(range(len(capex_breakdown)-1))
        ax.pie([v for k, v in capex_breakdown.items() if k != 'Total CAPEX'],
               labels=[k for k in capex_breakdown.keys() if k != 'Total CAPEX'],
               autopct='%1.1f%%',
               colors=colors,
               startangle=90)
        ax.set_title('CAPEX Breakdown')
        st.pyplot(fig)
    
    with tab2:
        rev_df = pd.DataFrame({
            'Revenue Source': list(revenues_breakdown.keys()),
            'Annual Amount (USD)': [f"${v:,.0f}" for v in revenues_breakdown.values()],
            'Share (%)': [f"{v/revenues_breakdown['Total Revenue']*100:.1f}%" 
                         for v in revenues_breakdown.values()]
        })
        st.dataframe(rev_df, use_container_width=True, hide_index=True)
        
        # Bar chart
        fig, ax = plt.subplots(figsize=(10, 6))
        rev_items = {k: v for k, v in revenues_breakdown.items() if k != 'Total Revenue'}
        ax.barh(list(rev_items.keys()), list(rev_items.values()), color='#1976D2')
        ax.set_xlabel('Annual Revenue (USD)')
        ax.set_title('Revenue Breakdown')
        ax.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with tab3:
        spc_capex = capex_breakdown['Total CAPEX'] * (1 - public_capex)
        equity_amt = spc_capex * equity_share
        debt_amt = spc_capex * debt_share
        
        fin_summary = {
            'Total Project CAPEX': f"${capex_breakdown['Total CAPEX']:,.0f}",
            'Public/Grant Share': f"${capex_breakdown['Total CAPEX'] * public_capex:,.0f} ({public_capex*100:.0f}%)",
            'SPC CAPEX': f"${spc_capex:,.0f}",
            'Equity Investment': f"${equity_amt:,.0f} ({equity_share*100:.0f}%)",
            'Debt Financing': f"${debt_amt:,.0f} ({debt_share*100:.0f}%)",
            'Debt Interest Rate': f"{interest_rate*100:.2f}% p.a.",
            'Debt Tenor': f"{tenor_years} years",
            'Grace Period': f"{grace_years} years",
            'Tax Rate': f"{tax_rate*100:.0f}%",
            'Tax Holiday': f"{tax_holiday} years",
        }
        
        for k, v in fin_summary.items():
            st.write(f"**{k}:** {v}")
    
    st.markdown("---")
    
    # Annual Cash Flow Table
    st.header("💰 Annual Cash Flow Projections")
    
    # Format cash flow table for display (include new columns)
    cf_display = cashflows[['Year', 'PV_Energy_MWh', 'BESS_Capacity_MWh', 'Revenue', 'OPEX', 
                            'Replacement_CAPEX', 'EBITDA', 'EBIT', 'Interest', 'Tax', 
                            'Net_Income', 'FCFF', 'FCFE', 'DSCR']].copy()
    
    # Format numbers
    for col in cf_display.columns:
        if col not in ['Year', 'DSCR', 'PV_Energy_MWh', 'BESS_Capacity_MWh']:
            cf_display[col] = cf_display[col].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "-")
        elif col == 'DSCR':
            cf_display[col] = cf_display[col].apply(lambda x: f"{x:.2f}" if x > 0 else "-")
        elif col in ['PV_Energy_MWh', 'BESS_Capacity_MWh']:
            cf_display[col] = cf_display[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "-")
    
    st.dataframe(cf_display, use_container_width=True, hide_index=True, height=400)
    
    # Download button
    csv = cashflows.to_csv(index=False)
    st.download_button(
        label="📥 Download Cash Flow Data (CSV)",
        data=csv,
        file_name="ethiopia_apv_cashflows.csv",
        mime="text/csv"
    )
    
    st.markdown("---")
    
    # Charts
    st.header("📈 Financial Performance Charts")
    
    chart_tab1, chart_tab2, chart_tab3, chart_tab4 = st.tabs(["Revenue vs OPEX", "Cash Flows", "DSCR", "Degradation Curves"])
    
    with chart_tab1:
        fig, ax = plt.subplots(figsize=(12, 6))
        years = cashflows['Year'][1:]
        ax.plot(years, cashflows['Revenue'][1:]/1e6, marker='o', label='Revenue', linewidth=2)
        ax.plot(years, cashflows['OPEX'][1:]/1e6, marker='s', label='OPEX', linewidth=2)
        ax.plot(years, cashflows['EBITDA'][1:]/1e6, marker='^', label='EBITDA', linewidth=2)
        ax.set_xlabel('Year')
        ax.set_ylabel('Million USD')
        ax.set_title('Annual Revenue, OPEX, and EBITDA')
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with chart_tab2:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(cashflows['Year'], cashflows['FCFF']/1e6, marker='o', 
               label='FCFF (Project)', linewidth=2, color='#1976D2')
        ax.plot(cashflows['Year'], cashflows['FCFE']/1e6, marker='s', 
               label='FCFE (Equity)', linewidth=2, color='#388E3C')
        ax.axhline(y=0, color='black', linestyle='--', alpha=0.5)
        ax.set_xlabel('Year')
        ax.set_ylabel('Million USD')
        ax.set_title('Free Cash Flows')
        ax.legend()
        ax.grid(alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
    
    with chart_tab3:
        dscr_data = cashflows[cashflows['DSCR'] > 0]
        if len(dscr_data) > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.bar(dscr_data['Year'], dscr_data['DSCR'], color='#FF9800', alpha=0.7)
            ax.axhline(y=1.0, color='red', linestyle='--', label='Min DSCR = 1.0', linewidth=2)
            ax.axhline(y=1.3, color='green', linestyle='--', label='Target DSCR = 1.3', linewidth=2)
            ax.set_xlabel('Year')
            ax.set_ylabel('DSCR')
            ax.set_title('Debt Service Coverage Ratio (DSCR)')
            ax.legend()
            ax.grid(alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("No debt service in this scenario")
    
    # NEW: Degradation curves tab
    with chart_tab4:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # PV degradation
        years_plot = cashflows['Year'][1:]
        ax1.plot(years_plot, cashflows['PV_Energy_MWh'][1:], marker='o', linewidth=2, color='#FF9800')
        ax1.set_xlabel('Year')
        ax1.set_ylabel('PV Energy Output (MWh/year)')
        ax1.set_title(f'PV Energy Degradation ({pv_degradation*100:.1f}%/year)')
        ax1.grid(alpha=0.3)
        
        # BESS degradation & replacement
        ax2.plot(years_plot, cashflows['BESS_Capacity_MWh'][1:], marker='s', linewidth=2, color='#4CAF50')
        ax2.axvline(x=bess_replacement_year, color='red', linestyle='--', 
                    label=f'Replacement (Year {bess_replacement_year})', linewidth=2)
        ax2.set_xlabel('Year')
        ax2.set_ylabel('BESS Capacity (MWh)')
        ax2.set_title(f'BESS Capacity Degradation ({bess_degradation*100:.1f}%/year)')
        ax2.legend()
        ax2.grid(alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    st.markdown("---")
    
    # Sensitivity Analysis
    st.header("🔍 Sensitivity Analysis")
    
    st.markdown("Analyze how changes in key parameters affect Project IRR")
    
    sens_col1, sens_col2 = st.columns([1, 2])
    
    with sens_col1:
        sens_parameter = st.selectbox(
            "Select Parameter",
            options=['CAPEX', 'OPEX', 'Crop Yield', 'Crop Prices', 'Energy Tariff', 'Interest Rate']
        )
        
        variations = [-0.20, -0.10, 0, 0.10, 0.20]
        
        if st.button("Run Sensitivity Analysis", type="primary"):
            st.session_state['sens_results'] = run_sensitivity_analysis(
                capex_breakdown, opex_inputs, revenue_inputs, financing_inputs,
                sens_parameter, variations,
                degradation_inputs, replacement_inputs, inflation_inputs,
                public_capex, revenue_share, pv_generation
            )
    
    with sens_col2:
        if 'sens_results' in st.session_state:
            sens_df = st.session_state['sens_results']
            
            # Display table
            display_df = sens_df.copy()
            display_df['Project IRR'] = display_df['Project IRR'].apply(
                lambda x: f"{x*100:.2f}%" if not np.isnan(x) else "N/A"
            )
            display_df['Equity IRR'] = display_df['Equity IRR'].apply(
                lambda x: f"{x*100:.2f}%" if not np.isnan(x) else "N/A"
            )
            display_df['NPV'] = display_df['NPV'].apply(
                lambda x: f"${x/1e6:.2f}M" if not np.isnan(x) else "N/A"
            )
            
            st.dataframe(display_df[['Variation', 'Project IRR', 'Equity IRR', 'NPV']], 
                        use_container_width=True, hide_index=True)
            
            # Tornado chart
            fig, ax = plt.subplots(figsize=(10, 6))
            base_irr = sens_df.loc[sens_df['Variation_Value'] == 0, 'Project IRR'].values[0]
            irr_delta = (sens_df['Project IRR'] - base_irr) * 100
            
            colors = ['red' if x < 0 else 'green' for x in irr_delta]
            ax.barh(sens_df['Variation'], irr_delta, color=colors, alpha=0.7)
            ax.axvline(x=0, color='black', linestyle='-', linewidth=1)
            ax.set_xlabel('Change in Project IRR (percentage points)')
            ax.set_ylabel(f'{sens_parameter} Variation')
            ax.set_title(f'Sensitivity of Project IRR to {sens_parameter}')
            ax.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
    
    st.markdown("---")
    
    # NEW: Scenario Comparison
    st.header("📊 Scenario Comparison")
    
    st.markdown("Compare Base / Pessimistic / Optimistic scenarios with varying degradation and escalation assumptions")
    
    if st.button("Run Scenario Analysis", type="primary"):
        scenario_results = calculate_scenario_comparison(
            {}, capex_breakdown, opex_inputs, revenue_inputs, financing_inputs,
            degradation_inputs, replacement_inputs, inflation_inputs,
            public_capex, revenue_share, pv_generation
        )
        st.session_state['scenario_results'] = scenario_results
    
    if 'scenario_results' in st.session_state:
        st.dataframe(st.session_state['scenario_results'], use_container_width=True, hide_index=True)
        
        st.markdown("""
        **Scenario Definitions:**
        - **Base Case**: Current input parameters
        - **Pessimistic**: 40% worse PV degradation, 30% worse BESS degradation, 20% higher inflation, 
          30-40% faster cost escalation, 30-40% slower revenue escalation
        - **Optimistic**: 40% better PV degradation, 30% better BESS degradation, 20% lower inflation,
          10-20% slower cost escalation, 20-30% faster revenue escalation
        """)
    
    st.markdown("---")
    
    # Model Notes
    with st.expander("📖 Model Notes & Documentation"):
        st.markdown("""
        ### Ethiopia Smart APV Nexus Financial Model (Advanced)
        
        **Model Calibration:**
        - Based on Ethiopia Smart APV Nexus Feasibility Study, Chapter VIII "Financial and Economic Analysis"
        - Reference site: Abijata/Hawassa region
        - Technical configuration: 2.5 MWp APV + 4 MWh BESS + 500 ha irrigation
        - Analysis horizon: 20 operating years (Year 0 = construction, Years 1-20 = operations)
        - **New**: Includes degradation modeling, replacement CAPEX, and nominal/real analysis modes
        
        **Advanced Features:**
        - **Technical Degradation**: PV output degrades at 0.5%/year, BESS capacity at 2%/year
        - **Equipment Replacement**: Inverters (Year 12), Pumps (Year 10), BESS (Year 10), Overhauls (Year 12)
        - **Inflation/Escalation**: Nominal mode applies separate escalation rates to costs and revenues
        - **Scenario Analysis**: Base/Pessimistic/Optimistic scenarios with varying assumptions
        
        **Analysis Modes:**
        - **Nominal** (default): Costs and revenues escalate with inflation; use nominal discount rate (12%)
        - **Real**: Constant prices; use real discount rate (8%)
        
        **Default Base Case (Model E):**
        - Total CAPEX: ~$5.6 million
        - Financing: 30% equity, 70% debt at 5% interest (concessional)
        - Debt tenor: 15 years with 3-year grace period
        - Annual OPEX: ~$150,000
        - Annual revenues: ~$1.16 million (energy + crops + processing)
        - Discount rate: 10% real
        
        **Revenue Structure:**
        - **Energy**: Surplus electricity sold at $0.10/kWh (~$246k/year)
        - **Crop production**: 404.6 ha generating ~1,000 tons/year
          - 30% sold fresh
          - 30% stored and sold later
          - 40% processed into value-added products
        - **Other value-added**: Coffee processing, grading, packaging (~$40k/year)
        
        **Business Models:**
        - **Model A**: Fully private SPC with commercial debt (16% interest)
        - **Model B**: SPC owns APV only, sells energy to cooperative
        - **Model C**: PPP hybrid with public co-financing
        - **Model D**: Grant-funded demonstration pilot
        - **Model E**: Blended finance with concessional debt (reference case)
        - **Model F**: Cooperative ownership with anchor buyer
        - **Model G**: Joint SPC (cooperative + private investor)
        
        **Key Assumptions:**
        - Corporate tax: 30% with 5-year tax holiday
        - Depreciation: Straight-line over 20 years
        - No working capital requirements modeled
        - No CAPEX reinvestment during operations (conservative)
        - DSCR calculated as (EBITDA - Tax) / (Interest + Principal)
        
        **Usage:**
        1. Select a business model from the sidebar
        2. Adjust technical, financial, and revenue parameters as needed
        3. Review KPIs, cash flows, and charts in main area
        4. Run sensitivity analysis to test key assumptions
        
        **Notes:**
        - All parameters are editable to support scenario analysis
        - Model assumes SPC as vertically integrated owner-operator
        - Energy self-consumption treated as cost-avoiding (embedded in CAPEX/OPEX)
        - Sensitivity analysis shows impact of ±20% changes in key variables
        
        For questions or support, refer to the original feasibility study documentation.
        """)
    
    # Copyright Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #757575; padding: 20px 0; font-size: 0.9em;'>
        <p><strong>Ethiopia Smart APV Nexus Financial Model v2.0</strong></p>
        <p>© 2025 ENVELOPS. All rights reserved.</p>
        <p style='font-size: 0.85em; margin-top: 10px;'>Developed for internal testing and project feasibility analysis.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
