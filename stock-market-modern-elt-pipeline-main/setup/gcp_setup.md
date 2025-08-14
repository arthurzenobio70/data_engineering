# Google Cloud Platform Setup

## GCP Account

- Create a [GCP Account](https://console.cloud.google.com/freetrial/) if you don't have one.
- Create a [GCP project](https://console.cloud.google.com/projectcreate?inv=1&invt=Ab0mdg) and note your project ID.

## GCP SDK

- Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install) locally.

- Initialize the gcloud CLI:

```
gcloud init
```

- Follow the instructions to authenticate with your Google account and configure your project.

## Configure Credentials

- Create a Service Account:
  - Go to GCP Console > IAM & Admin > Service Accounts
  - Select `+ CREATE SERVICE ACCOUNT`
  - Enter a name and description
  - Assign the `Viewer` role
  - Add the following additional roles: `Storage Admin`, `Storage Object Admin`, and `BigQuery Admin`

- Select the service account > Keys > Add Key > Create new key.
- Choose `JSON` and click `Create`. The key file will be downloaded to your machine.

> [!WARNING]
> Do not share this key file publicly.

- Rename the .json key file to `google_credentials.json`.
- Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your downloaded GCP keys:

**Windows**

```
set GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\google_credentials.json"
```

**macOS and Linux**

```
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/google_credentials.json"
```

- Verify authentication and default credentials:

```
gcloud auth application-default login
```

- Make sure the following service APIs are enabled:
  - [IAM API](https://console.cloud.google.com/apis/library/iam.googleapis.com?inv=1&invt=Ab0m7A)
  - [Cloud Storage](https://console.cloud.google.com/apis/api/storage-component.googleapis.com/credentials?inv=1&invt=Ab0yZw)
  - [BigQuery](https://console.cloud.google.com/apis/api/bigquery.googleapis.com/metrics?hl=en&inv=1&invt=Ab0ybw)
  - [Cloud Composer](https://console.cloud.google.com/apis/library/composer.googleapis.com?hl=en&inv=1&invt=Ab09MQ)
  - [Dataproc](https://console.cloud.google.com/dataproc/overview?referrer=search&hl=en&inv=1&invt=Ab1kmA)
