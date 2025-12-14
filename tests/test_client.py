"""Tests for the Earnings Feed client."""

import httpx
import pytest
import respx

from earningsfeed import (
    APIError,
    AuthenticationError,
    EarningsFeed,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


@pytest.fixture
def client():
    """Create a test client."""
    return EarningsFeed("test_api_key", base_url="https://api.test.com")


class TestClientInitialization:
    def test_client_sets_auth_header(self, client):
        assert client._client.headers["Authorization"] == "Bearer test_api_key"

    def test_client_sets_user_agent(self, client):
        assert "earningsfeed-python" in client._client.headers["User-Agent"]

    def test_client_context_manager(self):
        with EarningsFeed("test_key") as client:
            assert client._api_key == "test_key"


class TestErrorHandling:
    @respx.mock
    def test_authentication_error(self, client):
        respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )
        with pytest.raises(AuthenticationError):
            client.filings.list()

    @respx.mock
    def test_rate_limit_error(self, client):
        respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(
                429,
                json={"error": "Rate limit exceeded"},
                headers={"X-RateLimit-Reset": "1234567890"},
            )
        )
        with pytest.raises(RateLimitError) as exc_info:
            client.filings.list()
        assert exc_info.value.reset_at == 1234567890

    @respx.mock
    def test_not_found_error(self, client):
        respx.get("https://api.test.com/api/v1/filings/invalid").mock(
            return_value=httpx.Response(404, json={"error": "Not found"})
        )
        with pytest.raises(NotFoundError):
            client.filings.get("invalid")

    @respx.mock
    def test_validation_error(self, client):
        respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(400, json={"error": "Invalid parameter"})
        )
        with pytest.raises(ValidationError):
            client.filings.list()

    @respx.mock
    def test_generic_api_error(self, client):
        respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(
                500, json={"error": "Server error", "code": "INTERNAL_ERROR"}
            )
        )
        with pytest.raises(APIError) as exc_info:
            client.filings.list()
        assert exc_info.value.status_code == 500
        assert exc_info.value.code == "INTERNAL_ERROR"


class TestFilingsResource:
    @respx.mock
    def test_list_filings(self, client):
        respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "accessionNumber": "0000320193-24-000126",
                            "accessionNoDashes": "000032019324000126",
                            "cik": 320193,
                            "companyName": "Apple Inc.",
                            "formType": "10-K",
                            "filedAt": "2024-10-30T16:05:00.000Z",
                            "acceptTs": "2024-10-30T16:05:12.000Z",
                            "provisional": False,
                            "feedDay": "2024-10-30",
                            "sizeBytes": 1234567,
                            "url": "https://sec.gov/...",
                            "title": "Form 10-K",
                            "status": "live",
                            "updatedAt": "2024-10-30T18:00:00.000Z",
                            "primaryTicker": "AAPL",
                            "primaryExchange": "Nasdaq",
                            "company": None,
                            "sortedAt": "2024-10-30T16:05:12.000Z",
                            "logoUrl": None,
                            "entityClass": "company",
                        }
                    ],
                    "nextCursor": "abc123",
                    "hasMore": True,
                },
            )
        )

        response = client.filings.list(ticker="AAPL", limit=10)

        assert len(response.items) == 1
        assert response.items[0].form_type == "10-K"
        assert response.items[0].company_name == "Apple Inc."
        assert response.has_more is True
        assert response.next_cursor == "abc123"

    @respx.mock
    def test_list_filings_with_forms_list(self, client):
        route = respx.get("https://api.test.com/api/v1/filings").mock(
            return_value=httpx.Response(
                200, json={"items": [], "nextCursor": None, "hasMore": False}
            )
        )

        client.filings.list(forms=["10-K", "10-Q"])

        assert "forms=10-K%2C10-Q" in str(route.calls[0].request.url)

    @respx.mock
    def test_get_filing(self, client):
        respx.get("https://api.test.com/api/v1/filings/0000320193-24-000126").mock(
            return_value=httpx.Response(
                200,
                json={
                    "accessionNumber": "0000320193-24-000126",
                    "accessionNoDashes": "000032019324000126",
                    "cik": 320193,
                    "formType": "10-K",
                    "filedAt": "2024-10-30T16:05:00.000Z",
                    "acceptTs": "2024-10-30T16:05:12.000Z",
                    "provisional": False,
                    "feedDay": "2024-10-30",
                    "title": "Form 10-K",
                    "url": "https://sec.gov/...",
                    "sizeBytes": 1234567,
                    "secRelativeDir": "edgar/data/320193/000032019324000126",
                    "companyName": "Apple Inc.",
                    "primaryTicker": "AAPL",
                    "company": None,
                    "documents": [
                        {
                            "seq": 1,
                            "filename": "aapl-20241030.htm",
                            "docType": "10-K",
                            "description": "Annual Report",
                            "isPrimary": True,
                        }
                    ],
                    "roles": [{"cik": 320193, "role": "filer"}],
                },
            )
        )

        filing = client.filings.get("0000320193-24-000126")

        assert filing.accession_number == "0000320193-24-000126"
        assert len(filing.documents) == 1
        assert filing.documents[0].is_primary is True
        assert len(filing.roles) == 1

    @respx.mock
    def test_iter_filings(self, client):
        # First page
        respx.get("https://api.test.com/api/v1/filings").mock(
            side_effect=[
                httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "accessionNumber": "0000000001-24-000001",
                                "accessionNoDashes": "000000000124000001",
                                "cik": 1,
                                "companyName": "Company 1",
                                "formType": "10-K",
                                "filedAt": "2024-10-30T16:05:00.000Z",
                                "acceptTs": "2024-10-30T16:05:12.000Z",
                                "provisional": False,
                                "feedDay": "2024-10-30",
                                "sizeBytes": 100,
                                "url": "https://sec.gov/1",
                                "title": "Filing 1",
                                "status": "live",
                                "updatedAt": "2024-10-30T18:00:00.000Z",
                                "primaryTicker": "C1",
                                "primaryExchange": "NYSE",
                                "company": None,
                                "sortedAt": "2024-10-30T16:05:12.000Z",
                                "logoUrl": None,
                                "entityClass": "company",
                            }
                        ],
                        "nextCursor": "page2",
                        "hasMore": True,
                    },
                ),
                httpx.Response(
                    200,
                    json={
                        "items": [
                            {
                                "accessionNumber": "0000000002-24-000002",
                                "accessionNoDashes": "000000000224000002",
                                "cik": 2,
                                "companyName": "Company 2",
                                "formType": "10-Q",
                                "filedAt": "2024-10-30T16:05:00.000Z",
                                "acceptTs": "2024-10-30T16:05:12.000Z",
                                "provisional": False,
                                "feedDay": "2024-10-30",
                                "sizeBytes": 200,
                                "url": "https://sec.gov/2",
                                "title": "Filing 2",
                                "status": "live",
                                "updatedAt": "2024-10-30T18:00:00.000Z",
                                "primaryTicker": "C2",
                                "primaryExchange": "NYSE",
                                "company": None,
                                "sortedAt": "2024-10-30T16:05:12.000Z",
                                "logoUrl": None,
                                "entityClass": "company",
                            }
                        ],
                        "nextCursor": None,
                        "hasMore": False,
                    },
                ),
            ]
        )

        filings = list(client.filings.iter(limit=1))

        assert len(filings) == 2
        assert filings[0].company_name == "Company 1"
        assert filings[1].company_name == "Company 2"


class TestInsiderResource:
    @respx.mock
    def test_list_insider_transactions(self, client):
        respx.get("https://api.test.com/api/v1/insider/transactions").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "accessionNumber": "0001234567-24-000123",
                            "filedAt": "2024-10-30T16:05:00.000Z",
                            "formType": "4",
                            "personCik": 1234567,
                            "personName": "John Doe",
                            "companyCik": 320193,
                            "companyName": "Apple Inc.",
                            "ticker": "AAPL",
                            "isDirector": True,
                            "isOfficer": True,
                            "isTenPercentOwner": False,
                            "isOther": False,
                            "officerTitle": "CEO",
                            "securityTitle": "Common Stock",
                            "isDerivative": False,
                            "transactionDate": "2024-10-28",
                            "transactionCode": "P",
                            "equitySwapInvolved": False,
                            "shares": "10000.0000",
                            "pricePerShare": "175.50",
                            "acquiredDisposed": "A",
                            "sharesAfter": "150000.0000",
                            "directIndirect": "D",
                            "ownershipNature": None,
                            "conversionOrExercisePrice": None,
                            "exerciseDate": None,
                            "expirationDate": None,
                            "underlyingSecurityTitle": None,
                            "underlyingShares": None,
                            "transactionValue": 1755000,
                        }
                    ],
                    "nextCursor": None,
                    "hasMore": False,
                },
            )
        )

        response = client.insider.list(ticker="AAPL")

        assert len(response.items) == 1
        txn = response.items[0]
        assert txn.person_name == "John Doe"
        assert txn.transaction_code == "P"
        assert txn.acquired_disposed == "A"


class TestInstitutionalResource:
    @respx.mock
    def test_list_institutional_holdings(self, client):
        respx.get("https://api.test.com/api/v1/institutional/holdings").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "cusip": "037833100",
                            "issuerName": "APPLE INC",
                            "classTitle": "COM",
                            "companyCik": 320193,
                            "ticker": "AAPL",
                            "value": 69900000000,
                            "shares": 400000000,
                            "sharesType": "SH",
                            "putCall": None,
                            "investmentDiscretion": "SOLE",
                            "otherManager": None,
                            "votingSole": 400000000,
                            "votingShared": 0,
                            "votingNone": 0,
                            "managerCik": 1067983,
                            "managerName": "Berkshire Hathaway",
                            "reportPeriodDate": "2024-09-30",
                            "filedAt": "2024-11-14T12:00:00.000Z",
                            "accessionNumber": "0001067983-24-000123",
                        }
                    ],
                    "nextCursor": None,
                    "hasMore": False,
                },
            )
        )

        response = client.institutional.list(ticker="AAPL")

        assert len(response.items) == 1
        holding = response.items[0]
        assert holding.issuer_name == "APPLE INC"
        assert holding.manager_name == "Berkshire Hathaway"
        assert holding.shares == 400000000


class TestCompaniesResource:
    @respx.mock
    def test_get_company(self, client):
        respx.get("https://api.test.com/api/v1/companies/320193").mock(
            return_value=httpx.Response(
                200,
                json={
                    "cik": 320193,
                    "name": "Apple Inc.",
                    "entityType": "Corporation",
                    "category": "Large Accelerated Filer",
                    "description": "Apple designs and manufactures...",
                    "tickers": [{"symbol": "AAPL", "exchange": "NASDAQ", "isPrimary": True}],
                    "primaryTicker": "AAPL",
                    "sicCodes": [{"code": 3571, "description": "Electronic Computers"}],
                    "ein": "94-2404110",
                    "fiscalYearEnd": "0930",
                    "stateOfIncorporation": "CA",
                    "stateOfIncorporationDescription": "California",
                    "phone": "(408) 996-1010",
                    "website": "https://www.apple.com",
                    "investorWebsite": "https://investor.apple.com",
                    "addresses": [
                        {
                            "type": "business",
                            "street1": "One Apple Park Way",
                            "street2": None,
                            "city": "Cupertino",
                            "stateOrCountry": "CA",
                            "stateOrCountryDescription": "California",
                            "zipCode": "95014",
                        }
                    ],
                    "logoUrl": "https://earningsfeed.com/logos/320193.png",
                    "hasInsiderTransactions": True,
                    "isInsider": False,
                    "updatedAt": "2024-11-01T12:00:00.000Z",
                },
            )
        )

        company = client.companies.get(320193)

        assert company.name == "Apple Inc."
        assert company.primary_ticker == "AAPL"
        assert len(company.tickers) == 1
        assert company.tickers[0].is_primary is True

    @respx.mock
    def test_search_companies(self, client):
        respx.get("https://api.test.com/api/v1/companies/search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "cik": 320193,
                            "name": "Apple Inc.",
                            "ticker": "AAPL",
                            "exchange": "NASDAQ",
                            "entityType": "Corporation",
                            "category": "Large Accelerated Filer",
                            "sicCode": 3571,
                            "sicDescription": "Electronic Computers",
                            "logoUrl": None,
                        }
                    ],
                    "nextCursor": None,
                    "hasMore": False,
                },
            )
        )

        response = client.companies.search(q="Apple")

        assert len(response.items) == 1
        assert response.items[0].name == "Apple Inc."
