"""MovieLens ratings dashboard — four questions, Streamlit."""

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "movie_ratings.csv"


def split_genres(val) -> list[str]:
    if pd.isna(val):
        return ["Unknown"]
    text = str(val).strip()
    if not text or text.lower() in {"nan", "none"}:
        return ["Unknown"]
    parts = [p.strip() for p in text.split("|") if p.strip()]
    if not parts:
        return ["Unknown"]
    return ["Unknown" if p.lower() == "unknown" else p for p in parts]


@st.cache_data
def load_ratings() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["genre_list"] = df["genres"].map(split_genres)
    return df


@st.cache_data
def movie_table(df: pd.DataFrame) -> pd.DataFrame:
    movies = df.drop_duplicates("movie_id")[
        ["movie_id", "title", "year", "decade", "genre_list"]
    ].copy()
    return movies


def explode_movies(movies: pd.DataFrame) -> pd.DataFrame:
    return movies.explode("genre_list").rename(columns={"genre_list": "genre"})


def explode_ratings(df: pd.DataFrame) -> pd.DataFrame:
    return df.explode("genre_list").rename(columns={"genre_list": "genre"})


def genre_movie_counts(movies: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_movies(movies)
    n_movies = movies["title"].nunique()
    out = (
        exploded.groupby("genre", as_index=False)["title"]
        .nunique()
        .rename(columns={"title": "n_movies"})
        .sort_values("n_movies", ascending=False)
    )
    out["pct_movies"] = 100.0 * out["n_movies"] / n_movies
    return out, n_movies


def genre_means(df: pd.DataFrame, movie_counts: pd.DataFrame) -> pd.DataFrame:
    exploded = explode_ratings(df)
    stats = exploded.groupby("genre", as_index=False).agg(
        mean_rating=("rating", "mean"),
        n_ratings=("rating", "size"),
        n_movies=("title", "nunique"),
    )
    median_movies = float(movie_counts["n_movies"].median())
    keep = set(movie_counts.loc[movie_counts["n_movies"] >= median_movies, "genre"])
    stats = stats[stats["genre"].isin(keep)].sort_values("mean_rating", ascending=False)
    return stats, median_movies


def decade_means(df: pd.DataFrame) -> pd.DataFrame:
    timed = df.dropna(subset=["decade"]).copy()
    timed["decade"] = timed["decade"].astype(int)
    return (
        timed.groupby("decade", as_index=False)
        .agg(
            mean_rating=("rating", "mean"),
            n_ratings=("rating", "size"),
            n_movies=("title", "nunique"),
        )
        .sort_values("decade")
    )


def movie_scores(df: pd.DataFrame) -> pd.DataFrame:
    stats = df.groupby("title", as_index=False).agg(
        n=("rating", "size"),
        mean=("rating", "mean"),
    )
    return stats.sort_values(["mean", "n", "title"], ascending=[False, False, True])


def horizontal_bar(data: pd.DataFrame, y: str, x: str, x_title: str, sort_field: str):
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            y=alt.Y(f"{y}:N", sort=alt.EncodingSortField(field=sort_field, order="descending"), title=""),
            x=alt.X(f"{x}:Q", title=x_title),
            tooltip=list(data.columns),
        )
        .properties(height=max(280, 22 * len(data)))
    )


st.set_page_config(page_title="Movie ratings", layout="wide")
df = load_ratings()
movies = movie_table(df)
counts, n_movies = genre_movie_counts(movies)
all_genres = counts["genre"].tolist()

st.title("Movie ratings")
st.caption("MovieLens ratings joined to titles, release years, and genres.")

with st.expander("How genres are counted (read this before the charts)", expanded=True):
    st.markdown(
        """
A movie can have several genres (`Comedy|Drama`). Before any genre count or average:

1. Split on `|` and **count the movie in every tag** (not as one combined label).
2. Empty / `unknown` tags are kept as **Unknown**.
3. **Q1 percents** are share of unique movies, so they **sum to more than 100%**.
4. **Q2** drops genres whose movie count is below the **median** movie count across genres.
5. **Q3** uses **release decade** from the dataset directly.
6. **Q4** ranks by `n × mean rating` among movies with at least the floor you set.
        """
    )

st.sidebar.header("Filters")
selected_genres = st.sidebar.multiselect(
    "Genres to show (Q1 and Q2)",
    options=all_genres,
    default=all_genres,
    help="Does not change how movies were tagged — only which bars appear.",
)
min_ratings = st.sidebar.slider(
    "Minimum ratings for top movies (Q4)",
    min_value=50,
    max_value=400,
    value=50,
    step=10,
    help="Assignment floors are 50 and 150. Drag to compare.",
)
compare_floor = st.sidebar.selectbox("Compare Q4 floor against", options=[50, 150], index=1)

if not selected_genres:
    st.warning("Select at least one genre in the sidebar.")
    st.stop()

counts_view = counts[counts["genre"].isin(selected_genres)]
means, median_movies = genre_means(df, counts)
means_view = means[means["genre"].isin(selected_genres)]
decades = decade_means(df)
scores = movie_scores(df)
top_now = scores[scores["n"] >= min_ratings].head(5)
top_compare = scores[scores["n"] >= compare_floor].head(5)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ratings", f"{len(df):,}")
c2.metric("Movies", f"{n_movies:,}")
c3.metric("Q2 median movie-count floor", f"{median_movies:.0f}")
c4.metric("Avg genre tags per movie", f"{counts['n_movies'].sum() / n_movies:.2f}")

st.subheader("Q1 — Genre breakdown")
st.caption(
    "Horizontal bars, sorted by movie count. "
    "Percents are share of unique movies and will not add to 100%."
)
st.altair_chart(
    horizontal_bar(counts_view, "genre", "n_movies", "Unique movies rated", "n_movies"),
    use_container_width=True,
)
st.dataframe(
    counts_view.assign(**{"% of movies": counts_view["pct_movies"].round(1)})[
        ["genre", "n_movies", "% of movies"]
    ],
    hide_index=True,
    use_container_width=True,
)

st.subheader("Q2 — Genre satisfaction")
st.caption(
    f"Mean of all ratings tagged with each genre. Genres with fewer than "
    f"{median_movies:.0f} movies (the median across genres) are omitted. Sorted by mean."
)
if means_view.empty:
    st.info("None of the filtered genres pass the median movie-count floor.")
else:
    st.altair_chart(
        horizontal_bar(means_view, "genre", "mean_rating", "Mean rating (1–5)", "mean_rating"),
        use_container_width=True,
    )
    hi = means.iloc[0]
    lo = means.iloc[-1]
    h1, h2 = st.columns(2)
    h1.metric("Highest mean (passing floor)", hi["genre"], f"{hi['mean_rating']:.3f}")
    h2.metric("Lowest mean (passing floor)", lo["genre"], f"{lo['mean_rating']:.3f}")
    st.dataframe(
        means_view.assign(**{"mean_rating": means_view["mean_rating"].round(3)}),
        hide_index=True,
        use_container_width=True,
    )

st.subheader("Q3 — Ratings over release decades")
st.caption(
    "Line chart of mean rating by movie release decade."
)
line = (
    alt.Chart(decades)
    .mark_line(point=True)
    .encode(
        x=alt.X("decade:O", title="Release decade"),
        y=alt.Y("mean_rating:Q", title="Mean rating", scale=alt.Scale(zero=False)),
        tooltip=["decade", "mean_rating", "n_ratings", "n_movies"],
    )
)
st.altair_chart(line, use_container_width=True)
st.dataframe(
    decades.assign(**{"mean_rating": decades["mean_rating"].round(3)}),
    hide_index=True,
    use_container_width=True,
)

st.subheader("Q4 — Best movies with a ratings floor")
st.caption(
    "Top 5 movies by highest mean rating, filtered by minimum number of ratings."
)
col_a, col_b = st.columns(2)
with col_a:
    st.markdown(f"**Top 5 with at least {min_ratings} ratings** (slider)")
    chart_now = (
        alt.Chart(top_now)
        .mark_bar()
        .encode(
            y=alt.Y("title:N", sort="-x", title=""),
            x=alt.X("mean:Q", title="Mean rating", scale=alt.Scale(domain=[0, 5])),
            tooltip=["title", "n", "mean"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart_now, use_container_width=True)
    show = top_now.copy()
    show["mean"] = show["mean"].round(3)
    st.dataframe(show[["title", "n", "mean"]], hide_index=True, use_container_width=True)
with col_b:
    st.markdown(f"**Top 5 with at least {compare_floor} ratings**")
    chart_cmp = (
        alt.Chart(top_compare)
        .mark_bar()
        .encode(
            y=alt.Y("title:N", sort="-x", title=""),
            x=alt.X("mean:Q", title="Mean rating", scale=alt.Scale(domain=[0, 5])),
            tooltip=["title", "n", "mean"],
        )
        .properties(height=260)
    )
    st.altair_chart(chart_cmp, use_container_width=True)
    show2 = top_compare.copy()
    show2["mean"] = show2["mean"].round(3)
    st.dataframe(show2[["title", "n", "mean"]], hide_index=True, use_container_width=True)

now_titles = list(top_now["title"])
cmp_titles = list(top_compare["title"])
if now_titles == cmp_titles:
    st.info(
        f"Same five titles at both floors ({min_ratings} and {compare_floor} minimum ratings)."
    )
else:
    dropped = [t for t in now_titles if t not in cmp_titles]
    added = [t for t in cmp_titles if t not in now_titles]
    st.warning(f"Dropped at the higher floor: {dropped}. Newly in the top 5: {added}.")