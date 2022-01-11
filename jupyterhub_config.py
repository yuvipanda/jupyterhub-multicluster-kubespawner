from jupyterhub.spawner import SimpleLocalProcessSpawner
from jupyterhub.auth import DummyAuthenticator
from multicluster_kubespawner.spawner import MultiClusterKubernetesSpawner

c.JupyterHub.hub_ip = "192.168.0.151"
c.Spawner.hub_connect_url = "https://34ed-36-255-233-17.ngrok.io"
# c.Spawner.hub_connect_ip = "192.168.0.151"

c.JupyterHub.spawner_class = MultiClusterKubernetesSpawner
c.JupyterHub.authenticator_class = DummyAuthenticator

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
      - path: /user/{{username}}
        pathType: Prefix
        backend:
          service:
            name: {{key}}
            port:
              number: 8888
"""
