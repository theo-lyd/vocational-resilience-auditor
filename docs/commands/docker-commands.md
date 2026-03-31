# Docker Commands (Project Usage)

## `docker compose up --build`
- Who: contributor or reviewer wanting containerized execution
- What: build images and start services
- When: reproducible local demo or environment parity run
- Where: repository root with `docker-compose.yml`
- Why: run pipeline/dashboard without manual dependency setup
- How: `docker compose up --build`
- Alternatives: `docker compose up` (no rebuild), manual local run via venv

## `docker compose up`
- Who: contributor
- What: start previously built services
- When: repeat runs after first build
- Where: repository root
- Why: faster startup when images already exist
- How: `docker compose up`
- Alternatives: `docker compose up --build` when Dockerfiles changed

## `docker compose down`
- Who: contributor
- What: stop and remove running compose services
- When: cleanup after demo/testing
- Where: repository root
- Why: free ports/resources and reset local state
- How: `docker compose down`
- Alternatives: `docker compose stop` (keep containers)

## `docker compose logs -f`
- Who: contributor/operator
- What: stream live logs for all compose services
- When: troubleshooting startup/runtime issues
- Where: repository root
- Why: inspect errors across services quickly
- How: `docker compose logs -f`
- Alternatives: `docker compose logs -f <service>`

## `docker compose ps`
- Who: contributor/operator
- What: list compose service status and ports
- When: verify services are running
- Where: repository root
- Why: quick runtime health check
- How: `docker compose ps`
- Alternatives: `docker ps`
