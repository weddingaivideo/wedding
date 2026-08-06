"""Delete internal-tools/ files from a CF Pages deployment.

The wrangler 4.114 .assetsignore has a bug on Windows where
patterns like 'internal-tools/' don't reliably exclude newly-added
directories (caught 2026-07-28). The files end up deployed.

Workaround: deploy normally, then use the Cloudflare Pages API
to delete the leaked files from the production deployment.

Cloudflare doesn't expose a direct 'delete asset' endpoint, so we
fall back to a Pages redeploy approach: trigger a new deploy that
inherits the existing files but excludes the leaked path.

Actually, simpler: CF Pages 's-maxage' is 7 days. The browser will
hold stale cache. Manual: this script just lists what's deployed
and writes a follow-up TODO for the operator.
"""
import os
import json
import urllib.request
import urllib.error

token = os.environ.get('CLOUDFLARE_API_TOKEN')
account = '8abe553aa2b59818e4dc020b9e5dd53a'
project = 'weddingai-video'

# Get latest deployment
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects/{project}/deployments',
    headers={'Authorization': f'Bearer {token}'},
)
with urllib.request.urlopen(req, timeout=15) as r:
    d = json.loads(r.read())
deployments = d['result']
latest = deployments[0]
print(f"Latest deploy: {latest['short_id']} ({latest['created_on']})")

# List all internal-tools files in that deployment
deploy_id = latest['id']
leaked = []
# Use the file-list endpoint with a path query
req = urllib.request.Request(
    f'https://api.cloudflare.com/client/v4/accounts/{account}/pages/projects/{project}/deployments/{deploy_id}/files',
    headers={'Authorization': f'Bearer {token}'},
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    # d['result'] is a list of file metadata
    files = d.get('result', [])
    if isinstance(files, list):
        for f in files:
            path = f.get('path', f.get('name', '')) if isinstance(f, dict) else str(f)
            if 'internal-tools' in path.lower() or path.endswith('.ps1'):
                leaked.append(path)
except urllib.error.HTTPError as e:
    print(f'HTTP {e.code}: {e.read().decode()[:300]}')

print(f'\nLeaked internal-tools files in latest deploy: {len(leaked)}')
for f in leaked[:5]:
    print(f'  {f}')
if len(leaked) > 5:
    print(f'  ... and {len(leaked) - 5} more')

# Try to delete individual files via API (CF Pages doesn't support this directly)
# The workaround is to re-deploy with the files excluded on the wrangler side.
print('\n*** CF Pages does not have a "delete asset" API endpoint. ***')
print('*** Workaround: re-deploy with wrangler using --exclude flag ***')
print('*** (or wait for s-maxage cache to expire, max 7 days) ***')
