from jupyterhub.spawner import SimpleLocalProcessSpawner
from jupyterhub.auth import DummyAuthenticator

c.JupyterHub.allow_named_servers = True
c.JupyterHub.cleanup_servers = False
c.Spawner.hub_connect_url = "https://71dc-36-255-233-17.ngrok.io"
# c.Spawner.hub_connect_ip = "192.168.0.151"

c.JupyterHub.spawner_class = "multicluster_kubespawner.MultiClusterKubeSpawner"
c.JupyterHub.authenticator_class = DummyAuthenticator

c.MultiClusterKubeSpawner.profile_list = [
    {
        "display_name": "minikube",
        "description": "Launch on local minikube",
        "spawner_override": {
            "kubernetes_context": "minikube",
            "ingress_public_url": "http://192.168.64.3:31974",
        },
    },
    {
        "display_name": "GKE",
        "description": "Launch on GKE on us-central-1",
        "spawner_override": {
            "kubernetes_context": "gke_ucb-datahub-2018_us-central1_fall-2019",
            "ingress_public_url": "http://35.238.7.135",
        },
    },
    {
        "display_name": "DigitalOcean SFO",
        "description": "Launch on a DigitalOcean Cluster in California",
        "spawner_override": {
            "kubernetes_context": "do-nyc3-nbss-1",
            "ingress_public_url": "http://144.126.250.129",
        },
    },
]


c.MultiClusterKubeSpawner.patches = {
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
    "02-cpu": """
    kind: Pod
    metadata:
        name: {{key}}
    spec:
        containers:
        - name: notebook
          resources:
            requests:
                cpu: 10m
    """,
}


# dask-kubernetes setup
c.MultiClusterKubeSpawner.objects.update(
    {
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
    }
)
