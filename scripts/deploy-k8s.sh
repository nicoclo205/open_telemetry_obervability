#!/bin/bash
# Despliega todo el stack en Kubernetes
# Usage: ./scripts/deploy-k8s.sh

set -e

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/pvc/
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/ingress/

echo "Waiting for deployments..."
kubectl rollout status deployment/sticker-api -n observabilidad
kubectl rollout status deployment/otel-collector -n observabilidad

echo "Deploy complete. Getting ingress IP..."
kubectl get ingress -n observabilidad
