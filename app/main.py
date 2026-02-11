"""
Portfolio Analysis API

FastAPI service that parses financial valuation PDFs,
structures the data, and provides Q&A + market analysis
for listed positions (Finance-Guru compatible).
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.portfolio import router as portfolio_router

app = FastAPI(
    title="Portfolio Analysis API",
    description=(
        "Upload a valuation PDF, extract structured financial data, "
        "ask questions, and get live market analysis for listed positions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — adjust for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(portfolio_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "Portfolio Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "upload": "POST /api/v1/upload",
            "portfolio": "GET /api/v1/portfolio/{session_id}",
            "ask": "POST /api/v1/ask/{session_id}",
            "listed": "GET /api/v1/listed/{session_id}",
            "market": "GET /api/v1/market/{session_id}",
            "risk": "GET /api/v1/risk/{session_id}/{ticker}",
            "momentum": "GET /api/v1/momentum/{session_id}/{ticker}",
            "correlation": "GET /api/v1/correlation/{session_id}",
        },
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
