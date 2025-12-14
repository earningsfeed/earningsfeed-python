"""
Earnings Feed Python SDK

Official Python client for the Earnings Feed API - SEC filings,
insider transactions, and institutional holdings.

Example:
    >>> from earningsfeed import EarningsFeed
    >>> client = EarningsFeed("your_api_key")
    >>>
    >>> # Get recent filings
    >>> filings = client.filings.list(ticker="AAPL", limit=10)
    >>> for filing in filings.items:
    ...     print(f"{filing.form_type}: {filing.title}")
    >>>
    >>> # Get company profile
    >>> apple = client.companies.get(320193)
    >>> print(apple.name, apple.primary_ticker)
"""

from .client import EarningsFeed
from .exceptions import (
    APIError,
    AuthenticationError,
    EarningsFeedError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import (
    Address,
    Company,
    CompanySearchResponse,
    CompanySearchResult,
    Filing,
    FilingCompany,
    FilingDetail,
    FilingDocument,
    FilingRole,
    FilingsResponse,
    InsiderTransaction,
    InsiderTransactionsResponse,
    InstitutionalHolding,
    InstitutionalHoldingsResponse,
    SicCode,
    Ticker,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "EarningsFeed",
    # Exceptions
    "EarningsFeedError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "APIError",
    # Models
    "Filing",
    "FilingCompany",
    "FilingDetail",
    "FilingDocument",
    "FilingRole",
    "FilingsResponse",
    "InsiderTransaction",
    "InsiderTransactionsResponse",
    "InstitutionalHolding",
    "InstitutionalHoldingsResponse",
    "Company",
    "CompanySearchResult",
    "CompanySearchResponse",
    "Ticker",
    "SicCode",
    "Address",
]
