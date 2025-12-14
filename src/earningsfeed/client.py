"""Earnings Feed API client."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Any, Literal

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from .models import (
    Company,
    CompanySearchResponse,
    CompanySearchResult,
    Filing,
    FilingDetail,
    FilingsResponse,
    InsiderTransaction,
    InsiderTransactionsResponse,
    InstitutionalHolding,
    InstitutionalHoldingsResponse,
)

DEFAULT_BASE_URL = "https://earningsfeed.com"
DEFAULT_TIMEOUT = 30.0


class EarningsFeed:
    """
    Client for the Earnings Feed API.

    Args:
        api_key: Your Earnings Feed API key.
        base_url: API base URL (default: https://earningsfeed.com).
        timeout: Request timeout in seconds (default: 30).

    Example:
        >>> from earningsfeed import EarningsFeed
        >>> client = EarningsFeed("your_api_key")
        >>> filings = client.filings.list(ticker="AAPL", limit=10)
        >>> for filing in filings:
        ...     print(f"{filing.form_type}: {filing.title}")
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "earningsfeed-python/0.1.0",
            },
            timeout=timeout,
        )

        # Resource namespaces
        self.filings = FilingsResource(self)
        self.insider = InsiderResource(self)
        self.institutional = InstitutionalResource(self)
        self.companies = CompaniesResource(self)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request."""
        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        response = self._client.request(method, path, params=params)

        if response.status_code == 401:
            raise AuthenticationError("Invalid or missing API key")
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {path}")
        if response.status_code == 429:
            reset_at = response.headers.get("X-RateLimit-Reset")
            raise RateLimitError(
                "Rate limit exceeded",
                reset_at=int(reset_at) if reset_at else None,
            )
        if response.status_code == 400:
            data = response.json()
            raise ValidationError(data.get("error", "Invalid request"))
        if response.status_code >= 400:
            try:
                data = response.json()
                raise APIError(
                    data.get("error", "Unknown error"),
                    status_code=response.status_code,
                    code=data.get("code"),
                )
            except ValueError:
                raise APIError(
                    f"HTTP {response.status_code}",
                    status_code=response.status_code,
                ) from None

        return response.json()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> EarningsFeed:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class FilingsResource:
    """SEC filings resource."""

    def __init__(self, client: EarningsFeed):
        self._client = client

    def list(
        self,
        *,
        limit: int = 25,
        cursor: str | None = None,
        forms: str | list[str] | None = None,
        cik: int | None = None,
        ticker: str | None = None,
        status: Literal["all", "final", "provisional"] = "all",
        issuer_type: Literal["company", "person"] | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        q: str | None = None,
    ) -> FilingsResponse:
        """
        List SEC filings.

        Args:
            limit: Number of items (1-100, default 25).
            cursor: Pagination cursor from previous response.
            forms: Form types to filter (e.g., "10-K" or ["10-K", "10-Q"]).
            cik: Filter by company CIK.
            ticker: Filter by stock ticker.
            status: Filter by status ("all", "final", "provisional").
            issuer_type: Filter by entity type ("company" or "person").
            start_date: Filter filings on or after this date.
            end_date: Filter filings on or before this date.
            q: Search query (company name, accession number, or title).

        Returns:
            FilingsResponse with items, next_cursor, and has_more.
        """
        if isinstance(forms, list):
            forms = ",".join(forms)
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        data = self._client._request(
            "GET",
            "/api/v1/filings",
            params={
                "limit": limit,
                "cursor": cursor,
                "forms": forms,
                "cik": cik,
                "ticker": ticker,
                "status": status,
                "issuerType": issuer_type,
                "startDate": start_date,
                "endDate": end_date,
                "q": q,
            },
        )
        return FilingsResponse.model_validate(data)

    def iter(
        self,
        *,
        forms: str | list[str] | None = None,
        cik: int | None = None,
        ticker: str | None = None,
        status: Literal["all", "final", "provisional"] = "all",
        issuer_type: Literal["company", "person"] | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        q: str | None = None,
        limit: int = 100,
    ) -> Iterator[Filing]:
        """
        Iterate through all filings matching the filters.

        Automatically handles pagination. Use limit to control page size.
        """
        cursor = None
        while True:
            response = self.list(
                limit=limit,
                cursor=cursor,
                forms=forms,
                cik=cik,
                ticker=ticker,
                status=status,
                issuer_type=issuer_type,
                start_date=start_date,
                end_date=end_date,
                q=q,
            )
            yield from response.items
            if not response.has_more:
                break
            cursor = response.next_cursor

    def get(self, accession: str) -> FilingDetail:
        """
        Get detailed information about a specific filing.

        Args:
            accession: SEC accession number (with or without dashes).

        Returns:
            FilingDetail with documents and roles.
        """
        data = self._client._request("GET", f"/api/v1/filings/{accession}")
        return FilingDetail.model_validate(data)


class InsiderResource:
    """Insider transactions resource."""

    def __init__(self, client: EarningsFeed):
        self._client = client

    def list(
        self,
        *,
        limit: int = 25,
        cursor: str | None = None,
        cik: int | None = None,
        ticker: str | None = None,
        insider_cik: int | None = None,
        direction: Literal["buy", "sell"] | None = None,
        codes: str | list[str] | None = None,
        derivative: bool | None = None,
        min_value: float | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> InsiderTransactionsResponse:
        """
        List insider transactions.

        Args:
            limit: Number of items (1-100, default 25).
            cursor: Pagination cursor.
            cik: Filter by company CIK.
            ticker: Filter by stock ticker.
            insider_cik: Filter by insider's CIK.
            direction: Filter by direction ("buy" or "sell").
            codes: Transaction codes (e.g., "P,S" or ["P", "S"]).
            derivative: Filter derivative (True) or equity (False) transactions.
            min_value: Minimum transaction value.
            start_date: Filter transactions on or after this date.
            end_date: Filter transactions on or before this date.

        Returns:
            InsiderTransactionsResponse with items, next_cursor, and has_more.
        """
        if isinstance(codes, list):
            codes = ",".join(codes)
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        data = self._client._request(
            "GET",
            "/api/v1/insider/transactions",
            params={
                "limit": limit,
                "cursor": cursor,
                "cik": cik,
                "ticker": ticker,
                "insiderCik": insider_cik,
                "direction": direction,
                "codes": codes,
                "derivative": derivative,
                "minValue": min_value,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return InsiderTransactionsResponse.model_validate(data)

    def iter(
        self,
        *,
        cik: int | None = None,
        ticker: str | None = None,
        insider_cik: int | None = None,
        direction: Literal["buy", "sell"] | None = None,
        codes: str | list[str] | None = None,
        derivative: bool | None = None,
        min_value: float | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        limit: int = 100,
    ) -> Iterator[InsiderTransaction]:
        """Iterate through all insider transactions matching the filters."""
        cursor = None
        while True:
            response = self.list(
                limit=limit,
                cursor=cursor,
                cik=cik,
                ticker=ticker,
                insider_cik=insider_cik,
                direction=direction,
                codes=codes,
                derivative=derivative,
                min_value=min_value,
                start_date=start_date,
                end_date=end_date,
            )
            yield from response.items
            if not response.has_more:
                break
            cursor = response.next_cursor


class InstitutionalResource:
    """Institutional holdings resource."""

    def __init__(self, client: EarningsFeed):
        self._client = client

    def list(
        self,
        *,
        limit: int = 25,
        cursor: str | None = None,
        company_cik: int | None = None,
        ticker: str | None = None,
        cusip: str | None = None,
        manager_cik: int | None = None,
        manager_name: str | None = None,
        report_period: str | None = None,
        put_call: Literal["put", "call", "equity"] | None = None,
        min_value: int | None = None,
        min_shares: int | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
    ) -> InstitutionalHoldingsResponse:
        """
        List institutional holdings from 13F filings.

        Args:
            limit: Number of items (1-100, default 25).
            cursor: Pagination cursor.
            company_cik: Filter by company CIK.
            ticker: Filter by stock ticker.
            cusip: Filter by CUSIP.
            manager_cik: Filter by manager CIK.
            manager_name: Filter by manager name (partial match).
            report_period: Filter by report period (YYYY-MM-DD).
            put_call: Filter by position type ("put", "call", "equity").
            min_value: Minimum position value.
            min_shares: Minimum number of shares.
            start_date: Filter filings on or after this date.
            end_date: Filter filings on or before this date.

        Returns:
            InstitutionalHoldingsResponse with items, next_cursor, and has_more.
        """
        if isinstance(start_date, date):
            start_date = start_date.isoformat()
        if isinstance(end_date, date):
            end_date = end_date.isoformat()

        data = self._client._request(
            "GET",
            "/api/v1/institutional/holdings",
            params={
                "limit": limit,
                "cursor": cursor,
                "companyCik": company_cik,
                "ticker": ticker,
                "cusip": cusip,
                "managerCik": manager_cik,
                "managerName": manager_name,
                "reportPeriod": report_period,
                "putCall": put_call,
                "minValue": min_value,
                "minShares": min_shares,
                "startDate": start_date,
                "endDate": end_date,
            },
        )
        return InstitutionalHoldingsResponse.model_validate(data)

    def iter(
        self,
        *,
        company_cik: int | None = None,
        ticker: str | None = None,
        cusip: str | None = None,
        manager_cik: int | None = None,
        manager_name: str | None = None,
        report_period: str | None = None,
        put_call: Literal["put", "call", "equity"] | None = None,
        min_value: int | None = None,
        min_shares: int | None = None,
        start_date: date | str | None = None,
        end_date: date | str | None = None,
        limit: int = 100,
    ) -> Iterator[InstitutionalHolding]:
        """Iterate through all institutional holdings matching the filters."""
        cursor = None
        while True:
            response = self.list(
                limit=limit,
                cursor=cursor,
                company_cik=company_cik,
                ticker=ticker,
                cusip=cusip,
                manager_cik=manager_cik,
                manager_name=manager_name,
                report_period=report_period,
                put_call=put_call,
                min_value=min_value,
                min_shares=min_shares,
                start_date=start_date,
                end_date=end_date,
            )
            yield from response.items
            if not response.has_more:
                break
            cursor = response.next_cursor


class CompaniesResource:
    """Companies resource."""

    def __init__(self, client: EarningsFeed):
        self._client = client

    def get(self, cik: int) -> Company:
        """
        Get company profile by CIK.

        Args:
            cik: SEC Central Index Key.

        Returns:
            Company profile with tickers, addresses, and metadata.
        """
        data = self._client._request("GET", f"/api/v1/companies/{cik}")
        return Company.model_validate(data)

    def search(
        self,
        *,
        q: str | None = None,
        ticker: str | None = None,
        sic_code: int | None = None,
        category: str | None = None,
        entity_type: str | None = None,
        state: str | None = None,
        has_insider_transactions: bool | None = None,
        limit: int = 25,
        cursor: str | None = None,
    ) -> CompanySearchResponse:
        """
        Search for companies.

        Args:
            q: Search query (name or ticker).
            ticker: Exact ticker match.
            sic_code: Filter by SIC code.
            category: Filter by SEC category.
            entity_type: Filter by entity type.
            state: Filter by state of incorporation.
            has_insider_transactions: Filter by insider filing activity.
            limit: Number of items (1-100, default 25).
            cursor: Pagination cursor.

        Returns:
            CompanySearchResponse with items, next_cursor, and has_more.
        """
        data = self._client._request(
            "GET",
            "/api/v1/companies/search",
            params={
                "q": q,
                "ticker": ticker,
                "sicCode": sic_code,
                "category": category,
                "entityType": entity_type,
                "state": state,
                "hasInsiderTransactions": has_insider_transactions,
                "limit": limit,
                "cursor": cursor,
            },
        )
        return CompanySearchResponse.model_validate(data)

    def iter_search(
        self,
        *,
        q: str | None = None,
        ticker: str | None = None,
        sic_code: int | None = None,
        category: str | None = None,
        entity_type: str | None = None,
        state: str | None = None,
        has_insider_transactions: bool | None = None,
        limit: int = 100,
    ) -> Iterator[CompanySearchResult]:
        """Iterate through all companies matching the search."""
        cursor = None
        while True:
            response = self.search(
                q=q,
                ticker=ticker,
                sic_code=sic_code,
                category=category,
                entity_type=entity_type,
                state=state,
                has_insider_transactions=has_insider_transactions,
                limit=limit,
                cursor=cursor,
            )
            yield from response.items
            if not response.has_more:
                break
            cursor = response.next_cursor
