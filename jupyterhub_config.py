from jupyterhub.spawner import SimpleLocalProcessSpawner
from jupyterhub.auth import DummyAuthenticator
from multicluster_kubespawner.spawner import MultiClusterKubernetesSpawner

c.JupyterHub.allow_named_servers = True
c.JupyterHub.cleanup_servers = False
c.Spawner.hub_connect_url = "https://71dc-36-255-233-17.ngrok.io"
# c.Spawner.hub_connect_ip = "192.168.0.151"

c.JupyterHub.spawner_class = MultiClusterKubernetesSpawner
c.JupyterHub.authenticator_class = DummyAuthenticator

c.MultiClusterKubernetesSpawner.profile_list = [
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


c.MultiClusterKubernetesSpawner.ingress_public_url = "http://34.69.164.86"
c.MultiClusterKubernetesSpawner.patches = {
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
                cpu: 0.01
    """,
}

c.MultiClusterKubernetesSpawner.objects = {
    # sa must come before pod, as pod references sa
    "01-sa": """
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: {{key}}
    """,
    "02-pod": """
    apiVersion: v1
    kind: Pod
    metadata:
        name: {{key}}
    spec:
        serviceAccountName: {{key}}
        containers:
        - name: notebook
          image: jupyter/scipy-notebook:latest
          command: {{spawner.cmd|tojson}}
          args: {{spawner.get_args()|tojson}}
          ports:
          - containerPort: {{spawner.port}}
          env:
          {% for k, v in spawner.get_env().items() -%}
          - name: {{k}}
            value: {{v|tojson}}
          {% endfor %}
    """,
    "03-service": """
    apiVersion: v1
    kind: Service
    metadata:
        name: {{key}}
    spec:
        selector:
            mcks.hub.jupyter.org/key: {{key}}
        ports:
            - protocol: TCP
              port: 8888
              targetPort: 8888
    """,
    "04-ingress": """
    apiVersion: networking.k8s.io/v1
    kind: Ingress
    metadata:
        name: {{key}}
    spec:
        ingressClassName: contour
        rules:
        - http:
            paths:
            - path: {{proxy_spec}}
              pathType: Prefix
              backend:
                service:
                   name: {{key}}
                   port:
                       number: 8888
    """,
}
