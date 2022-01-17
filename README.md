# jupyterhub-multicluster-kubespawner

Launch user pods into many different kubernetes clusters from the same JupyterHub!

## Why?

A single JupyterHub as an 'entrypoint' to compute in a variety of clusters
can be extremely useful. Users can dynamically decide to launch their notebooks
(and dask clusters) dynamically based on a variety of factors - closer to their
data, on different cloud providers, paid for by different billing accounts, etc.
It also makes life much easier for JupyterHub operators.

You can check out an early demo of the spawner in action
[here](https://twitter.com/yuvipanda/status/1480938588523008001).

## Installation

`jupyterhub-multicluster-kubespawner` is available from PyPI:

```bash
pip install jupyterhub-multicluster-kubespawner
```

You'll also need to install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)
as well as any tools needed to *authenticate* to your target clusters.

| Cloud Provider | Tool |
| - | - |
| Google Cloud | [gcloud](https://cloud.google.com/sdk/docs/install) |
| AWS | [aws](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| Azure | [az](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) |
| DigitalOcean | [doctl](https://github.com/digitalocean/doctl) |

## Configuration

You can ask JupyterHub to use `MultiClusterKubeSpawner` with the following config
snippet in your `jupyterhub_config.py` file, although more configuration is
needed to connect the hub to different clusters.

### Configuration philosophy

`MultiClusterKubeSpawner` tries to be as kubernetes-native as possible, unlike
the venerable [kubespawner](https://github.com/jupyterhub/kubespawner). It doesn't
try to provide a layer of abstraction over what kubernetes offers, as we have
found that is often a very leaky abstraction. This makes it difficult for JupyterHub
operators to take advantage of all the powerful features Kubernetes offers, and
increases maintenance burden for the maintainers.

`MultiClusterKubeSpawner` uses the popular [kubectl](https://kubernetes.io/docs/reference/kubectl/kubectl/)
under the hood, making the configuration familiar for anyone who has a basic
understanding of working with Kubernetes clusters. The flip side is that *some*
familiarity with Kubernetes is required to successfully configure this spawner,
but the tradeoff seems beneficial for everyone.

### Setting up `KUBECONFIG`

Since multicluster-kubespawner talks to multiple Kubernetes clusters, it uses a
[kubeconfig](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/)
file connect to the kubernetes clusters. It looks for the file in `~/.kube/config` -
in production environments, your file probably exists elsewhere - you can set the
`KUBECONFIG` environment variable to point to the location of the file.

Each cluster is represented by a [context](https://kubernetes.io/docs/tasks/access-application-cluster/configure-access-multiple-clusters/),
which is a combination of a pointer to where the cluster's kubernetes API endpoint
is as well as what credentials to use to authenticate to it. More details
[here](https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/).

The easiest way to construct a `kubeconfig` that will work with all the clusters
you want to use is to **carefully** construct it locally on your laptop and then
copy that file to your deployment.

Start by setting your `KUBECONFIG` env var locally to a file that you can then copy
over.

```bash
export KUBECONFIG=jupyterhub-mcks-kubeconfig
```

#### On Google Cloud

1. Create a [Google Cloud Service Account](https://cloud.google.com/iam/docs/service-accounts),
   and give it enough permissions to access your Kubernetes cluster. `roles/container.developer`
   *should* be enough permission.

2. Create a JSON [Service Account Key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)
   for your service account. This is what `kubectl` will eventually use to authenticate to
   the kubernetes cluster. You'll need to put this service account key in your production
   JupyterHub environment as well.

3. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to the location of
   this JSON Service Account key.

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=<path-to-json-service-account-key>
   ```

4. Generate an appropriate entry in your custom `kubeconfig` file.

   ```bash
   gcloud container clusters get-credentials <cluster-name> --zone=<zone>
   ```

When you deploy your JupyterHub, make sure that you set the environment variable
`GOOGLE_APPLICATION_CREDENTIALS` to point to the service account key in a place where
JupyterHub can find it.

#### On AWS with EKS

AWS has a plethora of interesting options to authenticate with it, here we will
specify the simplest (albeit maybe not the most secure or 'best practice').

1. Create an AWS [IAM User](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users.html)
   for use by `kubectl` to authenticate to AWS. This user will need a access key
   and access secret, but no console access.

2. Create an [access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
   for this user. JupyterHub will need these while running to make requests to the kubernetes
   API, set as [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

3. Grant the user access to the `eks:DescribeCluster` permission, either directly or
   via a group you create specifically for this purpose.

4. Grant the user access to the Kubernetes API by editing the `aws-auth` configmap
   as [described in this document](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html#aws-auth-users).

5. Generate an appropriate entry in your `KUBECONFIG` file:

   ```bash
   export AWS_ACCESS_KEY_ID=<access-key-id>
   export AWS_SECRET_ACCESS_KEY=<access-key-secret>
   aws eks update-kubeconfig --name=<cluster-name> --region=<aws-region>
   ```

When you deploy your JupyterHub, you need to set the environment variables
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` on the JupyterHub process itself
so it can talk to the Kubernetes API properly.


#### On DigitalOcean

1. Install [doctl](https://github.com/digitalocean/doctl)

2. Create a [personal access token](https://docs.digitalocean.com/reference/api/create-personal-access-token/)
   to access your kubernetes cluster. Unlike the other cloud providers, this
   can not be scoped - it grants full access to your entire DO account! So
   use with care.

3. Generate an appropriate entry in your `KUBECONFIG` file:

   ```bash
   export DIGITALOCEAN_ACCESS_TOKEN=<your-digitalocean-access-token>
   doctl kubernetes cluster kubeconfig save <cluster-name>
   ```

When you deploy your JupyterHub, you need to set the environment variable
`DIGITALOCEAN_ACCESS_TOKEN` on the JupyterHub process itself so it can talk
to the Kubernetes API properly.

### Setting up target clusters

Each target cluster needs to have an [Ingress Controller](https://kubernetes.io/docs/concepts/services-networking/ingress-controllers/)
installed that the spawner can talk to. This provides a *public IP* that
JupyterHub can use to proxy traffic to the user pods on that cluster.

Any ingress provider will do, although the current suggested one is
to use [Project Contour](https://projectcontour.io/getting-started/),
as it's faster than the more popular [nginx-ingress](https://kubernetes.github.io/ingress-nginx/)
at picking up routing changes.

A 'production' install might use [helm](https://helm.sh) and the
[contour helm chart](https://github.com/bitnami/charts/tree/master/bitnami/contour/#installing-the-chart).
But to quickly get started, you can also just configure your `kubectl`
to point to the correct kubernes cluster and run
`kubectl apply --wait -f https://projectcontour.io/quickstart/contour.yaml`. After
it succeeds, you can get the public IP of the ingress controller with
`kubectl -n projectcontour get svc envoy`. The `EXTERNAL-IP` value here
can be passed to the `ingress_public_url` configuration option for your
cluster.

### Setup `profile_list`

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

### Customizations with `patches`

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

### Additional per-user kubernetes resources with `resources`

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
