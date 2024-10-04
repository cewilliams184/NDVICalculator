import datetime
import threading
import sys

download_path = r'C:\Users\cewil\Documents\GitHub\NDVICalculator\Data'
config_file_path = r'C:\Users\cewil\Documents\GitHub\NDVICalculator\Data\config.json'
# coordinates = [[35.95397342058534, -76.64996823193624], [35.95397342058534, -75.97293004875567], [35.52305406304399, -75.97293004875567], [35.52305406304399, -76.64996823193624], [35.95397342058534, -76.64996823193624]]
coordinates = sys.argv
maxthreads = 5 #threads count for downloads
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")