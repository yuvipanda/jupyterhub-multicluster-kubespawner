# Setting up target clusters

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