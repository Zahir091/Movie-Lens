# Build log (raw process notes)

## Moment 1 — first prompt vs first AI plan
**Prompt:** Analyze movie ratings for four questions (genre mix, genre satisfaction, ratings over time, top movies with a 50 then 150 floor).

**First AI move:** Treat this as a notebook/canvas analysis and list ~12 ambiguities (movies vs ratings, explode vs exclusive genre, mean of ratings vs mean of movie means, release year vs rating year, etc.).

**What I changed:** Answered the ambiguities myself instead of leaving defaults: movie = title/`movie_id`, add multi-genre films to both tags, keep unknown, use mean of ratings, Q2 floor = median movie count, group by release decade, drop missing years, rank Q4 by n × mean.

## Moment 2 — inverted “best movie” formula
**Prompt / choice:** Combat low-n high-star vs high-n slightly lower stars with a ratio. First idea: `# ratings / average rating`.

**What the AI flagged:** Dividing by the mean ranks a 500-rating 3-star film above a 50-rating 5-star film.

**What I changed:** Flip to **n × mean**. Keep the assignment floors of 50 and 150.

## Moment 3 — course overlay (charts + Streamlit)
**Guideline:** Ambiguity is on purpose; pick chart types; deploy Streamlit Community Cloud from a public GitHub repo; widgets required; no write-up in the app.

**What I didn’t need to re-answer:** Methodology already locked. Remaining work is charts + `app.py`.

**AI chart defaults (to judge later):**
- Q1: sorted horizontal bar (not pie — too many genres)
- Q2: sorted horizontal bar of means
- Q3: line by **release** decade
- Q4: bars of n × mean for top 5; slider for the floor

**Result of 50 vs 150:** Same top 5 (all have 420+ ratings). Left that in the UI instead of inventing a change.
