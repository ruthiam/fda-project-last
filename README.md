# 🛡️ Market Risk Monitoring - Phase 1

## Choice of Dashboard
I have provided two versions of the app to suit your needs:

### Option A: The "Instant" Dashboard (`index.html`)
**Zero Setup Required.** This is a standalone "mini webapp" that runs entirely in your browser.
1.  **Open**: Double-click `index.html`.
2.  **Upload**: Select `data/market_data.csv` (or any tidy CSV with Date, Asset, Price).
3.  **Analyze**: View interactive reports, normality checks, and rolling risk instantly.

### Option B: The "Pro" Dashboard (`app.py`)
**Requires Python.** Supports live data fetching from Yahoo Finance and more advanced analytics.
1.  **Launch**: Click the **"Play" button** in VS Code (top right) or run `python app.py`.
2.  **Install Dependencies**: (Only needed once)
    ```bash
    pip install -r requirements.txt
    ```

3. **Export Data**:
   The data is automatically exported to `data/market_data.csv` on the first run. You can also manually trigger an export via the sidebar button.

## Project Structure
- `app.py`: Main Streamlit application.
- `requirements.txt`: Python package dependencies.
- `data/`: Directory where the exported CSV is stored.
- `README.md`: Project documentation.
