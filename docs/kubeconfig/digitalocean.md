# On DigitalOcean

1. Install [doctl](https://github.com/digitalocean/doctl)

2. Create a [personal access token](https://docs.digitalocean.com/reference/api/create-personal-access-token/)
   to access your kubernetes cluster. Unlike the other cloud providers, this
   can not be scoped - it grants full access to your entire DO account! So
   use with care.

3. Generate an appropriate entry in your `KUBECONFIG` file:

   ```bash
   export DIGITALOCEAN_ACCESS_TOKEN=<your-digitalocean-access-token>
   doctl kubernetes cluster kubeconfig save <cluster-name>
   ```

When you deploy your JupyterHub, you need to set the environment variable
`DIGITALOCEAN_ACCESS_TOKEN` on the JupyterHub process itself so it can talk
to the Kubernetes API properly.