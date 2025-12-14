# Earnings Feed Python SDK

[![PyPI](https://img.shields.io/pypi/v/earningsfeed)](https://pypi.org/project/earningsfeed/)

Official Python client for the [Earnings Feed API](https://earningsfeed.com/api) — SEC filings, insider transactions, and institutional holdings.

## Installation

```bash
pip install earningsfeed
```

## Quick Start

```python
from earningsfeed import EarningsFeed

client = EarningsFeed("your_api_key")

# Get recent 10-K and 10-Q filings
filings = client.filings.list(forms=["10-K", "10-Q"], limit=10)
for filing in filings.items:
    print(f"{filing.form_type}: {filing.company_name} - {filing.title}")

# Get a company profile
apple = client.companies.get(320193)
print(f"{apple.name} ({apple.primary_ticker})")
```

## Features

- **Type hints** — Full type annotations for IDE autocomplete
- **Pydantic models** — Validated response objects
- **Pagination helpers** — `.iter()` methods for automatic pagination
- **Context manager** — Use with `with` statement for automatic cleanup

## Usage

### SEC Filings

```python
# List filings with filters
filings = client.filings.list(
    ticker="AAPL",
    forms=["10-K", "10-Q", "8-K"],
    status="final",
    limit=25,
)

# Iterate through all filings (auto-pagination)
for filing in client.filings.iter(ticker="AAPL", forms="8-K"):
    print(filing.title)

# Get filing details with documents
detail = client.filings.get("0000320193-24-000123")
for doc in detail.documents:
    print(f"{doc.doc_type}: {doc.filename}")
```

### Insider Transactions

```python
# Recent insider purchases
purchases = client.insider.list(
    ticker="AAPL",
    direction="buy",
    codes=["P"],  # Open market purchases
    limit=50,
)

for txn in purchases.items:
    print(f"{txn.person_name}: {txn.shares} shares @ ${txn.price_per_share}")

# Large sales across all companies
for txn in client.insider.iter(direction="sell", min_value=1_000_000):
    print(f"{txn.company_name}: ${txn.transaction_value:,.0f}")
```

### Institutional Holdings (13F)

```python
# Who owns Apple?
holdings = client.institutional.list(
    ticker="AAPL",
    min_value=1_000_000_000,  # $1B+ positions
)

for h in holdings.items:
    print(f"{h.manager_name}: {h.shares:,} shares (${h.value:,})")

# Track a specific fund
for h in client.institutional.iter(manager_cik=1067983):  # Berkshire
    print(f"{h.issuer_name}: {h.shares:,} shares")
```

### Companies

```python
# Get company profile
company = client.companies.get(320193)
print(f"{company.name}")
print(f"Ticker: {company.primary_ticker}")
print(f"Industry: {company.sic_codes[0].description}")

# Search companies
results = client.companies.search(q="software", state="CA", limit=10)
for company in results.items:
    print(f"{company.name} ({company.ticker})")
```

## Error Handling

```python
from earningsfeed import (
    EarningsFeed,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
)

client = EarningsFeed("your_api_key")

try:
    filing = client.filings.get("invalid-accession")
except NotFoundError:
    print("Filing not found")
except RateLimitError as e:
    print(f"Rate limited. Resets at: {e.reset_at}")
except AuthenticationError:
    print("Invalid API key")
```

## Context Manager

```python
with EarningsFeed("your_api_key") as client:
    filings = client.filings.list(limit=10)
    # Connection automatically closed when exiting the block
```

## API Reference

Full API documentation: [earningsfeed.com/api/docs](https://earningsfeed.com/api/docs)

## License

MIT
