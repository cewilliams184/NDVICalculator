# use USGS Machine-2-Machine (M2M) API to access, fileter, and download data
# Chantel Williams
# August 2024

import datetime
import json
import os
import re
import requests
import threading
import M2M_constants as cn
import M2M_API_Filters



class ApiService:
    def __init__(self,
                 config_file_path = cn.config_file_path,
                 download_filepath = cn.download_path,
                 sema=cn.sema):
        self.config_file_path = config_file_path
        self.load_config()
        self.api_key = None
        self.contact_id = 0
        self.download_filepath = download_filepath
        self.sema = sema
        self.threads = []

    def load_config(self):
        with open(self.config_file_path, 'r') as config_file:
            config = json.load(config_file)
            self.endpoint = config['endpoint']
            self.username = config['username']
            self.password = config['password']
            self.timeout = config['timeout']

    def authenticate(self):
        parameters = {
            'username': self.username,
            'password': self.password,
            'authType': 'EROS',
            'catalogId': 'EE'
        }

        try:
            response = self.dispatch_request('login', parameters)
            self.api_key = response['data']
            return True
        except:
            return False

    def dispatch_request(self, route, parameters=None):
        url = f"{self.endpoint}{route}"
        headers = {'X-Auth-Token': self.api_key} if self.api_key else {}
        headers['Content-Type'] = 'application/json'
        payload = json.dumps(parameters) if parameters else {}

        response = requests.post(url, data=payload, headers=headers, timeout=self.timeout)
        return self.parse_response(response)

    def downloadFile(self, url):
        self.sema.acquire()
        attempts = 0
        try:
            response = requests.get(url, stream=True)
            disposition = response.headers['content-disposition']
            filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
            print(f"Downloading {filename} ...\n")
            if config_file_path != "" and self.download_filepath[-1] != "/":
                filename = "/" + filename
            open(self.download_filepath + filename, 'wb').write(response.content)
            print(f"Downloaded {filename}\n")
            self.sema.release()


        except Exception as e:
            print(f"Failed to download from {url}. {e}. Will try to re-download.\n")
            if attempts < 5:
                self.sema.release()
                self.runDownload(self.threads, url)
                attempts +=1

    def parse_response(self, response):
        result = response.json()

        if not result or any(
                key not in result for key in ['errorCode', 'errorMessage', 'data', 'requestId', 'version']):
            raise ApiException("Invalid response from API")

        if result['errorCode']:
            raise ApiException(f"{result['errorCode']}: {result['errorMessage']}")

        return result

    def runDownload(self, threads, url):
        thread = threading.Thread(target=self.downloadFile, args=(url,))
        threads.append(thread)
        thread.start()

    def search(self, scene_filter, dataset_name, max_results=100, starting_number=1, sort_field='acquisitionDate',
               sort_direction='DESC'):
        parameters = {
            'sceneFilter': scene_filter,
            'datasetName': dataset_name.lower(),
            'maxResults': max_results,
            'startingNumber': starting_number,
            'sortField': sort_field,
            'sortDirection': sort_direction
        }

        return self.dispatch_request('scene-search', parameters)


class ApiException(Exception):
    pass


def parse_results(datasets, coordinates):
    # https://m2m.cr.usgs.gov/api/docs/example/download_data-py
    # search document for : download datasets
    for dataset in datasets['data']['results']:
        if not dataset['displayId'].startswith('LC08_'):
            print(f"Found dataset {dataset['displayId']} but skipping it.\n")
            continue

    if datasets['data']['recordsReturned'] > 0:
        sceneIds = []
        for result in datasets['data']['results']:
            #determine if centroid in result polgyon
            centroid_in_polygon = M2M_API_Filters.filter_on_centroid(result, coordinates)
            if centroid_in_polygon == True:
                sceneIds.append(result['entityId'])
        #find smallest cloud cover dataset
        if len(sceneIds) > 1:
            cloud_cover_dictionary = {}
            for result in datasets['data']['results']:
                cloud_cover_dictionary[result['entityId']] = result['cloudCover']

            minimum_cloud_cover = [min(cloud_cover_dictionary, key = cloud_cover_dictionary.get)]
        if len(minimum_cloud_cover) == 1 :
            sceneId = minimum_cloud_cover
        else:
            #return first value in dictionary
            #https://stackoverflow.com/questions/21930498/how-to-get-the-first-value-in-a-python-dictionary
            sceneId = cloud_cover_dictionary[0]
            pass

        # find download options for these scenes
        payload = {'datasetName': 'landsat_ot_c2_l2', 'entityIds': sceneId}
        downloadOptions = api_service.dispatch_request('download-options', payload)

        downloads = []
        for product in downloadOptions['data']:
            #Make sure product is available for the scene
            if product['available'] == True:
                downloads.append({'entityId': product['entityId'],
                                  'productId': product['id']})
        #did we find products?
        if downloads:
            requestDownloadCount = len(downloads)
            #set a label for the download request
            label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            payload = {'downloads': downloads,
                       'label': label
                       }
            #Call the downloads to get the direct download urls
            requestResults = api_service.dispatch_request('download-request', payload)

            #Call the download retrieve method to get download that is immediately available for downlaod
            if requestResults['data']['preparingDownloads'] is not None and len(requestResults['data']['preparingDownloads']) > 0:
                payload = {'label': label}
                moreDownloadUrls = api_service.dispatch_request('dowload-retrieve', payload)

                downloadIds = []

                for download in moreDownloadUrls['available']:
                    if str(download['downloadID']) in requestResults['newRecords'] or str(download['downloadId']):
                        downloadIds.append(download['downloadId'])
                        api_service.runDownload(api_service.threads, download['url'])
            else:
                #Get all available downlaods
                for download in requestResults['data']['availableDownloads']:
                    api_service.runDownload(api_service.threads, download['url'])
        else:
            print("Search found no results.\n")

    print("Downloading files... Please do not close the program\n")
    for thread in api_service.threads:
        thread.join()

    print("Complete Downloading")

    return


# Example usage:
config_file_path = cn.config_file_path
api_service = ApiService(config_file_path)
coordinates = cn.coordinates

if api_service.authenticate():

    results = api_service.search(scene_filter=M2M_API_Filters.create_scene_filter(coordinates)[0],
                                 dataset_name='landsat_ot_c2_l2',
                                 )


    # print(results)
    print("Found ", len(results), " datasets\n")
    parse_results(results, coordinates)

    #log out so the API key cannot be used anymore
    if api_service.dispatch_request('logout') is None:
        print ("Logged Out\n\n")
    else:
        print("Logout Failed\n\n")