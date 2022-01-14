import asyncio
from tornado import gen
from io import StringIO
from jinja2 import Template
from textwrap import dedent
import tempfile
import string
import escapism
from ruamel.yaml import YAML
import json
from slugify import slugify

yaml = YAML(typ="safe")

from jupyterhub.spawner import Spawner
from traitlets.config import Unicode, Dict, List
from traitlets import default, Union, Callable


class MultiClusterKubernetesSpawner(Spawner):
    start_timeout = 300

    # Notebook servers must always listen on 0.0.0.0, otherwise there is no
    # way for the Ingress providers to talk to them
    ip = "0.0.0.0"

    objects = Dict(
        Unicode,
        {},
        help="""
        Jinja2 Template to generate kubernetes objects generated by the spawner.

        Objects are sorted by key before they are evaluated.
        """,
        config=True,
    )
    key_template = Unicode("jupyter-{{username}}--{{servername}}", config=True)

    patches = Dict(
        Unicode,
        {},
        help="""
        Customize generated resources by patching them where necessary.

        A jinja2 template that can produce multiple YAML documents, which will be
        merged with generated objects from object_template. metadata.name will
        be used to decide which objects are patched.

        The patches are sorted by key before they are evaluated.
        """,
        config=True,
    )

    ingress_public_url = Unicode(
        "",
        help="""
        Address of the ingress controller's public endpoint in the targe cluster
        """,
        config=True,
    )

    kubernetes_context = Unicode(
        "",
        help="""
        Kubernetes context to use for connecting to the kubernetes cluster.
        """,
        config=True,
    )

    profile_list = Union(
        trait_types=[List(trait=Dict()), Callable()],
        config=True,
        help="""
        List of profiles to offer for selection by the user.

        Signature is: `List(Dict())`, where each item is a dictionary that has two keys:

        - `display_name`: the human readable display name (should be HTML safe)
        - `slug`: the machine readable slug to identify the profile
          (missing slugs are generated from display_name)
        - `description`: Optional description of this profile displayed to the user.
        - `spawner_override`: a dictionary with overrides to apply to the Spawner
          settings. Each value can be either the final value to change or a callable that
          take the `Spawner` instance as parameter and return the final value.
        - `default`: (optional Bool) True if this is the default selected option

        Example::

            c.MultiClusterKubeSpawner.profile_list = [
                {
                    'display_name': 'Training Env - Python',
                    'slug': 'training-python',
                    'default': True,
                    'spawner_override': {
                        'image': 'training/python:label',
                        'cpu_limit': 1,
                        'mem_limit': '512M',
                    }
                }, {
                    'display_name': 'Training Env - Datascience',
                    'slug': 'training-datascience',
                    'spanwer_override': {
                        'image': 'training/datascience:label',
                        'cpu_limit': 4,
                        'mem_limit': '8G',
                    }
                }, {
                    'display_name': 'DataScience - Small instance',
                    'slug': 'datascience-small',
                    'spawner_override': {
                        'image': 'datascience/small:label',
                        'cpu_limit': 10,
                        'mem_limit': '16G',
                    }
                }, {
                    'display_name': 'DataScience - Medium instance',
                    'slug': 'datascience-medium',
                    'spawner_override': {
                        'image': 'datascience/medium:label',
                        'cpu_limit': 48,
                        'mem_limit': '96G',
                    }
                }, {
                    'display_name': 'DataScience - Medium instance (GPUx2)',
                    'slug': 'datascience-gpu2x',
                    'spawner_override': {
                        'image': 'datascience/medium:label',
                        'cpu_limit': 48,
                        'mem_limit': '96G',
                        'extra_resource_guarantees': {"nvidia.com/gpu": "2"},
                    }
                }
            ]

        Instead of a list of dictionaries, this could also be a callable that takes as one
        parameter the current spawner instance and returns a list of dictionaries. The
        callable will be called asynchronously if it returns a future, rather than
        a list. Note that the interface of the spawner class is not deemed stable
        across versions, so using this functionality might cause your JupyterHub
        or MultiClusterKubeSpawner upgrades to break.
        """,
    )
    profile_form_template = Unicode(
        """
        <style>
        /* The profile description should not be bold, even though it is inside the <label> tag */
        #multicluster-kubespawner-profiles-list label p {
            font-weight: normal;
        }
        </style>

        <div class='form-group' id='multicluster-kubespawner-profiles-list'>
        {% for profile in profile_list %}
        <label for='profile-item-{{ profile.slug }}' class='form-control input-group'>
            <div class='col-md-1'>
                <input type='radio' name='profile' id='profile-item-{{ profile.slug }}' value='{{ profile.slug }}' {% if profile.default %}checked{% endif %} />
            </div>
            <div class='col-md-11'>
                <strong>{{ profile.display_name }}</strong>
                {% if profile.description %}
                <p>{{ profile.description }}</p>
                {% endif %}
            </div>
        </label>
        {% endfor %}
        </div>
        """,
        config=True,
        help="""
        Jinja2 template for constructing profile list shown to user.

        Used when `profile_list` is set.

        The contents of `profile_list` are passed in to the template.
        This should be used to construct the contents of a HTML form. When
        posted, this form is expected to have an item with name `profile` and
        the value the index of the profile in `profile_list`.
        """,
    )

    @default("env_keep")
    def _env_keep_default(self):
        return []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Key depends on other params here, so do it last
        self.key = Template(self.key_template).render(**self.template_vars).rstrip("-")
        # Our default port is 8888
        if self.port == 0:
            self.port = 8888

    @property
    def template_vars(self):
        # Make sure username and servername match the restrictions for DNS labels
        # Note: '-' is not in safe_chars, as it is being used as escape character
        safe_chars = set(string.ascii_lowercase + string.digits)

        raw_servername = self.name or ""
        safe_servername = escapism.escape(
            raw_servername, safe=safe_chars, escape_char="-"
        ).lower()

        safe_username = escapism.escape(
            self.user.name, safe=safe_chars, escape_char="-"
        ).lower()
        params = dict(
            userid=self.user.id,
            username=safe_username,
            unescaped_username=self.user.name,
            servername=safe_servername,
            unescaped_servername=raw_servername,
            proxy_spec=self.proxy_spec,
        )

        return params

    def get_labels(self):
        """
        Default labels added on to all objects generated by this spawner
        """
        return {
            "mcks.hub.jupyter.org/key": self.key,
        }

    async def apply_patches(self, objects):
        params = self.template_vars.copy()
        params["key"] = self.key
        params["spawner"] = self

        named_objects = {f"{o['kind']}/{o['metadata']['name']}": o for o in objects}

        patches = [
            yaml.load(Template(p).render(**params))
            for k, p in sorted(self.patches.items())
        ]

        for patch in patches:
            patch_name = f"{patch['kind']}/{patch['metadata']['name']}"
            with tempfile.NamedTemporaryFile(mode="w") as f:
                yaml.dump(named_objects[patch_name], f)
                f.flush()
                cmd = [
                    "kubectl",
                    "patch",
                    "--local",
                    "-f",
                    f.name,
                    "--patch",
                    json.dumps(patch),
                    "-o",
                    "yaml",
                ]
                if self.kubernetes_context:
                    cmd.append(f"--context={self.kubernetes_context}")

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await proc.communicate()
                if await proc.wait() != 0:
                    raise ValueError(
                        f"kubectl patch failed for {patch_name}: {stdout}, {stderr}"
                    )
                named_objects[patch_name] = yaml.load(stdout.decode())

        return list(named_objects.values())

    def augment_notebook_container(self, objects):
        """
        Augment the notebook container object after all patches are done

        Used to set JUPYTER_IMAGE and JUPYTER_IMAGE_SPEC env vars, as they can
        be modified by patches, but we can't refer to them from the env directly.
        """
        for object in objects:
            if object["kind"] == "Pod" and object["metadata"]["name"] == self.key:
                for c in object["spec"]["containers"]:
                    if c["name"] == "notebook":
                        c["env"].append({"name": "JUPYTER_IMAGE", "value": c["image"]})
                        c["env"].append(
                            {"name": "JUPYTER_IMAGE_SPEC", "value": c["image"]}
                        )

                        # Short circuit and return
                        return objects

    def get_objects_spec(self):
        """
        Render the templated YAML
        """
        params = self.template_vars.copy()
        params["key"] = self.key
        params["spawner"] = self
        parsed = [
            yaml.load(Template(dedent(o)).render(**params))
            for k, o in sorted(self.objects.items())
        ]

        for p in parsed:
            # Inject metadata into every object
            labels = p.setdefault("metadata", {}).setdefault("labels", {})
            labels.update(self.get_labels())

        return parsed

    def get_state(self):
        """
        Save state required to reinstate this user's pod from scratch
        """
        state = super().get_state()
        state["key"] = self.key
        state["kubernetes_context"] = self.kubernetes_context
        state["ingress_public_url "] = self.ingress_public_url
        return state

    def load_state(self, state):
        """
        Load state from storage required to reinstate this user's pod
        """
        if "key" in state:
            self.key = state["key"]
        if "ingress_public_url" in state:
            self.ingress_public_url = state["ingress_public_url"]
        if "kubernetes_context" in state:
            self.kubernetes_context = state["kubernetes_context"]

    async def kubectl_apply(self, spec):
        cmd = [
            "kubectl",
            "apply",
            "--wait",  # Wait for objects to be 'ready' before returning
            "-f",
            "-",
        ]
        if self.kubernetes_context:
            cmd.append(f"--context={self.kubernetes_context}")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        with StringIO() as s:
            yaml.dump_all(spec, s)
            s.seek(0)
            objs = s.read()
        self.log.debug(f"kubectl applying {objs}")
        stdout, stderr = await proc.communicate(objs.encode())

        if (await proc.wait()) != 0:
            raise ValueError(f"kubectl apply failed: {stdout}, {stderr}")

    async def kubectl_wait(self, timeout=30):
        cmd = [
            "kubectl",
            "wait",
            "--for=condition=Ready",
            f"pod/{self.key}",
            f"--timeout={timeout}s",
        ]
        if self.kubernetes_context:
            cmd.append(f"--context={self.kubernetes_context}")
        proc = await asyncio.create_subprocess_exec(*cmd)
        return await proc.wait()

    async def start(self):
        # load user options (including profile)
        await self.load_user_options()

        spec = self.augment_notebook_container(
            await self.apply_patches(self.get_objects_spec())
        )
        await self.kubectl_apply(spec)
        await self.kubectl_wait(self.start_timeout)

        # We aren't waiting long enough for the ingress object to be fully
        # picked up by the controllers.
        # FIXME: Wait for ingress to become ready instead
        await asyncio.sleep(1)

        # We always just return the public URL of the ingress provider, as both
        # our proxy and the ingress controller on the target cluster keep the
        # url path intact, and route to the correct pod
        return self.ingress_public_url

    async def stop(self):
        # delete all doesn't seem to delete ingresses, lol?!
        # https://github.com/kubernetes/kubectl/issues/7
        resources = ["all", "ingress"]
        for r in resources:
            cmd = [
                "kubectl",
                "delete",
                r,
                "-l",
                f"mcks.hub.jupyter.org/key={self.key}",
            ]
            if self.kubernetes_context:
                cmd.append(f"--context={self.kubernetes_context}")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            print(stdout, stderr)

    async def poll(self):
        ret = await self.kubectl_wait()
        if ret == 0:
            return None
        return ret

    _profile_list = None

    def _render_options_form(self, profile_list):
        self._profile_list = self._init_profile_list(profile_list)
        profile_form_template = Template(self.profile_form_template)
        return profile_form_template.render(profile_list=self._profile_list)

    async def _render_options_form_dynamically(self, current_spawner):
        profile_list = await gen.maybe_future(self.profile_list(current_spawner))
        profile_list = self._init_profile_list(profile_list)
        return self._render_options_form(profile_list)

    @default("options_form")
    def _options_form_default(self):
        """
        Build the form template according to the `profile_list` setting.

        Returns:
            '' when no `profile_list` has been defined
            The rendered template (using jinja2) when `profile_list` is defined.
        """
        if not self.profile_list:
            return ""
        if callable(self.profile_list):
            return self._render_options_form_dynamically
        else:
            return self._render_options_form(self.profile_list)

    @default("options_from_form")
    def _options_from_form_default(self):
        return self._options_from_form

    def _options_from_form(self, formdata):
        """get the option selected by the user on the form

        This only constructs the user_options dict,
        it should not actually load any options.
        That is done later in `.load_user_options()`

        Args:
            formdata: user selection returned by the form

        To access to the value, you can use the `get` accessor and the name of the html element,
        for example::

            formdata.get('profile',[0])

        to get the value of the form named "profile", as defined in `form_template`::

            <select class="form-control" name="profile"...>
            </select>

        Returns:
            user_options (dict): the selected profile in the user_options form,
                e.g. ``{"profile": "cpus-8"}``
        """
        return {"profile": formdata.get("profile", [None])[0]}

    async def _load_profile(self, slug):
        """Load a profile by name

        Called by load_user_options
        """

        # find the profile
        default_profile = self._profile_list[0]
        for profile in self._profile_list:
            if profile.get("default", False):
                # explicit default, not the first
                default_profile = profile

            if profile["slug"] == slug:
                break
        else:
            if slug:
                # name specified, but not found
                raise ValueError(
                    "No such profile: %s. Options include: %s"
                    % (slug, ", ".join(p["slug"] for p in self._profile_list))
                )
            else:
                # no name specified, use the default
                profile = default_profile

        self.log.debug(
            "Applying Spawner override for profile '%s'", profile["display_name"]
        )
        spawner_override = profile.get("spawner_override", {})
        for k, v in spawner_override.items():
            if callable(v):
                v = v(self)
                self.log.debug(
                    ".. overriding Spawner value %s=%s (callable result)", k, v
                )
            else:
                self.log.debug(".. overriding Spawner value %s=%s", k, v)
            setattr(self, k, v)

    # set of recognised user option keys
    # used for warning about ignoring unrecognised options
    _user_option_keys = {
        "profile",
    }

    def _init_profile_list(self, profile_list):
        # generate missing slug fields from display_name
        for profile in profile_list:
            if "slug" not in profile:
                profile["slug"] = slugify(profile["display_name"])

        return profile_list

    async def load_user_options(self):
        """Load user options from self.user_options dict

        This can be set via POST to the API or via options_from_form

        Only supported argument by default is 'profile'.
        Override in subclasses to support other options.
        """

        if self._profile_list is None:
            if callable(self.profile_list):
                profile_list = await gen.maybe_future(self.profile_list(self))
            else:
                profile_list = self.profile_list

            self._profile_list = self._init_profile_list(profile_list)

        selected_profile = self.user_options.get("profile", None)
        if self._profile_list:
            await self._load_profile(selected_profile)
        elif selected_profile:
            self.log.warning(
                "Profile %r requested, but profiles are not enabled", selected_profile
            )

        # help debugging by logging any option fields that are not recognized
        option_keys = set(self.user_options)
        unrecognized_keys = option_keys.difference(self._user_option_keys)
        if unrecognized_keys:
            self.log.warning(
                "Ignoring unrecognized Spawner user_options: %s",
                ", ".join(map(str, sorted(unrecognized_keys))),
            )
