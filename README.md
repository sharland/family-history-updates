# Family history updates

Short posts from Brian about what he has been finding out about the family — sent first to a family WhatsApp group, then kept here so they can be read again.

**Read them:** <https://sharland.github.io/family-history-updates/>

There are two streams, one for each side of the family, named for Brian's grandparents:

- **Sharland and Crowe** — <https://sharland.github.io/family-history-updates/sharland-crowe/>
- **Ferreira and Gresty** — <https://sharland.github.io/family-history-updates/ferreira-gresty/>

Living relatives are referred to by first name and initial only. Replies go to the WhatsApp group, not here.

## How a post gets out

1. As things are found, a short note goes into `queue/items/<branch>/` — one file per finding.
2. When there are three or more, they are assembled into a post in `queue/ready/<branch>/`, checked (`python site/check.py <file>`), and handed to Brian.
3. Brian pastes it into WhatsApp. Only then does the file move to `posts/<branch>/` with its `sent:` date, the items it used move to `queue/used/<branch>/`, and `python site/build.py` regenerates `docs/`, which GitHub Pages serves.

Posts without a `sent:` date are never published. Sent posts are never edited; corrections go in the next post.

## Running the scripts

Run the tools as `python site/build.py`, `python site/check.py <draft>` and `python -m pytest`. Never run `python -c "import posts"` (or a REPL) from the repo root: the top-level `posts/` folder shadows `site/posts.py`.

`python site/build.py` re-checks every sent post first and writes nothing if any check fails.

The design is in `design/`. Tests: `python -m pytest -q`.
