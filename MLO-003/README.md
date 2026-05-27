# MLO-003: Kubernetes Deployment

## What This Is
Deploys the embedding service to Kubernetes with production-grade configuration: 2 replicas, resource requests and limits measured from real `docker stats` data, liveness and readiness probes, ConfigMap-driven environment variables, and a NodePort Service for external access.

---

## Prerequisites
- MLO-002 completed
- minikube installed and running (`minikube start`)
- kubectl configured
- Docker image pushed to a registry (Docker Hub)

---

## Project Structure
```
MLO-003/
├── k8s/
│   ├── deployment.yaml   # 2 replicas, resource limits, probes
│   ├── service.yaml      # NodePort — external access
│   └── configmap.yaml    # MODEL_NAME, MODEL_CACHE, APP_ENV
├── app/
└── Dockerfile
```

---

## What You Will Learn
- How to write a Kubernetes Deployment manifest from scratch
- The difference between resource `requests` and `limits` — and why both matter
- How to measure real memory and CPU usage with `docker stats` before setting limits
- Why `emptyDir` volumes wipe container data on pod restart
- How ConfigMaps decouple configuration from container images
- The difference between ClusterIP, NodePort, and LoadBalancer services
- Why `imagePullPolicy: Always` with mutable tags is dangerous
- How Kubernetes rolling updates work and how probes protect traffic during rollout

---

## Deploy

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Verify
kubectl get pods -l app=mlo-embed
kubectl rollout status deployment/mlo-embed

# Access service
minikube service mlo-embed --url
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `requests: memory 640Mi, cpu 300m` | Measured from `docker stats` during real inference — not guessed |
| `limits: memory 850Mi, cpu 1000m` | 30% headroom above observed peak — prevents OOMKill under burst |
| `initialDelaySeconds: 30` | Model loads in ~15-20s; probes need buffer or they fire too early |
| `envFrom: configMapRef` | Config changes don't require image rebuilds |
| Removed `emptyDir` volume | emptyDir wipes its contents when pod restarts — destroys baked model |
| Versioned image tag `:v5` not `:latest` | Latest is mutable — you can't reliably roll back to `:latest` |

---

## What You Learned
- **Never guess resource limits** — run `docker stats` under realistic load and add 20-30% headroom. Too low = OOMKill. Too high = wasted capacity.
- **`emptyDir`** is a temporary scratch space that is **always empty when the pod starts**. Never use it for data you expect to persist across restarts.
- **`requests`** = guaranteed minimum. Kubernetes uses this for scheduling decisions. **`limits`** = hard cap. Exceeding memory limit = OOMKill. Exceeding CPU limit = throttling (not kill).
- **ConfigMap** decouples config from code. Changing `MODEL_NAME` doesn't require a new Docker image build and push.
- Rolling update default: Kubernetes replaces pods one at a time. Readiness probes ensure the new pod is healthy before the old one is terminated — zero downtime if configured correctly.
- **ClusterIP**: only reachable inside the cluster. **NodePort**: exposes on a port on every node. **LoadBalancer**: provisions a cloud load balancer (AWS ELB, GCP LB).

---

## Interview Questions

**Kubernetes Fundamentals**
1. What is the difference between a Pod and a Deployment? Why would you never create a Pod directly in production?
2. Explain the difference between `requests` and `limits` for CPU and memory. What happens when a pod exceeds its memory limit? Its CPU limit?
3. How does Kubernetes decide which node to schedule a pod on? What role do resource `requests` play in this decision?
4. What is a ReplicaSet and what is its relationship to a Deployment?
5. You have 2 replicas and deploy a new image. Walk me through exactly what happens during a rolling update.

**Configuration & Storage**
6. What is a ConfigMap? What is the difference between mounting it as a volume vs using `envFrom`?
7. What is the difference between a ConfigMap and a Secret? How are Secrets stored in etcd by default, and why is that a problem?
8. What is an `emptyDir` volume? What data does it contain when a pod starts? Give a use case where it is appropriate.
9. What is a PersistentVolume vs a PersistentVolumeClaim? What is the provisioner's role?
10. Why is `imagePullPolicy: Always` potentially dangerous with versioned tags? When is it necessary?

**Networking & Services**
11. What is the difference between ClusterIP, NodePort, and LoadBalancer service types? When would you use each?
12. How does Kubernetes DNS work for Service discovery? What is the full DNS name for a service named `mlflow` in the `default` namespace?
13. A pod needs to talk to another service in a different namespace. What hostname does it use?
14. What is an Ingress? How does it differ from a LoadBalancer Service?
15. Your service has 3 pods. A request comes in — how does Kubernetes decide which pod receives it?
