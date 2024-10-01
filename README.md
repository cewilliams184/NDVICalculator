Purpose: Calculate NDVI of a selected area. Landsat Collection 2 Level 2 satellite inagery is used to calculate the NDVI of a selected area. A raster of the caluclated NDVI, the mean and standard NDVI valeus are also returned and displayed in the web application.
Process Kick off: the process starts when an event listener is activated from the NDVI web application when a rectangle is drawn in the web app by a user. The rectangles coordinates are fed to the NDVI_Calcualtor script as inputs for the proces

Steps: 
1. The process starts at the script: NDVI_Calculator 
2. The NDVI_Calculator calls the M2M_API.py which uses user-defined coordinate pairs to filter scenes in the EROS M2M API with the purpose of downloading the latest landsat-2 dataset
3. The M2M_API.py makes use of functions defined in M2M_API_Filter to filter the scenes by location and time (data created within the last month)
4. Once the M2M_API.py has finished running the NDVI calculations are run
5. The outputs are image files (NIR and R rasters) and the average NDVI value for the user selected area (polygon/ coordinate pairs)


