import os
import json
from dotenv import load_dotenv
from odk_client import ODKClient

load_dotenv()
url = os.getenv("ODK_SERVER_URL", "")
email = os.getenv("ODK_EMAIL", "")
pwd = os.getenv("ODK_PASSWORD", "")
pid = os.getenv("ODK_PROJECT_ID", "1")
fid = os.getenv("ODK_FORM_ID", "")

client = ODKClient(url, email, pwd, int(pid), fid)
if client.authenticate():
    print("Connected.")
    subs = client.get_submissions()
    if subs:
        sub = subs[0]
        print(f"Submission ID: {sub.get('__id', sub.get('instanceID'))}")
        # Find all keys that have a string value ending in .jpg or .png
        for k, v in sub.items():
            if isinstance(v, str) and (v.endswith('.jpg') or v.endswith('.png')):
                print(f"Direct match: {k} -> {v}")
            elif isinstance(v, dict):
                # Sometimes it's a dict like {'filename': '...'}
                if 'filename' in v:
                    print(f"Dict match: {k} -> {v['filename']}")
            elif isinstance(v, list):
                print(f"List match: {k}")
        
        # Also let's print the raw attachments for this submission to see what server expects
        inst_id = sub.get('__id', sub.get('instanceID', getattr(sub, '_instance_id', '')))
        if inst_id:
            api_id_encoded = __import__('urllib.parse').parse.quote(inst_id)
            url_list = f"{client.server_url}/v1/projects/{client.project_id}/forms/{client.form_id}/submissions/{api_id_encoded}/attachments"
            r = client.session.get(url_list)
            if r.status_code == 200:
                print("Attachments on server:", json.dumps(r.json(), indent=2))
            else:
                print("Failed to get attachments with encoded ID. Status:", r.status_code)
                print("Trying without uuid: ...")
                r2 = client.session.get(url_list.replace("uuid%3A", ""))
                if r2.status_code == 200:
                    print("Attachments on server (NO UUID):", json.dumps(r2.json(), indent=2))
                else:
                    print("Also failed without uuid.")
else:
    print("Auth failed.")
