# RepoMind-AI

RepoMind AI serves the frontend and API from one origin. It uses local Ollama
by default and can use OpenAI on a hosted deployment.

## Run locally

Install the backend dependencies, start Ollama, then run the API from the
`backend` directory:

```powershell
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). If serving the standalone
frontend with `python -m http.server 5500` from the `frontend` directory, open
`http://127.0.0.1:5500` instead. The API docs are at `/docs` on port 8000. Set
`OLLAMA_URL` or `OLLAMA_MODEL` in the environment to use a different Ollama
server or model. To use OpenAI locally, set `AI_PROVIDER=openai`,
`OPENAI_API_KEY`, and optionally `OPENAI_MODEL`.

## Deploy publicly on Render

The repository includes a `render.yaml` Blueprint that serves the frontend and
API together, configures OpenAI, and asks you to provide the API key as a
private environment variable.

1. Push this project to a GitHub repository you control.
2. Sign in to Render, choose **New + → Blueprint**, and connect that repository.
3. When prompted, enter your OpenAI API key for `OPENAI_API_KEY` in Render's
   private environment settings. Never put the key in source code or commit it.
4. Deploy the Blueprint. Render will provide an `onrender.com` URL after the
   deployment succeeds; open that URL to use the website.

The free web-service plan can sleep when idle, so the first request after idle
may be delayed. OpenAI API usage is billed separately by OpenAI. The public
`/ask` endpoint is unauthenticated and rate-limited; set an OpenAI usage budget
and monitor it in your OpenAI account. Do not expose server filesystem scanning
on a public deployment.

## Deploy on an Ubuntu VPS

Point a domain's DNS `A` record to the VPS public IP and allow inbound ports 80
and 443 in the VPS firewall. Install Python 3, Ollama, and Caddy on the VPS;
pull the model with `ollama pull gemma4:e2b`. Confirm the VPS has enough memory
for this model. Keep Ollama's port 11434 private.

From the project directory, install the Python dependencies:

```sh
python3 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt
```

The example systemd service assumes the project is installed at
`/opt/repomind-ai`. Create a dedicated service account, install the project at
that path, and grant the account read access:

```sh
sudo useradd --system --create-home --shell /usr/sbin/nologin repomind
sudo chown -R repomind:repomind /opt/repomind-ai
sudo cp /opt/repomind-ai/deploy/repomind.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now repomind
```

The service binds only to localhost and trusts forwarded client IPs only from
localhost. Configure Caddy to proxy your domain to `127.0.0.1:8000`:

```sh
sudo cp /opt/repomind-ai/deploy/Caddyfile.example /etc/caddy/Caddyfile
# Edit the Caddyfile and replace your-domain.example with your domain.
sudo systemctl reload caddy
```

Caddy obtains and renews the HTTPS certificate automatically. Do not expose
ports 8000 or 11434 directly to the internet.

The public `/ask` endpoint is open and limited to 10 requests per minute per
client IP. This in-memory limit is intended for a single Uvicorn worker; use
one worker unless you add a shared rate-limit store. Public AI usage can still
consume VPS resources. Project scanning is disabled unless `SCAN_ROOT` is set;
if enabled, requests are restricted to that directory.