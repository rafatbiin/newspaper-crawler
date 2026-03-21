# ProthomAlo Spider Upgrade Plan

## Background

The prothomalo.com website has migrated to a Next.js/React architecture.
Two things broke:
1. **Article URLs** changed from `/article/<digits>` to `/<section>/<alphanumeric-slug>`
   (e.g. `/bangladesh/63pv7s72ir`). The spider's `LinkExtractor` finds zero articles.
2. **Publish date selector** `.time span:nth-child(1)` returns nothing — dates are
   rendered client-side and not in the static HTML.
3. **Bonus bug**: `dateparser.parse(None)` crashes the spider with `TypeError`
   when the selector finds nothing (regression introduced by dateparser >= 1.0.0).

The good news: the site exposes a **public REST API** that returns structured article
data including URLs, timestamps, images, and section metadata — no authentication needed.

---

## Verified API Facts

| Property | Value |
|---|---|
| Endpoint | `https://www.prothomalo.com/api/v1/stories` |
| Pagination | `?limit=N&offset=N` |
| Section filter | `?section=bangladesh` |
| Response shape | `{ "stories": [ { ...fields } ] }` |
| Key fields per story | `url`, `slug`, `headline`, `published-at` (Unix ms), `author-name`, `sections`, `hero-image-s3-key`, `story-template`, `metadata.excerpt` |
| Auth required | None |

Article text/body is **not** in the API — it must still be fetched from the article
HTML page and parsed by the newspaper3k pipeline (unchanged).

Publish date is also available in article HTML via a JSON-LD block
(`script[type="application/ld+json"]` → `datePublished`), usable as a fallback.

---

## Files to Change

### 1. `crawler/crawler/spiders/prothomalo.py` — Full rewrite

Replace the `CrawlSpider` with a plain `Spider` that:

**a) Discovers articles via the API (replaces LinkExtractor)**
- `start_requests()` hits `/api/v1/stories?limit=50&offset=0`
- Parses the JSON, yields a `Request` for each article URL to fetch HTML
- Follows pagination: while the response contains `limit` stories,
  increment offset and yield another API request

**b) Pre-populates item fields from API JSON (replaces CSS selectors)**
- `url` → `story["url"]`
- `publish_date` → `datetime.fromtimestamp(story["published-at"] / 1000, tz=timezone.utc)`
- `headline` (new convenience field, already in `News` item) — optional
- `language` → `"bn"` (unchanged)
- Passes article URL + pre-populated metadata to `parse_article`

**c) `parse_article` extracts HTML body**
- Sets `news["html"] = response.body` (unchanged)
- Does NOT call `dateparser.parse()` — date already set from API
- Yields the item for the pipeline

**d) JSON-LD date fallback (for robustness)**
- If `publish_date` is somehow missing, attempt to extract
  `datePublished` from `script[type="application/ld+json"]` blocks

**e) Fix the dateparser None bug (one-liner)**
```python
# Before (crashes when selector returns None):
news['publish_date'] = dateparser.parse(response.css("...").extract_first())

# After (guarded, only needed if keeping CSS selector as fallback):
raw = response.css("...").extract_first() or ""
news['publish_date'] = dateparser.parse(raw) if raw else None
```

### 2. `crawler/crawler/pipelines/news_details_extractor.py` — Minor adjustment

The pipeline currently extracts `title` from the newspaper-parsed HTML and
overwrites it. Since the API gives us `headline` already, the pipeline should:
- Skip overwriting `title` if it's already populated from the API
- Skip overwriting `publish_date` if it's already populated
- Everything else (`text`, `images`, `top_image`, `videos`, `tags`) continues
  to come from newspaper3k as before

This keeps the pipeline reusable for other spiders unchanged.

### 3. `crawler/crawler/test/test_prothomalo_spider.py` — Update tests

**Unit tests** (mock-based, no network):
- Remove tests that mock the old CSS selector approach
- Add tests for `parse_api_response()`: verifies URL/date/language fields
  are correctly extracted from a mock API JSON payload
- Add test for API pagination: verifies a new API request is yielded
  when a full page of results is returned
- Keep the `parse_article` test (HTML body captured)
- Keep the dateparser bug test (or update it to confirm the bug is fixed)

**Live integration tests** (hit real site):
- Replace the broken link-pattern test with: API returns ≥1 story
- Replace the broken CSS-selector date test with: API story `published-at`
  is a valid Unix timestamp
- Keep `test_live_homepage_reachable` as-is

---

## Step-by-Step Implementation Order

1. **Fix the spider** (`prothomalo.py`)
   - Rewrite using the API-based approach above
   - Keep `allowed_domains` and `name` unchanged (pipeline still uses `spider.name`)

2. **Adjust the pipeline** (`news_details_extractor.py`)
   - Guard `title` and `publish_date` assignments with `if not item.get(...)`

3. **Update the tests** (`test_prothomalo_spider.py`)
   - Replace old unit tests with API-response-based mocks
   - Update live tests to validate the API

4. **Run the full test suite** to verify nothing in the other spiders broke

5. **Commit and push** to `claude/review-content-vFSNL`

---

## What Is NOT Changing

- `bdnews24.py` and `thedailystar.py` spiders — untouched
- `mongodb.py` pipeline — untouched
- `news.py` item definition — untouched (all fields already exist)
- `url_processor.py` — untouched
- Docker/docker-compose setup — untouched
- newspaper3k submodule — untouched

---

## Risk & Trade-offs

| Risk | Mitigation |
|---|---|
| API may rate-limit aggressive pagination | Use `DOWNLOAD_DELAY` (already 4s) and `limit=50` |
| API response schema may change in future | Live test validates schema each run |
| Article body still requires HTML fetch | No change to newspaper3k pipeline |
| `published-at` is in milliseconds, not seconds | Divide by 1000 before `datetime.fromtimestamp()` |
| Tags not in API response | newspaper3k still extracts them from HTML as before |
