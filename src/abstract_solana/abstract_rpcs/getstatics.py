texts = """Got it — you’re **intentionally not short-circuiting** inflight calls because *freshness semantics live elsewhere*. That actually makes sense given this table registry 👍

What you’re really asking is:

> **Which RPC methods are expected to be *effectively static* (cacheable forever / near-forever), vs which are inherently dynamic and must be refreshed?**

Below is a **clean, opinionated classification** of what you posted, grounded in Solana RPC semantics.

I’ll group them by **immutability horizon**.

---

# 🟢 Truly Static (Genesis-level / Network identity)

**These never change for a given cluster. Cache forever.**

* `getGenesisHash`
* `getIdentity`
* `getVersion`
* `getEpochSchedule`
* `getInflationGovernor` *(effectively static; governance changes are rare and epoch-scoped)*
* `getMinimumLedgerSlot` *(monotonic; once observed it never decreases)*

➡️ These should **never** require `fresh_call = true` after first success.

---

# 🟢 Immutable After Creation (Historical, slot-addressed)

**Safe to cache permanently once fetched.**

* `getBlock`
* `getBlockTime`
* `getBlockCommitment`
* `getTransaction` ✅ *(you already marked this correctly as `fresh_call: false`)*
* `getConfirmedTransaction` (if added later)
* `confirmTransaction` *(status becomes terminal)*

➡️ These are **append-only history**. Perfect DB materialization targets.

---

# 🟡 Quasi-Static (Epoch / Slot windowed)

**Changes, but slowly and predictably. Cache per epoch or slot.**

* `getEpochInfo`
* `getLeaderSchedule`
* `getSlotLeader`
* `getRecentPerformanceSamples`
* `getVoteAccounts`
* `getInflationRate`
* `getClusterNodes`

➡️ These benefit from:

* TTL cache
* epoch-keyed cache
* slot-range bucketing

---

# 🟡 Commitment-Dependent but Stable

**Stable for a given commitment, but changes across commitments.**

* `getBlockHeight`
* `getSlot`
* `getTransactionCount`
* `getSupply`
* `getLatestBlockhash` ⚠️ *(short-lived but deterministic)*

➡️ Cache **per commitment** with short TTL.

---

# 🔵 Account-Scoped, Mutable (Stateful)

**Must be refreshed depending on write activity.**

* `getBalance`
* `getAccountInfo`
* `getAccountInfoJsonParsed`
* `getStakeActivation`
* `getTokenAccountBalance`
* `getTokenAccountsByOwner`
* `getTokenAccountsByDelegate`
* `getMultipleAccounts`
* `getProgramAccounts`
* `getTokenLargestAccounts`
* `getTokenSupply`

➡️ These are **correctly marked `fresh_call: true`**, but:

* dedupe inflight
* cache with blockhash / slot watermark if desired

---

# 🔴 Always Dynamic (User-initiated / write path)

**Never cache, never reuse.**

* `requestAirdrop`
* `sendTransaction`
* `sendRawTransaction`
* `simulateTransaction`
* `postSendWithConfirm`
* `validatorExit`

➡️ These should **never** be deduped or reused, even accidentally.

---

# 🟣 Signature / History Queries (Sliding Window)

**Cacheable, but only as a range index.**

* `getSignaturesForAddress`
* `getSignatureStatuses`

➡️ Best handled as:

* `(address, before, until)` window materialization
* incremental append strategy

---

# 🧠 Summary Table (condensed)

| Category                       | Expected Static?     |
| ------------------------------ | -------------------- |
| Genesis / Identity             | ✅ Always             |
| Slot / Block / Tx (historical) | ✅ After finalization |
| Epoch / Cluster                | 🟡 Slowly            |
| Commitment-scoped              | 🟡 Per commitment    |
| Account state                  | ❌ No                 |
| Transactions (send)            | ❌ Never              |
| Signature history              | 🟣 Windowed          |

---

# 🔧 Strong Design Suggestion (fits your registry perfectly)

Add **one derived field** instead of `fresh_call`:

```ts
stability: "static" | "historical" | "epoch" | "stateful" | "write"
```

Then `fresh_call` becomes a *policy*, not a fact.

Example:

```ts
{
  tableName: "gettransaction",
  stability: "historical"
}
```

This lets you later enforce:

* TTL
* dedupe
* retry strategy
* fallback behavior

**without touching call-sites**.

---

## Final verdict

You’re modeling this correctly — your instinct to *not* short-circuit inflight is justified **because freshness ≠ duplication**.

What matters is:

* **Which calls are immutable**
* **Which are monotonic**
* **Which are volatile**

And you already have 90% of that encoded.

If you want, next I can:

* normalize this list programmatically
* generate a `MethodStabilityRegistry`
* or help you auto-derive caching rules from this table

This is solid system design work.
"""

types = ['Static','Immutable','Quasi-Static','Commitment-Dependent','Account-Scoped','Dynamic']
js = {'Dynamic':[]}
for text in texts.split('---')[1:]:
    
    if len(js.keys()) < len(types):
        type_strings = [line for line in text.split('#')[1].split('\n')[0].split(' ') if line]
        for typ in types:
            if typ in type_strings:
                js[typ]=[]
                break
        for call in text.split('* `')[1:]:
            call = call.split('`')[0]
            js[typ].append(call)
        print(js)
input(js)

    
