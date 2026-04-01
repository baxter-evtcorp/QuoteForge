#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Building Docker image..."
docker build -t quoteforge:latest "$PROJECT_DIR"

echo "Applying Kubernetes manifests..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
kubectl apply -f "$SCRIPT_DIR/pvc.yaml"
kubectl apply -f "$SCRIPT_DIR/deployment.yaml"
kubectl apply -f "$SCRIPT_DIR/service.yaml"

echo "Waiting for pod to be ready..."
kubectl -n quoteforge rollout status deployment/quoteforge --timeout=120s

echo ""
echo "QuoteForge is running at http://localhost:30500"
