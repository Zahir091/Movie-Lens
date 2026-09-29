# Movie ratings dashboard

Streamlit app for four MovieLens questions: genre mix, genre satisfaction, mean rating by release decade, and top movies under a ratings floor.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Create a **public** GitHub repo, commit `app.py`, `requirements.txt`, and `movie_ratings.csv`, push `main`.
2. At [share.streamlit.io](https://share.streamlit.io) sign in with GitHub.
3. New app → that repo → branch `main` → main file `app.py` → Deploy.
