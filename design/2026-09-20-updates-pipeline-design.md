# Family history updates — design

*Agreed between Brian and Claude, 20 September 2026, in conversation. This is the record of that agreement; the implementation plan follows from it.*

## 1. Purpose

Brian researches his family history in a private Dropbox folder (`D:\Dropbox\Family\family history`). A few relatives want to hear how it is going. One is in her eighties and uses only email and WhatsApp. Updates today are occasional emails and WhatsApp messages, written when Brian remembers.

This system makes the updates regular without making them a chore:

- Claude notes each tellable finding **as it happens** during research sessions.
- When enough has accumulated, Claude **assembles a short post** and hands it to Brian.
- Brian **pastes it into a WhatsApp group** and says so.
- The post is then **published to a public web page**, which every later post links to as "read past updates".

It is deliberately small. It is not the eventual dossier website; it is the thing that keeps relatives in touch until that exists, and it produces a dated archive of posts that site can absorb.

## 2. Two audiences, two branches

Brian's four grandparents were Clive **Sharland** and Joan **Crowe**; Cyril **Ferreira** and Doreen **Gresty**. The two sides of the family do not know each other, and there is (or was) a separate Ferreira family WhatsApp group. So there are **two independent streams**, named for the grandparents:

| Branch key | Covers | WhatsApp group | Page |
|---|---|---|---|
| `sharland-crowe` | Sharland, Solomon, Mattocks, Crowe, Rixom, Southwell/Cardell and their lines | the Sharland relatives | `/sharland-crowe/` |
| `ferreira-gresty` | Ferreira, Tiran, Gresty, Truscott and their lines | the Ferreira relatives | `/ferreira-gresty/` |

A post belongs to exactly one branch and its page mirrors exactly what that group received. An item relevant to both sides is written twice, once for each audience. Nothing merges the two, on the page or anywhere else, because neither group signed up to read the other family's news.

## 3. What is fixed by decision

- **Sending is manual, by copy-and-paste.** WhatsApp's Groups API (2026) is restricted to Official Business Accounts, creates its own groups of at most eight, and charges per message; the unofficial libraries breach WhatsApp's terms and risk the number. So: Claude drafts, Brian pastes. Not to be revisited without a change in WhatsApp's terms.
- **Trigger for a post:** content-based — three or more untold items in a branch — with a backstop of one item and 21 days since that branch's last post. Never time-based alone.
- **Length:** 150–250 words, three to five items, one closing link.
- **Text only.** No images on either channel. Photograph policy is deferred indefinitely.
- **Voice:** first person, Brian's. The posts do not say that an AI helped; Brian may change this.
- **Living people are shortened:** first name and initial of current surname — "Alice P." No addresses, health, contact details or exact birth dates for the living. No minors under any name. The dead in full.
- **A sent post is never edited.** Corrections are a line in the next post.
- **Nothing unsent is ever published.** The build ignores posts without a `sent:` date.
- **Page:** public, indexable, no JavaScript, no tracking, no images, no email address (the introduction says replies come on WhatsApp). Titles: *"Sharland and Crowe family history — updates from Brian"* and *"Ferreira and Gresty family history — updates from Brian"*.
- **The nudge lives in Claude's memory**, not in a scheduler (Claude's scheduled routines run in the cloud and cannot read local files).
- **Used items are archived, not deleted** (`queue\used\`), in keeping with the research folder's rule that nothing is deleted.

## 4. Repository layout

Public GitHub repository `sharland/family-history-updates`, working copy `D:\Claude-work\family-history-updates\` (outside Dropbox).

```
family-history-updates\
  README.md                       what this is; how a post gets out
  design\                         this document
  queue\
    items\
      sharland-crowe\             one file per untold finding — the unit the nudge counts
      ferreira-gresty\
    ready\
      sharland-crowe\             assembled posts awaiting Brian's paste
      ferreira-gresty\
    used\
      sharland-crowe\             items already folded into a sent post
      ferreira-gresty\
  posts\
    sharland-crowe\               sent posts only — the page is built from these
    ferreira-gresty\
  site\
    build.py                      posts\ → docs\
    check.py                      lints one draft against the rules
    template.html                 the one page template, CSS inline
  docs\                           GENERATED; GitHub Pages serves this from main
    index.html                    landing page: names the two families, links to each
    sharland-crowe\index.html
    ferreira-gresty\index.html
  tests\
    test_build.py
    test_check.py
    fixtures\
```

**Branch is expressed by folder**, never by a field. A file's branch is the folder it sits in; there is nothing to mistype.

**Kept in the private Dropbox folder, not in the repo:**

- `D:\Dropbox\Family\family history\.claude\living-people.txt` — the living-people list (see §6).
- `D:\Dropbox\Family\family history\.claude\digest-style.md` — the style notes for writing items and posts, so the public repo carries no working notes about named relatives.

## 5. The two file types

### 5.1 An item — `queue\items\<branch>\YYYY-MM-DD-<slug>.md`

Written the moment a tellable thing happens, not at the end of the session. One item, one file.

```
---
date: 2026-09-19
weight: 2
source: Documents\Family correspondence\2026-09-19 Conversation with Alice P.md
---
*Grandpa Crowe's nickname was "Chough".* Alice P. told me it was because a chough is "the least objectionable bird of the crow family". Grandad built a small sailing boat in Rhodesia in 1958 and named it after him — there's a photograph of Gran christening it with a bottle.
```

- `weight`: 1 minor, 2 normal, 3 big enough to carry a post alone. Used when choosing what goes in a post; not published.
- `source`: a private pointer into the research folder for Claude's own use. **Never copied into a post.**
- The body is already in post form — WhatsApp dialect, living-people rule applied — so assembling a post is selection and light editing, not rewriting.

What counts as tellable: a question answered, a record found, a dossier finished, a story recorded, a person identified. Housekeeping (moving folders, fixing links) is not.

### 5.2 A post — `queue\ready\<branch>\YYYY-MM-DD.md`, then `posts\<branch>\YYYY-MM-DD.md`

```
---
date: 2026-09-21
items:
  - 2026-09-17-crowe-1911-census
  - 2026-09-19-chough
  - 2026-09-20-sybil-dossier
sent:
---
*Family history — 21 September*

Three things from the last fortnight.

*Grandpa Crowe's nickname was "Chough".* …

*The 1911 census found the whole Crowe household at the Royal Pier Hotel.* …

*Great-granny Sybil now has a file of her own.* …

Read past updates: https://sharland.github.io/family-history-updates/sharland-crowe/
```

- The body is **WhatsApp's own formatting**: `*bold*`, `_italic_`, paragraphs separated by blank lines, no headings, no Markdown, one link at the end. The code block Claude gives Brian is this file verbatim; the page is built from the same bytes.
- `sent:` is empty until Brian says the post has gone. Claude fills it with the date Brian gives (default today) when moving the file to `posts\`.
- `items:` lists the item slugs used, so used items can be moved to `queue\used\` and the post's provenance is traceable.
- A post without `sent:` is not rendered. A post with `sent:` is never changed.

## 6. The living-people rule and `check.py`

**`living-people.txt`** (private, in the Dropbox `.claude\` folder). One person per line: the full name as it appears in the tree or documents, a pipe, the display form.

```
# Living people — full name | how they appear in posts. Comments start with #.
Alice Margaret Penrose | Alice P.
Peter Trevithick | Peter T.
```

Seeded once from GEDCOM v3 — every individual with no death event whose birth is after 1926 or unknown — and corrected by Brian; Claude adds people as they arise. Minors are listed with display form `—`, meaning "do not mention".

**`check.py <draft>`** exits non-zero and prints each problem when a draft:

1. contains a listed person's full name, or their bare surname as a standalone word (case-insensitive, punctuation-tolerant);
2. contains any name whose display form is `—`;
3. has fewer than 150 or more than 250 words in the body (front matter excluded; the closing link counts as one word);
4. lacks a final line beginning `Read past updates: https://sharland.github.io/family-history-updates/<branch>/` matching the folder it is in;
5. uses Markdown formatting — `**`, a line beginning `#`, or `[text](url)`;
6. has a non-empty `source:` line anywhere in the body (a private pointer leaked from an item).

It passes a clean draft silently. Claude runs it before showing Brian any draft, and again after edits.

The check is a net, not the rule. Claude applies the rule when writing; the check catches what slipped.

## 7. The flow in a session, and the nudge

**Capture** — during any session in the research folder, when something tellable lands, Claude writes the item file immediately, in the right branch.

**Nudge** — at the start of every session in the research folder, Claude counts `queue\items\<branch>\` for each branch and reads the newest filename in `posts\<branch>\`. For any branch with three or more items, or one or more items and 21+ days since its last post (or no post ever), Claude tells Brian before anything else — how many items, since when, which branch — and offers to assemble now or at the end. The check repeats at the end of a session that added items. Brian can also ask at any time. Claude never assembles unasked and never publishes anything not confirmed sent.

The rule is stored as a feedback memory in Claude's memory directory for this project and indexed in `MEMORY.md`, so it is read whenever the folder is opened.

**Assemble** — on Brian's yes: choose three to five items (most recent, or one theme if they form one; weight 3 may stand alone), write `queue\ready\<branch>\YYYY-MM-DD.md`, run `check.py`, then hand Brian the body in a code block. Optionally also send the file to Brian's phone via the session's file-sending tool so it can be pasted from there.

**Edit** — Brian changes wording by telling Claude or editing the file; Claude re-runs the check.

**Send** — Brian pastes into the group and says "sent" (plus the date if not today). Claude:

1. fills in `sent:`;
2. moves the file to `posts\<branch>\`;
3. moves each listed item from `queue\items\<branch>\` to `queue\used\<branch>\`;
4. runs the tests, runs `build.py`, verifies `docs\` changed only as expected;
5. commits (post, moved items, regenerated docs) and pushes;
6. reports the page URL and confirms the post is visible there.

**Backlog** — `queue\ready\<branch>\` may hold several posts. They go out oldest first; Claude suggests a few days between them.

**Corrections** — a mistake in a sent post is corrected by a sentence in the next post of that branch, never by editing the sent file or the page.

## 8. The page and `build.py`

`build.py` reads `posts\<branch>\*.md`, keeps those with a `sent:` date, sorts newest first, converts the WhatsApp dialect to HTML, and writes `docs\<branch>\index.html` from `template.html`; and writes `docs\index.html`, the landing page. It takes no arguments, has no dependencies beyond the Python standard library, and is deterministic: the same inputs produce byte-identical output.

**Conversion rules:** `*text*` → `<strong>`, `_text_` → `<em>`, blank-line-separated blocks → `<p>`, the first line of a post (its `*Family history — date*` line) → the post's `<h2>`, the closing link → a real `<a>`, everything else HTML-escaped. Each post is a `<article>` with `id="YYYY-MM-DD"` so a single update can be linked to. The sent date is shown in words ("Sent on Sunday 21 September 2026").

**Landing page (`docs\index.html`):** the site title, one paragraph naming the two families and saying what the pages are, two links.

**Branch page:** title; a short standing introduction (what the page is, that living relatives' names are shortened, that replies come on WhatsApp); then every post in full, newest first. One page per branch until it grows long; `build.py` will split by year when a branch passes about forty posts — not built until needed.

**Presentation:** system font stack; body text 20px, line height 1.6, maximum width 38em, dark grey on white, generous margins; readable on a phone without zooming; no JavaScript, no external requests of any kind, no images, no analytics. `<html lang="en-GB">`, a `<meta name="viewport">`, and headings in order, so it reads well aloud too.

**Hosting:** GitHub Pages from branch `main`, folder `/docs`, enabled once with `gh api`. Pushing `main` publishes within about a minute. No Actions, no build service, no custom domain (can be added later without changing anything else).

## 9. Testing

`pytest`, run by Claude before every push.

`tests\test_build.py`, against fixtures in `tests\fixtures\`:

- three posts render newest first, each with its date anchor and sent date in words;
- a post with empty `sent:` is absent from the output;
- `*bold*`, `_italic_`, paragraphs and the closing link convert correctly;
- `<`, `>`, `&` and quotes in a post are escaped;
- the landing page links to both branch pages;
- running the build twice produces identical bytes;
- an empty branch produces a valid page saying there are no updates yet.

`tests\test_check.py`:

- a clean 200-word draft passes;
- a full name from the list fails, and so does the bare surname;
- a `—` (minor) name fails;
- 149 and 251 words fail; 150 and 250 pass;
- missing link, link for the wrong branch, `**`, `# `, `[x](y)` and a leaked `source:` each fail with a message naming the problem;
- the list parser ignores comment and blank lines.

## 10. First run

1. Seed `living-people.txt` from GEDCOM v3 and give Brian the list to correct once.
2. Write `digest-style.md` (the rules of §3 and §5 in working form, with a few example items).
3. Repository: layout, `README.md`, `.gitignore`, the scripts and tests, first push; enable Pages; confirm the landing page is live with two empty branch pages before any post exists.
4. Items for September 2026 so far: about eight to `sharland-crowe` (the 1881, 1891 and 1911 censuses and what they settled; Bunny's 1924 marriage and the Bird Wedding; the *Chough*; the tap and die set; Sybil's dossier; the Ancestry corrections list) and three or four to `ferreira-gresty` (Percy's dossier and his service record; Doreen's dossier; Gwendoline Truscott's parentage confirmed).
5. Assemble one catch-up post per branch, run the checks, hand the Sharland–Crowe one to Brian first.
6. Pointers: a line each in `INDEX.md` and `Resource Links.md` in the research folder; the nudge rule saved to memory.

## 11. Out of scope

Automatic sending; email as a channel (the same text pastes into an email if ever needed); photographs; RSS; comments; a custom domain; per-post pages; the eventual dossier website.

## 12. Decisions taken along the way

| Decision | Chosen | Alternative rejected |
|---|---|---|
| Page privacy | Public, indexable; living people shortened | Unlisted (false privacy); private (defeats the purpose) |
| Trigger | 3 items per branch, or 1 item + 21 days | Weekly regardless; one post per finding |
| Photos | None, deferred | One approved image per post |
| Site generator | ~100-line `build.py`, no dependencies | Jekyll (opaque failures; stock theme too small for the reader) |
| One page or two | Two branch pages, one build | Tabs or filter (JavaScript; mixes families) |
| Used items | Archived to `queue\used\` | Deleted in the sending commit |
| Email on page | No | Yes |
| AI mention in posts | No | — |
