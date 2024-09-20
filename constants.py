import os

#project info
project_path = r"C:\Users\cewil\Documents\GitHub\NDVICalculator"

#input files
near_infrared_band= os.path.join(project_path, r"Data\LC09_L2C2_20240722\LC08_L2SP_016035_20240715_20240722_02_T1_SR_B5.tif") #band 5 L2C2
red_band= os.path.join(project_path, r"Data\LC09_L2C2_20240722\LC08_L2SP_016035_20240715_20240722_02_T1_SR_B4.tif")  #band 4 L2C2

#raster_name
raster_name=os.path.split(near_infrared_band)[-1].split('_')[-5]

#output path
output_path= os.path.join(project_path, 'Results')