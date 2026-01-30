import ee
import json
import os
import re
import httplib2
from pathlib import Path

def init_ee_from_service_account():
    """Initialize Earth Engine using a service account (preferred for CI/CD)."""
    if "EARTHENGINE_SERVICE_ACCOUNT" in os.environ:
        try:
            private_key = os.environ["EARTHENGINE_SERVICE_ACCOUNT"]
            ee_data = json.loads(private_key)
            ee_user = ee_data["client_email"]
            
            # Connect to GEE using a ServiceAccountCredentials object
            credentials = ee.ServiceAccountCredentials(ee_user, key_data=private_key)
            # httplib2 transport is used for better compatibility in CI/CD environments
            ee.Initialize(
                credentials=credentials,
                project=credentials.project_id,
                http_transport=httplib2.Http()
            )
            return True
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(
                f"Invalid EARTHENGINE_SERVICE_ACCOUNT format: {e}. "
                "Please ensure it contains valid service account JSON."
            )
    return False

def init_ee_from_token():
    """Initialize Earth Engine using a token (fallback method)."""
    if "EARTHENGINE_TOKEN" in os.environ:
        ee_token = os.environ["EARTHENGINE_TOKEN"]
        
        # Remove quotes if present (readthedocs workaround)
        pattern = re.compile(r"^'[^']*'$")
        ee_token = ee_token[1:-1] if pattern.match(ee_token) else ee_token
        
        # Write the token to the credentials file
        credential_folder_path = Path.home() / ".config" / "earthengine"
        credential_folder_path.mkdir(parents=True, exist_ok=True)
        credential_file_path = credential_folder_path / "credentials"
        credential_file_path.write_text(ee_token)
        # Set restrictive permissions (owner read/write only)
        credential_file_path.chmod(0o600)
        
        # Get project ID
        project_id = os.environ.get("EARTHENGINE_PROJECT")
        if project_id is None:
            # Try to extract from token
            try:
                token_data = json.loads(ee_token)
                project_id = token_data.get("project") or token_data.get("project_id")
            except (json.JSONDecodeError, AttributeError):
                pass
        
        if project_id is None:
            raise ValueError(
                "Project ID cannot be detected. "
                "Please set the EARTHENGINE_PROJECT environment variable or "
                "include 'project' field in your credentials."
            )
        
        # httplib2 transport is used for better compatibility in CI/CD environments
        ee.Initialize(project=project_id, http_transport=httplib2.Http())
        return True
    return False

# Try service account authentication first (preferred), then token-based
if not init_ee_from_service_account():
    if not init_ee_from_token():
        raise ValueError(
            "No valid authentication method found. "
            "Please set either EARTHENGINE_SERVICE_ACCOUNT or EARTHENGINE_TOKEN "
            "environment variable."
        )

print(ee.String("Greetings from the Earth Engine servers!").getInfo())
