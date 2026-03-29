# SHIPIQ — Cargo optimization service

REST API that allocates cargo volumes into vessel tanks under **single-cargo-type-per-tank** rules: a tank may hold only one cargo ID at a time (splitting that cargo across many tanks is allowed). The objective is to **maximize total loaded volume**.

## Approach

- **Exact optimization (MILP)** via [PuLP](https://coin-or.github.io/pulp/) + CBC for correctness on realistic instance sizes (tens to low thousands of tanks/cargos). Variables:
  - `y[i,j] ∈ {0,1}` — tank `j` is dedicated to cargo `i`
  - `x[i,j] ≥ 0` — volume of cargo `i` in tank `j`
- **Constraints:** at most one `i` per tank, tank capacity, cargo availability, and `x[i,j] ≤ capacity[j] · y[i,j]`.
- **Trade-offs:** MILP is optimal but worst-case exponential in branch-and-bound; for very large fleets, swap the solver module for a documented heuristic (e.g. large-neighborhood search or greedy + local search) while keeping the same HTTP schema.

## Assumptions

- Volumes and capacities are in the same unit (e.g. m³).
- Cargo and tank IDs are unique within a request (duplicates are rejected).
- Numeric fields are positive (no zero-volume cargo or zero-capacity tank in API validation).
- In-memory job store: one active “job” at a time (`POST /input` replaces prior input). Suitable for the assignment/demo; production would use a persistent queue and idempotent job IDs.

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/input` | Accept `cargos` and `tanks` JSON arrays |
| `POST` | `/optimize` | Run allocation on the last `/input` |
| `GET` | `/results` | Last optimization output |
| `GET` | `/health` | Liveness |

### `POST /input`

```json
{
  "cargos": [
    { "id": "C1", "volume": 1234 },
    { "id": "C2", "volume": 4352 }
  ],
  "tanks": [
    { "id": "T1", "capacity": 5000 },
    { "id": "T2", "capacity": 4000 }
  ]
}
```

### `POST /optimize` / `GET /results`

Response body (fields always present; `allocations` lists positive loads only):

```json
{
  "status": "optimal",
  "total_loaded": 12345.0,
  "total_cargo_volume": 20000.0,
  "total_tank_capacity": 25000.0,
  "allocations": [
    { "tank_id": "T1", "cargo_id": "C2", "volume": 4352.0 }
  ],
  "solver_message": null
}
```

Optional auth: set `SHIPIQ_API_KEY` and send header `X-API-Key: <value>` (skipped for `/health`).

## Local setup

**Python 3.11+** recommended.

```bash
cd shipiq
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PYTHONPATH=src
cp .env.example .env
python -m shipiq.api.app
```

Server listens on `PORT` (default `8080`).

### Tests

**Unit:** `allocate_cargo_to_tanks` (including bottlenecks, empty input, per-tank constraints), `Cargo`/`Tank` validation, and `parse_cargos_tanks`. **Integration (Flask):** `/input` → `/optimize` → `/results`, error statuses, and optional `X-API-Key`.

```bash
cd shipiq
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

On macOS, if CBC is missing, install a CBC binary PuLP can find (e.g. `brew install cbc`) or run tests inside Docker where `coinor-cbc` is installed.

### Docker

```bash
cd shipiq
docker build -t shipiq:latest .
docker run --rm -p 8080:8080 shipiq:latest
```

The container runs `gunicorn shipiq.wsgi:app` with `PYTHONPATH=/app/src`.

Example:

```bash
curl -s http://localhost:8080/health
curl -s -X POST http://localhost:8080/input \
  -H 'Content-Type: application/json' \
  -d '{"cargos":[{"id":"A","volume":150}],"tanks":[{"id":"T1","capacity":100},{"id":"T2","capacity":100}]}'
curl -s -X POST http://localhost:8080/optimize
curl -s http://localhost:8080/results
```

## Cloud deploy (bonus)

Build and push the image to your registry, then run on Cloud Run, ECS, or AKS with `PORT` matching the platform’s injected port. Ensure CBC is available (this image installs `coinor-cbc`).

## Layout

```
shipiq/
  src/shipiq/
    domain/           # entities + result DTOs
    services/         # allocation (MILP)
    application/      # job store
    api/              # Flask app, routes, validation
  tests/
  Dockerfile
  requirements.txt
```

## License

Assignment / demo code — adjust as needed for your submission.
