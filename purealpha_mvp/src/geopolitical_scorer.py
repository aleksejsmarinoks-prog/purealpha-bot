"""
Geopolitical Scoring System
Manual + Automated scoring of geopolitical events

Phase 1: Manual scoring (you score events 0-10 daily)
Phase 2: Automated news parsing (future)
"""
import json
import os
from datetime import datetime
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class GeopoliticalScorer:
    """
    Manual geopolitical risk scoring system
    
    20 factors, scored 0-10 each
    Updates daily via simple JSON file
    """
    
    FACTORS = {
        # Middle East (5 factors)
        'hormuz_tension': {
            'name': 'Hormuz Strait Tension',
            'description': 'Risk of closure (Iran threats, naval activity)',
            'impact': 'Oil spike → Inflation → Fed hawkish → Liquidity drain',
            'weight': 0.08
        },
        'israel_iran': {
            'name': 'Israel-Iran Conflict',
            'description': 'Direct conflict escalation',
            'impact': 'Regional war → Oil disruption → Safe haven flows',
            'weight': 0.06
        },
        'saudi_stability': {
            'name': 'Saudi Arabia Stability',
            'description': 'Political/security situation',
            'impact': 'Oil production reliability',
            'weight': 0.04
        },
        'yemen_shipping': {
            'name': 'Yemen Red Sea Disruption',
            'description': 'Houthi attacks on shipping',
            'impact': 'Trade route costs → Inflation',
            'weight': 0.03
        },
        'iraq_syria': {
            'name': 'Iraq/Syria Instability',
            'description': 'Regional spillover risks',
            'impact': 'Oil infrastructure threats',
            'weight': 0.02
        },
        
        # Asia-Pacific (4 factors)
        'taiwan_tension': {
            'name': 'Taiwan Strait Tension',
            'description': 'China-Taiwan-US military posture',
            'impact': 'Semiconductor supply → Tech shock → Market crash',
            'weight': 0.08
        },
        'south_china_sea': {
            'name': 'South China Sea Disputes',
            'description': 'Territorial conflicts, naval incidents',
            'impact': 'Trade route disruption',
            'weight': 0.03
        },
        'north_korea': {
            'name': 'North Korea Provocations',
            'description': 'Missile tests, nuclear threats',
            'impact': 'Regional instability → Safe haven demand',
            'weight': 0.02
        },
        'japan_china': {
            'name': 'Japan-China Relations',
            'description': 'Diplomatic/economic tensions',
            'impact': 'Asia supply chain stress',
            'weight': 0.02
        },
        
        # Europe (4 factors)
        'russia_ukraine': {
            'name': 'Russia-Ukraine War',
            'description': 'Escalation/de-escalation dynamics',
            'impact': 'Energy prices → European recession → Capital flows',
            'weight': 0.07
        },
        'eu_cohesion': {
            'name': 'EU Cohesion',
            'description': 'Political unity, budget disputes',
            'impact': 'EUR weakness → Dollar strength',
            'weight': 0.05
        },
        'nato_unity': {
            'name': 'NATO Unity',
            'description': 'Defense spending, article 5 credibility',
            'impact': 'Security architecture stability',
            'weight': 0.04
        },
        'baltics_poland': {
            'name': 'Eastern European Tensions',
            'description': 'Baltic states, Poland, Belarus border issues',
            'impact': 'NATO response triggers',
            'weight': 0.03
        },
        
        # Americas (3 factors)
        'us_china_trade': {
            'name': 'US-China Trade War',
            'description': 'Tariffs, tech restrictions, sanctions',
            'impact': 'Supply chain reconfiguration → Inflation',
            'weight': 0.06
        },
        'us_political': {
            'name': 'US Political Stability',
            'description': 'Domestic political risk, policy uncertainty',
            'impact': 'Market volatility → Safe haven flows',
            'weight': 0.05
        },
        'latam_instability': {
            'name': 'Latin America Instability',
            'description': 'Venezuela, Argentina, Mexico issues',
            'impact': 'Commodity supply, migration',
            'weight': 0.02
        },
        
        # Other (4 factors)
        'india_pakistan': {
            'name': 'India-Pakistan Tensions',
            'description': 'Kashmir, border conflicts',
            'impact': 'Nuclear risk (low prob, high impact)',
            'weight': 0.03
        },
        'africa_coups': {
            'name': 'African Instability',
            'description': 'Coups, civil wars, resource conflicts',
            'impact': 'Commodity supply disruptions',
            'weight': 0.02
        },
        'cyber_attacks': {
            'name': 'Major Cyber Attacks',
            'description': 'State-sponsored infrastructure attacks',
            'impact': 'Economic disruption, trust erosion',
            'weight': 0.04
        },
        'terrorism': {
            'name': 'Terrorism Threat',
            'description': 'Major attacks or elevated threat',
            'impact': 'Travel/trade disruption, safe haven flows',
            'weight': 0.03
        }
    }
    
    def __init__(self, scores_file: str = 'geopolitical_scores.json'):
        """
        Initialize scorer
        
        Args:
            scores_file: Path to JSON file storing scores
        """
        self.scores_file = scores_file
        self.scores = self._load_scores()
        logger.info(f"Geopolitical Scorer initialized ({len(self.FACTORS)} factors)")
    
    def _load_scores(self) -> Dict:
        """Load scores from file or create default"""
        if os.path.exists(self.scores_file):
            try:
                with open(self.scores_file, 'r') as f:
                    scores = json.load(f)
                logger.info(f"Loaded scores from {self.scores_file}")
                return scores
            except Exception as e:
                logger.warning(f"Failed to load scores: {e}")
        
        # Create default scores (all 5 = moderate)
        default_scores = {
            'last_updated': datetime.now().isoformat(),
            'scores': {factor: 5.0 for factor in self.FACTORS.keys()}
        }
        
        self._save_scores(default_scores)
        return default_scores
    
    def _save_scores(self, scores: Dict):
        """Save scores to file"""
        try:
            with open(self.scores_file, 'w') as f:
                json.dump(scores, f, indent=2)
            logger.info(f"Saved scores to {self.scores_file}")
        except Exception as e:
            logger.error(f"Failed to save scores: {e}")
    
    def update_score(self, factor: str, score: float, note: str = ""):
        """
        Update single factor score
        
        Args:
            factor: Factor key (e.g. 'hormuz_tension')
            score: 0-10 (0=no risk, 10=critical)
            note: Optional note about why you're setting this score
        """
        if factor not in self.FACTORS:
            raise ValueError(f"Unknown factor: {factor}")
        
        if not 0 <= score <= 10:
            raise ValueError(f"Score must be 0-10, got {score}")
        
        self.scores['scores'][factor] = score
        self.scores['last_updated'] = datetime.now().isoformat()
        
        if note:
            if 'notes' not in self.scores:
                self.scores['notes'] = {}
            self.scores['notes'][factor] = {
                'note': note,
                'timestamp': datetime.now().isoformat()
            }
        
        self._save_scores(self.scores)
        
        logger.info(f"✓ Updated {factor}: {score}/10")
    
    def batch_update(self, updates: Dict[str, float]):
        """
        Update multiple scores at once
        
        Args:
            updates: Dict of {factor: score}
        """
        for factor, score in updates.items():
            self.update_score(factor, score)
    
    def calculate_total_score(self) -> float:
        """
        Calculate weighted total geopolitical risk score
        
        Returns:
            0-100 score (0=peaceful, 100=multiple critical crises)
        """
        total = 0.0
        
        for factor, info in self.FACTORS.items():
            score = self.scores['scores'].get(factor, 5.0)
            weight = info['weight']
            total += score * weight * 10  # Scale to 0-100
        
        return min(100, total)  # Cap at 100
    
    def get_top_risks(self, n: int = 5) -> List[Dict]:
        """
        Get top N risk factors
        
        Returns:
            List of {factor, score, name, impact}
        """
        risks = []
        
        for factor, info in self.FACTORS.items():
            score = self.scores['scores'].get(factor, 5.0)
            risks.append({
                'factor': factor,
                'score': score,
                'name': info['name'],
                'impact': info['impact'],
                'weight': info['weight']
            })
        
        # Sort by weighted score
        risks.sort(key=lambda x: x['score'] * x['weight'], reverse=True)
        
        return risks[:n]
    
    def get_status_summary(self) -> Dict:
        """Get summary of geopolitical situation"""
        total_score = self.calculate_total_score()
        
        if total_score < 30:
            status = "LOW_RISK"
            description = "Geopolitical environment stable"
        elif total_score < 50:
            status = "MODERATE_RISK"
            description = "Some tensions but manageable"
        elif total_score < 70:
            status = "HIGH_RISK"
            description = "Multiple significant tensions"
        else:
            status = "CRITICAL_RISK"
            description = "Severe geopolitical crisis environment"
        
        return {
            'total_score': total_score,
            'status': status,
            'description': description,
            'last_updated': self.scores.get('last_updated'),
            'top_risks': self.get_top_risks(3)
        }
    
    def get_factor_info(self, factor: str = None) -> Dict:
        """
        Get information about factor(s)
        
        Args:
            factor: Specific factor, or None for all
        """
        if factor:
            if factor not in self.FACTORS:
                raise ValueError(f"Unknown factor: {factor}")
            
            info = self.FACTORS[factor].copy()
            info['current_score'] = self.scores['scores'].get(factor, 5.0)
            return info
        else:
            # Return all factors with current scores
            result = {}
            for f, info in self.FACTORS.items():
                result[f] = info.copy()
                result[f]['current_score'] = self.scores['scores'].get(f, 5.0)
            return result
    
    def generate_daily_update_form(self) -> str:
        """
        Generate simple text form for daily scoring
        
        Returns:
            String to copy-paste for daily updates
        """
        form = "# PUREALPHA GEOPOLITICAL DAILY SCORING\n"
        form += f"# Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        form += f"# Last updated: {self.scores.get('last_updated', 'Never')}\n\n"
        
        form += "# Instructions: Rate each factor 0-10\n"
        form += "# 0 = No risk, 5 = Moderate, 10 = Critical\n\n"
        
        # Group by region
        groups = {
            'Middle East': ['hormuz_tension', 'israel_iran', 'saudi_stability', 'yemen_shipping', 'iraq_syria'],
            'Asia-Pacific': ['taiwan_tension', 'south_china_sea', 'north_korea', 'japan_china'],
            'Europe': ['russia_ukraine', 'eu_cohesion', 'nato_unity', 'baltics_poland'],
            'Americas': ['us_china_trade', 'us_political', 'latam_instability'],
            'Other': ['india_pakistan', 'africa_coups', 'cyber_attacks', 'terrorism']
        }
        
        for region, factors in groups.items():
            form += f"## {region}\n"
            for factor in factors:
                info = self.FACTORS[factor]
                current = self.scores['scores'].get(factor, 5.0)
                form += f"{factor}: {current:.1f}  # {info['name']}\n"
            form += "\n"
        
        form += "# Copy this file, update scores, then run:\n"
        form += "# python scripts/update_geopolitical_scores.py scores.txt\n"
        
        return form
