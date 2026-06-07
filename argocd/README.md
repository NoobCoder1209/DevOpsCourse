# Applying the Argo CD manifests

These manifests assume Argo CD is already installed in the `argocd` namespace.
For a quick spin-up against any cluster (kind, k3d, your dev cluster):

```bash
kubectl create namespace argocd
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --version 7.6.12 --wait

# UI
kubectl port-forward -n argocd svc/argocd-server 8080:443

# Get the bootstrap admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d ; echo
```

Then apply either an individual `Application` or the `ApplicationSet`:

```bash
# Single env (dev only):
kubectl apply -n argocd -f argocd/application-dev.yaml

# Both envs via the ApplicationSet:
kubectl apply -n argocd -f argocd/applicationset.yaml
```

`gitops-e2e.yml` does the full kind + Argo CD + sync round-trip on every PR
that touches `chart/`, `environments/`, or `argocd/`.
