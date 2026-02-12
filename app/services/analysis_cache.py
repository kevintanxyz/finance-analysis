"""
Analysis Cache Service for WealthPoint

BUSINESS VALUE:
- Reduce costs (avoid redundant yfinance calls)
- Faster responses (instant cache hits)
- Better UX (no waiting for repeated queries)

CACHE STRATEGY:
- Risk analysis: 5 minutes TTL (market data changes)
- PDF analysis: No expiry (static data)
- Key format: "{analysis_type}:{ticker}:{params_hash}"
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.database import get_session, AnalysisCache


class AnalysisCacheService:
    """
    Manages caching of analysis results.

    IMPROVEMENT: Intelligent caching with business-appropriate TTLs
    """

    # Cache TTLs by analysis type (in minutes)
    CACHE_TTLS = {
        "risk_analysis": 5,      # Market data changes frequently
        "momentum": 5,           # Technical indicators update often
        "correlation": 10,       # Matrix calculations are expensive
        "options": 1,            # Options prices very volatile
        "pdf_analysis": None,    # PDF data is static (no expiry)
    }

    @staticmethod
    def _generate_cache_key(
        analysis_type: str,
        ticker: str | None,
        parameters: dict
    ) -> str:
        """
        Generate unique cache key from parameters.

        IMPROVEMENT: Hash-based keys for complex parameters
        """
        # Sort parameters for consistent hashing
        params_str = json.dumps(parameters, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]

        if ticker:
            return f"{analysis_type}:{ticker}:{params_hash}"
        else:
            return f"{analysis_type}:{params_hash}"

    @staticmethod
    def get_cached_result(
        portfolio_id: str,
        analysis_type: str,
        ticker: str | None = None,
        parameters: dict | None = None,
    ) -> dict | None:
        """
        Retrieve cached analysis result if valid.

        Args:
            portfolio_id: Portfolio session ID
            analysis_type: Type of analysis (risk_analysis, momentum, etc.)
            ticker: Optional ticker symbol
            parameters: Analysis parameters (for cache key)

        Returns:
            Cached result dict or None if not found/expired

        BUSINESS VALUE: Instant responses for repeated queries
        """
        parameters = parameters or {}

        with get_session() as session:
            # Find matching cache entry
            cache_entry = session.query(AnalysisCache).filter(
                AnalysisCache.portfolio_id == portfolio_id,
                AnalysisCache.analysis_type == analysis_type,
                AnalysisCache.ticker == ticker,
            ).first()

            if not cache_entry:
                return None

            # Check if expired
            if cache_entry.expires_at:
                if datetime.utcnow() > cache_entry.expires_at:
                    # Expired - delete it
                    session.delete(cache_entry)
                    session.commit()
                    return None

            # Parse and return result
            try:
                return json.loads(cache_entry.result_json)
            except json.JSONDecodeError:
                # Corrupted cache - delete it
                session.delete(cache_entry)
                session.commit()
                return None

    @staticmethod
    def save_result(
        portfolio_id: str,
        analysis_type: str,
        result: dict,
        ticker: str | None = None,
        parameters: dict | None = None,
    ) -> None:
        """
        Save analysis result to cache.

        Args:
            portfolio_id: Portfolio session ID
            analysis_type: Type of analysis
            result: Analysis result to cache
            ticker: Optional ticker symbol
            parameters: Analysis parameters

        BUSINESS VALUE: Future queries are instant + free
        """
        parameters = parameters or {}

        # Calculate expiry time
        ttl_minutes = AnalysisCacheService.CACHE_TTLS.get(analysis_type)
        expires_at = None
        if ttl_minutes is not None:
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        with get_session() as session:
            # Check if entry exists
            existing = session.query(AnalysisCache).filter(
                AnalysisCache.portfolio_id == portfolio_id,
                AnalysisCache.analysis_type == analysis_type,
                AnalysisCache.ticker == ticker,
            ).first()

            if existing:
                # Update existing entry
                existing.result_json = json.dumps(result)
                existing.parameters = json.dumps(parameters)
                existing.expires_at = expires_at
                existing.created_at = datetime.utcnow()
            else:
                # Create new entry
                cache_entry = AnalysisCache(
                    id=str(uuid.uuid4()),
                    portfolio_id=portfolio_id,
                    analysis_type=analysis_type,
                    ticker=ticker,
                    parameters=json.dumps(parameters),
                    result_json=json.dumps(result),
                    expires_at=expires_at,
                )
                session.add(cache_entry)

            session.commit()

    @staticmethod
    def invalidate_cache(
        portfolio_id: str,
        analysis_type: str | None = None,
        ticker: str | None = None,
    ) -> int:
        """
        Invalidate (delete) cache entries.

        Args:
            portfolio_id: Portfolio session ID
            analysis_type: Optional filter by analysis type
            ticker: Optional filter by ticker

        Returns:
            Number of entries deleted

        BUSINESS USE CASE: User requests fresh analysis
        """
        with get_session() as session:
            query = session.query(AnalysisCache).filter(
                AnalysisCache.portfolio_id == portfolio_id
            )

            if analysis_type:
                query = query.filter(AnalysisCache.analysis_type == analysis_type)

            if ticker:
                query = query.filter(AnalysisCache.ticker == ticker)

            count = query.delete()
            session.commit()

            return count

    @staticmethod
    def cleanup_expired() -> int:
        """
        Clean up all expired cache entries.

        Returns:
            Number of entries deleted

        BUSINESS VALUE: Keep database lean, prevent bloat

        RECOMMENDED: Run this in a background job every hour
        """
        with get_session() as session:
            count = session.query(AnalysisCache).filter(
                AnalysisCache.expires_at.isnot(None),
                AnalysisCache.expires_at < datetime.utcnow()
            ).delete()

            session.commit()

            return count


__all__ = ["AnalysisCacheService"]
