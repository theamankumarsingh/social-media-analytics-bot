# Social Media Analytics Bot

Generate a LinkedIn performance report with:

- Organization-level share statistics.
- Recent post-level metrics (impressions, clicks, likes, comments, shares, engagement).
- AI-generated strategic analysis using Ollama.

The script creates a markdown report in the project root named like report-YYYY-MM-DD.md.

## Prerequisites

- Python 3.12+ (for local run).
- Docker (optional, for container run).
- LinkedIn access token with permissions to read organization analytics.
- Running Ollama endpoint and available model.

## Setup

1. Clone the repository and move into the project folder.
2. Create your environment file from the example:

```bash
cp .env.example .env
```

3. Fill .env values:

- OLLAMA_BASE_URL: Base URL for Ollama API, for example http://host.docker.internal:11434 (Docker) or http://localhost:11434 (local).
- OLLAMA_MODEL: Model name in Ollama, for example llama3.
- LINKEDIN_ACCESS_TOKEN: Your LinkedIn access token.
- LINKEDIN_ORGANIZATION_ID: Numeric organization id or full urn:li:organization:*.
- LINKEDIN_RECENT_POST_MAX: Fetch up to this many recent posts.

If fewer posts exist than LINKEDIN_RECENT_POST_MAX, the bot automatically processes only available posts.

## Run Locally

1. Create and activate a virtual environment.
2. Install dependencies.
3. Run the script.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## Run with Docker

Build and run with Docker Compose:

```bash
docker compose up --build
```

The Compose file:

- builds the image from the local [Dockerfile](Dockerfile)
- loads variables from [.env](.env)
- mounts the project so the generated report is written back to the workspace
- maps `host.docker.internal` for Ollama access on Linux

If you want to run the container directly without Compose, you can still use:

```bash
docker build -t social-bot .
docker run --rm --env-file .env -v $(pwd):/app:z social-bot
```

## Output

- Report file: report-YYYY-MM-DD.md
- Includes:
	- AI strategic analysis.
	- Organization notable metrics.
	- Recent posts summary and detailed post table.
	- Raw API data audit section.

## Troubleshooting

- LinkedIn API 400/403:
	- Verify token scopes and organization access.
	- Confirm LINKEDIN_ORGANIZATION_ID is correct.
	- Ensure token is not expired.
- No recent posts in report:
	- Confirm your organization has recent shares.
	- Increase LINKEDIN_RECENT_POST_MAX.
- AI analysis fails:
	- Verify OLLAMA_BASE_URL is reachable from where the script runs.
	- Confirm OLLAMA_MODEL exists in your Ollama instance.