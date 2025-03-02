# Name: NDVI_Calcualtor_For_ExperienceBuiilder
# Author : Chantel Williams
# Start Date : 12/6/2024
# Purpose: create class that calculates NDVI from landsat raster files downloaded from Earth Explorer using Landsat Collection 2 data bands 4 and 5
# Tutorials Used:

#iterate through folder of landsat c2 data sorted into folders by year
    #reproject each image --> WGS84 WKID: 3857
        #output name datecollectecd_P
        #bilinearinterpolation
    #calcualte NDVI=(B5-B4)/(B5+B4) with raster calcualtor or use arcpy NDVI tool
    #add NDVI path to a list
#iterate through list of NDVI paths
    #extract NDVI by Raleigh Mask
    #use statistics to add: mean, min, and max by id (date) toi a table

#calculate Mean, min, max/year in table
#publish each layer as a tiled imagery layer
