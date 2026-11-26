# Small Business Stock Tracker (Track B: Containers)

AWS Cloud Computing individual project. A small REST API that lets a small business owner create, read, update and delete stock items, each with a quantity and a reorder level.

- **Track:** B, Containers (EC2 + Docker + ECR)
- **Entity:** `Item` (one MySQL table, `items`)
- **Environment:** AWS Academy lab account (Lab Project: Microservices and CI/CD Pipeline Builder), region `us-east-1`

## Services

| Service | Image | Role |
| --- | --- | --- |
| `api` | Built from [`app/`](app/) (Python, Flask, gunicorn), pushed to Amazon ECR as `items-api` | REST API on port 80 |
| `db` | Official `mysql:8.4` | Stores the `items` table in a Docker volume; not exposed outside the Docker network |

Both run on one EC2 instance with Docker Compose ([`docker-compose.yml`](docker-compose.yml)).

## CRUD endpoints

| Operation | Method and path | Success | Errors |
| --- | --- | --- | --- |
| Create | `POST /items` | `201` | `400` |
| Read | `GET /items/{itemId}` | `200` | `404` |
| Update | `PUT /items/{itemId}` | `200` | `400`, `404` |
| Delete | `DELETE /items/{itemId}` | `204` | `404` |

`GET /health` returns `200` for connectivity checks. Full details are in the [design brief](docs/design-brief.md).

## Run locally

Needs Docker Desktop.

```powershell
copy .env.example .env      # then change the passwords in .env
docker compose up -d --build
```

Then, in Git Bash:

```bash
API_URL=http://localhost bash scripts/test_api.sh   # expects 9 passed, 0 failed
python -m unittest discover -s tests                # validation unit tests
docker compose down
```

## Repository layout

```
README.md
docker-compose.yml   the two services
.env.example         settings template (copy to .env, never commit .env)
app/                 items-api: app.py, validation.py, Dockerfile, requirements.txt
db/init.sql          creates the items table on first start
tests/               validation unit tests
scripts/test_api.sh  end-to-end API test, saves output to evidence/
docs/                design brief and architecture diagram
evidence/            AWS screenshots and test outputs
```

## Status

- [x] Use case and data entity
- [x] API image, Docker Compose, tests (passing locally: 9/9 API checks)
- [ ] Design brief and diagram updated for Track B
- [ ] Deployed to EC2 with the image in ECR
- [ ] AWS evidence
