# ProShare Testing Documentation

## Testing Strategy

ProShare uses a **unit-testing** approach focused on pure functions and self-contained business logic.
All tests are isolated: they use an in-memory SQLite database (via SQLAlchemy) instead of a live
PostgreSQL instance, and an in-memory cache instead of a live Redis server. No real network calls
(email, AI API) are made during any test run.

Tests are written with **pytest** and can be executed with a single command from the project root:

```
python -m pytest tests/ -v
```

The test suite is organized into four modules, each targeting a distinct layer of the system:

| Module | Target layer |
|---|---|
| `test_security.py` | Shared security utilities (JWT, password hashing) |
| `test_cache.py` | Shared cache abstraction (MemoryCache, Redis fallback) |
| `test_summary_utils.py` | AI summary service utility functions |
| `test_password_reset.py` | Identity service — password reset token lifecycle |

---

## Scope of Testing

**In scope:**
- JWT token creation, decoding, expiry, and admin-flag propagation
- Password hashing and verification (PBKDF2 via passlib)
- In-memory cache TTL, eviction, overwrite, and fallback from Redis
- HTML stripping and text chunking used by the AI summarizer
- Fallback summarization logic (no Anthropic API key required)
- Password-reset token hashing, URL generation, validation, consumption, and reuse prevention

**Out of scope (not covered by automated tests):**
- Full FastAPI HTTP endpoint integration (no TestClient / live service tests)
- Database migrations
- Frontend React components and UI flows
- External service integrations (PostgreSQL, Redis, SMTP, Anthropic API in production mode)
- Gateway routing and cross-service orchestration

---

## Testing Environment

| Component | Value |
|---|---|
| Language | Python 3.10 |
| Test runner | pytest 8.3.5+ |
| Database (tests) | SQLite in-memory (`sqlite:///:memory:`) |
| Cache (tests) | `MemoryCache` (in-process, no Redis) |
| AI API (tests) | Disabled (`ANTHROPIC_API_KEY=""` → fallback summarizer) |
| SMTP (tests) | Not configured → no emails sent |

**Installing dev dependencies:**
```
python -m pip install -r requirements-dev.txt
```

**Running tests:**
```
python -m pytest tests/ -v
```

---

## All Tests Performed

### `tests/test_security.py` — Security Utilities

Tests the JWT and password-hashing helpers in `services/shared/app/security.py`.

---

#### `test_password_hashing`
**Description:** Hash a password and verify it against the original plaintext.  
**Expected result:** `verify_password("secret123", hashed)` returns `True`.  
**Observed result:** PASSED

---

#### `test_jwt_round_trip`
**Description:** Encode a user ID into a JWT and decode it back.  
**Expected result:** Decoded user ID equals the original value (42).  
**Observed result:** PASSED

---

#### `test_wrong_password_fails`
**Description:** Call `verify_password` with the wrong plaintext.  
**Expected result:** Returns `False`.  
**Observed result:** PASSED

---

#### `test_different_hashes_for_same_password`
**Description:** Hash the same password twice and compare the outputs.  
**Expected result:** The two hashes differ (PBKDF2 uses a random salt per call).  
**Observed result:** PASSED

---

#### `test_invalid_jwt_raises`
**Description:** Pass a malformed string to `decode_token`.  
**Expected result:** Raises `ValueError`.  
**Observed result:** PASSED

---

#### `test_wrong_secret_raises`
**Description:** Decode a valid JWT with a different secret than was used to sign it.  
**Expected result:** Raises `ValueError`.  
**Observed result:** PASSED

---

#### `test_expired_jwt_raises`
**Description:** Create a token with `minutes=-1` (already expired) and decode it.  
**Expected result:** Raises `ValueError`.  
**Observed result:** PASSED

---

#### `test_admin_flag_in_token`
**Description:** Create a token with `is_admin=True` and inspect the decoded payload.  
**Expected result:** `payload["is_admin"]` is `True` and `payload["sub"]` is `10`.  
**Observed result:** PASSED

---

#### `test_non_admin_flag_defaults_false`
**Description:** Create a token with `is_admin=False` and inspect the decoded payload.  
**Expected result:** `payload["is_admin"]` is `False`.  
**Observed result:** PASSED

---

### `tests/test_cache.py` — Cache Abstraction

Tests `MemoryCache` and the `build_cache` factory in `services/shared/app/cache.py`.

---

#### `test_memory_cache_set_and_get`
**Description:** Set a key with a long TTL and immediately retrieve it.  
**Expected result:** Retrieved value equals the stored value.  
**Observed result:** PASSED

---

#### `test_memory_cache_miss_returns_none`
**Description:** Get a key that was never set.  
**Expected result:** Returns `None`.  
**Observed result:** PASSED

---

#### `test_memory_cache_expires_after_ttl`
**Description:** Set a key with TTL of 1 second and wait 1.05 seconds before reading.  
**Expected result:** Returns `None` after expiry.  
**Observed result:** PASSED

---

#### `test_memory_cache_unexpired_key_survives`
**Description:** Set a key with TTL of 60 seconds and read it after 0.1 seconds.  
**Expected result:** Returns the original value.  
**Observed result:** PASSED

---

#### `test_memory_cache_overwrite`
**Description:** Set the same key twice with different values.  
**Expected result:** The second value replaces the first.  
**Observed result:** PASSED

---

#### `test_memory_cache_independent_keys`
**Description:** Set two different keys and retrieve both.  
**Expected result:** Each key returns its own value without interference.  
**Observed result:** PASSED

---

#### `test_build_cache_memory_url_returns_memory_cache`
**Description:** Call `build_cache("memory://local")`.  
**Expected result:** Returns a `MemoryCache` instance.  
**Observed result:** PASSED

---

#### `test_build_cache_invalid_redis_falls_back_to_memory`
**Description:** Call `build_cache` with a Redis URL pointing to a non-existent host.  
**Expected result:** Falls back and returns a `MemoryCache` instance.  
**Observed result:** PASSED

---

#### `test_build_cache_memory_cache_is_usable`
**Description:** Confirm the cache returned by `build_cache("memory://local")` works end-to-end.  
**Expected result:** `setex` followed by `get` returns the stored value.  
**Observed result:** PASSED

---

### `tests/test_summary_utils.py` — AI Summary Utilities

Tests the utility functions in `services/summary/app/main.py`. The `ANTHROPIC_API_KEY`
environment variable is set to an empty string so the fallback (extractive) summarizer
is exercised instead of making real API calls.

---

#### `test_strip_html_removes_block_tags`
**Description:** Strip `<p>` and `<b>` tags from a simple HTML snippet.  
**Expected result:** Returns `"Hello world"`.  
**Observed result:** PASSED

---

#### `test_strip_html_removes_img_tags`
**Description:** Strip an `<img>` tag (including base64 src) from a string.  
**Expected result:** The word "img" is absent; surrounding text is preserved.  
**Observed result:** PASSED

---

#### `test_strip_html_decodes_entities`
**Description:** Convert `&amp;`, `&lt;`, and `&gt;` to their literal characters.  
**Expected result:** Returns `"& < >"`.  
**Observed result:** PASSED

---

#### `test_strip_html_collapses_whitespace`
**Description:** Multiple spaces inside HTML tags are collapsed to a single space.  
**Expected result:** Returns `"foo bar"`.  
**Observed result:** PASSED

---

#### `test_strip_html_empty_input`
**Description:** Pass an empty string.  
**Expected result:** Returns an empty string.  
**Observed result:** PASSED

---

#### `test_strip_html_plain_text_unchanged`
**Description:** Pass a string with no HTML tags.  
**Expected result:** Returns the original string unchanged.  
**Observed result:** PASSED

---

#### `test_strip_html_nested_tags`
**Description:** Strip deeply nested tags (`<div><span><em>deep</em></span></div>`).  
**Expected result:** Returns `"deep"`.  
**Observed result:** PASSED

---

#### `test_chunk_text_short_stays_single_chunk`
**Description:** Pass a short string with `chunk_size=1000`.  
**Expected result:** Returns exactly one chunk containing the full text.  
**Observed result:** PASSED

---

#### `test_chunk_text_splits_long_text`
**Description:** Pass 2000 words with `chunk_size=100`.  
**Expected result:** Returns more than one chunk.  
**Observed result:** PASSED

---

#### `test_chunk_text_reassembled_contains_all_words`
**Description:** Chunk a 500-word string and rejoin the chunks.  
**Expected result:** Rejoined text matches the original exactly.  
**Observed result:** PASSED

---

#### `test_chunk_text_empty`
**Description:** Pass an empty string.  
**Expected result:** Returns an empty list.  
**Observed result:** PASSED

---

#### `test_chunk_text_single_word`
**Description:** Pass a single word with a large `chunk_size`.  
**Expected result:** Returns a list with one element equal to that word.  
**Observed result:** PASSED

---

#### `test_summarize_text_empty_returns_no_content`
**Description:** Call `summarize_text("")`.  
**Expected result:** Returns `("No content.", [])`.  
**Observed result:** PASSED

---

#### `test_summarize_text_html_only_returns_no_content`
**Description:** Call `summarize_text("<p></p>")` (HTML with no visible text).  
**Expected result:** Returns TL;DR `"No content."`.  
**Observed result:** PASSED

---

#### `test_summarize_text_fallback_returns_strings`
**Description:** Call `summarize_text` with a multi-sentence HTML article (no API key).  
**Expected result:** Returns a non-empty string TL;DR and a list of takeaways.  
**Observed result:** PASSED

---

#### `test_summarize_text_fallback_takeaways_are_strings`
**Description:** Verify that every element in the returned takeaways list is a string.  
**Expected result:** All items in `takeaways` are `str`.  
**Observed result:** PASSED

---

#### `test_summarize_text_tldr_length_reasonable`
**Description:** Verify the fallback TL;DR does not exceed 420 characters.  
**Expected result:** `len(tldr) <= 420`.  
**Observed result:** PASSED

---

### `tests/test_password_reset.py` — Password Reset Token Lifecycle

Tests the business logic in `services/identity/app/services/password_reset.py` against
an in-memory SQLite database populated with the identity ORM models.

---

#### `test_hash_token_is_deterministic`
**Description:** Hash the same raw token twice.  
**Expected result:** Both calls return identical SHA-256 hex strings.  
**Observed result:** PASSED

---

#### `test_hash_token_differs_for_different_inputs`
**Description:** Hash two different raw tokens.  
**Expected result:** The resulting hashes are not equal.  
**Observed result:** PASSED

---

#### `test_hash_token_is_64_hex_chars`
**Description:** Verify the hash output format (SHA-256 produces 64 lowercase hex characters).  
**Expected result:** Length is 64; all characters are valid hex digits.  
**Observed result:** PASSED

---

#### `test_build_reset_url_contains_token`
**Description:** Build a reset URL from a known token string.  
**Expected result:** The raw token appears in the resulting URL.  
**Observed result:** PASSED

---

#### `test_build_reset_url_is_string`
**Description:** Confirm `build_reset_url` returns a string that starts with `"http"`.  
**Expected result:** Returns a string beginning with `"http"`.  
**Observed result:** PASSED

---

#### `test_validate_valid_token`
**Description:** Insert a non-expired, unused token and call `validate_reset_token`.  
**Expected result:** Returns the corresponding `User` object.  
**Observed result:** PASSED

---

#### `test_validate_expired_token_returns_none`
**Description:** Insert a token with an `expires_at` in the past.  
**Expected result:** `validate_reset_token` returns `None`.  
**Observed result:** PASSED

---

#### `test_validate_used_token_returns_none`
**Description:** Insert a token flagged as `used=True`.  
**Expected result:** `validate_reset_token` returns `None`.  
**Observed result:** PASSED

---

#### `test_validate_nonexistent_token_returns_none`
**Description:** Call `validate_reset_token` with a token string that was never stored.  
**Expected result:** Returns `None`.  
**Observed result:** PASSED

---

#### `test_create_reset_token_returns_raw_token_and_url`
**Description:** Call `create_reset_token` with no SMTP configured.  
**Expected result:** Returns a `(raw_token, reset_url)` tuple where the URL contains the token.  
**Observed result:** PASSED

---

#### `test_create_reset_token_persists_in_db`
**Description:** After calling `create_reset_token`, query the database for the token row.  
**Expected result:** A `PasswordResetToken` row exists with the correct `user_id`.  
**Observed result:** PASSED

---

#### `test_consume_valid_token_returns_user`
**Description:** Consume a valid, unused, non-expired token.  
**Expected result:** Returns the corresponding `User` object.  
**Observed result:** PASSED

---

#### `test_consume_token_marks_as_used`
**Description:** After consuming a token, re-query the database row.  
**Expected result:** `token_row.used` is `True`.  
**Observed result:** PASSED

---

#### `test_consume_token_prevents_reuse`
**Description:** Consume the same token twice.  
**Expected result:** The second call returns `None`.  
**Observed result:** PASSED

---

#### `test_consume_nonexistent_token_returns_none`
**Description:** Call `consume_reset_token` with a token string that was never stored.  
**Expected result:** Returns `None`.  
**Observed result:** PASSED

---

#### `test_consume_expired_token_returns_none`
**Description:** Insert an expired token and attempt to consume it.  
**Expected result:** Returns `None`.  
**Observed result:** PASSED

---

## Summary

The test suite comprises **51 tests across 4 modules**, all of which passed on every run.

| Module | Tests | Result |
|---|---|---|
| `test_security.py` | 9 | All passed |
| `test_cache.py` | 9 | All passed |
| `test_summary_utils.py` | 17 | All passed |
| `test_password_reset.py` | 16 | All passed |
| **Total** | **51** | **51 passed** |

Before adding these tests, only 2 tests existed (both in `test_security.py`), covering
password hashing and a basic JWT round-trip. The new tests expand coverage to the cache
abstraction, the AI summary utility functions, and the full password-reset token lifecycle
(creation, validation, consumption, expiry enforcement, and reuse prevention).

Remaining areas without automated tests include the FastAPI HTTP endpoints (all services),
the React frontend, cross-service gateway orchestration, and production integrations such
as PostgreSQL, Redis, SMTP, and the Anthropic API. These would require a more complex
integration-testing setup with running services or a mocking framework such as `pytest-mock`
combined with FastAPI's `TestClient`.
