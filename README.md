# Django, Cloud Run, Terraform


## Prepare infrastructure

- Create project with billing enabled, and configure gcloud for that project

```
PROJECT_ID=$(gcloud config get-value core/project)
gcloud config set project $PROJECT_ID
REGION=us-central1
```

- Configure default credentials (allows Terraform to apply changes):

```
gcloud auth application-default login
```

- Enable base services:

```
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  cloudresourcemanager.googleapis.com \
  redis.googleapis.com
```
- Add the following roles to the `<project-number>-compute@developer.gserviceaccount.com` service account:
```
- Logs Writer
- Storage Object Viewer
- Artifact Registry Create-on-Push Writer
- Cloud SQL Client
- Secret Manager Secret Accessor
```
- Build base image

```
gcloud builds submit
```

- Apply Terraform

```
terraform init
terraform apply -var project=$PROJECT_ID
```

- Run database migrations

```
gcloud builds submit --config cloudbuild-migrate.yaml
```

- Open service, getting the URL and password from the Terraform output:

```
terraform output service_url
terraform output superuser_password
```

## Apply application updates

</br>

* Set **Project ID** and **Region** environment variables
   ```
   PROJECT_ID=$(gcloud config get-value core/project)
   REGION=us-central1
   ```

</br>

* Build base docker image and push to container registry
   ```
   gcloud builds submit
   ```

</br>

* Apply Terraform for any change in Terraform manifest
   ```
   terraform apply -var project=$PROJECT_ID
   ```

</br>

* Run the migration and collect static commands
   ```
   gcloud builds submit --config cloudbuild-full.yaml
   ```

</br>

* Update service
   ```
   gcloud run services update cpj --platform managed --region $REGION --image gcr.io/${PROJECT_ID}/cpj
   ```

</br>

* Get the URL and password from the Terraform output
   ```
   terraform output service_url
   terraform output superuser_password
   ```

</br>
</br>

## Run project on local environment

</br>

* [Download](https://cloud.google.com/sdk/docs/install#installation_instructions) and run **gcloud CLI**


* Initialize gcloud
   ```
   gcloud init
   ```
* Authorize gcloud
   ```
   gcloud auth login
   ```

</br>

* [Download](https://cloud.google.com/sql/docs/postgres/connect-instance-auth-proxy#install-proxy) and run **Cloud SQL
  Auth proxy** to connect to your Cloud SQL instance
   ```
   ./cloud-sql-proxy --address 0.0.0.0 --port PORT_NUMBER INSTANCE_CONNECTION_NAME
   ```
    >If there is any permission error, use a sevice account with proper permissions for accessing the Cloud SQL instance (`Cloud SQL Client` role) in the flag `--credential_file=PATH_TO_SERVICE_ACCOUNT_JSON_FILE` in the above command.
</br>

* Setup Python environment and install dependencies
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

</br>

* Create **.env** file in root directory of the project and add these environment variables to it
   ```
   SECRET_KEY="secret_key"
   DEBUG=on
   USE_CLOUD_SQL_AUTH_PROXY=True
   DATABASE_URL="postgres://DATABASE_USER:DATABASE_PASSWORD@//cloudsql/INSTANCE_CONNECTION_NAME/DATABASE_NAME"
   GS_BUCKET_NAME=BUECKET_NAME
   ```

</br>

* Run the project
   ```
   python manage.py runserver
   ```

<!-- </br>

### `jobseeker-dev` project specific values
Add these values to **.env** file for the project:
```
INSTANCE_CONNECTION_NAME=
PORT_NUMBER=5432

DATABASE_USER=django
DATABASE_NAME=django
DATABASE_PASSWORD=<RETRIEVE_FROM_SECRET_MANAGER>

BUECKET_NAME=
``` -->