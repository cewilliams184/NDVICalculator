Project: The NDVI Calculator is one piece of a larger project that explores a changing landscape in the City of Raleigh. Another piece of the project can be seen here in an <a href="https://experience.arcgis.com/experience/0e82a0e3dc704acabd5f122c5d1545dd/" target="_blank"><b>experience builder app</b></a>  that shows the changes in NDVI in the City of Raleigh in 2013. 


Purpose: Calculate NDVI of a selected area. Landsat Collection 2 Level 2 satellite imagery is used to calculate the NDVI of a selected area. A raster of the calculated NDVI, the mean and standard NDVI values are also returned and displayed in the web application. 
Process Kick off: the process starts when an event listener is activated from the NDVI web application when a rectangle is drawn in the web app by a user. The rectangles coordinates are fed to the NDVI_Calculator script as inputs for the process.

Steps: 
1. The process starts at the script: NDVI_Calculator 
2. The NDVI_Calculator calls the M2M_API.py which uses user-defined coordinate pairs to filter scenes in the EROS M2M API with the purpose of downloading the latest landsat-2 dataset
3. The M2M_API.py makes use of functions defined in M2M_API_Filter to filter the scenes by location and time (data created within the last month)
4. Once the M2M_API.py has finished running the NDVI calculations are run
5. The outputs are image files (NIR and R rasters) and the average NDVI value for the user selected area (polygon/ coordinate pairs)


