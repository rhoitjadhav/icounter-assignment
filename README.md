# Cloud/CDN/WAF IP Lookup Service

A Python service that collects public IP ranges from Cloud/CDN/WAF providers and identifies whether a given IP belongs to one of those providers.

---

## How to Run the Project

### Prerequisites
- Docker + Docker Compose

### Start the service

```bash
docker compose up --build
```

The API will be available at `http://localhost:8001`.

### Run database migrations

```bash
bash scripts/run_migrations.sh
```

### Verify service is running

```bash
curl http://localhost:8001/health
```

---

## How to Refresh IP Data

Fetches and stores the latest IP ranges from all providers.

```bash
curl -X POST http://localhost:8001/refresh
```

Sample response:

```json
{
  "AWS": {"success": true, "ranges_loaded": 7300},
  "Cloudflare": {"success": true, "ranges_loaded": 15},
  "GCP": {"success": true, "ranges_loaded": 512},
  "Azure": {"success": true, "ranges_loaded": 40231}
}
```

If one provider fails, others continue — failure is isolated per provider.

---

## How to Perform Lookup

Check whether an IP address belongs to a known Cloud/CDN/WAF provider.

```bash
curl "http://localhost:8001/lookup?ip=104.16.10.20"
```

Matched response:

```json
{
  "ip": "104.16.10.20",
  "matched": true,
  "matches": [
    {
      "provider": "Cloudflare",
      "cidr": "104.16.0.0/12",
      "source": "cloudflare",
      "region": null,
      "service": null,
      "last_fetched_at": "2026-07-02T10:30:00"
    }
  ]
}
```

Unmatched response:

```json
{
  "ip": "1.2.3.4",
  "matched": false,
  "matches": []
}
```

Invalid IP:

```json
{"detail": "Invalid IP address: 'not-an-ip'"}
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/refresh` | Fetch and store latest IP ranges from all providers |
| `GET` | `/lookup?ip=<ip>` | Check if an IP belongs to a provider |
| `GET` | `/providers` | List all providers with range counts |
| `GET` | `/health` | Service status, total ranges, last refresh time |

---

## Sources Used

| Provider | Format | URL |
|----------|--------|-----|
| AWS | JSON | `https://ip-ranges.amazonaws.com/ip-ranges.json` |
| Cloudflare | Plain text | `https://www.cloudflare.com/ips-v4` |
| GCP | JSON | `https://www.gstatic.com/ipranges/cloud.json` |
| Azure | JSON | `https://download.microsoft.com/download/.../ServiceTags_Public_{date}.json` (weekly) |

---

## Storage & Database Choice

**SQLite** (default) via SQLAlchemy ORM, with Alembic for migrations.

### Schema

```sql
CREATE TABLE ip_ranges (
    id            INTEGER PRIMARY KEY,
    cidr          TEXT,
    provider      TEXT,
    source        TEXT,
    ip_version    INTEGER,
    network_int   INTEGER,   -- network address as uint32
    broadcast_int INTEGER,   -- broadcast address as uint32
    region        TEXT,
    service       TEXT,
    fetched_at    DATETIME,
    UNIQUE(cidr, provider)
);
CREATE INDEX idx_range ON ip_ranges (network_int, broadcast_int);
```

### Why SQLite?

- Zero external dependencies — runs anywhere Docker runs
- B-tree index on `(network_int, broadcast_int)` enables O(log n) range queries
- SQLAlchemy ORM abstracts the backend — swap to PostgreSQL via a single env var change:
  ```
  SQLALCHEMY_DATABASE_URL=postgresql+psycopg2://user:pass@host/db
  ```

### How Lookup Works

Every IPv4 address and CIDR range is stored as a `uint32` integer pair (`network_int`, `broadcast_int`). Lookup converts the input IP to `uint32` and queries:

```sql
WHERE network_int <= :ip_int AND broadcast_int >= :ip_int
```

This is a direct B-tree range scan — O(log n), not a full table scan.

### How Refresh Works

1. Each provider's `fetch()` downloads raw data (JSON or plain text)
2. `parse()` normalizes records into a common schema
3. Records are upserted in batches of 100 to avoid SQLite variable limits
4. `UNIQUE(cidr, provider)` constraint handles duplicates — conflicts update `fetched_at` only
5. Each provider runs independently — one failure does not block others

---

## Design Decisions

**Provider abstraction**: Each provider implements `BaseProvider` (ABC) with `fetch()`, `parse()`, `normalize()`. Adding a new provider = one new file, zero changes elsewhere.

**Integer range storage**: Storing `network_int` and `broadcast_int` as integers instead of CIDR strings enables arithmetic range comparison with index support. `ipaddress.ip_network()` computes these directly.

**Batch upsert**: Azure alone has ~40k ranges. SQLite limits SQL variables to 999. Batching at 100 records (9 columns × 100 = 900 variables) stays safely under the limit.

**Provider failure isolation**: Each provider is wrapped in `try/except` inside `Refresh.run()`. A timeout or parse error on one provider is logged and reported, but all others complete.

**ORM + Alembic**: SQLAlchemy ORM means the storage backend is swappable. Alembic manages schema migrations cleanly without raw SQL files.

---

## Running Tests

```bash
.venv/bin/pytest tests/ -v
```

---

## Known Limitations

- **IPv4 only**: IPv6 CIDRs are parsed but skipped. `network_int`/`broadcast_int` are stored as standard integers which cannot hold 128-bit IPv6 values.
- **SQLite concurrent writes**: SQLite serializes writes. Under high-concurrency refresh load, consider PostgreSQL.
- **Azure URL**: Microsoft publishes weekly — `get_url()` probes the last 3 Mondays. If Microsoft changes the URL pattern, this breaks.
- **No in-memory cache**: Lookups hit the DB on every request. A `bisect`-based in-memory cache would eliminate DB reads entirely.
- **Cloudflare IPv4 only**: `https://www.cloudflare.com/ips-v4` — IPv6 ranges at `ips-v6` are not fetched.

---

## Future Improvements

- **In-memory bisect cache**: Load all `(network_int, broadcast_int, row)` into a sorted list on startup. Use `bisect` for O(log n) lookups without any DB hit. Rebuild after each refresh.
- **Parallel provider fetching**: Use `ThreadPoolExecutor` to fetch all providers concurrently — reduces refresh time from sum-of-all-fetches to slowest-single-fetch.
- **IPv6 support**: Store `network_int`/`broadcast_int` as `NUMERIC`/`BigInteger` and extend lookup to handle 128-bit addresses.
- **Scheduled refresh**: Add a background scheduler (APScheduler or Celery) to auto-refresh on a configurable interval.
- **PostgreSQL support**: Already wired — set `SQLALCHEMY_DATABASE_URL` to a PostgreSQL DSN. Enables concurrent writes and `inet` type for native CIDR operations.
- **ETag-based fetch caching**: Send `If-None-Match` headers on provider fetches — skip parse and upsert entirely when data hasn't changed.
- **More providers**: Fastly (`api.fastly.com/public-ip-list`), Akamai, and others follow the same `BaseProvider` pattern.
