# Name: NDVI_Calculations
# Author : Chantel Williams
# Start Date : 7/27/2024
# Purpose: create flexible class that calculates NDVI from landsat raster files
# Tutorials Used:
from datetime import datetime

import matplotlib.pyplot as plt
import json
import geopandas
import glob
import numpy
import os
from osgeo import gdal
import pathlib

import shapely.geometry
from PIL import Image
import pyproj
import rasterio
from rasterio.mask import mask
from rasterio.windows import get_data_window, transform, Window
from rasterio.crs import CRS
from rasterio.warp import reproject, Resampling
from rasterio.plot import show
import rioxarray
from shapely.geometry import Polygon
from shapely.ops import transform
from shapely.geometry import mapping
from shapely.geometry import box

import zipfile
import sys
import tarfile

import constants as cn
# import M2M_API_Raleigh as M2M_API
import M2M_API
from constants import output_path


# convert .tif to a numpy array

def getFeatures(gdf):
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


class NDVI_Calculations():
    def __init__(self,
                 # near_infrared_band=cn.near_infrared_band,
                 # near_infrared_band=None,
                 output_path=cn.output_path,
                 project_path=cn.project_path,
                 # red_band=cn.red_band,
                 result_path=cn.result_path
                 ):
        # self.near_infrared_band = near_infrared_band
        self.near_infrared_band = None
        self.output_path = output_path
        self.project_path = project_path
        self.red_band = None
        self.result_path=result_path
        self.downloaded_file = self.extracted_file()

    def extracted_file(self):
        if not self.file_downloaded_recently()[0]:
            self.downloaded_file = M2M_API.main()
            extracted_files = self.extract_downloaded_file()
        else:
            extracted_files= self.file_downloaded_recently()[1]
        return extracted_files

    def initialize_NDVI_Calculations(self):
        #check if file has been downloaded in past hour


        if self.downloaded_file != None:
            self.near_infrared_band = self.set_infrared_and_red_band_variables(self.downloaded_file)[0]
            self.red_band = self.set_infrared_and_red_band_variables(self.downloaded_file)[1]
            ndvi = self.calculate_ndvi()
        else:
            print("The NDVI value could not be calculated because no files were found for the selected area")
        return ndvi

    def execute_NDVI_Calculations(self):


        result = self.initialize_NDVI_Calculations()
        return result

    def file_downloaded_recently(self):
        latest_downloaded_file_directory = os.path.join(self.project_path, 'Data')
        tar_files = glob.glob(f"{latest_downloaded_file_directory}/*.tar")
        tar_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_file = datetime.fromtimestamp(os.path.getmtime(tar_files[0]))
        # if (os.path.getmtime(latest_file) - datetime.now()).seconds < 3600: #300seconds = 5min, 3600seconds = 1hour
        if (latest_file - datetime.now()).days < 1:  # 300
            download_new_file = True
        else:
            download_new_file = False
        return download_new_file, tar_files[0][:-4]

    def extract_downloaded_file(self):
        """ parse data folder for latest near infrared downloaded"""
        latest_downloaded_file_directory = glob.glob(f"{os.path.join(self.project_path, 'Data')}/*.tar")
        extracted_files = None
        for file in latest_downloaded_file_directory:
            if file.endswith('.tar'):#extract compressed .tar files
                    if not os.path.exists(file[:-4]):
                        compressed_file = tarfile.open(file)
                        compressed_file.extractall(
                            os.path.join(self.project_path, 'Data', f'{file[:-4]}'),
                            filter='data')
                        compressed_file.close()
                        extracted_files = file[:-4]
                    else:
                        result = 'File has already been extracted'
            else: #create list of files in uncompressed folder
                #grab latest extracted file
                extracted_files = os.listdir(file[:-4])
                latest_downloaded_file_directory = glob.glob(f"{os.path.join(self.project_path, 'Data')}/*.tar")
        return extracted_files

    def set_infrared_and_red_band_variables(self, extracted_files):
        # enter directory and pull out file ending in 'B5.tif'
        latest_downloaded_files = os.listdir(extracted_files)
        for file in latest_downloaded_files:
            if file[-6:] == 'B4.TIF':
                latest_red_band = os.path.join(extracted_files,file)
            if file[-6:] == 'B5.TIF':
                latest_near_infrared = os.path.join(extracted_files,file)

        return latest_near_infrared, latest_red_band

    def reproject_raster_to_find_bounds_and_center_in_degrees(self):
        # with rasterio.open(self.near_infrared_band) as src:
        #     src_transform = src.transform
        #
        #     dst_transform = src_transform*rasterio.Affine.translation( -src.width/2.0, -src.height/2.0)*rasterio.Affine.scale(2.0)
        #     data = src.read()
        #     kwargs=src.meta
        #     kwargs['transform'] = dst_transform
        #
        #     with rasterio.open(f'{os.path.dirname(self.near_infrared_band)}/zoomed-out.tif', 'w', **kwargs) as dst:
        #         for i, band in enumerate(data, 1):
        #             dest = numpy.zeros_like(band)
        #
        #             reproject(
        #                 source=rasterio.band(src,i),
        #                 destination=rasterio.band(dst,i),
        #                 src_transform=src_transform,
        #                 src_crs=f"EPSG:{int(src.crs.data['init'].split(":")[1])}",
        #                 dst_transform=dst_transform,
        #                 dst_crs="EPSG:3857",
        #                 resampling=Resampling.nearest)
        #             dst.write(dest, indexes=i)

        # red_band = rioxarray.open_rasterio(self.red_band,
        #                                    masked=True).squeeze()
        red_band = rioxarray.open_rasterio(self.red_band,
                                           masked=True)
        # red_band_crs = red_band.rio.crs
        # crs_wgs84 = CRS.from_string(value='EPSG:4326')
        red_band_wgs84 =red_band.rio.reproject("EPSG:4326")
        # red_band_new_crs = red_band_wgs84.rio.crs
        bounds = red_band_wgs84.rio.bounds()
        # transform_bounds = red_band.rio.transform_bounds(dst_crs="EPSG:4326", recalc=True)
        raster_transform = red_band_wgs84.rio.transform()
        return bounds, raster_transform

    def ndvi_values_to_RGB_values(self, ndvi):
        """ converts NDVI float values to predefined color ramp RGB values """
        # ndvi_rgb = numpy.where((ndvi[0]<-0.5), 12, ndvi[0])
        condition_list = [ndvi < -0.5,
                          (ndvi >= -0.5) & (ndvi <0),
                          (ndvi >= 0) & (ndvi < 0.1),
                          (ndvi >= 0.1) & (ndvi < 0.1),
                          (ndvi >= 0.2) & (ndvi < 0.2),
                          (ndvi >= 0.3) & (ndvi < 0.3),
                          (ndvi >= 0.4) & (ndvi < 0.4),
                          (ndvi >= 0.5) & (ndvi < 0.5),
                          (ndvi >= 0.6) & (ndvi <= 1.0)
                          ]
        color_list = [0,
                      25,
                      50,
                      75,
                      100,
                      125,
                      150,
                      175,
                      200]
        # color_list = ['#0c0c0c',
        #               '#eaeaea',
        #               '#ccc682',
        #               '#91bf51',
        #               '#70a33f',
        #               '#4f892d',
        #               '#306d1c',
        #               '#0f540a',
        #               '#004400']
        ndvi_rgb = numpy.select(condition_list, color_list, default = 0)


        return ndvi_rgb


    def calculate_ndvi(self):
        """ calculate NDVI raster from infrared and red bands"""
        near_infrared_band_rasterio_open = rasterio.open(self.near_infrared_band, mask=False)
        red_band_rasterio_open = rasterio.open(self.red_band, mask=False)
        projected_bounds, raster_transform = self.reproject_raster_to_find_bounds_and_center_in_degrees()
        # output_name = f'{os.path.split(near_infrared_band_rasterio_open.files[0])[1][:-4]}.jpg' #jpg does not suport RGBA A for transparency #does not save values properly
        # output_name = f'{os.path.split(near_infrared_band_rasterio_open.files[0])[1][:-4]}.png' #does not save values properly
        output_name = f'{os.path.split(near_infrared_band_rasterio_open.files[0])[1][:-4]}.png'

        near_infrared_band_rasterio_read = near_infrared_band_rasterio_open.read()  # open and read as numpy array
        red_band_rasterio_read = red_band_rasterio_open.read()

        # show(near_infrared_band_rasterio_read)
        # show(red_band_rasterio_read)

        near_infrared_band_rasterio_float = near_infrared_band_rasterio_read.astype(float)
        red_band_rasterio_float = red_band_rasterio_read.astype(float)

        numpy.seterr(divide='ignore', invalid='ignore')  # allow 0 division in numpy
        check = numpy.logical_or(near_infrared_band_rasterio_float > 0,
                                 red_band_rasterio_float > 0)  # apply filter on values > 0 to be used to calculate NDVI

        ndvi = numpy.where(check, (near_infrared_band_rasterio_float - red_band_rasterio_float) / (
                    near_infrared_band_rasterio_float + red_band_rasterio_float), 0)
        ndvi_rgb = self.ndvi_values_to_RGB_values(ndvi)
        image_center = f"{(projected_bounds[2] +projected_bounds[0])/2., (projected_bounds[3]+projected_bounds[1])/2.}"
        # show(ndvi, cmap='summer')

        #convert numpy array to a rasterio dataset
        profile = {
            'driver': 'GTiff',
            'height': ndvi.shape[1],
            'width': ndvi.shape[2],
            'count': ndvi.shape[0],
            'dtype': ndvi.dtype,
            'crs' : "EPSG:3857",
            'transform': raster_transform

        }
        with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi.tif'), 'w', **profile) as dst:
            dst.write(ndvi)

        ndvi_tiff = rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi.tif'), mask=False)
        #clip (mask) resulting raster to bounds of drawn rectangle
        # coordinates_list = sys.argv[1].split(',')
        # coordinates_float = [float(i) for i in coordinates_list]
        # bbox = box(projected_bounds[0],projected_bounds[1], projected_bounds[2], projected_bounds[3])
        # bbox = box(coordinates_float[0],coordinates_float[1],coordinates_float[2],coordinates_float[3])
        # geo = geopandas.GeoDataFrame({'geometry':bbox}, index=[0])
        # coords=getFeatures(geo)
        # ndvi_read = ndvi_tiff.read()
        # out_image, out_transform = mask(dataset=ndvi_tiff, shapes=coords, crop=True, filled=False)
        #
        # with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi.tif')) as src:
        #     cropped_profile = src.profile.copy()
        #     data_window = get_data_window(src.read(masked=True))
        #     data_transform = transform(data_window, src.transform)
        #     cropped_profile.update(
        #         transform=data_transform,
        #         height=data_window.height,
        #         width=data_window.width
        #     )
        #     data = src.read(window=data_window)
        #     write_window = rasterio.windows.from_bounds(coordinates_float[0], coordinates_float[1], coordinates_float[2],
        #                                           coordinates_float[3], raster_transform)
        #     # write_window = Window.from_slices((2540, 2584),(2540, 2584))
        # with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_clipped.png'), 'w', **cropped_profile) as dst:
        #     dst.write(data, window=write_window)
        #
        # ndvi_tiff_clipped = rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_clipped.png'))


        #save ndvi files to display on web app

        # ndvi_rioxarray = rioxarray.open_rasterio(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi.tif'))
        # ndvi_3857 = ndvi_rioxarray.rio.reproject("EPSG:3857")
        # with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_3857.tif'), 'w', **profile) as dst:
        #     dst.write(ndvi_3857)

        # with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_3857.tif'), **profile) as src:
        # with rasterio.open(os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_3857.tif')) as src:
        #     coordinates_list = sys.argv[1].split(',')
        #     coordinates_float = [float(i) for i in coordinates_list]
        #     polygon = Polygon(list(zip(coordinates_float[0::2], coordinates_float[1::2])))
        #     wgs84 = pyproj.CRS('EPSG:4326')
        #     proj_3857 = pyproj.CRS('EPSG:3857')
        #     project =  pyproj.Transformer.from_crs(wgs84, proj_3857, always_xy=True).transform
        #     polygon_bounds_3857 = transform(project, polygon)
        #     # polygon_3857 = Polygon((polygon_bounds_3857.bounds[0],polygon_bounds_3857.bounds[1]), (polygon_bounds_3857.bounds[2],polygon_bounds_3857.bounds[1]), (polygon_bounds_3857.bounds[2],polygon_bounds_3857.bounds[3]), (polygon_bounds_3857.bounds[0],polygon_bounds_3857.bounds[3]))
        #     # polygon_geometry = [{'type':'Polygon', 'coordinates':polygon_3857}]
        #     bbox = box(polygon.bounds[0],polygon.bounds[1],polygon.bounds[2],polygon.bounds[3])
        #     bbox = box(polygon_bounds_3857.bounds[0],polygon_bounds_3857.bounds[1], polygon_bounds_3857.bounds[2], polygon_bounds_3857.bounds[3])
        #     geo = geopandas.GeoDataFrame({'geometry':bbox}, index=[0])
        #     coords=getFeatures(geo)
        #
        #     out_image, out_transform = mask(src, coords, invert=True)
        #
        #     cropped_profile = src.profile.copy()
        #     data_window = get_data_window(out_image.read(masked=True))
        #     # data_transform = transform(data_window, src.transform)
        #     cropped_profile.update(
        #         transform=out_transform,
        #         height=data_window.height,
        #         width=data_window.width
        #     )
        #     data = src.read(window=data_window)
        #     data = data[data<=5]

        # #gdal translate
        # input_ndvi = os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi.tif')
        # output_tif = os.path.join(os.path.dirname(self.near_infrared_band), 'ndvi_3857.tif')
        # coordinates_list = sys.argv[1].split(',')
        # coordinates_float = [float(i) for i in coordinates_list]
        # polygon = Polygon(list(zip(coordinates_float[0::2], coordinates_float[1::2])))
        # # window = (polygon.bounds[0], polygon.bounds[1], polygon.bounds[2], polygon.bounds[3])
        # bbox = box(polygon.bounds[0], polygon.bounds[1], polygon.bounds[2], polygon.bounds[3])
        #
        # #3857
        # wgs84 = pyproj.CRS('EPSG:4326')
        # proj_3857 = pyproj.CRS('EPSG:3857')
        # project =  pyproj.Transformer.from_crs(wgs84, proj_3857, always_xy=True).transform
        # polygon_3857 = transform(project, polygon)
        # # polygon_3857 = Polygon((polygon_bounds_3857.bounds[0],polygon_bounds_3857.bounds[1]), (polygon_bounds_3857.bounds[2],polygon_bounds_3857.bounds[1]), (polygon_bounds_3857.bounds[2],polygon_bounds_3857.bounds[3]), (polygon_bounds_3857.bounds[0],polygon_bounds_3857.bounds[3]))
        # window = (polygon_3857.bounds[0],polygon_3857.bounds[1],polygon_3857.bounds[2],polygon_3857.bounds[3])
        # bbox = box(polygon_3857.bounds[0], polygon_3857.bounds[1], polygon_3857.bounds[2],
        #            polygon_3857.bounds[3])
        #
        # out_image = gdal.Translate(output_tif, input_ndvi, projWin=window)
        # im = Image.fromarray(out_image)

        im = Image.fromarray(ndvi_rgb[0])
        im.show()
        image_size = im.size
        # im = im.resize((3000, 2949), Image.Resampling.NEAREST)
        if im.mode != 'RGB':
            im = im.convert('RGB')
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        im.save(os.path.join(self.output_path, output_name))
        #TODO: save infrared and red images as .pngs to be pulled into web app for viewing

        #TODO: save values in a database
        # print(f"NDVI mean: {ndvi.mean()}")
        # print(f"NDVI standard deviation: {ndvi.std()}")
        file_name = self.downloaded_file.split('\\')[-1:][0] + '_SR_B5.jpeg'
        # result = f"NDVI Mean: {ndvi.mean()}, {ndvi.std()}, {os.path.join(self.downloaded_file, file_name)}, {projected_bounds},{image_center}"
        result = f"NDVI Mean: {ndvi.mean()}, {ndvi.std()}, {os.path.join(output_path, output_name)}, {projected_bounds},{image_center}"
        #TODO: determine how to display resulting NDVI as a layer on the leaflet map
        return result


def main():
    # M2M_API.main() # search for files based
    ndvic = NDVI_Calculations()
    ndvi = ndvic.execute_NDVI_Calculations()
    print(ndvi)
    return

if __name__ == "__main__":
    main()
