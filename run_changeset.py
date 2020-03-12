import json
import http.client
import re


def http_action(send_data, url, method="PUT", headers=None):
    data_body = json.dumps(send_data).encode('utf-8')
    conn = http.client.HTTPConnection(host, 80)  # for https support change this
    conn.request(method, url, data_body, headers)
    response = conn.getresponse()
    body = response.readlines()[0].decode("utf-8")
    if response.getcode() != 200:
        raise ValueError("API responded with HTTP {}".format(response.getcode()))
    return json.loads(body)


def get_token():
    username = input("InProd user name: ")
    password = input("Password: ")
    login_details = {'username': username, 'password': password}
    headers = {'Content-Type': 'application/json'}
    res = http_action(login_details, '/api/v1/admin/obtain-auth-token/', method="POST", headers=headers)
    return res['tokens']['auth']


host = input("InProd server name: ")
token = get_token()
headers = {'Authorization': "Token " + token, 'Content-Type': 'application/json'}
cs_id = input("Changeset Id: ")

url = "/api/v1/change-set/variable/?change_set={}".format(cs_id)
res = http_action(None, url, method="GET", headers=headers)
variables = {x['attributes']['name']: x['attributes']['value'] for x in res['data']}
if variables:
    print("Enter values for Changeset Variables")
    for (key, value) in variables.items():
        print("\nVariable: '{}' The default value is: {}".format(key, value))
        user_input = input("Enter new value, leave blank for default value: ")
        if len(user_input) > 0:
            variables[key] = user_input
        else:
            print("\t default used")

else:
    print("There are no variables for this Changeset")

print("Validating...")
url = "/api/v1/change-set/change-set/{}/validate/".format(cs_id)
variables_json = json.dumps(variables)
result = []
for i in http_action(variables_json, url=url, headers=headers):
    if len(i['errors'].keys()) > 0:
        result.append({'action_id': i['action_id'], 'errors': i['errors']})
        print("Action Id: {}".format(i['action_id']))
        for (field, errors) in i['errors'].items():
            print("\t{}: {}".format(field, " - ".join(errors)))

if len(result) != 0:
    print("There is an error with the changeset, it did not validate")
else:
    print("Changeset validated correctly")
    print("Executing...")
    url = "/api/v1/change-set/change-set/{}/execute/".format(cs_id)
    result = http_action(variables_json, url=url, headers=headers)
    if result['data']['attributes']['successful'] is True:
        print("Changeset was executed successfully")
    elif result['data']['attributes']['successful'] is False:
        print("Changeset execution was not successfully")
    else:
        print("Changeset is still running, results to be emailed")
    result_url = re.search(r"(http.*)\" ", result['data']['attributes']['description']).groups()
    if result_url:
        print(result_url[0])

print("\nCompleted.")
