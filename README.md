# ee-initialize-github-actions
_Instructions for initializing to Earth Engine in Python scripts run with GitHub Actions. There
are multiple ways to do this, I'd like to add several, but for now it demonstrates constructing
credentials from `google.oauth2.credentials.Credentials`_

So you want to test Earth Engine in your GitHub Actions? Great idea! To do it, you'll need
to authenticate and initialize to the Earth Engine service. This repo describes how to
generate a credentials file, save those credentials as a GitHub Secret, construct
oauth2 credentials and pass them to `ee.Initialize()`. A basic workflow file and Earth
Engine script are provided, but they are super minimal and not the focus of this demo.

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
If should be single-line JSON formatted like this:

```json
{"client_id": "value", "client_secret": "value", "refresh_token": "value", "project": "value"}
```

**Go to the GitHub repo where you're running GitHub Actions and create a new
[repository secret](https://docs.github.com/en/codespaces/managing-codespaces-for-your-organization/managing-development-environment-secrets-for-your-repository-or-organization).**
On the top tabs click "Actions", on the left TOC click "Secrets and variables", select "Actions",
and then "New repository secret"

![image](https://github.com/user-attachments/assets/65dbd501-fbbd-43dd-b9e0-44d886d7eddb)

You'll be prompted to name the secret; I suggest `EARTHENGINE_TOKEN`. Copy the credentials information
from your text editor into the secret input text box. It's important that the text be unaltered and
unformatted to avoid JSON decoding errors.

> We advise minifying your JSON into a single line string before storing it in a GitHub Secret. When a
> GitHub Secret is used in a GitHub Actions workflow, each line of the secret is masked in log output.
> This can lead to aggressive sanitization of benign characters like curly braces ({}) and brackets ([]).

## 3. Write your workflow and add the EARTHENGINE_TOKEN secret as an environmental varible

I'll not get into the [details of writing a workflow](https://docs.github.com/en/actions/writing-workflows/about-workflows).
You can [see my full example](https://github.com/gee-community/ee-initialize-github-actions/blob/main/.github/workflows/ee-test-with-oauth2.yml),
but **the important part to note is that I'm setting an environmental variable from the credentials secret
in the step that runs my Earth Engine script** ([ee-test-with-oauth2.py](https://github.com/gee-community/ee-initialize-github-actions/blob/main/ee-test-with-oauth2.py)).

```yml
- name: Run Earth Engine Script
  env:
    EARTHENGINE_TOKEN: ${{ secrets.EARTHENGINE_TOKEN }}
  run: |
    python ee-test-with-oauth2.py
```

## 4. Initialize to Earth Engine in your test file

In the test file ([ee-test-with-oauth2.py](https://github.com/gee-community/ee-initialize-github-actions/blob/main/ee-test-with-oauth2.py))
that makes Earth Engine requests, **construct Oauth2 credentials
from the credentials info in the secret**. The credentials info is fetched from
the environment variable we set previously, and then arranged as arguments
to `google.oauth2.credentials.Credentials` whose result is given to `ee.Initialize()`.

```python
import ee
import json
import os
import google.oauth2.credentials

stored = json.loads(os.getenv("EARTHENGINE_TOKEN"))
credentials = google.oauth2.credentials.Credentials(
    None,
    token_uri="https://oauth2.googleapis.com/token",
    client_id=stored["client_id"],
    client_secret=stored["client_secret"],
    refresh_token=stored["refresh_token"],
    quota_project_id=stored["project"],
)

ee.Initialize(credentials=credentials)

print(ee.String("Greetings from the Earth Engine servers!").getInfo())
```

## 5. Test the script

In this case, I'm just **manually triggering the workflow from the "Actions" tab,
clicking on the workflow, and running the workflow**. 

![image](https://github.com/user-attachments/assets/cd324247-f592-401c-afdd-e5cc5e2d1382)

As you can see, the scripts runs successfully and we get a nice message from the
Earth Engine servers 😁

![image](https://github.com/user-attachments/assets/280082ef-7caa-419e-8fa2-795bc1e888d1)

You can encounter the following errors
ee.ee_exception.EEException: Google Earth Engine API has not been used in project projectid before or it is disabled. Enable it by visiting https://console.developers.google.com/apis/api/earthengine.googleapis.com/overview?project=projectid then retry. If you enabled this API recently, wait a few minutes for the action to propagate to our systems and retry.

![image](https://github.com/thekester/ee-initialize-github-actions/blob/google-oauth2-credentials/enablegoogleeartengineapi.png)

![image](https://github.com/thekester/ee-initialize-github-actions/blob/google-oauth2-credentials/buttonenablegoogleearthengineapi.png)

