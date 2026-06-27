# abstract_solana

> **Python-first Solana SDK** — schema-driven RPC bodies, DB-backed response caching, explicit rate-limiting with fallback URLs, and PumpFun bonding-curve math. No magic defaults. No hidden globals.

[![PyPI version](https://img.shields.io/pypi/v/abstract_solana)](https://pypi.org/project/abstract_solana/)
[![Python](https://img.shields.io/pypi/pyversions/abstract_solana)](https://pypi.org/project/abstract_solana/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange)](https://pypi.org/project/abstract_solana/)

---

## What It Is

`abstract_solana` is a structured Python wrapper around the Solana JSON-RPC API. It treats every RPC call as a typed schema, every response as a cacheable record, and every endpoint as an explicitly wired URL — not something discovered at runtime.

The design priorities, in order:

1. **Schemas over ad-hoc dicts** — each RPC method maps to a dedicated body-builder function with typed parameters and validated conversions.
2. **Registries over globals** — RPC endpoints, DB table configs, and rate-limit state are held in explicit registries, not module-level singletons.
3. **DB caching over redundant calls** — responses are persisted to PostgreSQL (JSONB) keyed by the natural lookup column (pubkey, slot, commitment, etc.). Repeat calls hit the DB first.
4. **Explicit rate limiting with URL fallback** — a `RateLimiter` tracks per-method call counts and automatically falls back to a secondary RPC URL on 429s.
5. **PumpFun as a first-class citizen** — bonding curve derivation and associated token account resolution are built in, not bolted on.

---

## Package Structure

```
abstract_solana/
├── __init__.py                  # re-exports all submodules
├── abstract_rpcs/
│   ├── get_body.py              # per-method RPC body builders
│   ├── db_templates.py          # DB table configs (CREATE, INSERT, SELECT per method)
│   ├── solana_rpc_client.py     # get_rpc_dict, make_call, abstract_solana_rate_limited_call
│   └── rate_limiter.py          # RateLimiter — tracks usage, owns URL selection
├── pumpFun/
│   ├── bondingCurves.py         # derive_bonding_curve, derive_bonding_curve_accounts
│   ├── pubKeyUtils.py           # get_pubkey, pubkey_find_program_address
│   └── genesis_functions.py
├── rpc_utils/                   # lower-level HTTP/RPC helpers
└── abstract_solana_utils/       # shared utility functions
```

---

## Installation

```bash
pip install abstract_solana
```

**Dependencies:** `solana`, `solders`, `abstract_solcatcher`, `abstract_utilities`

---

## Core Modules

### `abstract_rpcs` — The RPC Engine

This is the heart of the package. It composes three responsibilities cleanly:

**Body construction (`get_body.py`)**

Each Solana RPC method (`getBalance`, `getAccountInfo`, `getBlock`, etc.) has a dedicated Python function that accepts typed arguments, validates them, converts pubkeys/signatures to their proper types, fills in defaults, and returns a well-formed JSON-RPC body dict.

```python
from abstract_solana.abstract_rpcs import get_rpc_dict

body = get_rpc_dict("getBalance", pubkey="YourWalletAddressHere")
# {'jsonrpc': '2.0', 'method': 'getBalance', 'params': [...], 'id': 1}
```

`get_rpc_dict` uses `inspect.signature` to discover each body-builder's parameters, then runs `get_conversions` to normalize and type-coerce every argument. Pubkeys and signatures are converted via `get_pubkey` / `get_sigkey` — no raw strings passed through.

**DB caching (`db_templates.py`)**

`get_insert_list()` returns a registry of table configs — one per RPC method — each specifying:

| Key | Purpose |
|---|---|
| `tableName` | PostgreSQL table name |
| `columnSearch` | The lookup key (e.g. `pubkey`, `slot`, `commitment`) |
| `insertName` | Column name for the response payload |
| `type` | Solana type name for the response |
| `searchQuery` | Parameterized SELECT |
| `insertQuery` | Parameterized INSERT |
| `table` | `CREATE TABLE IF NOT EXISTS` DDL |

Covered methods include: `isconnected`, `getbalance`, `getaccountinfo`, `getaccountinfojsonparsed`, `getblockcommitment`, `getblocktime`, `getclusternodes`, `getblock`, `getrecentperformancesamples`, `getblockheight`, `getblocks`, and many more.

**Rate-limited execution (`solana_rpc_client.py` + `rate_limiter.py`)**

```python
from abstract_solana.abstract_rpcs import abstract_solana_rate_limited_call

response = abstract_solana_rate_limited_call("getBalance", pubkey="YourAddressHere")
```

Under the hood:

1. Builds the request body via `get_rpc_dict`.
2. Asks `rate_limiter.get_url(method)` which URL to use — primary or fallback.
3. Makes the POST via `make_call` (which injects headers and handles retries).
4. Logs the response and `retry_after` header back to the rate limiter.
5. If the primary URL returns 429, automatically retries against the secondary URL.

The `RateLimiter` owns all URL state. Nothing is a module-level global.

---

### `pumpFun` — Bonding Curve Math

PumpFun's bonding curves are Program Derived Addresses (PDAs). This module wraps the derivation cleanly.

```python
from abstract_solana.pumpFun import (
    derive_bonding_curve_accounts,
    get_bonding_curve,
    get_associated_bonding_curve,
    isOnCurve,
)

accounts = derive_bonding_curve_accounts("TokenMintAddressHere")
# {
#   'bonding_curve': <Pubkey>,
#   'associated_bonding_curve': <Pubkey>
# }

# Check validity before any downstream call
if isOnCurve("TokenMintAddressHere"):
    curve = get_bonding_curve("TokenMintAddressHere")
```

`derive_bonding_curve_accounts` guards against invalid mints: if `mint.is_on_curve()` returns False, it returns an empty dict rather than propagating a bad PDA derivation.

`derive_bonding_curve` and `derive_associated_bonding_curve` both accept an optional `programId` — defaulting to `PUMP_FUN_PROGRAM` — so the same logic works against custom forks of the program without monkey-patching.

---

### Type Conversion Pipeline

A consistent type-coercion layer runs across all RPC calls:

```python
# pubkeys and signatures are detected by key name, not by caller convention
pubkeys    = ['address', 'account', 'pubkeys', 'pubkey', 'mint', 'owner', 'delegate']
signatures = ['until', 'before', 'tx_sig', 'signature', 'signatures']
```

If a kwarg key is in `pubkeys`, the value is passed through `get_pubkey`. If it's in `signatures`, through `get_sigkey`. Lists are handled element-wise. This means callers can pass raw strings; the SDK handles wrapping into `solders`/`solana-py` types.

---

## Supported RPC Methods (DB-Cached)

The DB template registry covers the following Solana RPC methods out of the box:

`isConnected` · `getBalance` · `getAccountInfo` · `getAccountInfoJsonParsed` · `getBlockCommitment` · `getBlockTime` · `getClusterNodes` · `getBlock` · `getRecentPerformanceSamples` · `getBlockHeight` · `getBlocks` · and more defined in `get_insert_list()`

Each maps to its own PostgreSQL table with an auto-generated schema. Tables are created idempotently on first use.

---

## Design Notes

**Why PostgreSQL for caching?** Solana RPC data is structured and queryable. JSONB lets you store the full response without schema churn while still indexing on lookup keys. A simple `WHERE pubkey = %s` is cheaper than a repeat RPC call on a rate-limited endpoint.

**Why explicit `fresh_call` flags?** Each table config carries `fresh_call: True`, making cache-bypass an explicit, per-method decision rather than a hidden TTL policy. You can override this per call — it's a field, not a behavior.

**Why `inspect.signature` for param discovery?** Body builders are plain functions. Using `inspect.signature` to drive `get_conversions` means adding a new RPC method is just adding a function — no registration boilerplate, no decorator magic.

---

## Author & License

**Author:** putkoff — [partners@abstractendeavors.com](mailto:partners@abstractendeavors.com)  
**License:** MIT  
**Version:** 0.0.2.141 (Alpha)
