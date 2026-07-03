# Cloud/CDN/WAF IP Lookup Service — Implementation Plan

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  REST API   │────▶│  Services         │────▶│  SQLite (SQLAlchemy) │
│  (main.py)  │     │  lookup.py        │     │  + Alembic migrations│
└─────────────┘     │  refresh.py       │     └──────────────────────┘
                    └──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Providers  │
                    │  AWS, CF,   │
                    │  GCP, Azure │
                    └─────────────┘
```

---

## Storage & Lookup Strategy

**Storage**: SQLite via SQLAlchemy ORM (file-based, no external dep, portable). Config supports PostgreSQL via env var swap.

**ORM Model** (`src/models/ip_ranges.py`):
```python
class IPRangesModel(Base):
    __tablename__ = 'ip_ranges'
    id            = Column(Integer, primary_key=True)
    cidr          = Column(String)
    provider      = Column(String)
    source        = Column(String)
    ip_version    = Column(Integer)
    network_int   = Column(Integer)   # network address as uint32
    broadcast_int = Column(Integer)   # broadcast address as uint32
    region        = Column(String)
    service       = Column(String)
    fetched_at    = Column(DateTime)
    __table_args__ = (
        UniqueConstraint("cidr", "provider", name="uq_cidr_provider"),
        Index("idx_range", "network_int", "broadcast_int"),
    )
```

**Lookup**: Convert IP → uint32, query:
```sql
WHERE network_int <= :ip_int AND broadcast_int >= :ip_int
```
B-tree index makes this O(log n), NOT a linear scan.

**In-memory cache**: On startup/refresh, load all `(network_int, broadcast_int, row_id)` into sorted list. Use `bisect` to find candidates where `network_int <= ip_int`, then filter `broadcast_int >= ip_int`. O(log n) bisect + small constant. Falls back to DB if cache not warm.

---

## Project Structure

```
icounter-assignment/
├── src/
│   ├── config.py            # DB URL from env (SQLALCHEMY_DATABASE_URL)
│   ├── database.py          # SQLAlchemy engine, SessionLocal, Base, get_db()
│   ├── main.py              # FastAPI app + uvicorn entry (port 8001)
│   ├── providers/
│   │   ├── base.py          # Abstract BaseProvider
│   │   ├── aws.py           # JSON: ip-ranges.amazonaws.com
│   │   ├── cloudflare.py    # Plain text: cloudflare.com/ips-v4
│   │   ├── gcp.py           # JSON: gstatic.com/ipranges/cloud.json
│   │   └── azure.py         # JSON: Azure ServiceTags download
│   ├── models/
│   │   └── ip_ranges.py     # SQLAlchemy IPRangesModel
│   ├── services/
│   │   ├── lookup.py        # IP → uint32, cache, query
│   │   └── refresh.py       # Orchestrate all providers
│   └── common/
│       └── helper.py        # to_dict() SQLAlchemy utility
├── tests/
│   ├── conftest.py          # Shared fixtures (in-memory SQLite)
│   ├── test_lookup.py       # Match, no-match, invalid IP
│   ├── test_parsers.py      # Each provider parser with mock data
│   └── test_refresh.py      # Duplicate dedup, partial failure
├── pyproject.toml           # uv-managed deps
├── uv.lock
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Data Sources (4 active, 1 dropped)

| Provider   | Format     | URL |
|------------|------------|-----|
| AWS        | JSON       | `https://ip-ranges.amazonaws.com/ip-ranges.json` |
| Cloudflare | Plain text | `https://www.cloudflare.com/ips-v4` |
| GCP        | JSON       | `https://www.gstatic.com/ipranges/cloud.json` |
| Azure      | JSON       | `https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_<date>.json` (weekly) |

> Fastly dropped from scope. Add back later if needed.

Each provider implements `BaseProvider`:
```python
class BaseProvider(ABC):
    name: str
    url: str

    def fetch(self) -> str: ...          # HTTP GET raw
    def parse(self, raw: str) -> list[dict]: ...  # → normalized records
```

---

## Implementation Steps

### Phase 1 — Core Foundation ✅ (boilerplate done)
1. ✅ `src/config.py`: DB URL from env
2. ✅ `src/database.py`: SQLAlchemy engine, `SessionLocal`, `Base`, `get_db()`
3. ✅ `src/models/ip_ranges.py`: `IPRangesModel` with `UniqueConstraint` + `idx_range`
4. ✅ `src/common/helper.py`: `to_dict()` for SQLAlchemy → dict conversion
5. ✅ `src/main.py`: FastAPI app skeleton with CORS middleware

### Phase 2 — Providers (stubs exist, need implementation)
6. `src/providers/base.py`: Abstract `BaseProvider` with `fetch()` + `parse()` + `normalize()`
7. Each provider: `aws.py`, `cloudflare.py`, `gcp.py`, `azure.py`
   - Parse own format → return list of normalized dicts
   - Fail independently (try/except, log, continue)

### Phase 3 — Services (stubs exist, need implementation)
8. `src/services/refresh.py`: `Refresh.run()` — iterate providers, fetch+parse, upsert to DB, rebuild cache
   - Atomic per-provider: if parse fails, skip provider, log, continue
   - Dedup: `UNIQUE(cidr, provider)` + `ON CONFLICT REPLACE` via SQLAlchemy `merge()`
9. `src/services/lookup.py`: `Lookup` class
   - `ip_to_int()`, `LookupCache` (sorted list + bisect), `lookup(ip)`
   - Falls back to DB query if cache cold

### Phase 4 — API Routes
10. Wire routes into `src/main.py`:
    - `POST /refresh` → `Refresh.run()`
    - `GET /lookup?ip=<ip>` → `Lookup.lookup(ip)` → JSON
    - `GET /providers` → list providers + range counts
    - `GET /health` → status + last_refreshed

### Phase 5 — Alembic Migrations
11. `alembic init alembic` + configure `env.py` to import `Base` from `src/database.py`
12. Generate initial migration for `ip_ranges` table

### Phase 6 — Tests
13. `tests/conftest.py`: in-memory SQLite fixture, mock provider
14. `tests/test_lookup.py`:
    - valid IP with match
    - valid IP no match
    - invalid IP → ValueError
    - multiple matches from different providers
    - boundary IPs (first/last in range)
15. `tests/test_parsers.py`:
    - AWS JSON parse → correct records
    - Cloudflare text parse → correct records
    - GCP JSON parse → correct records
    - CIDR normalization correctness
    - Duplicate CIDR dedup
16. `tests/test_refresh.py`:
    - one failing provider doesn't break refresh
    - refresh updates `fetched_at`
    - cache rebuilds after refresh

### Phase 7 — Packaging
17. `Dockerfile` + `docker-compose.yml`
18. `README.md`

---

## Key Design Decisions

**Why SQLAlchemy + Alembic?** ORM abstracts DB backend. Swap SQLite → PostgreSQL via env var, zero code change. Alembic handles schema migrations cleanly.

**Why SQLite default?** No external service needed. B-tree index on `(network_int, broadcast_int)` enables sub-millisecond range queries. At ~50k CIDR records, query time is negligible. Persists across restarts.

**Why in-memory cache?** Even faster than indexed SQLite for read-heavy workloads. Sorted array + bisect = O(log n). Rebuilt atomically after each refresh. Memory footprint: ~50k records × ~40 bytes = ~2MB — trivial.

**Why uint32 for IPv4?** Enables arithmetic range comparison (`network_int <= ip <= broadcast_int`) instead of string matching. `ipaddress.ip_network(cidr)` gives `network_address` and `broadcast_address` as integers directly.

**Duplicate handling**: `UNIQUE(cidr, provider)` in DB. Same CIDR from same provider → upsert updates `fetched_at`. Same CIDR from different providers → kept as separate records (both returned in matches).

**Provider failure isolation**: Each provider wrapped in try/except inside `Refresh.run()`. Failed providers logged, others continue. `/refresh` response includes per-provider status.

**No CLI**: Dropped Click CLI from scope. REST API only. Run via uvicorn.

**Scale path**: Replace SQLite with PostgreSQL (same integer range query works). Cache layer stays same. Add provider concurrency with `asyncio.gather()`. Current sync design easily migrated to async.

---

## Record Schema

```python
{
    "provider": "Cloudflare",
    "cidr": "104.16.0.0/12",
    "ip_version": 4,
    "source": "cloudflare",
    "fetched_at": "2026-05-21T10:30:00Z",
    "region": None,
    "service": None,
    "network_int": 1745879040,
    "broadcast_int": 1746927615
}
```

---

## API Responses

`GET /lookup?ip=104.16.10.20`
```json
{
  "ip": "104.16.10.20",
  "matched": true,
  "matches": [
    {
      "provider": "Cloudflare",
      "cidr": "104.16.0.0/12",
      "source": "cloudflare",
      "last_fetched_at": "2026-05-21T10:30:00Z"
    }
  ]
}
```

`GET /health`
```json
{
  "status": "ok",
  "total_ranges": 48312,
  "last_refreshed": "2026-05-21T10:30:00Z",
  "providers": ["AWS", "Cloudflare", "GCP", "Azure"]
}
```

`POST /refresh`
```json
{
  "status": "ok",
  "results": {
    "AWS": {"success": true, "ranges_loaded": 7300},
    "Cloudflare": {"success": true, "ranges_loaded": 15},
    "GCP": {"success": false, "error": "timeout"}
  }
}
```

---

## Dependencies (`pyproject.toml`)

```toml
[project]
dependencies = [
    "alembic>=1.16.5",
    "fastapi>=0.128.8",
    "sqlalchemy>=2.0.51",
    "uvicorn>=0.39.0",
    "httpx>=0.27",     # TODO: add for provider HTTP fetches
    "pydantic>=2.7",   # TODO: add for API response schemas
]
```

> `httpx` and `pydantic` not yet in `pyproject.toml` — add before Phase 2.

---

## Files Status

| File | Status |
|------|--------|
| `src/config.py` | ✅ Done |
| `src/database.py` | ✅ Done |
| `src/main.py` | ✅ Skeleton |
| `src/models/ip_ranges.py` | ✅ Done |
| `src/common/helper.py` | ✅ Done |
| `src/providers/base.py` | ⬜ Stub only |
| `src/providers/aws.py` | ⬜ Stub only |
| `src/providers/cloudflare.py` | ⬜ Stub only |
| `src/providers/gcp.py` | ⬜ Stub only |
| `src/providers/azure.py` | ⬜ Stub only |
| `src/services/lookup.py` | ⬜ Stub only |
| `src/services/refresh.py` | ⬜ Stub only |
| `tests/` | ⬜ Not started |
| `alembic/` | ⬜ Not started |
| `Dockerfile` | ⬜ Not started |
| `README.md` | ⬜ Not started |
