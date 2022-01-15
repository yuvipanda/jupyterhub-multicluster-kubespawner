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
          image: pangeo/pangeo-notebook:latest
          command: {{spawner.cmd|tojson}}
          args: {{spawner.get_args()|tojson}}
          resources: {{resources|tojson}}
          ports:
          - containerPort: {{spawner.port}}
          env:
          # The memory env vars can be set directly by kubernetes, as they just show up
          # as 'bytes'. The CPU ones are a bit more complicated, because kubernetes will
          # only provide integers, with a single unit being 1m or .001 of a CPU. JupyterHub
          # says they'll be floats, as fractions of a full CPU. There isn't really a way to
          # do that in kubernetes, so we've to resort to doing that manually. This kinda sucks.
          # An advantage with kubernetes would be that it knows the *real* limits, which can be
          # setup either by a LimitRange object, or by just the number of CPUs available in the
          # node. Our spawner doesn't have this information.
          - name: MEM_GUARANTEE
            valueFrom:
                resourceFieldRef:
                    containerName: notebook
                    resource: requests.memory
          - name: MEM_LIMIT
            valueFrom:
                resourceFieldRef:
                    containerName: notebook
                    resource: limits.memory
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
        annotations:
            # Required to get websockets to work with contour
            projectcontour.io/websocket-routes: {{proxy_spec}}
            contour.heptio.com/websocket-routes: {{proxy_spec}}
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
