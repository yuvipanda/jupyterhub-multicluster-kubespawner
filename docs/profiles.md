# Setup `profile_list`

After login, each user will be provided with a list of `profile`s to choose from.
Each profile can point to a different kubernetes cluster, as well as other
customizations such as image to use, amount of RAM / CPU, GPU use, etc.

Each item in the list is a python dictionary, with the following keys recognized:

1. **`display_name`**: Name to display to the user in the profile selection screen
2. **`description`**: Description to display to the user in the profile selection screen
3. **`spawner_override`**: Dictionary of spawner options for this profile, determining
   where the user pod is spawned and other properties of it.

The following properties are supported under `spawner_override`.

1. **`kubernetes_context`**: Name of the kubernetes context to use when connecting to
   this cluster. You can use `kubectl config get-contexts` to get a list of contexts
   available in your `KUBECONFIG` file.
2. **`ingress_public_url`**: URL to the public endpoint of the Ingress controller you
   setup earlier. This should be formatted as a URL, so don't forget the `http://`.
   For production systems, you should also setup HTTPS for your ingress controller,
   and provide the `https://<domain-name>` here.
3. **`patches`**: A list of patches (as passed to
   [`kubectl patch`](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/update-api-object-kubectl-patch/)).
   Described in more detail below. This is the primary method of customizing the
   user pod, although some convenience methods are also offered (detailed below).
4. **`environment`**: A dictionary of extra environment variables to set for the
   user pod.
5. **`image`**: The image to use for the user pod. Defaults to `pangeo/pangeo-notebook:latest`.
6. **`mem_limit`** and **`mem_guarantee`**, as [understood by JupyterHub](https://jupyterhub.readthedocs.io/en/stable/reference/spawners.html#memory-limits-guarantees)
7. **`cpu_limit`** and **`cpu_guarantee`**, as [understood by JupyterHub](https://jupyterhub.readthedocs.io/en/stable/reference/spawners.html#cpu-limits-guarantees)

Here is a simple example:

```python
c.MultiClusterKubeSpawner.profile_list = [
    {
        "display_name": "Google Cloud in us-central1",
        "description": "Compute paid for by funder A, closest to dataset X",
        "spawner_override": {
            "kubernetes_context": "<kubernetes-context-name-for-this-cluster">,
            "ingress_public_url": "http://<ingress-public-ip-for-this-cluster>"
        }
    },
    {
        "display_name": "AWS on us-east-1",
        "description": "Compute paid for by funder B, closest to dataset Y",
        "spawner_override": {
            "kubernetes_context": "<kubernetes-context-name-for-this-cluster">,
            "ingress_public_url": "http://<ingress-public-ip-for-this-cluster>",
            "patches": {
                "01-memory": """
                    kind: Pod
                    metadata:
                        name: {{key}}
                    spec:
                        containers:
                        - name: notebook
                        resources:
                            requests:
                                memory: 16Mi
                    """,
            }
        }
    },
]
```