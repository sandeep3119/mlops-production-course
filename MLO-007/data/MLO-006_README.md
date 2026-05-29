# MLO-006: Horizontal Pod Autoscaler + Load Testing with Locust

## What This Is
Adds automatic scaling to the embedding service using Kubernetes HPA (Horizontal Pod Autoscaler) configured at 70% CPU utilisation. Validates the scaling behaviour under real load using Locust, a Python-based load testing framework. Demonstrated: 2 → 6 pods in under 2 minutes under 100 concurrent users, 0% failure rate throughout, scale-down after 5-minute stabilisation window.

---

## Prerequisites
- MLO-005 completed and deployed
- metrics-server enabled in minikube
- `pip install locust`

---

## Project Structure
```
MLO-006/
├── k8s/
│   └── hpa.yaml           # HPA — 70% CPU, min 2, max 6, 300s scale-down window
└── locust/
    └── locustfile.py      # Load test — 25 varied sentences, task weighting
```

---

## What You Will Learn
- What HPA is, how it calculates desired replicas, and what metrics it uses
- Why CPU `requests` must be set for HPA to function — how utilisation % is calculated
- The difference between horizontal scaling (more pods) and vertical scaling (bigger pods)
- Why a scale-down stabilisation window prevents flapping
- How metrics-server works and how to fix the `cpu: <unknown>` issue in minikube
- How to write a Locust load test with task weighting and randomised payloads
- How to interpret Locust output: RPS, failure rate, response time distribution
- The difference between `maxReplicas` as a cost cap vs as a capacity ceiling

---

## Deploy & Run

```bash
# Apply HPA
kubectl apply -f k8s/hpa.yaml
kubectl get hpa mlo-embed-hpa

# Fix metrics-server if cpu shows <unknown>
kubectl patch deployment metrics-server -n kube-system \
  --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'

# Run load test
locust -f locust/locustfile.py --host=http://$(minikube service mlo-embed --url --silent)
# Open http://localhost:8089 → 100 users, 10/sec spawn rate

# Watch HPA in real time
kubectl get hpa mlo-embed-hpa --watch
```

---

## Key Design Decisions

| Decision | Why |
|---|---|
| `averageUtilization: 70` | Balance between cost (not scaling too early) and headroom (not at 100% before scaling) |
| `minReplicas: 2` | Never run on a single pod — one pod failure = 100% outage |
| `maxReplicas: 6` | Hard cost cap — prevents runaway scaling under a traffic spike or load test |
| `stabilizationWindowSeconds: 300` | Prevents flapping — waits 5 minutes of consistent low load before removing pods |
| Task weight 3:1 (embed vs health) | Realistic traffic ratio — health checks are less frequent than actual requests |
| 25 varied sentence lengths | Tests latency variance across input sizes — identical sentences can cache |

---

## Observed Results

| Metric | Value |
|---|---|
| Scale-up trigger | CPU: 267% of request (267% of 300m = ~800m) |
| Time to scale 2 → 6 pods | Under 2 minutes |
| Failure rate during scale-up | 0% |
| RPS under 100 users | 12.64 |
| Scale-down wait | Exactly 5 minutes (stabilisation window) |
| Scale-down step | 6 → 3 (conservative, then continues to 2) |

---

## What You Learned
- **HPA formula**: `desiredReplicas = ceil(currentReplicas × (currentMetric / targetMetric))`. At 267%/70% with 2 pods: `ceil(2 × 267/70) = ceil(7.6) = 8`, capped at `maxReplicas: 6`.
- **HPA uses `requests`, not `limits`** for utilisation calculation. If CPU request is 300m and target is 70%, HPA fires at 210m actual usage.
- **`cpu: <unknown>`** = metrics-server cannot scrape kubelets. In minikube: always a TLS issue. Fix with `--kubelet-insecure-tls`. On EKS/GKE, pre-configured correctly.
- **Horizontal vs vertical**: horizontal = more pods (stateless services). Vertical = bigger pod (stateful, large LLMs that can't be replicated easily).
- **Flapping**: without a stabilisation window, HPA scales down as soon as load drops, then immediately scales up again when load returns. Constant pod churn creates its own load.
- **Cluster Autoscaler vs HPA**: HPA scales pods within a node. Cluster Autoscaler adds nodes when pods can't be scheduled due to insufficient node capacity. They work together.
- **12.64 RPS at 100 users** is your measured capacity ceiling. Serving 500 RPS would require ~40x more capacity — GPU inference or a much larger cluster.

---

## Interview Questions

**HPA & Autoscaling**
1. What does HPA stand for? Explain in one sentence what it does.
2. Walk me through the HPA scaling formula. If you have 3 pods, target CPU is 50%, and current CPU is 120%, how many pods does HPA want?
3. Why does HPA require CPU `requests` to be set? What does it use them for in its calculation?
4. What is the difference between HPA and VPA (Vertical Pod Autoscaler)? When would you choose vertical scaling for an ML workload?
5. What is the difference between HPA and Cluster Autoscaler? Can they work together?

**Scaling Strategy**
6. Your HPA is set to maxReplicas: 10 but CPU is still at 200% with 10 pods. What are your options?
7. What is pod flapping? How does the `stabilizationWindowSeconds` setting prevent it?
8. Why would you set `minReplicas: 2` instead of 1 even when traffic is near zero?
9. Your service scales up fast but is slow to scale down. What setting controls scale-down rate and why might you intentionally keep it slow?
10. CPU-based HPA isn't ideal for all ML workloads. What other metrics could you scale on, and when would each be more appropriate? (hint: custom metrics, queue depth, GPU utilisation)

**Load Testing**
11. What is the difference between load testing and stress testing? What does each tell you?
12. In Locust, what does `wait_time = between(0.5, 2)` simulate? Why is it more realistic than 0?
13. Your Locust test shows 0% failure rate at 50 RPS but 15% failures at 100 RPS. What does this tell you about your service?
14. Why should you use varied payloads in a load test instead of the same sentence repeated?
15. You measured 12.64 RPS capacity in your load test. Your production SLA requires 500 RPS. Name three architectural changes to reach that target.
