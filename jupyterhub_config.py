from jupyterhub.spawner import SimpleLocalProcessSpawner
from jupyterhub.auth import DummyAuthenticator
from multicluster_kubespawner.spawner import MultiClusterKubernetesSpawner

c.JupyterHub.allow_named_servers = True
c.JupyterHub.hub_ip = "192.168.0.151"
c.Spawner.hub_connect_url = "https://34ed-36-255-233-17.ngrok.io"
# c.Spawner.hub_connect_ip = "192.168.0.151"

c.JupyterHub.spawner_class = MultiClusterKubernetesSpawner
c.JupyterHub.authenticator_class = DummyAuthenticator

c.MultiClusterKubernetesSpawner.profile_list = [
    {
        "display_name": "minikube",
        "spawner_override": {
            "kubernetes_context": "minikube",
            "ingress_public_url": "http://192.168.64.3:32258",
        },
    },
    {
        "display_name": "GKE",
        "spawner_override": {
            "kubernetes_context": "gke_ucb-datahub-2018_us-central1_fall-2019",
            "ingress_public_url": "http://34.69.164.86",
        },
    },
]


c.MultiClusterKubernetesSpawner.ingress_public_url = "http://34.69.164.86"
c.MultiClusterKubernetesSpawner.objects_template = """
apiVersion: v1
kind: Pod
metadata:
    name: {{key}}
spec:
    containers:
    - name: notebook
      image: jupyter/scipy-notebook:latest
      ports:
        - containerPort: 8888
      command:
      - /opt/conda/bin/jupyterhub-singleuser
      - --port=8888
---
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
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{key}}
spec:
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
"""
