import re

def update_test_file(path):
    with open(path, 'r') as f:
        content = f.read()

    # Change resp.json() to resp.json()["data"] when assigned to data
    content = content.replace('data = resp.json()', 'resp_json = resp.json()\n        assert resp_json["status"] is True\n        data = resp_json["data"]')

    # Change .json()["id"] to .json()["data"]["id"]
    content = content.replace('.json()["id"]', '.json()["data"]["id"]')
    
    # Change status_code == 204 to status_code == 200 for deletes
    content = content.replace('assert del_resp.status_code == 204', 'assert del_resp.status_code == 200')
    
    with open(path, 'w') as f:
        f.write(content)

update_test_file('tests/test_practitioner_api.py')
