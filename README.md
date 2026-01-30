# ee-initialize-github-actions
_Instructions for initializing to Earth Engine in Python scripts run with GitHub Actions._

So you want to test Earth Engine in your GitHub Actions? Great idea! To do it, you'll need
to authenticate and initialize to the Earth Engine service. This repo demonstrates two modern
authentication methods:

1. **Service Account Authentication** (Recommended for CI/CD) - Uses a Google Cloud service account
2. **Token-based Authentication** (Alternative) - Uses your personal Earth Engine credentials

Both methods are demonstrated with a basic workflow file and Earth Engine script.

## Method 1: Service Account Authentication (Recommended)

This is the **recommended approach for CI/CD workflows** as it's more secure and doesn't rely
on personal credentials.

### 1. Create a Service Account in Google Cloud

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Select your Earth Engine enabled project
3. Navigate to **IAM & Admin > Service Accounts**
4. Click **Create Service Account**
5. Give it a name (e.g., "github-actions-ee") and click **Create**
6. Grant the service account appropriate permissions (at minimum, it needs Earth Engine access)
7. Click **Done**

### 2. Create a Service Account Key

1. Click on the service account you just created
2. Go to the **Keys** tab
3. Click **Add Key > Create new key**
4. Select **JSON** format and click **Create**
5. A JSON file will be downloaded - keep this secure!

### 3. Register the Service Account with Earth Engine

You need to register this service account with Earth Engine:

```shell
earthengine set_account <service-account-email>@<project-id>.iam.gserviceaccount.com
```

Or register it through the [Earth Engine Code Editor](https://code.earthengine.google.com/) by sharing
assets with the service account email.

### 4. Add Secrets to GitHub

1. Go to your GitHub repository
2. Navigate to **Settings > Secrets and variables > Actions**
3. Click **New repository secret**
4. Create two secrets:
   - **Name:** `EARTHENGINE_SERVICE_ACCOUNT`
     - **Value:** The entire contents of the JSON key file (paste as-is)
   - **Name:** `EARTHENGINE_PROJECT`
     - **Value:** Your Google Cloud project ID

### 5. Update Your Workflow

Your workflow should set these environment variables:

```yml
- name: Run Earth Engine Script
  env:
    EARTHENGINE_SERVICE_ACCOUNT: ${{ secrets.EARTHENGINE_SERVICE_ACCOUNT }}
    EARTHENGINE_PROJECT: ${{ secrets.EARTHENGINE_PROJECT }}
  run: |
    python ee-test-with-oauth2.py
```

---

## Method 2: Token-based Authentication (Alternative)

This method uses your personal Earth Engine credentials. Note that modern Earth Engine credentials
no longer include OAuth2 client credentials.

## 1. Create Earth Engine credentials

**Install the latest version of `earthengine-api`**. Activate your development
environment and update the library. (I'm using micromamba for package management)

```shell
micromamba activate ee
micromamba install conda-forge::earthengine-api
```

**Authenticate to create a credentials file.** Run the
[`earthengine authenticate`](https://developers.google.com/earth-engine/guides/command_line#authenticate)
command. Use `--force` to ensure that the auth flow is triggered and new credentials are
written. If a browser is detected, it'll have you go online to complete authentication;
follow the prompts. If a browser is not available, see
[alternatives](https://developers.google.com/earth-engine/guides/auth#authentication_details).

```shell
earthengine authenticate --force
```

The credentials file will be written to `~/.config/earthengine/credentials`. It is meant to be
private, don't share it or people can use your Earth Engine resources.

**Add a cloud project to the credentials file.** All Earth Engine requests are routed through
Google Cloud projects. You'll need to specify a project when you initialize to Earth Engine services.
One way to do that is to include a default project in your credentials file. Here we add one using the
`earthengine set_project` command. Be sure to edit the project ID to one that you want associated
with running tests in your GitHub repo.

To check you existing projects ids you can use the following command

```shell
gcloud projects list
```

To include a default project in your credentials file, use the following command:

```shell
earthengine set_project <YOUR-PROJECT-ID>
```

The given project will now appear in the credentials file just created.

## 2. Add the credentials information as a GitHub secret

**Find your credentials file (`~/.config/earthengine/credentials`) and open it with a text editor.**
The modern format should look like this (single-line JSON):

```json
{"refresh_token": "value", "project": "value", ...}
```

Note: The credentials no longer contain `client_id` and `client_secret` - this is expected!

**Go to the GitHub repo where you're running GitHub Actions and create repository secrets.**
On the top tabs click "Actions", on the left TOC click "Secrets and variables", select "Actions",
and then "New repository secret"

![image](https://github.com/user-attachments/assets/65dbd501-fbbd-43dd-b9e0-44d886d7eddb)

Create two secrets:

1. **Name:** `EARTHENGINE_TOKEN`
   - **Value:** Copy the entire credentials file content (keep it as single-line JSON)

2. **Name:** `EARTHENGINE_PROJECT`
   - **Value:** Your Google Cloud project ID (e.g., "my-ee-project")

> We advise minifying your JSON into a single line string before storing it in a GitHub Secret. When a
> GitHub Secret is used in a GitHub Actions workflow, each line of the secret is masked in log output.
> This can lead to aggressive sanitization of benign characters like curly braces ({}) and brackets ([]).

---

## 3. Write your workflow and add the secrets as environment variables

I'll not get into the [details of writing a workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows).
You can [see my full example](https://github.com/gee-community/ee-initialize-github-actions/blob/main/.github/workflows/ee-test-with-oauth2.yml),
but **the important part is setting the environment variables in the step that runs your Earth Engine script**
([ee-test-with-oauth2.py](https://github.com/gee-community/ee-initialize-github-actions/blob/main/ee-test-with-oauth2.py)).

**For Service Account Authentication:**

```yml
- name: Run Earth Engine Script
  env:
    EARTHENGINE_SERVICE_ACCOUNT: ${{ secrets.EARTHENGINE_SERVICE_ACCOUNT }}
    EARTHENGINE_PROJECT: ${{ secrets.EARTHENGINE_PROJECT }}
  run: |
    python ee-test-with-oauth2.py
```

**For Token-based Authentication:**

```yml
- name: Run Earth Engine Script
  env:
    EARTHENGINE_TOKEN: ${{ secrets.EARTHENGINE_TOKEN }}
    EARTHENGINE_PROJECT: ${{ secrets.EARTHENGINE_PROJECT }}
  run: |
    python ee-test-with-oauth2.py
```

The script automatically detects which authentication method to use based on available environment variables.

## 4. Initialize to Earth Engine in your test file

In the test file ([ee-test-with-oauth2.py](https://github.com/gee-community/ee-initialize-github-actions/blob/main/ee-test-with-oauth2.py)),
the script **automatically detects and uses the appropriate authentication method**:

1. **Service Account** (if `EARTHENGINE_SERVICE_ACCOUNT` is set) - preferred method
2. **Token-based** (if `EARTHENGINE_TOKEN` is set) - fallback method

The modern implementation no longer requires manual OAuth2 credential construction:

```python
import ee
import json
import os
import re
import httplib2
from pathlib import Path

def init_ee_from_service_account():
    """Initialize Earth Engine using a service account (preferred for CI/CD)."""
    if "EARTHENGINE_SERVICE_ACCOUNT" in os.environ:
        private_key = os.environ["EARTHENGINE_SERVICE_ACCOUNT"]
        ee_user = json.loads(private_key)["client_email"]
        credentials = ee.ServiceAccountCredentials(ee_user, key_data=private_key)
        ee.Initialize(
            credentials=credentials,
            project=credentials.project_id,
            http_transport=httplib2.Http()
        )
        return True
    return False

def init_ee_from_token():
    """Initialize Earth Engine using a token (fallback method)."""
    if "EARTHENGINE_TOKEN" in os.environ:
        ee_token = os.environ["EARTHENGINE_TOKEN"]
        # Write token to credentials file
        credential_folder_path = Path.home() / ".config" / "earthengine"
        credential_folder_path.mkdir(parents=True, exist_ok=True)
        credential_file_path = credential_folder_path / "credentials"
        credential_file_path.write_text(ee_token)
        
        project_id = os.environ.get("EARTHENGINE_PROJECT")
        if project_id is None:
            raise ValueError("EARTHENGINE_PROJECT environment variable required")
        
        ee.Initialize(project=project_id, http_transport=httplib2.Http())
        return True
    return False

# Try service account first, then token-based
if not init_ee_from_service_account():
    if not init_ee_from_token():
        raise ValueError("No valid authentication method found")

print(ee.String("Greetings from the Earth Engine servers!").getInfo())
```

Key changes from the old approach:
- No longer requires `client_id` and `client_secret` 
- Supports modern service account authentication
- Works with new credential file format
- Automatic method detection

## 5. Test the script

In this case, I'm just **manually triggering the workflow from the "Actions" tab,
clicking on the workflow, and running the workflow**. 

![image](https://github.com/user-attachments/assets/cd324247-f592-401c-afdd-e5cc5e2d1382)

As you can see, the scripts runs successfully and we get a nice message from the
Earth Engine servers 😁

![image](https://github.com/user-attachments/assets/280082ef-7caa-419e-8fa2-795bc1e888d1)

### Possible Errors

While running the workflow, you may encounter the following errors:

#### Error 1: Google Earth Engine API Not Enabled

```shell
ee.ee_exception.EEException: Google Earth Engine API has not been used in project projectid before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project=projectid then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.
```

- ![Enable Google Earth Engine API](https://github.com/thekester/ee-initialize-github-actions/blob/google-oauth2-credentials/enablegoogleeartengineapi.png)

To resolve this, **enable the Google Earth Engine API** by visiting the following link: [Enable Google Earth Engine API](https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project=projectid). If you enabled the API recently, please wait a few minutes for the changes to propagate before retrying.

- ![Click Enable Button](https://github.com/thekester/ee-initialize-github-actions/blob/google-oauth2-credentials/buttonenablegoogleearthengineapi.png)

#### Error 2: API Disabled for Specific Project

```shell
ee.ee_exception.EEException: Google Earth Engine API has not been used in project gitactions-idfederation before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project=gitactions-idfederation then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.
```

- ![Project Not Registered](https://github.com/thekester/ee-initialize-github-actions/blob/google-oauth2-credentials/projectnotregistered.png)

Again, you'll need to **enable the Google Earth Engine API** for the specified project by visiting the following link: [Enable API for gitactions-idfederation](https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project=gitactions-idfederation). Please wait a few minutes if the API was recently enabled.

