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
