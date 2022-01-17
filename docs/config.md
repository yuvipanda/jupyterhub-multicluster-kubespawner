# Configuration

## Philosophy

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

## Setting up your installation

You can ask JupyterHub to use `MultiClusterKubeSpawner` with the following config
snippet in your `jupyterhub_config.py` file, although more configuration is
needed to connect the hub to different clusters.

```bash
c.JupyterHub.spawner_class = "multicluster_kubespawner.MultiClusterKubeSpawner"
```

```{toctree}
kubeconfig/index
target-clusters
profiles
patches
resources
```
