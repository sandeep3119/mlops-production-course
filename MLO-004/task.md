
## Ticket MLO-004 — CI/CD with GitHub Actions
Context: Right now your deploy process is:

docker build
docker push
kubectl apply

All manual. In a real team, engineers don't run these commands — a pipeline does. Your job is to automate this.
What the pipeline must do on every push to main:

Run your tests (pytest)
Build the Docker image
Push to Docker Hub with two tags — v<build-number> and latest
Update the Kubernetes deployment to the new image

What to create:
.github/
└── workflows/
    └── deploy.yml
Secrets you'll need in GitHub:

DOCKERHUB_USERNAME
DOCKERHUB_TOKEN — generate from Docker Hub → Account Settings → Security


Before you write a single line of YAML, answer this:
What is the difference between a GitHub Actions job and a step? And why would you split build and deploy into two separate jobs instead of one?
Answer first, then build.