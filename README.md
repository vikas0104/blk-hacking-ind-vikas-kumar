# Self Retirement Savings API

Automated retirement savings system that calculates micro-investments from expense rounding, applies temporal constraints, and projects inflation-adjusted returns for NPS and Index Fund instruments.

## Prerequisites

- Python 3.12+
- Docker

## Local Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python wsgi.py
```

The server starts on `http://localhost:5477`.

## Docker

```bash
# Build
docker build -t blk-hacking-ind-vikas-kumar .

# Run
docker run -d -p 5477:5477 blk-hacking-ind-vikas-kumar
```

## Testing

```bash
pytest test/ -v
```

## API Endpoints

All endpoints are prefixed with `/blackrock/challenge/v1`.

### POST /transactions:parse

Parses raw expenses into transactions with ceiling and remanent values.

```json
{
  "expenses": [
    {"timestamp": "2023-10-12 20:15:00", "amount": 250}
  ]
}
```

### POST /transactions:validator

Validates transactions for correctness (ceiling, remanent, duplicates, constraints).

```json
{
  "wage": 50000,
  "transactions": [
    {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50}
  ]
}
```

### POST /transactions:filter

Applies temporal constraints (q, p, k periods) and returns valid/invalid transactions.

```json
{
  "q": [{"fixed": 0, "start": "2023-07-01 00:00:00", "end": "2023-07-31 23:59:00"}],
  "p": [{"extra": 25, "start": "2023-10-01 08:00:00", "end": "2023-12-31 19:59:00"}],
  "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"}],
  "transactions": [
    {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50}
  ]
}
```

### POST /returns:nps

Calculates NPS investment returns with tax benefit.

### POST /returns:index

Calculates Index Fund (NIFTY 50) investment returns.

Both returns endpoints accept:

```json
{
  "age": 29,
  "wage": 50000,
  "inflation": 0.055,
  "q": [],
  "p": [],
  "k": [{"start": "2023-01-01 00:00:00", "end": "2023-12-31 23:59:00"}],
  "transactions": [
    {"date": "2023-10-12 20:15:00", "amount": 250, "ceiling": 300, "remanent": 50}
  ]
}
```

### GET /performance

Returns system execution metrics (uptime, memory usage, thread count).

