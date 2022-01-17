# On AWS with EKS

AWS has a plethora of interesting options to authenticate with it, here we will
specify the simplest (albeit maybe not the most secure or 'best practice').

1. Create an AWS [IAM User](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users.html)
   for use by `kubectl` to authenticate to AWS. This user will need a access key
   and access secret, but no console access.

2. Create an [access key](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)
   for this user. JupyterHub will need these while running to make requests to the kubernetes
   API, set as [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

3. Grant the user access to the `eks:DescribeCluster` permission, either directly or
   via a group you create specifically for this purpose.

4. Grant the user access to the Kubernetes API by editing the `aws-auth` configmap
   as [described in this document](https://docs.aws.amazon.com/eks/latest/userguide/add-user-role.html#aws-auth-users).

5. Generate an appropriate entry in your `KUBECONFIG` file:

   ```bash
   export AWS_ACCESS_KEY_ID=<access-key-id>
   export AWS_SECRET_ACCESS_KEY=<access-key-secret>
   aws eks update-kubeconfig --name=<cluster-name> --region=<aws-region>
   ```

When you deploy your JupyterHub, you need to set the environment variables
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` on the JupyterHub process itself
so it can talk to the Kubernetes API properly.
