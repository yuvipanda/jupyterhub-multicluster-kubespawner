import pytest
from unittest.mock import MagicMock
from multicluster_kubespawner.spawner import MultiClusterKubernetesSpawner


@pytest.fixture
def spawner():
    sp = MultiClusterKubernetesSpawner()
    user = MagicMock()
    user.name = "mock_name"
    user.id = "mock_id"
    user.url = "mock_url"
    sp.user = user

    hub = MagicMock()
    hub.public_host = "mock_public_host"
    hub.url = "mock_url"
    hub.base_url = "mock_base_url"
    hub.api_url = "mock_api_url"
    sp.hub = hub

    return sp


def test_key(spawner):
    template = """
    apiVersion: v1
    kind: Pod
    metadata:
        name: {{key}}
    spec:
        containers:
        - name: nginx
          image: nginx:1.14.2
          ports:
            - containerPort: 80
    """
    spawner.objects_template = template
    print(spawner.get_objects_yaml())
