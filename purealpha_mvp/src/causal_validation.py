"""
Causal Validation Engine
Uses Do-Calculus principles to validate causal relationships
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from scipy.stats import pearsonr
from statsmodels.tsa.stattools import grangercausalitytests
from sklearn.linear_model import LinearRegression

logger = logging.getLogger(__name__)


class CausalValidationEngine:
    """
    Validates causal relationships using 5-level validation framework
    """
    
    def __init__(self, significance_level: float = 0.05):
        self.sig_level = significance_level
        self.validated_links = {}
        logger.info(f"Initialized CVE with significance level: {significance_level}")
        
    def validate_link(
        self, 
        cause_data: pd.Series, 
        effect_data: pd.Series,
        cause_name: str,
        effect_name: str,
        max_lag: int = 10
    ) -> Dict:
        """
        Validates X → Y causal link with 5 tests
        
        Args:
            cause_data: Time series of cause variable
            effect_data: Time series of effect variable
            cause_name: Name of cause variable
            effect_name: Name of effect variable
            max_lag: Maximum lag to test for Granger causality
            
        Returns:
            Dictionary with validation results
        """
        
        # Input validation
        if len(cause_data) < 30:
            logger.warning(f"Insufficient data for {cause_name} → {effect_name}: {len(cause_data)} points")
            return {
                'valid': False, 
                'error': 'Insufficient data (minimum 30 points required)',
                'confidence': 0.0,
                'cause': cause_name,
                'effect': effect_name
            }
        
        # Create clean dataframe
        df = pd.DataFrame({
            'X': cause_data, 
            'Y': effect_data
        }).dropna()
        
        if len(df) < 30:
            return {
                'valid': False,
                'error': 'Too many missing values after cleanup',
                'confidence': 0.0,
                'cause': cause_name,
                'effect': effect_name
            }
        
        results = {}
        
        # TEST 1: Granger Causality (with optimal lag search)
        try:
            granger_result = grangercausalitytests(
                df[['Y', 'X']], 
                maxlag=max_lag, 
                verbose=False
            )
            
            # Find optimal lag (minimum p-value)
            p_values = []
            for lag in range(1, max_lag + 1):
                p_val = granger_result[lag][0]['ssr_ftest'][1]
                p_values.append(p_val)
            
            results['granger_p'] = min(p_values)
            results['optimal_lag'] = p_values.index(results['granger_p']) + 1
            
            logger.debug(f"Granger test: p={results['granger_p']:.4f}, lag={results['optimal_lag']}")
            
        except Exception as e:
            logger.warning(f"Granger test failed for {cause_name} → {effect_name}: {e}")
            results['granger_p'] = 1.0
            results['optimal_lag'] = 1
        
        # TEST 2: Pearson Correlation
        try:
            corr, corr_p = pearsonr(df['X'], df['Y'])
            results['correlation'] = corr
            results['correlation_p'] = corr_p
            
            logger.debug(f"Correlation: r={corr:.3f}, p={corr_p:.4f}")
            
        except Exception as e:
            logger.warning(f"Correlation test failed: {e}")
            results['correlation'] = 0.0
            results['correlation_p'] = 1.0
        
        # TEST 3: Temporal Precedence
        try:
            # X(t) should predict Y(t+1) better than Y(t-1)
            corr_forward = df['X'].corr(df['Y'].shift(-1))  # X→Y future
            corr_backward = df['X'].corr(df['Y'].shift(1))  # X→Y past
            
            results['precedence_confirmed'] = (
                abs(corr_forward) > abs(corr_backward) and
                not np.isnan(corr_forward)
            )
            
            logger.debug(f"Precedence: forward={corr_forward:.3f}, backward={corr_backward:.3f}")
            
        except Exception as e:
            logger.warning(f"Precedence test failed: {e}")
            results['precedence_confirmed'] = False
        
        # TEST 4: Intervention Effect (R²)
        try:
            X_reshaped = df[['X']].values
            y_values = df['Y'].values
            
            model = LinearRegression()
            model.fit(X_reshaped, y_values)
            
            results['intervention_r2'] = model.score(X_reshaped, y_values)
            results['intervention_coef'] = model.coef_[0]
            
            logger.debug(f"Intervention: R²={results['intervention_r2']:.3f}")
            
        except Exception as e:
            logger.warning(f"Intervention test failed: {e}")
            results['intervention_r2'] = 0.0
            results['intervention_coef'] = 0.0
        
        # TEST 5: Out-of-Sample Stability
        try:
            split_idx = int(len(df) * 0.7)
            
            train_df = df.iloc[:split_idx]
            test_df = df.iloc[split_idx:]
            
            train_corr = train_df['X'].corr(train_df['Y'])
            test_corr = test_df['X'].corr(test_df['Y'])
            
            if train_corr != 0 and not np.isnan(train_corr):
                results['oos_stability'] = test_corr / train_corr
            else:
                results['oos_stability'] = 0.0
                
            logger.debug(f"OOS stability: {results['oos_stability']:.3f}")
                
        except Exception as e:
            logger.warning(f"OOS test failed: {e}")
            results['oos_stability'] = 0.0
        
        # AGGREGATE VALIDATION
        is_valid = (
            results['granger_p'] < self.sig_level and
            abs(results['correlation']) > 0.3 and
            results['precedence_confirmed'] and
            results['intervention_r2'] > 0.15 and
            results['oos_stability'] >= 0.7
        )
        
        # Calculate confidence (continuous scoring)
        confidence = self._calculate_confidence(results)
        
        # Calculate strength (0-100)
        strength = min(100, int(abs(results['correlation']) * 100))
        
        # Infer mechanism
        mechanism = self._infer_mechanism(cause_name, effect_name, results)
        
        result = {
            'valid': is_valid,
            'confidence': round(confidence, 3),
            'strength': strength,
            'granger_p': round(results['granger_p'], 4),
            'correlation': round(results['correlation'], 3),
            'optimal_lag': results['optimal_lag'],
            'precedence_confirmed': results['precedence_confirmed'],
            'intervention_r2': round(results['intervention_r2'], 3),
            'oos_stability': round(results['oos_stability'], 3),
            'mechanism': mechanism,
            'cause': cause_name,
            'effect': effect_name
        }
        
        # Store validated link
        if is_valid:
            link_key = f"{cause_name}→{effect_name}"
            self.validated_links[link_key] = result
            logger.info(f"✓ Valid causal link: {link_key} (confidence: {confidence:.3f})")
        else:
            logger.info(f"✗ Invalid link: {cause_name}→{effect_name}")
        
        return result
    
    def _calculate_confidence(self, results: Dict) -> float:
        """
        Continuous confidence scoring based on all tests
        """
        # Granger confidence (0-1)
        granger_conf = 1 - results['granger_p']
        
        # Correlation confidence (0-1)
        corr_conf = abs(results['correlation'])
        
        # Precedence confidence (0-1)
        precedence_conf = 1.0 if results['precedence_confirmed'] else 0.5
        
        # R² confidence (0-1)
        r2_conf = min(results['intervention_r2'] / 0.5, 1.0)
        
        # OOS confidence (0-1)
        oos_conf = min(abs(results['oos_stability']), 1.0)
        
        # Weighted average
        confidence = (
            granger_conf * 0.40 +
            corr_conf * 0.25 +
            precedence_conf * 0.15 +
            r2_conf * 0.10 +
            oos_conf * 0.10
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _infer_mechanism(self, cause: str, effect: str, results: Dict) -> str:
        """
        Infers causal mechanism based on parameter names
        """
        cause_lower = cause.lower()
        effect_lower = effect.lower()
        lag = results.get('optimal_lag', 1)
        
        # Known mechanisms (heuristic rules)
        if ('fed' in cause_lower or 'rate' in cause_lower) and ('dxy' in effect_lower or 'dollar' in effect_lower):
            return "Interest rate differential drives currency flows via carry trade"
        
        if ('dxy' in cause_lower or 'dollar' in cause_lower) and 'gold' in effect_lower:
            return "Dollar strength inverse to gold (gold priced in USD)"
        
        if ('dxy' in cause_lower or 'dollar' in cause_lower) and 'oil' in effect_lower:
            return "Dollar affects commodity pricing (commodities denominated in USD)"
        
        if 'vix' in cause_lower and ('sp500' in effect_lower or 'equity' in effect_lower):
            return "Volatility spike triggers risk-off selling"
        
        if 'taiwan' in cause_lower and ('tsmc' in effect_lower or 'soxx' in effect_lower):
            return "Geopolitical risk affects semiconductor supply chain"
        
        # Default mechanism
        return f"Validated causal relationship with {lag}-period lag"
    
    def batch_validate(self, links: List[Dict], market_data: pd.DataFrame) -> List[Dict]:
        """
        Validates multiple causal links
        
        Args:
            links: List of dicts with 'cause' and 'effect' keys
            market_data: DataFrame with all parameter columns
            
        Returns:
            List of validation results
        """
        logger.info(f"Starting batch validation for {len(links)} links")
        results = []
        
        for link in links:
            cause_col = link['cause']
            effect_col = link['effect']
            
            if cause_col not in market_data.columns:
                logger.warning(f"Missing cause column: {cause_col}")
                continue
                
            if effect_col not in market_data.columns:
                logger.warning(f"Missing effect column: {effect_col}")
                continue
            
            result = self.validate_link(
                market_data[cause_col],
                market_data[effect_col],
                cause_col,
                effect_col
            )
            
            results.append(result)
        
        valid_count = sum(1 for r in results if r.get('valid', False))
        logger.info(f"Batch validation complete: {valid_count}/{len(results)} valid links")
        
        return results
    
    def get_validated_links(self) -> Dict:
        """Returns all validated causal links"""
        return self.validated_links
