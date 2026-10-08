## 📂 Project Architecture

* **`app.py`** – The main entry point for the Streamlit application. Handles global page configuration, routing, and the Entra ID authentication gate.
* **`core/`** – Contains business logic, financial calculations, and reusable UI components.
* **`views/`** – Houses the individual page modules rendered by the application router.
* **`data/`** – Stores Excel spreadsheets and data sources used across the forecasting tools.
