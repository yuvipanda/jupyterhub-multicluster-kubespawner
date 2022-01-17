# Setting up `KUBECONFIG`

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

Once set, you can follow instructions specific to your cloud provider to generate
appropriate context entries in your `KUBECONFIG` file and collect appropriate
credentials to  authenticate to your

```{toctree}
:caption: Kubeconfig setup for different cloud providers
gcp
digitalocean
aws
```