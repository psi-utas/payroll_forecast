## 📂 Project Architecture

* **`app.py`** – The main entry point for the Streamlit application. Handles global page configuration, routing, and the Entra ID authentication gate.
* **`core/`** – Contains business logic, financial calculations, and reusable UI components.
* **`views/`** – Houses the individual page modules rendered by the application router.
* **`data/`** – Stores Excel spreadsheets and data sources used across the forecasting tools.

## Install

### Create virtual environment
```bash
su - sa-gpgsim

git clone https://git.its.utas.edu.au/UTAS/payroll_forecast payroll_forecast

cd payroll_forecast

python3.12 -m venv venv

source venv/bin/activate
```

### Install packages
```bash
pip install -r requirements.txt
```

The deploy workflow keeps `venv/` out of its `rsync --delete` and re-runs
`pip install -r requirements.txt` on every deploy, so new requirements are picked up automatically.

### Register the app in Microsoft Entra ID
Sign-in uses Streamlit's built-in OIDC auth (`st.login("microsoft")`) against Entra ID.

1. Entra admin centre > **App registrations** > **New registration**
   - Supported account types: **Accounts in this organizational directory only** (single tenant)
   - Redirect URI: platform **Web**, `https://payrollforecast.utas.edu.au/oauth2callback`
     (add `http://localhost:8501/oauth2callback` too for local dev)
2. From **Overview**, note the **Application (client) ID** and **Directory (tenant) ID**.
3. **Certificates & secrets** > **New client secret**, and copy the secret **Value** (not its ID).
4. Optional: to limit access to specific people, set **Enterprise applications** > *app* >
   **Properties** > **Assignment required** to *Yes*, then add users/groups under **Users and groups**.

### Streamlit secrets
> [!NOTE]
> See the [Streamlit docs](https://docs.streamlit.io/develop/concepts/connections/authentication) for the full set of options.

`.streamlit/secrets.toml` is committed with `${...}` placeholders only. The deploy workflow
fills them in from these Gitea Actions secrets (repo **Settings** > **Actions** > **Secrets**):

| Secret | Value |
| --- | --- |
| `PAYROLL_COOKIE_SECRET` | Output of `python3 -c "import secrets; print(secrets.token_hex(32))"`. Keep it stable or users get logged out on every deploy. |
| `PAYROLL_ENTRA_CLIENT_ID` | Application (client) ID |
| `PAYROLL_ENTRA_CLIENT_SECRET` | Client secret **Value** |
| `PAYROLL_ENTRA_TENANT_ID` | Directory (tenant) ID |

The workflow also needs the same SSH settings as gpgsim: variables `SSH_HOST`, `SSH_USER`,
`SSH_PORT` and secret `SSH_KEY`.

Never commit real values to `secrets.toml`. For local dev, fill in the file locally (with
`redirect_uri = "http://localhost:8501/oauth2callback"`) and tell git to ignore your edits:

```bash
git update-index --skip-worktree .streamlit/secrets.toml
```

### Create systemd service
gpgsim already uses Streamlit's default port 8501 on this host, so this app listens on 8502.
Point the reverse proxy for `payrollforecast.utas.edu.au` at `127.0.0.1:8502`.

```bash
mkdir -p ~/.config/systemd/user

cat << EOF > ~/.config/systemd/user/payroll-forecast.service
[Unit]
Description=Payroll Forecast Streamlit App
After=network.target

[Service]
WorkingDirectory=/srv/sa-gpgsim/payroll_forecast/
ExecStart=/srv/sa-gpgsim/payroll_forecast/venv/bin/streamlit run /srv/sa-gpgsim/payroll_forecast/app.py --server.address 127.0.0.1 --server.port 8502
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now payroll-forecast
```
