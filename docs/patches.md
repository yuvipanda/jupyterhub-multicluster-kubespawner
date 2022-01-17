# Customize spawned resources with `patches`

To try and be as kubernetes-native as possible, we use [strategic merge patch](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/update-api-object-kubectl-patch/#notes-on-the-strategic-merge-patch)
as implemented by kubectl to allow JupyterHub operators to customize per-user resources.
This lets operators have fine grained control over what gets spawned per-user, without
requiring a lot of effort by the maintainers of this spawner to support each possible
customization.

Behind the scenes, `kubectl patch` is used to merge the initial list of generated
kubernetes resources for each user with some customizations before they are passed to
`kubectl apply`. Operators set these by customizing the `patches` traitlet. It can
be either set for all profiles by setting `c.MultiClusterKubeSpawner.patches` or just
for a particular set of profiles by setting `patches` under `spawner_override` for that
particular profile.

`patches` is a dictionary, where the key is used just for sorting and the value is
a string that should be a valid YAML object when parsed after template substitution.
Resources are merged based on the value for `kind` and `metadata.name` keys in the YAML.
`kubectl` knows when to add items to a list or merge their properties on appropriate
attributes.

To patch the user pod to add some extra annotations to the pod and request a GPU,
you could set the following:

```python

c.MultiClusterKubernetesSpawner.patches = {
    "01-annotations": """
    kind: Pod
    metadata:
        name: {{key}}
        annotations:
            something-else: hey
    """,
    "02-gpu": """
    kind: Pod
    metadata:
        name: {{key}}
    spec:
        containers:
        - name: notebook
          resources:
            limits:
                nvidia.com/gpu: 1
    """,
}
```

The values are first expanded via [jinja2 templates](https://jinja.palletsprojects.com/)
before being passed to `kubectl patch`. `{{key}}` expands to the name of the resource
created, and you should use it for all your modifications. In the `02-gpu` patch, `kubectl`
knows to merge this with the existing notebook container instead of create a new container
or replace all the existing values, because it knows there already exists a container with
the `name` property set to `notebook`. Hence it merges values provides in this patch with
the existing configuration for the container.

Please read the [`kubectl` documentation](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/update-api-object-kubectl-patch)
to understand how strategic merge patch works.