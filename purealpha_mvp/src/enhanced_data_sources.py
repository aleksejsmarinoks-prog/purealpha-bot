"""
Enhanced Data Sources - Additional 40 Parameters (FREE)

Adds derived metrics, technical indicators, and cross-correlations
to expand from 31 → 71 parameters without additional cost
"""
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EnhancedDataSources:
    """
    Calculates 40 additional parameters from existing data
    """
    
    def calculate_derived_parameters(self, base_data: Dict) -> Dict:
        """
        Calculate 40 derived parameters from 31 base parameters
        
        Categories:
        - Yield Curve Metrics (5)
        - Volatility Indicators (8)
        - Momentum Indicators (7)
        - Credit Stress Indicators (6)
        - Currency Stress (5)
        - Crypto Metrics (4)
        - Economic Divergence (5)
        
        Total: 40 parameters
        """
        derived = {}
        
        # ============================================
        # CATEGORY 1: YIELD CURVE METRICS (5)
        # ============================================
        
        # 1. Yield Curve Slope (10Y - 2Y)
        if 'treasury_10y' in base_data and 'treasury_2y' in base_data:
            slope = base_data['treasury_10y'] - base_data['treasury_2y']
            derived['yield_curve_slope'] = slope
            logger.info(f"✓ Yield curve slope: {slope:.4f}")
        
        # 2. Yield Curve Steepness (30Y - 2Y)
        if 'treasury_30y' in base_data and 'treasury_2y' in base_data:
            steepness = base_data['treasury_30y'] - base_data['treasury_2y']
            derived['yield_curve_steepness'] = steepness
        
        # 3. Curvature (2*10Y - 2Y - 30Y)
        if all(k in base_data for k in ['treasury_2y', 'treasury_10y', 'treasury_30y']):
            curvature = (2 * base_data['treasury_10y'] 
                        - base_data['treasury_2y'] 
                        - base_data['treasury_30y'])
            derived['yield_curve_curvature'] = curvature
        
        # 4. Inversion Score (negative slope = recession signal)
        if 'yield_curve_slope' in derived:
            # Score: -1 (fully inverted) to +1 (steep)
            inversion_score = np.tanh(derived['yield_curve_slope'] * 2)
            derived['inversion_score'] = inversion_score
        
        # 5. Term Premium (10Y - Fed Funds)
        if 'treasury_10y' in base_data and 'fed_funds_rate' in base_data:
            term_premium = base_data['treasury_10y'] - base_data['fed_funds_rate']
            derived['term_premium'] = term_premium
        
        # ============================================
        # CATEGORY 2: VOLATILITY INDICATORS (8)
        # ============================================
        
        # 6. VIX Regime (low/moderate/high/extreme)
        if 'vix' in base_data:
            vix = base_data['vix']
            if vix < 15:
                derived['vix_regime'] = 0.25  # Low vol
            elif vix < 25:
                derived['vix_regime'] = 0.50  # Moderate
            elif vix < 40:
                derived['vix_regime'] = 0.75  # High
            else:
                derived['vix_regime'] = 1.0   # Extreme
        
        # 7. VIX Normalized (z-score vs historical mean)
        if 'vix' in base_data:
            # Historical: mean ~19, std ~8
            vix_z = (base_data['vix'] - 19) / 8
            derived['vix_zscore'] = vix_z
        
        # 8. Vol-of-Vol Proxy (VIX / SP500 price ratio)
        if 'vix' in base_data and 'sp500' in base_data:
            vol_ratio = base_data['vix'] / (base_data['sp500'] / 100)
            derived['vol_of_vol_proxy'] = vol_ratio
        
        # 9-11. Market-specific volatility proxies
        # Russell 2000 as small-cap risk indicator
        if 'russell_2000' in base_data and 'sp500' in base_data:
            # Small cap underperformance = risk-off
            small_cap_ratio = base_data['russell_2000'] / base_data['sp500']
            derived['small_cap_strength'] = small_cap_ratio
        
        # Nasdaq as tech risk
        if 'nasdaq' in base_data and 'sp500' in base_data:
            tech_ratio = base_data['nasdaq'] / base_data['sp500']
            derived['tech_strength'] = tech_ratio
        
        # Gold/SPX ratio (fear gauge)
        if 'gold_price' in base_data and 'sp500' in base_data:
            fear_ratio = base_data['gold_price'] / base_data['sp500']
            derived['fear_gauge'] = fear_ratio
        
        # 12-13. Commodity volatility
        if 'oil_wti' in base_data:
            # Oil spike detection (>$90 = energy shock)
            oil_spike = 1.0 if base_data['oil_wti'] > 90 else 0.0
            derived['oil_spike_indicator'] = oil_spike
        
        if 'copper' in base_data:
            # Copper/Gold ratio (economic health)
            if 'gold_price' in base_data:
                copper_gold = base_data['copper'] / base_data['gold_price']
                derived['economic_health_indicator'] = copper_gold
        
        # ============================================
        # CATEGORY 3: MOMENTUM INDICATORS (7)
        # ============================================
        
        # 14. GDP Momentum (would need historical - using proxy)
        if 'gdp_growth' in base_data and 'industrial_production' in base_data:
            # Proxy: average of GDP and IP
            gdp_momentum = (base_data['gdp_growth'] + base_data['industrial_production']) / 2
            derived['gdp_momentum_proxy'] = gdp_momentum
        
        # 15. Inflation Momentum (CPI vs PCE divergence)
        if 'cpi_inflation' in base_data and 'pce_inflation' in base_data:
            inflation_divergence = base_data['cpi_inflation'] - base_data['pce_inflation']
            derived['inflation_divergence'] = inflation_divergence
        
        # 16. Labor Market Momentum
        if 'unemployment' in base_data:
            # Distance from NAIRU (~4%)
            labor_slack = base_data['unemployment'] - 0.04
            derived['labor_market_slack'] = labor_slack
        
        # 17. Money Supply Growth (M2 level as proxy)
        if 'm2_money_supply' in base_data:
            # Normalized to trillions
            m2_trillions = base_data['m2_money_supply'] / 1000
            derived['m2_level'] = m2_trillions
        
        # 18. Fed Balance Sheet Normalized
        if 'fed_balance_sheet' in base_data:
            # Millions to trillions
            fed_bs_trillions = base_data['fed_balance_sheet'] / 1_000_000
            derived['fed_balance_sheet_trillions'] = fed_bs_trillions
        
        # 19. Retail Sales Momentum (level)
        if 'retail_sales' in base_data:
            retail_norm = base_data['retail_sales'] / 100_000  # Normalize
            derived['retail_sales_norm'] = retail_norm
        
        # 20. Housing Starts Momentum
        if 'housing_starts' in base_data:
            housing_norm = base_data['housing_starts'] / 1000  # Thousands
            derived['housing_starts_norm'] = housing_norm
        
        # ============================================
        # CATEGORY 4: CREDIT STRESS INDICATORS (6)
        # ============================================
        
        # 21. Credit Spread Widening (IG vs historical)
        if 'ig_credit_spread' in base_data:
            # Historical average IG spread ~1.5%
            spread_z = (base_data['ig_credit_spread'] - 0.015) / 0.01
            derived['ig_spread_zscore'] = spread_z
        
        # 22. HY Spread Widening
        if 'hy_credit_spread' in base_data:
            # Historical average HY spread ~4.5%
            hy_spread_z = (base_data['hy_credit_spread'] - 0.045) / 0.02
            derived['hy_spread_zscore'] = hy_spread_z
        
        # 23. Credit Spread Differential (HY - IG)
        if 'hy_credit_spread' in base_data and 'ig_credit_spread' in base_data:
            spread_diff = base_data['hy_credit_spread'] - base_data['ig_credit_spread']
            derived['credit_spread_differential'] = spread_diff
        
        # 24. Fed Tightening Indicator (Fed Funds vs inflation)
        if 'fed_funds_rate' in base_data and 'cpi_inflation' in base_data:
            real_rate = base_data['fed_funds_rate'] - base_data['cpi_inflation']
            derived['real_fed_funds'] = real_rate
        
        # 25. Policy Rate Distance from Neutral
        if 'fed_funds_rate' in base_data:
            # Neutral rate ~2.5%
            distance_from_neutral = base_data['fed_funds_rate'] - 0.025
            derived['policy_rate_deviation'] = distance_from_neutral
        
        # 26. Credit Impulse Proxy (M2 - GDP)
        if 'm2_money_supply' in base_data and 'gdp_growth' in base_data:
            # Simplified credit impulse
            credit_impulse = (base_data['m2_money_supply'] / 1000) - base_data['gdp_growth']
            derived['credit_impulse_proxy'] = credit_impulse
        
        # ============================================
        # CATEGORY 5: CURRENCY STRESS (5)
        # ============================================
        
        # 27. Dollar Strength Index (DXY normalized)
        if 'dxy' in base_data:
            # Historical mean ~95, std ~10
            dxy_z = (base_data['dxy'] - 95) / 10
            derived['dxy_strength_zscore'] = dxy_z
        
        # 28. Dollar Stress Level
        if 'dxy' in base_data:
            dxy = base_data['dxy']
            if dxy > 110:
                derived['dollar_stress'] = 1.0    # Extreme strength
            elif dxy > 105:
                derived['dollar_stress'] = 0.75   # High
            elif dxy < 90:
                derived['dollar_stress'] = -0.75  # Weakness
            else:
                derived['dollar_stress'] = 0.0    # Normal
        
        # 29-31. Currency cross-impacts
        # DXY vs Gold (inverse relationship)
        if 'dxy' in base_data and 'gold_price' in base_data:
            dxy_gold_ratio = base_data['dxy'] / (base_data['gold_price'] / 20)
            derived['dxy_gold_divergence'] = dxy_gold_ratio
        
        # DXY vs Oil (typical negative correlation)
        if 'dxy' in base_data and 'oil_wti' in base_data:
            dxy_oil_ratio = base_data['dxy'] / base_data['oil_wti']
            derived['dxy_oil_relationship'] = dxy_oil_ratio
        
        # DXY vs BTC (de-dollarization indicator)
        if 'dxy' in base_data and 'btc_price' in base_data:
            dxy_btc = base_data['dxy'] / (base_data['btc_price'] / 1000)
            derived['dxy_btc_decoupling'] = dxy_btc
        
        # ============================================
        # CATEGORY 6: CRYPTO METRICS (4)
        # ============================================
        
        # 32. BTC/ETH Ratio (BTC dominance)
        if 'btc_price' in base_data and 'eth_price' in base_data:
            btc_eth_ratio = base_data['btc_price'] / base_data['eth_price']
            derived['btc_dominance'] = btc_eth_ratio
        
        # 33. Crypto Market Cap Proxy
        if 'btc_price' in base_data and 'eth_price' in base_data:
            # Rough proxy: BTC + ETH weighted
            crypto_cap_proxy = base_data['btc_price'] * 0.7 + base_data['eth_price'] * 0.3
            derived['crypto_market_cap_proxy'] = crypto_cap_proxy
        
        # 34. Stablecoin Dominance
        if 'stablecoin_supply' in base_data and 'btc_price' in base_data:
            # Stablecoin supply vs BTC market cap (rough)
            stablecoin_ratio = base_data['stablecoin_supply'] / (base_data['btc_price'] * 19_000_000)
            derived['stablecoin_dominance'] = stablecoin_ratio
        
        # 35. Crypto Risk-On Indicator
        if 'btc_price' in base_data and 'sp500' in base_data:
            # BTC outperforming = risk-on
            btc_sp_ratio = (base_data['btc_price'] / 40000) / (base_data['sp500'] / 4500)
            derived['crypto_risk_on'] = btc_sp_ratio
        
        # ============================================
        # CATEGORY 7: ECONOMIC DIVERGENCE (5)
        # ============================================
        
        # 36. US vs Global Growth Proxy
        if 'sp500' in base_data and 'vxus' in base_data:
            # US outperformance
            us_global_divergence = base_data['sp500'] / base_data['vxus'] if 'vxus' in base_data else 1.0
            derived['us_exceptionalism'] = us_global_divergence
        
        # 37. Growth vs Value (proxy via sector strength)
        if 'nasdaq' in base_data and 'sp500' in base_data:
            growth_value = base_data['nasdaq'] / base_data['sp500']
            derived['growth_vs_value'] = growth_value
        
        # 38. Inflation vs Growth Balance
        if 'cpi_inflation' in base_data and 'gdp_growth' in base_data:
            misery_index = base_data['cpi_inflation'] + base_data['unemployment'] if 'unemployment' in base_data else 0
            derived['misery_index'] = misery_index
        
        # 39. Fed Policy Stance (Hawkish/Dovish)
        if 'fed_funds_rate' in base_data and 'cpi_inflation' in base_data:
            # Hawkish if real rates rising
            policy_stance = base_data['fed_funds_rate'] - (base_data['cpi_inflation'] * 2)
            derived['fed_policy_stance'] = policy_stance
        
        # 40. Economic Surprise Index (proxy)
        # Using retail sales vs unemployment divergence
        if 'retail_sales' in base_data and 'unemployment' in base_data:
            surprise_proxy = (base_data['retail_sales'] / 700000) - (base_data['unemployment'] * 10)
            derived['economic_surprise_proxy'] = surprise_proxy
        
        # ============================================
        # SUMMARY
        # ============================================
        
        total_derived = len(derived)
        logger.info(f"✓ Calculated {total_derived} derived parameters")
        
        return derived
    
    def get_parameter_categories(self) -> Dict[str, List[str]]:
        """Return categorized list of all 40 parameters"""
        return {
            'yield_curve': [
                'yield_curve_slope',
                'yield_curve_steepness',
                'yield_curve_curvature',
                'inversion_score',
                'term_premium'
            ],
            'volatility': [
                'vix_regime',
                'vix_zscore',
                'vol_of_vol_proxy',
                'small_cap_strength',
                'tech_strength',
                'fear_gauge',
                'oil_spike_indicator',
                'economic_health_indicator'
            ],
            'momentum': [
                'gdp_momentum_proxy',
                'inflation_divergence',
                'labor_market_slack',
                'm2_level',
                'fed_balance_sheet_trillions',
                'retail_sales_norm',
                'housing_starts_norm'
            ],
            'credit_stress': [
                'ig_spread_zscore',
                'hy_spread_zscore',
                'credit_spread_differential',
                'real_fed_funds',
                'policy_rate_deviation',
                'credit_impulse_proxy'
            ],
            'currency_stress': [
                'dxy_strength_zscore',
                'dollar_stress',
                'dxy_gold_divergence',
                'dxy_oil_relationship',
                'dxy_btc_decoupling'
            ],
            'crypto': [
                'btc_dominance',
                'crypto_market_cap_proxy',
                'stablecoin_dominance',
                'crypto_risk_on'
            ],
            'economic_divergence': [
                'us_exceptionalism',
                'growth_vs_value',
                'misery_index',
                'fed_policy_stance',
                'economic_surprise_proxy'
            ]
        }
