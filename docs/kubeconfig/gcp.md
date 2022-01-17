# On Google Cloud

1. Create a [Google Cloud Service Account](https://cloud.google.com/iam/docs/service-accounts),
   and give it enough permissions to access your Kubernetes cluster. `roles/container.developer`
   *should* be enough permission.

2. Create a JSON [Service Account Key](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)
   for your service account. This is what `kubectl` will eventually use to authenticate to
   the kubernetes cluster. You'll need to put this service account key in your production
   JupyterHub environment as well.

3. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to the location of
   this JSON Service Account key.

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=<path-to-json-service-account-key>
   ```

4. Generate an appropriate entry in your custom `kubeconfig` file.

   ```bash
   gcloud container clusters get-credentials <cluster-name> --zone=<zone>
   ```

When you deploy your JupyterHub, make sure that you set the environment variable
`GOOGLE_APPLICATION_CREDENTIALS` to point to the service account key in a place where
JupyterHub can find it.