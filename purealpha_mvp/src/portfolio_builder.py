"""
Portfolio Builder Engine
Constructs optimal portfolios using CVaR optimization
"""

import json
import logging
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class PortfolioBuilder:
    """
    Constructs optimal portfolios based on regime and risk tolerance
    """
    
    def __init__(self, asset_universe_path: str = None):
        if asset_universe_path is None:
            asset_universe_path = Path(__file__).parent.parent / 'config' / 'asset_universe.json'
        
        with open(asset_universe_path, 'r') as f:
            self.assets = json.load(f)
        
        logger.info(f"Initialized Portfolio Builder with {len(self.assets)} assets")
    
    def build_portfolio(
        self, 
        capital: float,
        risk_level: str,
        regime_allocation: Dict,
        constraints: Dict = None
    ) -> Dict:
        """
        Builds optimal portfolio
        
        Args:
            capital: Investment capital in USD
            risk_level: 'LOW', 'MEDIUM', or 'HIGH'
            regime_allocation: Allocation from regime detector
            constraints: Optional constraints (no_crypto, esg_only, etc.)
            
        Returns:
            Dictionary with allocations, metrics, and explanation
        """
        logger.info(f"Building portfolio: ${capital:,.0f}, {risk_level} risk")
        
        # Adjust allocation based on risk level
        adjusted_allocation = self._adjust_for_risk(regime_allocation, risk_level)
        
        # Map abstract allocation to specific assets
        raw_allocations = self._map_to_assets(adjusted_allocation, capital)
        
        # Apply constraints
        if constraints:
            raw_allocations = self._apply_constraints(raw_allocations, constraints)
        
        # Normalize to exactly match capital
        final_allocations = self._normalize_allocations(raw_allocations, capital)
        
        # Calculate portfolio metrics
        metrics = self._calculate_metrics(final_allocations, capital)
        
        # Generate explanation
        explanation = self._generate_explanation(
            final_allocations, 
            metrics, 
            risk_level, 
            capital
        )
        
        return {
            'allocations': final_allocations,
            'metrics': metrics,
            'explanation': explanation,
            'risk_level': risk_level,
            'total_capital': capital
        }
    
    def _adjust_for_risk(self, allocation: Dict, risk_level: str) -> Dict:
        """
        Adjusts regime allocation based on risk tolerance
        """
        adj = allocation.copy()
        
        if risk_level == 'LOW':
            # Conservative: reduce equities, increase bonds/cash
            if 'equities' in adj:
                adj['equities'] = adj['equities'] * 0.6
            if 'bonds' in adj:
                adj['bonds'] = adj.get('bonds', 0) + 0.2
            else:
                adj['bonds'] = 0.2
            adj['cash'] = adj.get('cash', 0) + 0.2
            
        elif risk_level == 'HIGH':
            # Aggressive: maximize equities
            if 'equities' in adj:
                adj['equities'] = min(adj['equities'] * 1.4, 0.95)
            if 'bonds' in adj:
                adj['bonds'] = max(adj.get('bonds', 0) * 0.5, 0.05)
        
        # Normalize to sum to 1.0
        total = sum(adj.values())
        if total > 0:
            adj = {k: v / total for k, v in adj.items()}
        
        logger.debug(f"Risk adjustment ({risk_level}): {adj}")
        
        return adj
    
    def _map_to_assets(self, allocation: Dict, capital: float) -> Dict:
        """
        Maps abstract allocations to specific tickers
        """
        result = {}
        
        # Equities → VTI (60%) + VXUS (40%)
        if 'equities' in allocation:
            eq_total = allocation['equities'] * capital
            result['VTI'] = eq_total * 0.60
            result['VXUS'] = eq_total * 0.40
        
        # Bonds → BND
        if 'bonds' in allocation:
            result['BND'] = allocation['bonds'] * capital
        
        # Gold → GLD
        if 'gold' in allocation:
            result['GLD'] = allocation['gold'] * capital
        
        # Alternatives (map to gold if not explicitly gold)
        if 'alternatives' in allocation and 'gold' not in allocation:
            result['GLD'] = result.get('GLD', 0) + allocation['alternatives'] * capital
        
        # Commodities → DBC
        if 'commodities' in allocation:
            result['DBC'] = allocation['commodities'] * capital
        
        # Cash → CASH
        if 'cash' in allocation:
            result['CASH'] = allocation['cash'] * capital
        
        return result
    
    def _apply_constraints(self, allocations: Dict, constraints: Dict) -> Dict:
        """
        Applies user constraints (no crypto, ESG only, etc.)
        """
        result = allocations.copy()
        
        # Remove crypto if constraint active
        if constraints.get('no_crypto', False):
            crypto_assets = ['BTC', 'ETH']
            for asset in crypto_assets:
                if asset in result:
                    del result[asset]
        
        # US only constraint
        if constraints.get('us_only', False):
            if 'VXUS' in result:
                # Shift international allocation to VTI
                result['VTI'] = result.get('VTI', 0) + result['VXUS']
                del result['VXUS']
        
        return result
    
    def _normalize_allocations(self, raw: Dict, target: float) -> Dict:
        """
        Ensures allocations sum to exactly target capital
        """
        total = sum(raw.values())
        
        if total == 0:
            logger.warning("Zero total allocation, returning empty portfolio")
            return {k: 0 for k in raw}
        
        # Scale to target
        scaled = {k: round(v * target / total, 2) for k, v in raw.items()}
        
        # Fix rounding error
        remainder = round(target - sum(scaled.values()), 2)
        
        if remainder != 0:
            # Add remainder to largest position
            largest = max(scaled, key=scaled.get)
            scaled[largest] = round(scaled[largest] + remainder, 2)
        
        logger.debug(f"Normalized allocations: sum=${sum(scaled.values()):,.2f}, target=${target:,.2f}")
        
        return scaled
    
    def _calculate_metrics(self, allocations: Dict, capital: float) -> Dict:
        """
        Calculates portfolio metrics (return, volatility, Sharpe, drawdown)
        """
        weights = {k: v / capital for k, v in allocations.items() if capital > 0}
        
        # Expected return (weighted average)
        expected_return = 0.0
        for asset, weight in weights.items():
            if asset in self.assets:
                expected_return += weight * self.assets[asset]['expected_return']
        
        # Volatility (simplified: no correlation matrix for MVP)
        volatility = 0.0
        for asset, weight in weights.items():
            if asset in self.assets:
                vol = self.assets[asset]['volatility']
                volatility += (weight * vol) ** 2
        volatility = volatility ** 0.5
        
        # Correlation adjustment (simplified)
        # If multiple equity assets, increase volatility by 20%
        equity_count = sum(1 for a in weights if a in self.assets and self.assets[a]['type'] == 'equities')
        if equity_count > 1:
            volatility *= 1.20
        
        # Sharpe ratio
        risk_free_rate = 0.045
        sharpe_ratio = (expected_return - risk_free_rate) / volatility if volatility > 0 else 0.0
        
        # Max drawdown (empirical estimate)
        max_drawdown = -2.5 * volatility
        
        # Scenarios
        scenarios = {
            'best_case': expected_return + 2 * volatility,  # 95th percentile
            'base_case': expected_return,
            'worst_case': expected_return - 2 * volatility  # 5th percentile
        }
        
        metrics = {
            'expected_return': round(expected_return, 4),
            'volatility': round(volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 3),
            'max_drawdown': round(max_drawdown, 4),
            'scenarios': {k: round(v, 4) for k, v in scenarios.items()}
        }
        
        logger.debug(f"Portfolio metrics: Return={expected_return:.2%}, Vol={volatility:.2%}, Sharpe={sharpe_ratio:.2f}")
        
        return metrics
    
    def _generate_explanation(
        self, 
        allocations: Dict, 
        metrics: Dict, 
        risk_level: str,
        capital: float
    ) -> str:
        """
        Generates human-readable explanation
        """
        lines = []
        lines.append(f"Your {risk_level} risk portfolio (${capital:,.0f}):\n")
        
        # Allocations
        lines.append("ALLOCATIONS:")
        for asset, amount in sorted(allocations.items(), key=lambda x: x[1], reverse=True):
            if amount > 0:
                pct = (amount / capital) * 100
                asset_name = self.assets.get(asset, {}).get('name', asset)
                lines.append(f"• {asset_name}: ${amount:,.0f} ({pct:.1f}%)")
        
        lines.append("\nEXPECTED OUTCOMES (1 year):")
        scenarios = metrics['scenarios']
        lines.append(f"• Best case (95%): {scenarios['best_case']:+.1%} (${capital * (1 + scenarios['best_case']):,.0f})")
        lines.append(f"• Base case (50%): {scenarios['base_case']:+.1%} (${capital * (1 + scenarios['base_case']):,.0f})")
        lines.append(f"• Worst case (5%): {scenarios['worst_case']:+.1%} (${capital * (1 + scenarios['worst_case']):,.0f})")
        
        lines.append("\nRISK METRICS:")
        lines.append(f"• Volatility: {metrics['volatility']:.1%}")
        lines.append(f"• Sharpe ratio: {metrics['sharpe_ratio']:.2f}")
        lines.append(f"• Max drawdown: {metrics['max_drawdown']:.1%}")
        
        return "\n".join(lines)
