# Troubleshooting exercises

I broke two things on purpose in the `bugtrack` namespace of a local Kubernetes cluster (kind) and fixed them with the same five steps each time: identify, investigate, root cause, fix, verify. The manifests are `broken-image.yaml` and `broken-service.yaml` in this folder, and the output below is from the real runs. Screenshots: [bad image tag](../images/18-ts-image-error.png) and [selector mismatch and fix](../images/19-ts-selector.png).

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f troubleshooting/broken-image.yaml
kubectl apply -f troubleshooting/broken-service.yaml
```

## 1. Bad image tag (`broken-image.yaml`)

**Identify.** The Deployment exists but its Pod never becomes ready.

```
$ kubectl -n bugtrack get pods -l app=tb-image
NAME                       READY   STATUS         RESTARTS   AGE
tb-image-59f68c9d9-r8ddg   0/1     ErrImagePull   0          25s
```

**Investigate.** `kubectl describe pod` shows the pull failing and then backing off:

```
Normal   Pulling  kubelet  Pulling image "ghcr.io/pratham-onkar-singh/bugtrack-backend:does-not-exist"
Warning  Failed   kubelet  Failed to pull image "ghcr.io/pratham-onkar-singh/bugtrack-backend:does-not-exist": ... failed to authorize: failed to fetch anonymous token: ... 403 Forbidden
Warning  Failed   kubelet  Error: ErrImagePull
Normal   BackOff  kubelet  Back-off pulling image "ghcr.io/pratham-onkar-singh/bugtrack-backend:does-not-exist"
Warning  Failed   kubelet  Error: ImagePullBackOff
```

**Root cause.** The manifest points at a tag that does not exist (`does-not-exist`). GHCR answers an anonymous pull of a missing image with `403` and not a plain "not found", so the message looks like a login problem, but the real cause is the tag. The container never starts, so it is a manifest problem, not an application bug.

**Fix.** Point the Deployment at a tag that exists. In the real pipeline that is the commit SHA it pushed to GHCR. For this run I loaded a local build of the backend into the cluster and used that tag:

```
$ kubectl -n bugtrack set image deploy/tb-image app=ghcr.io/pratham-onkar-singh/bugtrack-backend:local-fix
deployment.apps/tb-image image updated
deployment "tb-image" successfully rolled out
```

**Verify.** The new Pod is `1/1 Running` and the old one terminates:

```
$ kubectl -n bugtrack get pods -l app=tb-image
NAME                        READY   STATUS        RESTARTS   AGE
tb-image-59f68c9d9-r8ddg    0/1     Terminating   0          27s
tb-image-6854b99447-jmvql   1/1     Running       0          2s
```

## 2. Service selector mismatch (`broken-service.yaml`)

**Identify.** The Pod is `Running` and the Service exists, yet the Service has no endpoints.

```
$ kubectl -n bugtrack get endpoints tb-svc
NAME     ENDPOINTS   AGE
tb-svc   <none>      19s
```

**Investigate.** Compare what the Service selects with what the Pod is labelled:

```
$ kubectl -n bugtrack get svc tb-svc -o jsonpath='{.spec.selector}'
{"app":"tb-service"}
$ kubectl -n bugtrack get pods -l app=tb-svc --show-labels
NAME                  READY   STATUS    RESTARTS   AGE   LABELS
tb-svc-f8975d-fnr46   1/1     Running   0          19s   app=tb-svc,pod-template-hash=f8975d
```

**Root cause.** The Service selects `app=tb-service`, the Pod carries `app=tb-svc`. A Service only routes to Pods whose labels match its selector exactly, so it had no endpoints even though the Pod was healthy.

**Fix.**

```
$ kubectl -n bugtrack patch svc tb-svc -p '{"spec":{"selector":{"app":"tb-svc"}}}'
service/tb-svc patched
```

**Verify.** The endpoint list now has the Pod IP:

```
$ kubectl -n bugtrack get endpoints tb-svc
NAME     ENDPOINTS       AGE
tb-svc   10.244.0.7:80   22s
```

## Clean up

```bash
kubectl delete -f troubleshooting/broken-image.yaml -f troubleshooting/broken-service.yaml
```
