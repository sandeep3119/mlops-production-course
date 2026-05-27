## MLO-006 — Horizontal Pod Autoscaler + Load Testing
Right now your deployment has replicas: 2 hardcoded. That's static — it doesn't matter if you have 1 request or 10,000, you always have 2 pods. HPA fixes this: Kubernetes watches a metric (CPU, memory, custom) and automatically scales replicas up when load increases and down when it drops.

Locust is a Python-based load testing tool. You write user behaviour as code, run it against your service, and it generates real HTTP traffic so you can observe how your service behaves under load.

What you will build:

k8s/hpa.yaml — HPA targeting your embedding deployment, scale on CPU utilisation
locust/locustfile.py — load test that hammers /embed with realistic text payloads
Confirm: under load, HPA triggers and new pods spin up. When load stops, pods scale back down.