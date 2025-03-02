# use USGS Machine-2-Machine (M2M) API to access, fileter, and download data
# Chantel Williams
# August 2024

import datetime
import json
import os
import re
import requests
import sys
import threading

from matplotlib.cbook import ls_mapper_r

import M2M_constants as cn
import M2M_API_Filters_Raleigh
# from M2M_constants import result_path


def parse_response(response):
    result = response.json()

    if not result or any(
            key not in result for key in ['errorCode', 'errorMessage', 'data', 'requestId', 'version']):
        raise ApiException("Invalid response from API")

    if result['errorCode']:
        raise ApiException(f"{result['errorCode']}: {result['errorMessage']}")

    return result


class M2M:
    def __init__(self,
                 coordinates = None,
                 config_file_path=cn.config_file_path,
                 download_filepath=cn.download_path,
                 sema=cn.sema):
        self.authentication = None
        if coordinates is None:
            self.coordinates = sys.argv[1]
        self.config_file_path = config_file_path
        self.config = self.load_config()
        self.endpoint = self.config['endpoint']
        self.username = self.config['username']
        self.password = self.config['password']
        self.timeout = self.config['timeout']
        self.api_key = None
        self.contact_id = 0
        self.download_filepath = download_filepath
        # self.rectangle = self.format_coordinates()
        self.sema = sema
        self.threads = []

    def initialize_M2M(self):
        # self.load_config()
        self.authentication = self.authenticate()
        results = self.pull_data_from_api_service()
        return results

    def execute_M2M(self):
        results = self.initialize_M2M()
        return results

    def load_config(self):
        with open(self.config_file_path, 'r') as config_file:
            config = json.load(config_file)
        # return config
            # self.endpoint = config['endpoint']
            # self.username = config['username']
            # self.password = config['password']
            # self.timeout = config['timeout']
        return config

    def authenticate(self):
        parameters = {
            'username': self.config['username'],
            'password': self.config['password'],
            'authType': 'EROS',
            'catalogId': 'EE'
        }

        try:
            self.dispatch_request('login', parameters)
            response = self.dispatch_request('login', parameters)
            self.api_key = response['data']
            return True
        except:
            return False

    def dispatch_request(self, route, parameters):
        url = f"{self.config['endpoint']}{route}"
        headers = {'X-Auth-Token': self.api_key} if self.api_key else {}
        headers['Content-Type'] = 'application/json'
        payload = json.dumps(parameters) if parameters else {}

        response = requests.post(url, data=payload, headers=headers, timeout=self.config['timeout'])
        return parse_response(response)

    def downloadFile(self, url):
        self.sema.acquire()
        attempts = 0
        try:
            response = requests.get(url, stream=True)
            disposition = response.headers['content-disposition']
            filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
            # print(f"Downloading {filename} ...\n")
            if self.config_file_path != "" and self.download_filepath[-1] != "/":
                filename = "/" + filename
            open(self.download_filepath + filename, 'wb').write(response.content)
            # print(f"Downloaded {filename}\n")
            self.sema.release()


        except Exception as e:
            # print(f"Failed to download from {url}. {e}. Will try to re-download.\n")
            if attempts < 5:
                self.sema.release()
                self.runDownload(self.threads, url)
                attempts += 1

    def parse_results(self, datasets):
        # https://m2m.cr.usgs.gov/api/docs/example/download_data-py
        # search document for : download datasets
        results = []
        for dataset in datasets['data']['results']:
            if not dataset['displayId'].startswith('LC08'):#,'LC09'):
                # print(f"Found dataset {dataset['displayId']} but skipping it.\n")
                continue
            #TODO: include an else if for 'LC09' datasets?

        if datasets['data']['recordsReturned'] > 0:
            sceneIds = []
            for result in datasets['data']['results']:
                # determine if centroid in result polygon
                # centroid_in_polygon = M2M_API_Filters_Raleigh.filter_on_centroid(result, self.rectangle)
                # if centroid_in_polygon == True:
                sceneIds.append(result['entityId'])
            # find smallest cloud cover dataset
            if len(sceneIds) > 1:
                cloud_cover_dictionary = {}
                for result in datasets['data']['results']:
                    cloud_cover_dictionary[result['entityId']] = result['cloudCover']

                minimum_cloud_cover = [min(cloud_cover_dictionary, key=cloud_cover_dictionary.get)]
            else:
                print('no sceneIds found')
            if len(minimum_cloud_cover) == 1:
                sceneId = minimum_cloud_cover
            else:
                # return first value in dictionary
                # https://stackoverflow.com/questions/21930498/how-to-get-the-first-value-in-a-python-dictionary
                sceneId = cloud_cover_dictionary[0]
                pass

            # find download options for these scenes
            payload = {'datasetName': 'landsat_ot_c2_l2', 'entityIds': sceneId}
            downloadOptions = self.dispatch_request('download-options', payload)

            downloads = []
            for product in downloadOptions['data']:
                # Make sure product is available for the scene
                if product['available'] == True:
                    downloads.append({'entityId': product['entityId'],
                                      'productId': product['id']})
            # did we find products?
            if downloads:
                requestDownloadCount = len(downloads)
                # set a label for the download request
                label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                payload = {'downloads': downloads,
                           'label': label
                           }
                # Call the downloads to get the direct download urls
                requestResults = self.dispatch_request('download-request', payload)

                # Call the download retrieve method to get download that is immediately available for download
                if requestResults['data']['preparingDownloads'] is not None and len(
                        requestResults['data']['preparingDownloads']) > 0:
                    payload = {'label': label}
                    moreDownloadUrls = self.dispatch_request('download-retrieve', payload)

                    downloadIds = []

                    for download in moreDownloadUrls['available']:
                        if str(download['downloadID']) in requestResults['newRecords'] or str(
                                download['downloadId']):
                            downloadIds.append(download['downloadId'])
                            self.runDownload(self.threads, download['url'])
                else:
                    # Get all available downloads
                    for download in requestResults['data']['availableDownloads']:
                        self.runDownload(self.threads, download['url'])
                results.append(f"{requestResults['data']['availableDownloads'][0]['url'].split('=')[1].split('&')[0]}")
            else:
                results.append("Search found no results.\n")

        # results.append("Downloading files... Please do not close the program\n")
        for thread in self.threads:
            thread.join()

        # results.append("Complete Downloading")

        return results

    def format_coordinates(self):
        coordinates_list = self.coordinates.split(',')
        coordinates_float = [float(i) for i in coordinates_list]
        rectangle = [[coordinates_float[i], coordinates_float[i + 1]] for i in range(0, len(coordinates_float), 2)]
        return rectangle

    def pull_data_from_api_service(self):
        # api_service.load_config()
        if self.authentication:

            results = self.search(scene_filter=M2M_API_Filters_Raleigh.create_scene_filter()[0],
                                  dataset_name='landsat_ot_c2_l2')

            # print(results)
            # print("Found ", len(results), " datasets\n")
            filtered_results = self.parse_results(results)

            # # log out so the API key cannot be used anymore
            # if self.dispatch_request('logout', None):
            #     print("Logged Out\n\n")
            # else:
            #     print("Logout Failed\n\n")
        else:
            filtered_results = 'M2M API_Service did not authenticate'
        return filtered_results

    def runDownload(self, threads, url):
        thread = threading.Thread(target=self.downloadFile, args=(url,))
        threads.append(thread)
        thread.start()

    def search(self, scene_filter, dataset_name):
        parameters = {
            'sceneFilter': scene_filter,
            'datasetName': dataset_name.lower(),
            'maxResults': 100,
            'startingNumber': 1,
            'sortField': 'acquisitionDate',
            'sortDirection': 'DESC'
        }
        # self.dispatch_request('scene-search', parameters)
        request = self.dispatch_request('scene-search', parameters)
        return request


class ApiException(Exception):
    pass


# class M2M:
#     def __init__(self,
#                  coordinates=None,
#                  config_file_path=cn.config_file_path,
#                  ):
#         if coordinates is None:
#             self.coordinates = sys.argv[1]
#         self.api_service = ApiService
#         self.config_file_path = config_file_path
#
#     def initialize_M2M(self):
#         # self.api_service = ApiService(self.config_file_path)
#         self.coordinates = sys.argv[1]
#         result = self.pull_data_from_api_service(self.coordinates, self.api_service)
#         return result
#
#     def execute_M2M(self):
#         result = self.initialize_M2M()
#         return result






# Example usage:
# config_file_path = cn.config_file_path
# api_service = ApiService(config_file_path)
# # coordinates = cn.coordinates
# coordinates = sys.argv

def main():
    # apis = ApiService()
    # apis.execute_ApiService()
    m2ma = M2M()
    result = m2ma.execute_M2M()
    return result


if __name__ == '__main__':
    main()


# # use USGS Machine-2-Machine (M2M) API to access, fileter, and download data
# # Chantel Williams
# # August 2024
#
# import datetime
# import json
# # import os
# import re
# import requests
# import sys
# import threading
#
# from matplotlib.cbook import ls_mapper_r
#
# import M2M_constants as cn
# import M2M_API_Filters
#
#
# class ApiService:
#     def __init__(self,
#                  config_file_path=cn.config_file_path,
#                  download_filepath=cn.download_path,
#                  sema=cn.sema):
#         self.config_file_path = config_file_path
#         self.config = self.load_config()
#         self.endpoint = self.config['endpoint']
#         self.username = self.config['username']
#         self.password = self.config['password']
#         self.timeout = self.config['timeout']
#         self.api_key = None
#         self.contact_id = 0
#         self.download_filepath = download_filepath
#         self.sema = sema
#         self.threads = []
#
#     def execute_ApiService(self):
#         self.load_config()
#         self.authenticate()
#         return
#
#     def load_config(self):
#         with open(self.config_file_path, 'r') as config_file:
#             config = json.load(config_file)
#         # return config
#             # self.endpoint = config['endpoint']
#             # self.username = config['username']
#             # self.password = config['password']
#             # self.timeout = config['timeout']
#         return config
#
#     def authenticate(self):
#         parameters = {
#             'username': self.config['username'],
#             'password': self.config['password'],
#             'authType': 'EROS',
#             'catalogId': 'EE'
#         }
#
#         try:
#             self.dispatch_request('login', parameters)
#             response = self.dispatch_request('login', parameters)
#             self.api_key = response['data']
#             return True
#         except:
#             return False
#
#     def dispatch_request(self, route, parameters):
#         url = f"{self.config['endpoint']}{route}"
#         headers = {'X-Auth-Token': self.api_key} if self.api_key else {}
#         headers['Content-Type'] = 'application/json'
#         payload = json.dumps(parameters) if parameters else {}
#
#         response = requests.post(url, data=payload, headers=headers, timeout=self.config['timeout'])
#         return self.parse_response(response)
#
#     def downloadFile(self, url):
#         self.sema.acquire()
#         attempts = 0
#         try:
#             response = requests.get(url, stream=True)
#             disposition = response.headers['content-disposition']
#             filename = re.findall("filename=(.+)", disposition)[0].strip("\"")
#             print(f"Downloading {filename} ...\n")
#             if self.config_file_path != "" and self.download_filepath[-1] != "/":
#                 filename = "/" + filename
#             open(self.download_filepath + filename, 'wb').write(response.content)
#             print(f"Downloaded {filename}\n")
#             self.sema.release()
#
#
#         except Exception as e:
#             print(f"Failed to download from {url}. {e}. Will try to re-download.\n")
#             if attempts < 5:
#                 self.sema.release()
#                 self.runDownload(self.threads, url)
#                 attempts += 1
#
#     def parse_response(self, response):
#         result = response.json()
#
#         if not result or any(
#                 key not in result for key in ['errorCode', 'errorMessage', 'data', 'requestId', 'version']):
#             raise ApiException("Invalid response from API")
#
#         if result['errorCode']:
#             raise ApiException(f"{result['errorCode']}: {result['errorMessage']}")
#
#         return result
#
#     def runDownload(self, threads, url):
#         thread = threading.Thread(target=self.downloadFile, args=(url,))
#         threads.append(thread)
#         thread.start()
#
#     def search(self, scene_filter, dataset_name):
#         parameters = {
#             'sceneFilter': scene_filter,
#             'datasetName': dataset_name.lower(),
#             'maxResults': 100,
#             'startingNumber': 1,
#             'sortField': 'acquisitionDate',
#             'sortDirection': 'DESC'
#         }
#         # self.dispatch_request('scene-search', parameters)
#         request = self.dispatch_request('scene-search', parameters)
#         return request
#
#
# class ApiException(Exception):
#     pass
#
#
# class M2M:
#     def __init__(self,
#                  coordinates=None,
#                  config_file_path=cn.config_file_path,
#                  ):
#         if coordinates is None:
#             self.coordinates = sys.argv[1]
#         self.api_service = ApiService
#         self.config_file_path = config_file_path
#
#     def initialize_M2M(self):
#         # self.api_service = ApiService(self.config_file_path)
#         self.coordinates = sys.argv[1]
#         result = self.pull_data_from_api_service(self.coordinates, self.api_service)
#         return result
#
#     def execute_M2M(self):
#         result = self.initialize_M2M()
#         return result
#
#     def parse_results(self, datasets, coordinates, api_service):
#         # https://m2m.cr.usgs.gov/api/docs/example/download_data-py
#         # search document for : download datasets
#         results = []
#         for dataset in datasets['data']['results']:
#             if not dataset['displayId'].startswith('LC08_'):
#                 print(f"Found dataset {dataset['displayId']} but skipping it.\n")
#                 continue
#
#         if datasets['data']['recordsReturned'] > 0:
#             sceneIds = []
#             for result in datasets['data']['results']:
#                 # determine if centroid in result polygon
#                 centroid_in_polygon = M2M_API_Filters.filter_on_centroid(result, coordinates)
#                 if centroid_in_polygon == True:
#                     sceneIds.append(result['entityId'])
#             # find smallest cloud cover dataset
#             if len(sceneIds) > 1:
#                 cloud_cover_dictionary = {}
#                 for result in datasets['data']['results']:
#                     cloud_cover_dictionary[result['entityId']] = result['cloudCover']
#
#                 minimum_cloud_cover = [min(cloud_cover_dictionary, key=cloud_cover_dictionary.get)]
#             if len(minimum_cloud_cover) == 1:
#                 sceneId = minimum_cloud_cover
#             else:
#                 # return first value in dictionary
#                 # https://stackoverflow.com/questions/21930498/how-to-get-the-first-value-in-a-python-dictionary
#                 sceneId = cloud_cover_dictionary[0]
#                 pass
#
#             # find download options for these scenes
#             payload = {'datasetName': 'landsat_ot_c2_l2', 'entityIds': sceneId}
#             downloadOptions = api_service.dispatch_request('download-options', payload)
#
#             downloads = []
#             for product in downloadOptions['data']:
#                 # Make sure product is available for the scene
#                 if product['available'] == True:
#                     downloads.append({'entityId': product['entityId'],
#                                       'productId': product['id']})
#             # did we find products?
#             if downloads:
#                 requestDownloadCount = len(downloads)
#                 # set a label for the download request
#                 label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
#                 payload = {'downloads': downloads,
#                            'label': label
#                            }
#                 # Call the downloads to get the direct download urls
#                 requestResults = api_service.dispatch_request('download-request', payload)
#
#                 # Call the download retrieve method to get download that is immediately available for download
#                 if requestResults['data']['preparingDownloads'] is not None and len(
#                         requestResults['data']['preparingDownloads']) > 0:
#                     payload = {'label': label}
#                     moreDownloadUrls = api_service.dispatch_request('download-retrieve', payload)
#
#                     downloadIds = []
#
#                     for download in moreDownloadUrls['available']:
#                         if str(download['downloadID']) in requestResults['newRecords'] or str(download['downloadId']):
#                             downloadIds.append(download['downloadId'])
#                             api_service.runDownload(api_service.threads, download['url'])
#                 else:
#                     # Get all available downloads
#                     for download in requestResults['data']['availableDownloads']:
#                         api_service.runDownload(api_service.threads, download['url'])
#             else:
#                 results.append("Search found no results.\n")
#
#         results.append("Downloading files... Please do not close the program\n")
#         for thread in api_service.threads:
#             thread.join()
#
#         results.append("Complete Downloading")
#
#         return results
#
#     def pull_data_from_api_service(self, coordinates, api_service):
#         # api_service.load_config()
#         if api_service.authenticate:
#             coordinates_list = coordinates.split(',')
#             coordinates_float = [float(i) for i in coordinates_list]
#             rectangle = [[coordinates_float[i], coordinates_float[i + 1]] for i in range(0, len(coordinates_float), 2)]
#             # rectangle = list(zip(coordinates_float[::2], coordinates_float[1::2]))
#
#             results = api_service.search(self,
#                                          scene_filter=M2M_API_Filters.create_scene_filter(rectangle)[0],
#                                          dataset_name='landsat_ot_c2_l2')
#
#             # print(results)
#             print("Found ", len(results), " datasets\n")
#             filtered_results = self.parse_results(results, coordinates, api_service)
#
#             # log out so the API key cannot be used anymore
#             if api_service.dispatch_request(self, 'logout') is None:
#                 print("Logged Out\n\n")
#             else:
#                 print("Logout Failed\n\n")
#         else:
#             filtered_results = 'M2M API_Service did not authenticate'
#         return filtered_results
#
#
# # Example usage:
# # config_file_path = cn.config_file_path
# # api_service = ApiService(config_file_path)
# # # coordinates = cn.coordinates
# # coordinates = sys.argv
#
# def main():
#     apis = ApiService()
#     apis.execute_ApiService()
#     m2ma = M2M(sys.argv[1])
#     result = m2ma.execute_M2M()
#     return result
#
#
# if __name__ == '__main__':
#     main()

