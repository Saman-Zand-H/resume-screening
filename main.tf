terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.84.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

data "google_project" "project" {
  project_id = var.project
}

variable "project" {
  type        = string
  description = "Google Cloud Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Google Cloud Region"
}

variable "service" {
  type        = string
  default     = "job-seekers-django-api"
  description = "Name of the service containing Django application"
}

variable "pubsub_service" {
  type        = string
  default     = "job-seekers-django-pubsub-email"
  description = "Name of the service containing Django PubSub application"
}

variable "react_service" {
  type        = string
  default     = "job-seekers-react"
  description = "Name of the service containing React application"
}

variable "database" {
  type        = string
  default     = "job-seekers"
  description = "Name of the database"

}

# Activate service APIs
resource "google_project_service" "run" {
  service            = "run.googleapis.com"
  disable_on_destroy = false
}


resource "google_project_service" "sql-component" {
  service            = "sql-component.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "sqladmin" {
  service            = "sqladmin.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "secretmanager" {
  service            = "secretmanager.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "redis" {
  service            = "redis.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "pubsub" {
  service            = "pubsub.googleapis.com"
  disable_on_destroy = false
}


# Create a custom Service Account
resource "google_service_account" "js-api" {
  account_id = "js-api"
}


# Create the database
resource "random_password" "database_password" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "instance" {
  name             = var.database
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier      = "db-perf-optimized-N-2"
    disk_size = 20

    ip_configuration {
      ipv4_enabled = false
      # TODO: Check if this is working
      private_network                               = "projects/${var.project}/global/networks/default"
      enable_private_path_for_google_cloud_services = true
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "database" {
  name     = "js-s-db"
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "django" {
  name     = "js-s-user"
  instance = google_sql_database_instance.instance.name
  password = random_password.database_password.result
}


# Create the storage buckets
resource "google_storage_bucket" "main" {
  name     = "job-seekers"
  location = "US"

  uniform_bucket_level_access = true
}


resource "google_storage_bucket" "static" {
  name     = "job-seekers-static"
  location = "US"

  uniform_bucket_level_access = true
}


resource "google_storage_bucket" "errors" {
  name     = "job-seekers-errors"
  location = "US"

  uniform_bucket_level_access = true
}

# Create the secrets
resource "random_password" "django_secret_key" {
  length  = 50
  special = false
}

resource "google_secret_manager_secret" "job-seekers-settings" {
  secret_id = "job-seekers-settings"

  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "job-seekers-settings" {
  secret = google_secret_manager_secret.job-seekers-settings.id

  secret_data = templatefile("etc/env.tpl", {
    bucket     = google_storage_bucket.main.name
    secret_key = random_password.django_secret_key.result
    user       = google_sql_user.django
    instance   = google_sql_database_instance.instance
    database   = google_sql_database.database
    url        = google_cloud_run_service.service.status[0].url
    redis      = google_redis_instance.redis_instance
  })
}

resource "google_secret_manager_secret_iam_binding" "job-seekers-settings" {
  secret_id = google_secret_manager_secret.job-seekers-settings.id
  role      = "roles/secretmanager.secretAccessor"
  members   = [local.cloudbuild_serviceaccount, local.django_serviceaccount]
}

locals {
  cloudbuild_serviceaccount = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"
  django_serviceaccount     = "serviceAccount:${google_service_account.js-api.email}"
}


# Generate a JSON key for the Cloud Run service account
resource "google_service_account_key" "cloud_run_service_account_key" {
  service_account_id = google_service_account.js-api.name
}

resource "google_secret_manager_secret" "cloud_run_service_account_key" {
  secret_id = "job-seekers-credentials"

  replication {
    auto {}
  }
  depends_on = [google_project_service.secretmanager]
}

resource "google_secret_manager_secret_version" "cloud_run_service_account_key" {
  secret      = google_secret_manager_secret.cloud_run_service_account_key.id
  secret_data = google_service_account_key.cloud_run_service_account_key.private_key
}

# Create Cloud Run service
resource "google_cloud_run_v2_service" "service" {
  name                       = var.service
  location                   = var.region

  ingress = "INGRESS_TRAFFIC_ALL"

  template {

    service_account = google_service_account.js-api.email

    scaling {
      max_instance_count = 100
      min_instance_count = 1
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.instance.connection_name]
      }
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      resources {
        limits = {
          cpu    = "4"
          memory = "4Gi"
        }
      }

      env {
        name = "DJANGO_SETTINGS_MODULE"
        value = "config.settings.stage"
      }
      env {
        name = "GOOGLE_CLOUD_CREDENTIALS"
        value = "/secrets/credentials/job-seekers-credentials"
      }
      env {
        name = "ENV_FILE_PATH"
        value = "/secrets/settings/job-seekers-settings"
      }
      env {
        name = "settings"
        value_source {
          secret_key_ref {
            secret = google_secret_manager_secret.job-seekers-settings.id
            version = "1"
          }
        }
      }
      env {
        name = "credentials"
        value_source {
          secret_key_ref {
            secret = google_secret_manager_secret.cloud_run_service_account_key.id
            version = "1"
          }
        }
      } 
      volume_mounts {
        name = "cloudsql"
        mount_path = "/cloudsql"
      }

    }
  }

  traffic {
      type = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
      percent = 100
  }

  depends_on = [google_secret_manager_secret_version.job-seekers-settings]


  # template {
  #   spec {
  #     service_account_name = google_service_account.js-api.email
  #   }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "autoscaling.knative.dev/minScale"      = "1"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.instance.connection_name
        "run.googleapis.com/client-name"        = "terraform"
        "run.googleapis.com/ingress"            = "internal-and-cloud-load-balancer" # Allow internal traffic and external load balancers

      }
    }
  }
}


# Specify Cloud Run permissions
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}


resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_v2_service.service.location
  project  = google_cloud_run_service.service.project
  service  = google_cloud_run_service.service.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


# Create Cloud Run pubsub service
resource "google_cloud_run_service" "pubsub_service" {
  name                       = var.pubsub_service
  location                   = var.region
  autogenerate_revision_name = true

  template {
    spec {
      service_account_name = google_service_account.js-api.email
      containers {
        image = "gcr.io/cloudrun/hello"
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale"      = "100"
        "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.instance.connection_name
        "run.googleapis.com/client-name"        = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}


resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.pubsub_service.location
  project  = google_cloud_run_service.pubsub_service.project
  service  = google_cloud_run_service.pubsub_service.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


# Create Cloud Run React service
resource "google_cloud_run_service" "react_service" {
  name                       = var.react_service
  location                   = var.region
  autogenerate_revision_name = true

  template {
    spec {
      # service_account_name = google_service_account.js-api.email
      containers {
        image = "gcr.io/cloudrun/hello"
      }
    }

    metadata {
      annotations = {
        "autoscaling.knative.dev/maxScale" = "100"
        # "run.googleapis.com/cloudsql-instances" = google_sql_database_instance.instance.connection_name
        "run.googleapis.com/client-name" = "terraform"
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}


resource "google_cloud_run_service_iam_policy" "noauth" {
  location = google_cloud_run_service.react_service.location
  project  = google_cloud_run_service.react_service.project
  service  = google_cloud_run_service.react_service.name

  policy_data = data.google_iam_policy.noauth.policy_data
}


# Grant access for running Cloud Build yaml files
resource "google_project_iam_binding" "default_compute_service_account_roles" {
  for_each = toset([
    "run.developer",
    "iam.serviceAccountUser",
    "storage.objectAdmin",
    "secretmanager.secretAccessor",
    "cloudsql.client"
  ])

  role    = "roles/${each.key}"
  members = ["serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"]
  project = var.project
}

resource "google_service_account_iam_binding" "cloudbuild_sa" {
  service_account_id = google_service_account.js-api.name
  role               = "roles/iam.serviceAccountUser"

  members = [local.cloudbuild_serviceaccount]
}

resource "google_redis_instance" "redis_instance" {
  name               = "job-seekers"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = "default"
}

resource "google_project_iam_binding" "django_serviceaccount_permissions" {
  for_each = toset([
    "redis.admin",
    "cloudscheduler.admin",
    "pubsub.admin",
    "visionai.serviceAgent",
    "storage.objectAdmin",
    "run.admin",
    "cloudsql.client"
  ])
  role    = "roles/${each.key}"
  members = [local.django_serviceaccount]
  project = var.project
}


resource "google_project_iam_binding" "cloudbuild_serviceaccount_permissions" {
  for_each = toset([
    "artifactregistry.writer",
    "cloudbuild.builds.builder",
    "iam.serviceAccountUser",
    "logging.logWriter",
    "storage.objectAdmin"
    "run.admin",
    "cloudsql.client"
  ])
  role    = "roles/${each.key}"
  members = [local.cloudbuild_serviceaccount]
  project = var.project
}


# View final output
output "service_url" {
  value = google_cloud_run_service.service.status[0].url
}
