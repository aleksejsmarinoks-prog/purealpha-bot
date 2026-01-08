"""
Content Generator for Analytical Posts
- Telegram (Russian): Deep, contrarian, data-heavy
- LinkedIn (English): Professional, authoritative

Generates daily market analysis based on PureAlpha regime detection
"""
import anthropic
from typing import Dict, Tuple
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentGenerator:
    """
    Auto-generate analytical posts for TG (Russian) + LinkedIn (English)
    
    Style: Deep analysis, no fluff, data-driven, contrarian when appropriate
    Goal: Build authority, drive traffic to PureAlpha
    """
    
    def __init__(self, anthropic_api_key: str = None):
        """
        Initialize Claude API for content generation
        
        Args:
            anthropic_api_key: Anthropic API key (or use ANTHROPIC_API_KEY env var)
        """
        if anthropic_api_key is None:
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY required for content generation")
        
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        logger.info("Content Generator initialized")
    
    def generate_daily_analysis(
        self,
        market_data: Dict,
        regime: str,
        regime_confidence: float,
        lsi: float,
        lsi_status: str,
        portfolio: Dict
    ) -> Tuple[str, str]:
        """
        Generate daily market analysis
        
        Args:
            market_data: Dictionary of market parameters
            regime: Current market regime (e.g. "GOLDILOCKS")
            regime_confidence: Confidence score 0-1
            lsi: Liquidity Stress Index 0-100
            lsi_status: "NORMAL", "MODERATE_STRESS", etc
            portfolio: Recommended portfolio allocation
            
        Returns:
            (telegram_post, linkedin_post)
        """
        
        # Extract key metrics
        key_metrics = self._extract_key_metrics(market_data)
        
        # Build prompt for Claude
        prompt = self._build_prompt(
            regime=regime,
            confidence=regime_confidence,
            lsi=lsi,
            lsi_status=lsi_status,
            metrics=key_metrics,
            portfolio=portfolio
        )
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.7,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = response.content[0].text
            
            # Parse response into TG (Russian) and LinkedIn (English)
            tg_post, linkedin_post = self._parse_response(content)
            
            logger.info("✓ Content generated successfully")
            
            return tg_post, linkedin_post
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    def _extract_key_metrics(self, market_data: Dict) -> Dict:
        """Extract most important metrics for analysis"""
        key_params = [
            'vix', 'sp500', 'dxy', 'oil_wti', 'gold_price',
            'btc_price', 'eth_price', 'unemployment',
            'fed_funds_rate', 'treasury_10y', 'yield_curve_slope',
            'ig_credit_spread', 'hy_credit_spread'
        ]
        
        metrics = {}
        for param in key_params:
            if param in market_data:
                metrics[param] = market_data[param]
        
        return metrics
    
    def _build_prompt(
        self,
        regime: str,
        confidence: float,
        lsi: float,
        lsi_status: str,
        metrics: Dict,
        portfolio: Dict
    ) -> str:
        """Build prompt for Claude"""
        
        today = datetime.now().strftime("%d.%m.%Y")
        
        prompt = f"""
Generate TWO analytical market posts based on current PureAlpha data.

TODAY'S DATE: {today}

CURRENT MARKET STATE:
- Regime: {regime}
- Confidence: {confidence:.1%}
- LSI (Liquidity Stress): {lsi:.1f}/100 ({lsi_status})

KEY METRICS:
{self._format_metrics(metrics)}

RECOMMENDED PORTFOLIO:
{self._format_portfolio(portfolio)}

===================================================
GENERATE TWO POSTS:
===================================================

POST 1: TELEGRAM (RUSSIAN)
---------------------------
Language: Russian
Length: 1500-2000 characters
Style: Deep, analytical, contrarian, no fluff
Tone: Authoritative but accessible
Emojis: OK (strategic use)

Structure:
1. Headline: Hook with regime name (2-3 words)
2. Current situation: 3-4 key metrics with commentary
3. Causal analysis: What CAUSES what (not correlations)
4. Geopolitical context: If relevant (Hormuz, Taiwan, EU, etc)
5. Strategy: PureAlpha's recommendation
6. Warning/Opportunity: What to watch
7. Call-to-action: Subtle reference to PureAlpha access

Requirements:
- Use SPECIFIC numbers from metrics above
- Reference causal relationships (X → Y → Z)
- Contrarian perspective when appropriate
- No generic advice ("diversify", etc) - be specific
- Mention PureAlpha as "мы" or "наш анализ"
- End with subtle CTA about getting PureAlpha access

Example tone:
"Рынок вошёл в режим GOLDILOCKS, но это не повод расслабляться. 
VIX 18.5 + LSI 38 говорят о скрытом напряжении. Причинно-следственная 
цепочка Fed→DXY→Gold (валидация 0.82) показывает..."

---------------------------

POST 2: LINKEDIN (ENGLISH)
---------------------------
Language: English
Length: 1000-1500 characters
Style: Professional, data-driven, institutional tone
Tone: Expert commentary, confident
Emojis: Minimal (1-2 max)

Structure:
1. Headline: Professional hook
2. Market state: Current regime + key drivers
3. Analysis: Causal relationships (institutional language)
4. Portfolio implications: Strategic allocation
5. Risk factors: What could change
6. Sign-off: Reference to PureAlpha's methodology

Requirements:
- Use institutional language (LSI, regime detection, causal validation)
- Cite specific metrics with precision
- Reference Causal AI methodology
- Position PureAlpha as institutional-grade tool
- Target audience: Investors, financial professionals, advisors
- End with professional sign-off + link suggestion

Example tone:
"Markets entered GOLDILOCKS regime today (confidence: 75%). 
Our Liquidity Stress Index at 38 indicates moderate pressure. 
Causal validation (5-level framework) confirms Fed→DXY→Gold 
transmission mechanism..."

===================================================
FORMAT YOUR RESPONSE:
===================================================

[TELEGRAM_RU]
<your Russian Telegram post here>

[LINKEDIN_EN]
<your English LinkedIn post here>

===================================================

CRITICAL RULES:
1. NO generic advice - be specific with numbers
2. NO correlations - only CAUSAL relationships
3. NO fluff - every sentence adds value
4. YES data-driven - cite metrics
5. YES contrarian - challenge conventional wisdom when appropriate
6. YES authority - position PureAlpha as institutional-grade

Generate both posts now.
"""
        
        return prompt
    
    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics for prompt"""
        lines = []
        for key, value in metrics.items():
            if isinstance(value, float):
                if value > 1:
                    lines.append(f"- {key}: {value:.2f}")
                else:
                    lines.append(f"- {key}: {value:.4f}")
            else:
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)
    
    def _format_portfolio(self, portfolio: Dict) -> str:
        """Format portfolio for prompt"""
        if 'allocations' in portfolio:
            allocs = portfolio['allocations']
            lines = []
            for asset, amount in allocs.items():
                pct = (amount / sum(allocs.values())) * 100
                lines.append(f"- {asset}: {pct:.1f}% (${amount:,.0f})")
            return "\n".join(lines)
        return "No portfolio data"
    
    def _parse_response(self, content: str) -> Tuple[str, str]:
        """
        Parse Claude's response into two posts
        
        Returns:
            (telegram_russian, linkedin_english)
        """
        # Split by markers
        parts = content.split('[TELEGRAM_RU]')
        if len(parts) < 2:
            raise ValueError("Response missing [TELEGRAM_RU] marker")
        
        after_tg = parts[1]
        
        tg_parts = after_tg.split('[LINKEDIN_EN]')
        if len(tg_parts) < 2:
            raise ValueError("Response missing [LINKEDIN_EN] marker")
        
        telegram_post = tg_parts[0].strip()
        linkedin_post = tg_parts[1].strip()
        
        # Clean up any remaining markers
        telegram_post = telegram_post.replace('[TELEGRAM_RU]', '').strip()
        linkedin_post = linkedin_post.replace('[LINKEDIN_EN]', '').strip()
        
        return telegram_post, linkedin_post
    
    def generate_geopolitical_special(
        self,
        event: str,
        impact_score: float,
        market_data: Dict
    ) -> Tuple[str, str]:
        """
        Generate special analysis for major geopolitical events
        
        Args:
            event: Event description (e.g. "Hormuz Strait closure threat")
            impact_score: 0-10 severity
            market_data: Current market state
            
        Returns:
            (telegram_post, linkedin_post)
        """
        
        prompt = f"""
Generate URGENT geopolitical analysis posts.

EVENT: {event}
IMPACT SCORE: {impact_score}/10
DATE: {datetime.now().strftime("%d.%m.%Y")}

MARKET DATA:
{self._format_metrics(self._extract_key_metrics(market_data))}

Generate TWO posts (same format as daily analysis):

1. TELEGRAM (RUSSIAN): 2000 chars, urgent tone, specific implications
2. LINKEDIN (ENGLISH): 1500 chars, professional analysis, strategic response

Focus on:
- Causal chain: Event → Market impact
- Primary effects (immediate: 24-48 hours)
- Secondary effects (cascading: 1-2 weeks)
- Portfolio implications (what to do NOW)
- Risk scenarios (best/base/worst case)

Use same format markers: [TELEGRAM_RU] and [LINKEDIN_EN]
"""
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                temperature=0.8,  # Slightly higher for urgent content
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = response.content[0].text
            return self._parse_response(content)
            
        except Exception as e:
            logger.error(f"Geopolitical content generation failed: {e}")
            raise
