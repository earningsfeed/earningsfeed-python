"""Pydantic models for Earnings Feed API responses."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class FilingCompany(BaseModel):
    """Company details attached to a filing."""

    cik: int = Field(description="SEC Central Index Key")
    name: str = Field(description="Company name")
    state_of_incorporation: str | None = Field(
        None, alias="stateOfIncorporation", description="State/country code"
    )
    state_of_incorporation_description: str | None = Field(
        None, alias="stateOfIncorporationDescription", description="Full state/country name"
    )
    fiscal_year_end: str | None = Field(
        None, alias="fiscalYearEnd", description="Fiscal year end (MMDD)"
    )


class Filing(BaseModel):
    """SEC filing from the filings feed."""

    accession_number: str = Field(alias="accessionNumber", description="SEC accession number")
    accession_no_dashes: str | None = Field(
        None, alias="accessionNoDashes", description="Accession number without dashes"
    )
    cik: int = Field(description="Filer CIK")
    company_name: str | None = Field(None, alias="companyName")
    form_type: str = Field(alias="formType", description="SEC form type (10-K, 8-K, etc.)")
    filed_at: datetime = Field(alias="filedAt", description="Filing submission time")
    accept_ts: datetime | None = Field(None, alias="acceptTs", description="SEC acceptance time")
    provisional: bool = Field(description="Whether filing is provisional")
    feed_day: str | None = Field(None, alias="feedDay", description="Feed day (YYYY-MM-DD)")
    size_bytes: int = Field(alias="sizeBytes", description="Primary document size")
    url: str = Field(description="SEC EDGAR URL")
    title: str = Field(description="Filing title")
    status: str = Field(description="Filing status")
    updated_at: datetime = Field(alias="updatedAt")
    primary_ticker: str | None = Field(None, alias="primaryTicker")
    primary_exchange: str | None = Field(None, alias="primaryExchange")
    company: FilingCompany | None = None
    sorted_at: datetime = Field(alias="sortedAt", description="Sort timestamp")
    logo_url: str | None = Field(None, alias="logoUrl")
    entity_class: Literal["company", "person"] | None = Field(None, alias="entityClass")


class FilingDocument(BaseModel):
    """Document within a filing."""

    seq: int = Field(description="Document sequence number")
    filename: str = Field(description="Filename on SEC EDGAR")
    doc_type: str = Field(alias="docType", description="Document type")
    description: str | None = Field(None, description="Document description")
    is_primary: bool = Field(alias="isPrimary", description="Whether primary document")


class FilingRole(BaseModel):
    """Entity role in a filing."""

    cik: int = Field(description="Entity CIK")
    role: str = Field(description="Role type (filer, issuer, reporting-owner, etc.)")


class FilingDetail(BaseModel):
    """Detailed filing information."""

    accession_number: str = Field(alias="accessionNumber")
    accession_no_dashes: str | None = Field(None, alias="accessionNoDashes")
    cik: int
    form_type: str = Field(alias="formType")
    filed_at: datetime = Field(alias="filedAt")
    accept_ts: datetime | None = Field(None, alias="acceptTs")
    provisional: bool
    feed_day: str | None = Field(None, alias="feedDay")
    title: str
    url: str
    size_bytes: int = Field(alias="sizeBytes")
    sec_relative_dir: str | None = Field(None, alias="secRelativeDir")
    company_name: str | None = Field(None, alias="companyName")
    primary_ticker: str | None = Field(None, alias="primaryTicker")
    company: FilingCompany | None = None
    documents: list[FilingDocument] = Field(default_factory=list)
    roles: list[FilingRole] = Field(default_factory=list)


class InsiderTransaction(BaseModel):
    """Insider transaction from Form 3/4/5."""

    accession_number: str = Field(alias="accessionNumber")
    filed_at: datetime = Field(alias="filedAt")
    form_type: str = Field(alias="formType")
    person_cik: int = Field(alias="personCik", description="Insider's CIK")
    person_name: str = Field(alias="personName", description="Insider's name")
    company_cik: int = Field(alias="companyCik", description="Company CIK")
    company_name: str | None = Field(None, alias="companyName")
    ticker: str | None = None
    is_director: bool = Field(alias="isDirector")
    is_officer: bool = Field(alias="isOfficer")
    is_ten_percent_owner: bool = Field(alias="isTenPercentOwner")
    is_other: bool = Field(alias="isOther")
    officer_title: str | None = Field(None, alias="officerTitle")
    security_title: str = Field(alias="securityTitle")
    is_derivative: bool = Field(alias="isDerivative")
    transaction_date: str = Field(alias="transactionDate", description="YYYY-MM-DD")
    transaction_code: str = Field(alias="transactionCode", description="P, S, A, M, G, etc.")
    equity_swap_involved: bool = Field(alias="equitySwapInvolved")
    shares: Decimal | None = None
    price_per_share: Decimal | None = Field(None, alias="pricePerShare")
    acquired_disposed: Literal["A", "D"] = Field(alias="acquiredDisposed")
    shares_after: Decimal | None = Field(None, alias="sharesAfter")
    direct_indirect: Literal["D", "I"] = Field(alias="directIndirect")
    ownership_nature: str | None = Field(None, alias="ownershipNature")
    conversion_or_exercise_price: Decimal | None = Field(None, alias="conversionOrExercisePrice")
    exercise_date: str | None = Field(None, alias="exerciseDate")
    expiration_date: str | None = Field(None, alias="expirationDate")
    underlying_security_title: str | None = Field(None, alias="underlyingSecurityTitle")
    underlying_shares: Decimal | None = Field(None, alias="underlyingShares")
    transaction_value: float | None = Field(None, alias="transactionValue")


class InstitutionalHolding(BaseModel):
    """Institutional holding from 13F filing."""

    cusip: str = Field(description="9-character CUSIP")
    issuer_name: str = Field(alias="issuerName")
    class_title: str = Field(alias="classTitle")
    company_cik: int | None = Field(None, alias="companyCik")
    ticker: str | None = None
    value: int = Field(description="Market value in USD")
    shares: int
    shares_type: Literal["SH", "PRN"] = Field(alias="sharesType")
    put_call: Literal["Put", "Call"] | None = Field(None, alias="putCall")
    investment_discretion: Literal["SOLE", "DFND", "OTHER"] = Field(alias="investmentDiscretion")
    other_manager: str | None = Field(None, alias="otherManager")
    voting_sole: int | None = Field(None, alias="votingSole")
    voting_shared: int | None = Field(None, alias="votingShared")
    voting_none: int | None = Field(None, alias="votingNone")
    manager_cik: int = Field(alias="managerCik")
    manager_name: str = Field(alias="managerName")
    report_period_date: str = Field(alias="reportPeriodDate", description="Quarter end YYYY-MM-DD")
    filed_at: datetime = Field(alias="filedAt")
    accession_number: str = Field(alias="accessionNumber")


class Ticker(BaseModel):
    """Stock ticker information."""

    symbol: str
    exchange: str
    is_primary: bool = Field(alias="isPrimary")


class SicCode(BaseModel):
    """Standard Industrial Classification code."""

    code: int
    description: str


class Address(BaseModel):
    """Company address."""

    type: str
    street1: str | None = None
    street2: str | None = None
    city: str | None = None
    state_or_country: str | None = Field(None, alias="stateOrCountry")
    state_or_country_description: str | None = Field(None, alias="stateOrCountryDescription")
    zip_code: str | None = Field(None, alias="zipCode")


class Company(BaseModel):
    """Company profile."""

    cik: int
    name: str
    entity_type: str | None = Field(None, alias="entityType")
    category: str | None = None
    description: str | None = None
    tickers: list[Ticker] = Field(default_factory=list)
    primary_ticker: str | None = Field(None, alias="primaryTicker")
    sic_codes: list[SicCode] = Field(default_factory=list, alias="sicCodes")
    ein: str | None = None
    fiscal_year_end: str | None = Field(None, alias="fiscalYearEnd")
    state_of_incorporation: str | None = Field(None, alias="stateOfIncorporation")
    state_of_incorporation_description: str | None = Field(
        None, alias="stateOfIncorporationDescription"
    )
    phone: str | None = None
    website: str | None = None
    investor_website: str | None = Field(None, alias="investorWebsite")
    addresses: list[Address] = Field(default_factory=list)
    logo_url: str | None = Field(None, alias="logoUrl")
    has_insider_transactions: bool = Field(alias="hasInsiderTransactions")
    is_insider: bool = Field(alias="isInsider")
    updated_at: datetime = Field(alias="updatedAt")


class CompanySearchResult(BaseModel):
    """Company search result."""

    cik: int
    name: str
    ticker: str | None = None
    exchange: str | None = None
    entity_type: str | None = Field(None, alias="entityType")
    category: str | None = None
    sic_code: int | None = Field(None, alias="sicCode")
    sic_description: str | None = Field(None, alias="sicDescription")
    logo_url: str | None = Field(None, alias="logoUrl")


# Response wrappers for paginated endpoints


class PaginatedResponse(BaseModel):
    """Base for paginated responses."""

    next_cursor: str | None = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class FilingsResponse(PaginatedResponse):
    """Response from /filings endpoint."""

    items: list[Filing]


class InsiderTransactionsResponse(PaginatedResponse):
    """Response from /insider/transactions endpoint."""

    items: list[InsiderTransaction]


class InstitutionalHoldingsResponse(PaginatedResponse):
    """Response from /institutional/holdings endpoint."""

    items: list[InstitutionalHolding]


class CompanySearchResponse(PaginatedResponse):
    """Response from /companies/search endpoint."""

    items: list[CompanySearchResult]
