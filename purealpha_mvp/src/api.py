"""
PureAlpha 3.1 API
FastAPI application for portfolio generation
"""

import logging
import time
from typing import Dict, Optional, List
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .regime_detection import RegimeDetector
from .portfolio_builder import PortfolioBuilder
from .causal_validation import CausalValidationEngine
from .data_ingestion_real import RealDataIngestion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(
    title="PureAlpha 3.1 API",
    version="1.0.0",
    description="AI Investment Copilot using Causal AI"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
regime_detector = RegimeDetector()
portfolio_builder = PortfolioBuilder()
causal_engine = CausalValidationEngine()
data_ingestion = RealDataIngestion()

logger.info("PureAlpha API initialized successfully")
logger.info("Real data sources enabled - using FRED, Yahoo Finance, CoinGecko")


# Request/Response models
class InvestmentQuery(BaseModel):
    capital: float = Field(..., gt=0, le=10_000_000, description="Investment capital in USD")
    years: int = Field(default=1, ge=1, le=30, description="Investment horizon in years")
    risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$", description="Risk tolerance level")
    constraints: Optional[Dict] = Field(default={}, description="Portfolio constraints")


class PortfolioResponse(BaseModel):
    status: str
    query_id: str
    portfolio: Dict[str, float]
    metrics: Dict
    market_context: Dict
    explanation: str
    warnings: List[str]
    timestamp: str


# Middleware for logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Duration: {duration:.4f}s"
    )
    
    return response


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "PureAlpha 3.1 API",
        "version": "1.0.0",
        "description": "AI Investment Copilot using Causal AI",
        "data_sources": "REAL (FRED + Yahoo Finance + CoinGecko)",
        "parameters": "31 real parameters",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "analyze": "/api/v1/analyze",
            "regimes": "/api/v1/regimes",
            "assets": "/api/v1/assets",
            "market": "/api/v1/market",
            "refresh": "/api/v1/market/refresh"
        }
    }
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "data_sources": {
            "FRED": data_ingestion.fred is not None,
            "Yahoo Finance": data_ingestion.yahoo is not None,
            "CoinGecko": data_ingestion.coingecko is not None
        }
    }


# Market data refresh endpoint
@app.get("/api/v1/market/refresh")
async def refresh_market_data():
    """
    Manually refresh market data from all sources
    
    Returns current market state with fresh data
    """
    try:
        logger.info("Manual market data refresh requested")
        
        # Fetch fresh data (bypass cache)
        market_data = data_ingestion.fetch_all_parameters(use_cache=False)
        
        # Validate
        is_valid, warnings = data_ingestion.validate_data(market_data)
        
        # Get stats
        stats = data_ingestion.get_fetch_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "parameters_fetched": len(market_data),
            "validation": {
                "passed": is_valid,
                "warnings": warnings
            },
            "sources": stats['sources_available'],
            "fetch_stats": {
                "total_fetches": stats['total_fetches'],
                "last_fetch": stats['last_fetch_time']
            },
            "sample_data": {
                k: v for k, v in list(market_data.items())[:5]
            }
        }
        
    except Exception as e:
        logger.error(f"Market data refresh failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to refresh market data: {str(e)}"
        )


# Main analysis endpoint
@app.post("/api/v1/analyze", response_model=PortfolioResponse)
async def analyze_portfolio(query: InvestmentQuery):
    """
    Generate personalized portfolio recommendation
    
    - **capital**: Investment amount in USD ($1 - $10M)
    - **years**: Time horizon (1-30 years)
    - **risk_level**: LOW, MEDIUM, or HIGH
    - **constraints**: Optional (no_crypto, us_only, etc.)
    """
    try:
        # Generate query ID
        query_id = f"q_{int(time.time())}"
        
        logger.info(f"Processing query {query_id}: ${query.capital:,.0f}, {query.risk_level} risk")
        
        # Get market data from real sources (with 15min cache)
        try:
            market_data = data_ingestion.fetch_all_parameters(use_cache=True, cache_ttl=900)
            logger.info(f"Fetched {len(market_data)} parameters from real sources")
        except Exception as e:
            logger.error(f"Failed to fetch real market data: {e}")
            raise HTTPException(
                status_code=503,
                detail="Unable to fetch market data. Please try again later."
            )
        
        # Validate data
        is_valid, validation_warnings = data_ingestion.validate_data(market_data)
        if not is_valid:
            logger.warning(f"Market data validation issues: {validation_warnings}")
            # Continue but add warning to response
        
        # Detect regime
        regime_result = regime_detector.detect_regime(market_data)
        
        # Calculate LSI
        lsi_result = regime_detector.calculate_lsi(market_data)
        
        # Build portfolio
        portfolio = portfolio_builder.build_portfolio(
            capital=query.capital,
            risk_level=query.risk_level,
            regime_allocation=regime_result['allocation'],
            constraints=query.constraints
        )
        
        # Generate warnings
        warnings = []
        
        # Add data validation warnings if any
        if not is_valid and validation_warnings:
            for vw in validation_warnings[:2]:  # Max 2 validation warnings
                warnings.append(f"⚠️ Data: {vw}")
        
        if lsi_result['lsi'] > 75:
            warnings.append("⚠️ Critical liquidity stress detected (LSI > 75)")
        elif lsi_result['lsi'] > 50:
            warnings.append("⚠️ Severe liquidity stress detected (LSI > 50)")
        
        if regime_result['confidence'] < 0.5:
            warnings.append("⚠️ Low regime confidence - market transition possible")
        
        # Prepare response
        response = {
            "status": "success",
            "query_id": query_id,
            "portfolio": portfolio['allocations'],
            "metrics": portfolio['metrics'],
            "market_context": {
                "regime": regime_result['regime'],
                "regime_confidence": regime_result['confidence'],
                "regime_description": regime_result['description'],
                "lsi": lsi_result['lsi'],
                "lsi_status": lsi_result['status']
            },
            "explanation": portfolio['explanation'],
            "warnings": warnings,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        logger.info(f"Query {query_id} completed successfully")
        
        return response
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# List all regimes endpoint
@app.get("/api/v1/regimes")
async def list_regimes():
    """
    List all available market regimes with definitions
    """
    try:
        regimes = regime_detector.list_all_regimes()
        
        # Format for response
        formatted = {}
        for name, data in regimes.items():
            formatted[name] = {
                "description": data['description'],
                "expected_return": data['expected_return'],
                "max_drawdown": data['max_drawdown'],
                "allocation": data['allocation']
            }
        
        return {
            "status": "success",
            "count": len(formatted),
            "regimes": formatted
        }
        
    except Exception as e:
        logger.error(f"Failed to list regimes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# List available assets endpoint
@app.get("/api/v1/assets")
async def list_assets():
    """
    List all available assets in the universe
    """
    try:
        return {
            "status": "success",
            "count": len(portfolio_builder.assets),
            "assets": portfolio_builder.assets
        }
        
    except Exception as e:
        logger.error(f"Failed to list assets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Current market state endpoint
@app.get("/api/v1/market")
async def get_market_state():
    """
    Get current market state (regime, LSI, key parameters)
    
    Uses cached data if fresh (15min TTL)
    """
    try:
        # Get market data (with cache)
        market_data = data_ingestion.fetch_all_parameters(use_cache=True, cache_ttl=900)
        
        # Validate
        is_valid, warnings = data_ingestion.validate_data(market_data)
        
        regime_result = regime_detector.detect_regime(market_data)
        lsi_result = regime_detector.calculate_lsi(market_data)
        
        # Get fetch stats
        stats = data_ingestion.get_fetch_stats()
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data_quality": {
                "validation_passed": is_valid,
                "parameters_count": len(market_data),
                "last_fetch": stats['last_fetch_time']
            },
            "regime": {
                "name": regime_result['regime'],
                "confidence": regime_result['confidence'],
                "description": regime_result['description']
            },
            "liquidity": {
                "lsi": lsi_result['lsi'],
                "status": lsi_result['status'],
                "components": lsi_result['components']
            },
            "key_parameters": {
                k: v for k, v in market_data.items() 
                if k in ['vix', 'sp500', 'dxy', 'gold_price', 'btc_price', 
                        'unemployment', 'fed_funds_rate', 'treasury_10y']
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get market state: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
