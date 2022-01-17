# JupyterHub MultiCluster KubeSpawner

Launch user pods into many different kubernetes clusters from the same JupyterHub!

## Why?

A single JupyterHub as an 'entrypoint' to compute in a variety of clusters
can be extremely useful. Users can dynamically decide to launch their notebooks
(and dask clusters) dynamically based on a variety of factors - closer to their
data, on different cloud providers, paid for by different billing accounts, etc.
It also makes life much easier for JupyterHub operators.

```{toctree}
:caption: Table of Contents
:maxdepth: 2

install
config
reference
```