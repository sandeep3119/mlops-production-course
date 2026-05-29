# MLO-004: CI/CD Pipeline with GitHub Actions

## What This Is
Automated CI/CD pipeline using GitHub Actions. Every push to `main` that touches `MLO-004/**` triggers: dependency install → linting → unit tests (with mocked model) → Docker build (model baked in) → push to Docker Hub. Separates test builds (`DOWNLOAD_MODEL=false`) from production builds (`DOWNLOAD_MODEL=true`).

---

## Prerequisites
- MLO-003 completed and deployed
- GitHub repository with the project
- Docker Hub account with credentials stored as GitHub Secrets:
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

---

## Project Structure
```
MLO-004/
├── .github/
│   └── workflows/
│       └── deploy.yml    # CI/CD pipeline definition
├── app/
│   ├── main.py
│   └── model.py
├── tests/
│   └── test_api.py       # Tests with mocked model — no download in CI
└── Dockerfile
```

---

## What You Will Learn
- How to structure a GitHub Actions workflow with sequential jobs (`needs:`)
- Why CI tests use a mocked model (`unittest.mock`) while production builds bake the real model in
- The difference between `ARG` (build-time) and `ENV` (runtime) in Dockerfiles
- How relative Python imports break when a Dockerfile flattens the package structure
- Why `imagePullPolicy: Always` matters when tags are mutable
- How to use GitHub secrets securely in workflows
- Path filtering — only triggering CI when relevant files change
- Node.js deprecation warnings in older GitHub Actions versions

---

## Pipeline Flow

```
push to main (MLO-004/** changed)
        │
        ▼
  build-and-test
  ├── checkout
  ├── setup Python 3.10
  ├── login to Docker Hub
  ├── pip install requirements
  ├── flake8 lint
  ├── pytest (model mocked — no download)
  ├── docker build --build-arg DOWNLOAD_MODEL=true
  └── docker push :v{run_number} + :latest
        │
        ▼ (needs: build-and-test)
      deploy
      └── echo kubectl set image command
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `DOWNLOAD_MODEL=false` in test job | Tests mock `embed_text` — downloading 90MB for mocked tests wastes 2+ minutes per CI run |
| `DOWNLOAD_MODEL=true` in docker build | Bakes model into production image — pods start without internet dependency |
| `needs: build-and-test` on deploy job | Deploy only runs if tests pass — gates broken code from reaching production |
| Path filtering `paths: MLO-004/**` | Prevents CI from running on unrelated file changes |
| `:v${{ github.run_number }}` tag | Immutable versioned tags — enable reliable rollbacks |
| `actions/checkout@v4`, `setup-python@v5` | Upgraded from v3 to fix Node.js 20 deprecation warning |

---

## What You Learned
- `DOWNLOAD_MODEL=true/false` separates CI (fast, mocked) from production (real model baked in). A CI build that downloads the model on every PR is slow and unreliable.
- `unittest.mock.patch("app.model.embed_text")` patches the function at test time — the model is never loaded, CI runs in seconds.
- Client-server version alignment matters: if your local MLflow SDK is 3.x but your server is 2.x, API calls will fail with 404.
- `from app import model` fails in a container where `COPY app/ ./` was used — there's no `app` package, only its contents. Fix: `import model` or change to `COPY app/ ./app/` and use `uvicorn app.main:app`.
- Relative imports (`from .utility.logger import X`) require the file to be part of a package. They fail when the module is loaded as a top-level script.
- GitHub Actions `run_number` increments on every workflow run — gives you a simple immutable version tag without extra tooling.

---

## Interview Questions

**CI/CD Fundamentals**
1. What is the difference between Continuous Integration and Continuous Deployment? Where does your pipeline stop and why?
2. Your CI pipeline takes 12 minutes. A developer complains it's too slow. What are the first three things you would do to speed it up?
3. What is a pipeline gate? Give an example of where you would add one and what it checks.
4. How do you handle secrets in GitHub Actions? What are the risks of printing them in logs?
5. What is path filtering in a CI trigger? Why would you use it in a monorepo?

**Docker in CI/CD**
6. Why do you use `DOWNLOAD_MODEL=false` when running tests in CI but `DOWNLOAD_MODEL=true` when building the production image?
7. What is the difference between `ARG` and `ENV` in a Dockerfile? Which one is available at runtime?
8. Your Docker build is slow in CI because it re-downloads pip packages every run. How do you fix this using Docker layer caching?
9. What is the risk of tagging your production image as `:latest` and deploying it to Kubernetes?
10. How would you implement a rollback in Kubernetes if a new image causes failures? What command would you run?

**Python & Testing**
11. What is `unittest.mock.patch` and how does it work? What does it mean to patch `"app.model.embed_text"` vs `"model.embed_text"`?
12. What is flake8 and what category of issues does it catch? Name one thing it will NOT catch.
13. Why does a relative Python import (`from .module import X`) fail when a file is run as a top-level script?
14. What is the difference between `from app import model` and `import model`? When does each work and fail?
15. Your tests pass in CI but fail in production. Name three causes of this environment mismatch and how you would diagnose each.
