# Create additional per-user kubernetes resources with `resources`

You can also create arbitrary additional kubernetes resources for each user
by setting the `resources` configuration. It's a dictionary where the key is used
for sorting, and the value should be valid YAML after expansion via jinja2 template.

For example, the following config creates a Kubernetes [Role and RoleBinding](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
for each user to allow them to (insecurely!) run a [dask-kubernetes](https://kubernetes.dask.org/en/latest/)
cluster.

```python
c.MultiClusterKubernetesSpawner.resources = {
    "10-dask-role": """
    apiVersion: rbac.authorization.k8s.io/v1
    kind: Role
    metadata:
      name: {{key}}-dask
    rules:
    - apiGroups:
      - ""
      resources:
      - pods
      verbs:
      - list
      - create
      - delete
    """,
    "11-dask-rolebinding": """
    apiVersion: rbac.authorization.k8s.io/v1
    kind: RoleBinding
    metadata:
      name: {{key}}-dask
    roleRef:
      apiGroup: rbac.authorization.k8s.io
      kind: Role
      name: {{key}}-dask
    subjects:
    - apiGroup: ""
      kind: ServiceAccount
      name: {{key}}
    """,
)
```

This takes advantage of the fact that by default a Kubernetes
[Service Account](https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/)
is already created for each pod by `MultiClusterUserSpawner`, and gives it just
enough rights to create, list and delete pods.