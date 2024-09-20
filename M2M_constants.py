import datetime
import threading

download_path = r'C:\Users\cewil\Documents\GitHub\NDVICalculator\Data'
config_file_path = r'C:\Users\cewil\Documents\GitHub\NDVICalculator\Data\config.json'
maxthreads = 5 #threads count for downloads
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")