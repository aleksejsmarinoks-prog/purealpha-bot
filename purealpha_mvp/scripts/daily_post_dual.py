"""
Dual-Channel Auto-Posting Bot
Posts to TWO Telegram channels (Russian + English) + LinkedIn

Updated version for 2-channel setup
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_ingestion_real import RealDataIngestion
from src.regime_detection import RegimeDetector
from src.portfolio_builder import PortfolioBuilder
from src.content_generator import ContentGenerator
from src.geopolitical_scorer import GeopoliticalScorer

import logging
from datetime import datetime
import asyncio

# Telegram bot
try:
    from telegram import Bot
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️  python-telegram-bot not installed")
    print("Install: pip install python-telegram-bot")

# LinkedIn API
try:
    from linkedin_api import Linkedin
    LINKEDIN_AVAILABLE = True
except ImportError:
    LINKEDIN_AVAILABLE = False
    print("⚠️  linkedin-api not installed")
    print("Install: pip install linkedin-api")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DualChannelPoster:
    """
    Automated daily posting to:
    - Telegram RU (Russian channel)
    - Telegram EN (English channel)  
    - LinkedIn (English)
    """
    
    def __init__(self):
        """Initialize all components"""
        
        # Data & Analysis
        self.data_ingestion = RealDataIngestion()
        self.regime_detector = RegimeDetector()
        self.portfolio_builder = PortfolioBuilder()
        self.content_generator = ContentGenerator()
        self.geo_scorer = GeopoliticalScorer()
        
        # Telegram (ONE bot, TWO channels)
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        telegram_channel_ru = os.getenv('TELEGRAM_CHANNEL_RU')  # Russian channel
        telegram_channel_en = os.getenv('TELEGRAM_CHANNEL_EN')  # English channel
        
        if TELEGRAM_AVAILABLE and telegram_token:
            self.telegram_bot = Bot(token=telegram_token)
            self.telegram_channel_ru = telegram_channel_ru
            self.telegram_channel_en = telegram_channel_en
            
            if telegram_channel_ru:
                logger.info(f"✓ Telegram RU channel: {telegram_channel_ru}")
            else:
                logger.warning("⚠️  TELEGRAM_CHANNEL_RU not set")
            
            if telegram_channel_en:
                logger.info(f"✓ Telegram EN channel: {telegram_channel_en}")
            else:
                logger.warning("⚠️  TELEGRAM_CHANNEL_EN not set")
        else:
            self.telegram_bot = None
            logger.warning("⚠️  Telegram not configured")
        
        # LinkedIn
        linkedin_email = os.getenv('LINKEDIN_EMAIL')
        linkedin_password = os.getenv('LINKEDIN_PASSWORD')
        
        if LINKEDIN_AVAILABLE and linkedin_email and linkedin_password:
            try:
                self.linkedin = Linkedin(linkedin_email, linkedin_password)
                logger.info("✓ LinkedIn authenticated")
            except Exception as e:
                logger.error(f"LinkedIn auth failed: {e}")
                self.linkedin = None
        else:
            self.linkedin = None
            logger.warning("⚠️  LinkedIn not configured")
    
    async def generate_and_post(self):
        """Main workflow: analyze → generate → post to 2 channels"""
        
        logger.info("=" * 60)
        logger.info("STARTING DUAL-CHANNEL POST WORKFLOW")
        logger.info("=" * 60)
        
        try:
            # 1. Fetch market data
            logger.info("\n[1/6] Fetching market data...")
            market_data = self.data_ingestion.fetch_all_parameters(use_cache=False)
            logger.info(f"✓ Fetched {len(market_data)} parameters")
            
            # 2. Detect regime
            logger.info("\n[2/6] Detecting market regime...")
            regime_result = self.regime_detector.detect_regime(market_data)
            lsi_result = self.regime_detector.calculate_lsi(market_data)
            
            logger.info(f"✓ Regime: {regime_result['regime']}")
            logger.info(f"✓ Confidence: {regime_result['confidence']:.1%}")
            logger.info(f"✓ LSI: {lsi_result['lsi']:.1f} ({lsi_result['status']})")
            
            # 3. Build sample portfolio
            logger.info("\n[3/6] Building portfolio...")
            portfolio = self.portfolio_builder.build_portfolio(
                capital=10000,
                risk_level="MEDIUM",
                regime_allocation=regime_result['allocation'],
                constraints=[]
            )
            logger.info("✓ Portfolio built")
            
            # 4. Get geopolitical context
            logger.info("\n[4/6] Getting geopolitical context...")
            geo_status = self.geo_scorer.get_status_summary()
            logger.info(f"✓ Geo score: {geo_status['total_score']:.1f} ({geo_status['status']})")
            
            # Add geo score to market data
            market_data['geopolitical_score'] = geo_status['total_score']
            market_data['geopolitical_status'] = geo_status['status']
            market_data['top_geo_risks'] = [r['name'] for r in geo_status['top_risks']]
            
            # 5. Generate content (RU + EN)
            logger.info("\n[5/6] Generating content...")
            tg_post_ru, linkedin_post_en = self.content_generator.generate_daily_analysis(
                market_data=market_data,
                regime=regime_result['regime'],
                regime_confidence=regime_result['confidence'],
                lsi=lsi_result['lsi'],
                lsi_status=lsi_result['status'],
                portfolio=portfolio
            )
            
            logger.info("✓ Content generated")
            logger.info(f"  - TG RU post: {len(tg_post_ru)} chars")
            logger.info(f"  - LinkedIn/TG EN post: {len(linkedin_post_en)} chars")
            
            # 6. Post to platforms
            logger.info("\n[6/6] Posting to platforms...")
            
            # Post to Telegram RU channel
            if self.telegram_bot and self.telegram_channel_ru:
                try:
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel_ru,
                        text=tg_post_ru,
                        parse_mode='HTML'
                    )
                    logger.info(f"✓ Posted to Telegram RU ({self.telegram_channel_ru})")
                except TelegramError as e:
                    logger.error(f"✗ Telegram RU post failed: {e}")
            else:
                logger.warning("⊘ Telegram RU not configured, showing preview:")
                logger.info(tg_post_ru[:500] + "...")
            
            # Post to Telegram EN channel
            if self.telegram_bot and self.telegram_channel_en:
                try:
                    await self.telegram_bot.send_message(
                        chat_id=self.telegram_channel_en,
                        text=linkedin_post_en,
                        parse_mode='HTML'
                    )
                    logger.info(f"✓ Posted to Telegram EN ({self.telegram_channel_en})")
                except TelegramError as e:
                    logger.error(f"✗ Telegram EN post failed: {e}")
            else:
                logger.warning("⊘ Telegram EN not configured, showing preview:")
                logger.info(linkedin_post_en[:500] + "...")
            
            # Post to LinkedIn
            if self.linkedin:
                try:
                    self.linkedin.post(linkedin_post_en)
                    logger.info("✓ Posted to LinkedIn")
                except Exception as e:
                    logger.error(f"✗ LinkedIn post failed: {e}")
            else:
                logger.warning("⊘ LinkedIn not configured")
            
            # Log posts to file
            self._save_posts(tg_post_ru, linkedin_post_en, regime_result, lsi_result)
            
            logger.info("\n" + "=" * 60)
            logger.info("DUAL-CHANNEL POST WORKFLOW COMPLETE ✓")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}", exc_info=True)
            raise
    
    def _save_posts(self, tg_post_ru: str, linkedin_post_en: str, regime: dict, lsi: dict):
        """Save posts to archive"""
        
        os.makedirs('post_archive', exist_ok=True)
        
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = f"post_archive/{date_str}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# PUREALPHA DUAL-CHANNEL POST - {date_str}\n\n")
            f.write(f"Regime: {regime['regime']}\n")
            f.write(f"Confidence: {regime['confidence']:.1%}\n")
            f.write(f"LSI: {lsi['lsi']:.1f} ({lsi['status']})\n\n")
            f.write("=" * 60 + "\n")
            f.write("TELEGRAM RU (RUSSIAN CHANNEL)\n")
            f.write("=" * 60 + "\n\n")
            f.write(tg_post_ru)
            f.write("\n\n")
            f.write("=" * 60 + "\n")
            f.write("TELEGRAM EN + LINKEDIN (ENGLISH)\n")
            f.write("=" * 60 + "\n\n")
            f.write(linkedin_post_en)
            f.write("\n")
        
        logger.info(f"✓ Saved to {filename}")

async def main():
    """Main entry point"""
    
    print("""
╔════════════════════════════════════════════════╗
║   PUREALPHA DUAL-CHANNEL POSTER                ║
║   TG RU + TG EN + LinkedIn                     ║
╚════════════════════════════════════════════════╝
""")
    
    poster = DualChannelPoster()
    await poster.generate_and_post()

if __name__ == "__main__":
    asyncio.run(main())
