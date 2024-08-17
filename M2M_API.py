# use USGS Machine-2-Machine (M2M) API to access, fileter, and download data
# Chantel Williams
# August 2024

import datetime
import requests
import json
import M2M_constants as cn
import M2M_API_Filters


class ApiService:
    def __init__(self, config_file_path):
        self.load_config(config_file_path)
        self.api_key = None
        self.contact_id = 0

    def load_config(self, config_file_path):
        with open(config_file_path, 'r') as config_file:
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

    def parse_response(self, response):
        result = response.json()

        if not result or any(
                key not in result for key in ['errorCode', 'errorMessage', 'data', 'requestId', 'version']):
            raise ApiException("Invalid response from API")

        if result['errorCode']:
            raise ApiException(f"{result['errorCode']}: {result['errorMessage']}")

        return result

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


def parse_results(datasets):
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
            centroid_in_polygon = M2M_API_Filters.filter_on_centroid(result)
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
            # sceneId = cloud_cover_dictionary[0]
            pass

        # find download options for these scenes
        payload = {'datasetName': 'landsat_ot_c2_l2', 'entityIds': sceneId}
        # downloadOptions = se

    return


# Example usage:
config_file_path = r'C:\PersonalProject\NDVICalculator\Data\config.json'
api_service = ApiService(config_file_path)

if api_service.authenticate():
    results = api_service.search(scene_filter=M2M_API_Filters.create_scene_filter(r"C:\PersonalProject\web-projects"
                                                                                  r"\PocosinWildlifeRefuge\data\Shapefiles"
                                                                                  r"\Pocosin_FWS\Pocosin_FWS_AOI_WGS84.shp")[
        0],
                                 dataset_name='landsat_ot_c2_l2',
                                 )
    # print(results)
    print("Found ", len(results), " datasets\n")
    parse_results(results)


