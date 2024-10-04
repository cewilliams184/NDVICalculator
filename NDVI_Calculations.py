# Name: NDVI_Calculations
# Author : Chantel Williams
# Start Date : 7/27/2024
# Purpose: create flexible class that calculates NDVI from landsat raster files
# Tutorials Used:

import matplotlib.pyplot as plt
import numpy
import os
from PIL import Image
import rasterio
from rasterio.plot import show
import zipfile
import sys
import tarfile

import constants as cn
import M2M_API as M2M_API


# convert .tif to a numpy array

class NDVI_Calculations():
    def __init__(self,
                 # near_infrared_band=cn.near_infrared_band,
                 # near_infrared_band=None,
                 results_path=cn.output_path,
                 project_path=cn.project_path,
                 # red_band=cn.red_band,
                 ):
        # self.near_infrared_band = near_infrared_band
        self.near_infrared_band = None
        self.project_path = project_path
        self.red_band = None
        self.results_path = results_path

    def initialize_NDVI_Calculations(self):
        extracted_files = self.locate_latest_near_infrared_band_downloaded()
        if extracted_files != None:
            self.near_infrared_band = self.set_infrared_and_red_band_variables(extracted_files)[0]
            self.red_band = self.set_infrared_and_red_band_variables(extracted_files)[1]
            ndvi = self.calcualte_NDVI()
        else:
            print("The NDVI value could not be calculated because no files were found for the selected area")
        return ndvi

    def execute_NDVI_Calculations(self):
        result = self.initialize_NDVI_Calculations()
        return result

    def locate_latest_near_infrared_band_downloaded(self):
        """ parse data folder for latest near infrared downloaded"""
        global latest_near_infrared, latest_red_band, extracted_files
        data_folder = os.path.join(self.project_path, 'Data')
        downloaded_files = []
        with os.scandir(data_folder) as it:
            for entry in it:
                if not entry.name.endswith('.json'):
                    downloaded_files.append(entry.path)
        downloaded_files.sort(key=os.path.getctime, reverse=True)

        latest_downloaded_file_directory = downloaded_files
        extracted_files = None
        for file in latest_downloaded_file_directory:
            if file.endswith('.tar'): #extract compressed .tar files
                if file[:-4] not in latest_downloaded_file_directory:
                    compressed_file = tarfile.open(file)
                    compressed_file.extractall(os.path.join(self.project_path, 'Data', downloaded_files[0][:-4]))
                    compressed_file.close()
                    extracted_files = file[:-4]
            else: #create list of files in uncompressed folder
                extracted_files = file
                break
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

    def calcualte_NDVI(self):
        """ calculate NDVI raster from infrared and red bands"""
        near_infrared_band_rasterio_open = rasterio.open(self.near_infrared_band)
        red_band_rasterio_open = rasterio.open(self.red_band)

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
                    near_infrared_band_rasterio_float + red_band_rasterio_float), -999)
        # show(ndvi, cmap='summer')

        #save ndvi files to display on web app
        im = Image.fromarray(ndvi[0])
        if im.mode != 'L':
            im = im.convert('L')
        if not os.path.exists(self.results_path):
            os.makedirs(self.results_path)
        im.save(os.path.join(self.results_path,output_name))
        #TODO: save infrared and red images as .pngs to be pulled into web app for viewing

        #TODO: save values in a database
        print(f"NDVI mean: {ndvi.mean()}")
        print(f"NDVI standard deviation: {ndvi.std()}")
        result = {"NDVI_mean": str(ndvi.mean()), "NDVI_standard_deviation": str(ndvi.std())}
        #TODO: determine how to display resulting NDVI as a layer on the leaflet map
        return result


def main():
    M2M_API.M2M(sys.argv)  # search for files based
    NDVIC = NDVI_Calculations()
    NDVIC.execute_NDVI_Calculations()


if __name__ == "__main__":
    main()
