import datetime
import threading

download_path = r'C:\PersonalProject\NDVICalculator\Data'
maxthreads = 5 #threads count for downloads
sema = threading.Semaphore(value=maxthreads)
label = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")