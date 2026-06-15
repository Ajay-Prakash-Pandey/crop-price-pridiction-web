# Host This Website Free Without A Card

Use **GitHub Pages**. It is free, does not need a credit card, and keeps the website available without Render-style sleeping.

This project now works in two modes:

- With `server.py`: full Python backend with live API data.
- Without `server.py`: static browser demo with saved crop/region assumptions, charts, and CSV/JSON export.

GitHub Pages uses the second mode.

## Steps

1. Create a GitHub account.
2. Create a new public repository.
3. Upload these files and folders:
   - `index.html`
   - `styles.css`
   - `app.js`
   - `data/`
   - `README.md`
4. Open the repository on GitHub.
5. Go to **Settings**.
6. Go to **Pages**.
7. Under **Build and deployment**, choose:
   - Source: `Deploy from a branch`
   - Branch: `main`
   - Folder: `/root`
8. Click **Save**.
9. Wait 1-3 minutes.
10. Open the Pages link shown by GitHub.

The link will look like:

```text
https://your-username.github.io/your-repository-name/
```

## Important

GitHub Pages cannot run Python files. The hosted site will use the browser-only prediction mode.

For a college project/demo, this is usually enough because:

- The website opens 24/7.
- No credit card is needed.
- Forecasts, history chart, assumptions, drivers, and export buttons work.

For live market API data, you still need a Python server such as Render paid, PythonAnywhere, or a VPS.
