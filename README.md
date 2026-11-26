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
scripts/deploy_ec2.sh  EC2 setup: Docker, image build and push to ECR, start services
scripts/test_api.sh  end-to-end API test, saves output to evidence/
docs/                design brief and architecture diagram
evidence/            AWS screenshots and test outputs
```

## Deployment plan (AWS)

Region `us-east-1`, AWS Academy lab account. Each step produces evidence for `evidence/`.

1. **ECR:** create the private repository `items-api`.
2. **Security group `items-api-sg`:** inbound HTTP 80 from your IP; SSH 22 from the EC2 Instance Connect range for `us-east-1` (`18.206.107.24/29`).
3. **EC2:** launch `items-api-host` with Amazon Linux 2023, `t3.small`, a public IP, `items-api-sg`, IAM instance profile `LabInstanceProfile`, and an encrypted 8 GB gp3 volume.
4. **Connect** with EC2 Instance Connect, then on the instance:

   ```bash
   sudo dnf install -y git
   git clone https://github.com/Nalen518/Cloud-Computing-Final-Project.git
   cd Cloud-Computing-Final-Project
   bash scripts/deploy_ec2.sh
   ```

   The script installs Docker and Compose, creates `.env` with random passwords, builds the `api` image, pushes it to ECR, starts both services and checks `/health`.
5. **Test** from your laptop (Git Bash):

   ```bash
   API_URL=http://<instance public IP> bash scripts/test_api.sh   # expects 9 passed, 0 failed
   ```

6. **Cost control:** stop the instance after each session (about $0.03 per hour while running). After grading, terminate it and delete the ECR repository.

## Status

- [x] Use case and data entity
- [x] API image, Docker Compose, tests (passing locally: 9/9 API checks)
- [x] Design brief and architecture diagram (Track B)
- [x] Deployment script and plan
- [ ] Deployed to EC2 with the image in ECR
- [ ] AWS evidence
