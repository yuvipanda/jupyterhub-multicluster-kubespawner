# Installation

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