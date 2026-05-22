## Ticket MLO-003
Title: Push this service to a container registry and write a Kubernetes deployment
Context: The service works locally. Now the platform team needs to deploy it to a Kubernetes cluster. Your job is to write the Kubernetes manifests.

### Task 1 — Tag and push to Docker Hub
bashdocker build -t <your-dockerhub-username>/mlo-embed:v1 .
docker push <your-dockerhub-username>/mlo-embed:v1
Create a free Docker Hub account if you don't have one.
### Task 2 — Write Kubernetes manifests
Create a k8s/ folder with three files:
k8s/
├── deployment.yaml
├── service.yaml
└── configmap.yaml
deployment.yaml must have:

2 replicas
Your Docker Hub image
Liveness probe hitting /health/live
Readiness probe hitting /health/ready
CPU and memory resource requests and limits
MODEL_NAME and MODEL_CACHE pulled from the configmap

service.yaml must expose the deployment inside the cluster.
configmap.yaml must hold MODEL_NAME and MODEL_CACHE as config values.
### Task 3 — Apply it locally with minikube
Install minikube if you don't have it, then:
bashminikube start
kubectl apply -f k8s/
kubectl get pods
kubectl get svc
Paste the output of kubectl get pods and kubectl describe pod <pod-name>.