import requests
import os
import sys
from urllib.parse import urljoin

artifactory_server='https://us.artifactory.automotive.cloud/artifactory/'
repository_path='vni_otp_generic_l/'

with open(os.path.join(os.environ["HOME"], '.credentials/artifactory')) as CREDENTIALS_FILE:
  artifactory_token = CREDENTIALS_FILE.read()

artifactory_user = artifactory_token.split(':')[0]
artifactory_password = artifactory_token.split(':')[1]
if artifactory_password[-1] == '\n':
  artifactory_password = artifactory_password[:-1]

artifactory_session = requests.Session()
artifactory_session.auth = (artifactory_user, artifactory_password)
artifactory_session.verify = False

def build_url(artifact_path, release_id, api_path = ""):
  if release_id[-1] != '/':
      release_id += '/'
  print("Build URL:\n\tpath [{}]\n\tRELEASE_ID [{}]\n\tapi_path [{}]".format(artifact_path, release_id, api_path))
  request_url = urljoin(artifactory_server, api_path)
  request_url = urljoin(request_url, repository_path)
  request_url = urljoin(request_url, release_id)
  request_url = urljoin(request_url, artifact_path)
  print("Build URL:\n\tResult [{}]".format(request_url))

  return request_url

def search_artifactory(search_string):
  #search_url = urljoin(artifactory_server, "/artifactory/api/search/folder")
  search_url = urljoin(artifactory_server, "/artifactory/api/search/artifact")
  if search_string[-1] == '/':
     search_for = search_string[:-1]
  else:
     search_for = search_string
  params = {'name':search_for,'repos':repository_path[:-1]}
  request = requests.PreparedRequest()
  request.prepare_url(search_url, params)
  print("Search URL: {}".format(request.url))
  response = artifactory_session.get(request.url, verify = False)
  response.raise_for_status()
  if response.status_code != 204:
    #data = response.json()
    return response.text
  return None

def get_metainfo(source_path, release_id = "conmod-sa515m-3.y/", ret_as_text=False):
  metainfo_url = build_url(source_path, release_id, "/artifactory/api/storage/")
  print("Get metainfo: from [{}]".format(metainfo_url))
  response = artifactory_session.get(metainfo_url, verify = False)
  response.raise_for_status()
  if response.status_code != 204:
    if ret_as_text == True:
      data = response.text
    else:
      data = response.json()
    return data
  else:
    return None

def download_artifact(source_path, destination_path, release_id = "conmod-sa515m-3.y/"):
  download_url = build_url(source_path, release_id)
  print("download_artifact: [{}] from to [{}]".format(download_url, destination_path))
  with artifactory_session.get(download_url) as download_request:
    with open(destination_path, 'wb') as output_file:
      output_file.write(download_request.content)

def upload_artifact(source_path, destination_path, release_id = "conmod-sa515m-3.y/"):
  upload_url = build_url(destination_path, release_id)

  print("upload_artifact: [{}] to [{}]".format(source_path, upload_url))

  with open(source_path, 'rb') as input_file:
    request_result = artifactory_session.put(upload_url, data=input_file, verify = False)
    print (request_result.text)
    return (request_result.status_code) == 200 or (request_result.status_code) == 201


def move_artifact(source_path, destination_path, release_id = "conmod-sa515m-3.y/"):
  move_url = build_url(source_path, release_id, "/artifactory/api/move/") + "?to=/" + repository_path + release_id + destination_path

  request_result = artifactory_session.post(move_url, verify = False)
  return (request_result.status_code) == 200 or (request_result.status_code) == 201

def list_files(source_path, release_id = "conmod-sa515m-3.y/"):
  list_url = build_url(source_path, release_id, "/artifactory/api/storage/")
  request_result = artifactory_session.get(list_url, verify = False)
  return request_result.text

def delete_artifact(source_path, release_id = "conmod-sa515m-3.y/"):
  delete_url = build_url(source_path, release_id)

  request_result = artifactory_session.delete(delete_url)
  print (request_result.text)
  return (request_result.status_code) == 200 or (request_result.status_code) == 201

def copy_artifact(source_file_path, destination_file_path, release_id = "conmod-sa515m-3.y/"):
  if release_id[-1] != '/':
     release_id += '/'

  copy_url = build_url(source_file_path, release_id, "/artifactory/api/copy/")
  copy_url = copy_url + "?to=/" + repository_path + release_id + destination_file_path
  request_result = artifactory_session.post(copy_url, verify = False)
  return (request_result.status_code) == 200 or (request_result.status_code) == 201

