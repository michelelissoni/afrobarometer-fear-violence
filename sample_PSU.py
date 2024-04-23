##########################################################################################################
#
# python sample_PSU.py [-k] [-p] 
#
# This script samples the PSU level variables (except for the ecological zones and the urban/rural binary)
# over the four countries, saving the result to a CSV file.
#
# Depending on the arguments provided to the script in the command line, the operation can be performed
# over different spatial units:
#
# 	no arguments: the operation is performed with the PSU polygons
#	
#	-k: the script loops over the fixed-distance buffers
#
#	-p: the script loops over the percent-area buffers 
#
# This script uses the Google Earth Engine Python API and thus requires a GEE account. 
# As uploading the spatial unit shapefiles through the script would be too time-consuming, you should
# upload them manually before running this code (look for them in the GIS subfolders). Then, set your GEE 
# path here below:
#
GEE_path =
# 
##########################################################################################################

import sys
import ee
import numpy as np
import pandas as pd
import geopandas as gpd
import netCDF4
import rasterio
from scipy.stats import gaussian_kde
from shapely.geometry import mapping
from datetime import datetime, date, timedelta
from rasterio.transform import from_origin, rowcol
from rasterio.features import geometry_mask
import time

# Reading command line arguments
arg_len = len(sys.argv)

poly_buffer=False
if(arg_len==1):
	poly_buffer=True
elif(sys.argv[1]=="-p"):
	percent_buffer=True
elif(sys.argv[1]=="-k"):
	percent_buffer=False

# Triggering the Google Earth Engine authentication flow
ee.Authenticate()
ee.Initialize()

win_len=2 # Time interval (in years) considered for the variables
lta_start=2000 # Start of the long-term average

country_codes={'kenya': 'KEN', 'nigeria': 'NIG', 'ethiopia': 'ETH', 'southafrica': 'SAF'}
country_names={'kenya': 'Kenya', 'nigeria': 'Nigeria', 'ethiopia': 'Ethiopia', 'southafrica': 'South Africa'}

# Temporal coordinates of the Afrobarometer coordinates 
country_years={'kenya': 2019, 'nigeria': 2020, 'ethiopia': 2019, 'southafrica': 2021}
country_months={'kenya': 8, 'nigeria': 1, 'ethiopia': 12, 'southafrica': 4}

# Lists of buffers
percents=[200,300,400,500,750,1000]
kms=[1,2,5,10,20,50]

if(poly_buffer):
	buffer_strs=['poly']
elif(percent_buffer):
	buffer_strs=[str(percent) for percent in percents]
else:
	buffer_strs=[str(km)+'km' for km in kms]

# Looping over the countries
for country in list(country_codes.keys()):

	# Looping over the buffers
	for buffer_str in buffer_strs:
	
		print(country, buffer_str)

		country_code=country_codes[country]
		country_year=country_years[country]
		country_month=country_months[country]
		country_name=country_names[country]
		month_start = (country_month % 12) + 1
		year_start = country_year - (country_month!=12) - (win_len-1)

		buff_folder = 'GIS/'+country_code+'/'
		dest_folder = 'Afrobarometer/'+country_code+'/'
		
		# Reading the shapefile 
		if(poly_buffer):
			buffer_file=country_code+'_R8_PSU_polys'
		else:
			buffer_file=country_code+'_R8_PSU_'+buffer_str+'_buffers'

		buffers = gpd.read_file(buff_folder+buffer_file+'.shp')

		buffers['geometry'] = buffers['geometry'].to_crs(epsg=4326)
		feat_num=len(buffers)

		## NIGHTTIME LIGHTS

		buffers_ee = ee.FeatureCollection(GEE_path+buffer_file) # Accessing the shapefile uploaded on GEE

		dataset = ee.ImageCollection('NOAA/VIIRS/DNB/ANNUAL_V21').filter(ee.Filter.date(str(country_year)+'-01-01', str(country_year+1)+'-01-01'))

		light_image = dataset.select('maximum').first()
		crs = light_image.projection()

		feature_num=buffers_ee.size()

		features=buffers_ee.toList(feature_num)
		
		# This function is mapped over all the spatial unit polygons and finds the mean value in each one
		def sampler(feature):

			geom = ee.Feature(feature).geometry().transform(crs,ee.ErrorMargin(10))

			meanDict2 = light_image.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom)

			light_value1=ee.Number(meanDict2.get('maximum'))

			centroid=geom.centroid(1)
			sample_size = ee.Number(light_image.sample(centroid, 464).size())

			light_value2 = ee.Algorithms.If(sample_size, ee.Number(light_image.sample(centroid, 464).first().get('maximum')), ee.Number(0))

			return(ee.Algorithms.If(light_value1, light_value1, light_value2))

		meanList=buffers_ee.toList(buffers_ee.size()).map(sampler)

		light_values = list(meanList.getInfo())

		light_df = pd.DataFrame({'nighttime': light_values})
		light_df['EA_Num']=buffers['EA_Num']
		light_df['EA_Num']=light_df['EA_Num'].astype('int64')
		
		print('nighttime')

		## LAND SURFACE TEMPERATURE

		temp_dataset = ee.ImageCollection('MODIS/061/MOD11A1').select(['LST_Day_1km'])
		crs = temp_dataset.first().projection()

		first_date = datetime(year_start, month_start, 1, 0, 0)

		date_list = ee.List([datetime(year, month_start, 1, 0, 0).strftime('%Y-%m-%d') for year in range(lta_start,year_start+1)])

		# This function creates the bi-yearly means
		def year_mapper(date_str):
			startDate = ee.Date(date_str)
			endDate = startDate.advance(win_len, 'year')
			biYearlyCollection = temp_dataset.filterDate(startDate, endDate)

			biYearlyMean = biYearlyCollection.mean();

			yearProperties = {
			'system:time_start': startDate.millis(),
			'system:time_end': endDate.millis()
			}

			return biYearlyMean.set(yearProperties) 

		yearAverages = ee.ImageCollection.fromImages(date_list.map(year_mapper))
		
		# Long-term average and standard deviation

		ltaDate1 = ee.Date(date_list.get(0))
		ltaDate2 = ee.Date(date_list.reverse().get(0)).advance(-win_len+1, 'year')
		ltaAverages = yearAverages.filterDate(ltaDate1, ltaDate2)

		ltaMean = ltaAverages.mean()

		ltaStd = ltaAverages.reduce(ee.Reducer.stdDev())

		lastImg = yearAverages.sort('system:time_start',False).first()

		resImg = lastImg.subtract(ltaMean)
		anomImg = resImg.divide(ltaStd) # Standardized anomaly
		
		# This function is mapped over all the spatial unit polygons and finds the mean value in each one
		def sampler(feature):

			geom = ee.Feature(feature).geometry().transform(crs,ee.ErrorMargin(10))

			meanDict2 = anomImg.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom)

			anom_value1=ee.Number(meanDict2.get('LST_Day_1km'))

			centroid=geom.centroid(1)
			sample_size = ee.Number(anomImg.sample(centroid, 1000).size())
			
			# In case the polygon is too small to straddle a pixel, the nearest value to the centroid is used
			anom_value2 = ee.Algorithms.If(sample_size, ee.Number(anomImg.sample(centroid, 1000).first().get('LST_Day_1km')), ee.Number(0))

			return(ee.Algorithms.If(anom_value1, anom_value1, anom_value2))

		tempAnomList=buffers_ee.toList(buffers_ee.size()).map(sampler)
		
		tempAnom_values=tempAnomList.getInfo()

		light_df['LST_anoms']=tempAnom_values

		print('LST')

		## VEGETATION

		ndvi_dataset = ee.ImageCollection("MODIS/061/MOD13Q1").select(['NDVI'])
		crs = ndvi_dataset.first().projection()

		first_date = datetime(year_start, month_start, 1, 0, 0)

		date_list = ee.List([datetime(year, month_start, 1, 0, 0).strftime('%Y-%m-%d') for year in range(lta_start,year_start+1)])

		# This function creates the bi-yearly means
		def year_mapper(date_str):
			startDate = ee.Date(date_str)
			endDate = startDate.advance(1, 'year')
			biYearlyCollection = ndvi_dataset.filterDate(startDate, endDate)

			biYearlyMean = biYearlyCollection.mean();

			yearProperties = {
			'system:time_start': startDate.millis(),
			'system:time_end': endDate.millis()
			}

			return biYearlyMean.set(yearProperties) 

		yearAverages = ee.ImageCollection.fromImages(date_list.map(year_mapper))
		
		# Long-term average and standard deviation

		ltaDate1 = ee.Date(date_list.get(0))
		ltaDate2 = ee.Date(date_list.reverse().get(0)).advance(-win_len+1, 'year')
		ltaAverages = yearAverages.filterDate(ltaDate1, ltaDate2)

		ltaMean = ltaAverages.mean()

		ltaStd = ltaAverages.reduce(ee.Reducer.stdDev())

		lastImg = yearAverages.sort('system:time_start',False).first()

		resImg = lastImg.subtract(ltaMean)
		anomImg = resImg.divide(ltaStd) # Standardized anomaly

		# This function is mapped over all the spatial unit polygons and finds the mean value in each one
		def sampler(feature):

			geom = ee.Feature(feature).geometry().transform(crs,ee.ErrorMargin(10))

			meanDict2 = anomImg.reduceRegion(reducer=ee.Reducer.mean(), geometry=geom)

			anom_value1=ee.Number(meanDict2.get('NDVI'))

			centroid=geom.centroid(1)
			sample_size = ee.Number(anomImg.sample(centroid, 250).size())

			# In case the polygon is too small to straddle a pixel, the nearest value to the centroid is used 
			anom_value2 = ee.Algorithms.If(sample_size, ee.Number(anomImg.sample(centroid, 250).first().get('NDVI')), ee.Number(0))


			return ee.Algorithms.If(anom_value1, anom_value1, anom_value2)

		ndviAnomList=buffers_ee.toList(buffers_ee.size()).map(sampler)

		ndviAnom_values=ndviAnomList.getInfo()

		light_df['NDVI_anoms']=ndviAnom_values

		print('NDVI')

		## RAINFALL

		nc_file_path='TAMSAT/'+country+'_rainfall.nc'

		nc = netCDF4.Dataset(nc_file_path, 'r')
		time_values = nc.variables['time'][:]
		year_values = np.array([date.fromtimestamp(time_value).year for time_value in time_values])
		month_values = np.array([date.fromtimestamp(time_value).month for time_value in time_values])

		lon = nc.variables['lon'][:]
		lat = nc.variables['lat'][:]
		pixel_size_x = abs(lon[1] - lon[0])
		pixel_size_y = abs(lat[1] - lat[0])

		# Choose the upper-left corner coordinates
		upper_left_x = min(lon)
		upper_left_y = max(lat)

		transform = from_origin(upper_left_x, upper_left_y, pixel_size_x, pixel_size_y)

		data_values = np.array(nc.variables['rfe'][:])

		# Calculating the bi-yearly means

		biYearly_rasters = np.zeros((year_start+1-lta_start,len(lat),len(lon)))

		for year in range(lta_start,year_start+1):
		    
			time_mask = np.flatnonzero(np.logical_and(month_values==month_start, year_values==year))[0]+np.arange(win_len*12,dtype=int)

			biYearly_raster = np.sum(data_values[time_mask,:,:], axis=0)

			biYearly_rasters[year-lta_start,:,:]=biYearly_raster

		# Calcuating the standardized anomaly
		mean_raster = np.mean(biYearly_rasters[:-win_len,:,:], axis=0)
		std_raster = np.std(biYearly_rasters[:-win_len,:,:], axis=0)

		afb_raster = biYearly_rasters[-1,:,:]

		anom_raster = (afb_raster - mean_raster)/std_raster
		    
		# Finding the mean values within each polygon
		rfe_anoms = np.zeros(feat_num)
		    
		for index,row in buffers.iterrows(): 
			polygon = row['geometry']
		    
			poly_mask = geometry_mask([polygon], out_shape=(len(lat), len(lon)), transform=transform, invert=False)

			masked_data = np.ma.masked_array(anom_raster, poly_mask)
			if(np.ma.count(masked_data)==0):
				row,col=rowcol(transform, polygon.centroid.x, polygon.centroid.y)
				rfe_anoms[index]=np.nan_to_num(anom_raster[row,col], nan=0)
			else:
				rfe_anoms[index]=np.nanmean(masked_data)
				
			if(~np.isfinite(rfe_anoms[index])):
				print(rfe_anoms[index])
				rfe_anoms[index]=0
		    
		light_df['rfe_anoms']=rfe_anoms
		
		print('RFE')

		## ACLED
		
		# Code to create the ACLED kernel density and map them to TIF files
		'''
		acled_file='ACLED/2017-01-01-2024-03-05-Ethiopia-Kenya-Nigeria-South_Africa.csv'

		acled_df=pd.read_csv(acled_file)

		acled_df=acled_df.loc[acled_df['country']==country_name]
		acled_df['datetime']=pd.to_datetime(acled_df['event_date'], format='%d %B %Y')

		year_end = year_start + win_len
		start_date=datetime(year_start, month_start, 1,0,0,0)
		end_date=datetime(year_end, month_start, 1,0,0,0)

		acled_df = acled_df.loc[(acled_df['datetime'] >= start_date) & (acled_df['datetime'] < end_date),:]

		acled_df=acled_df.loc[acled_df['sub_event_type']!="Peaceful protest"]
		len_acled=len(acled_df)

		acled_data=gpd.GeoDataFrame(acled_df,geometry=gpd.points_from_xy(acled_df['longitude'],acled_df['latitude']), crs='EPSG:4326')

		# Extract the coordinates from the GeoDataFrame
		x = acled_data.geometry.x
		y = acled_data.geometry.y

		# Set up raster grid parameters
		resolution = 8.98E-3 # About 1 km; adjust as needed
		grid_y, grid_x = np.mgrid[lower_right_y:upper_left_y:resolution, upper_left_x:lower_right_x:resolution]
		grid_points = np.vstack([grid_x.ravel(), grid_y.ravel()])

		# Calculate the kernel density estimate
		kde = gaussian_kde(np.vstack([x,y]), bw_method='scott')
		density = kde(grid_points)

		# Reshape the density values to match the grid shape
		density_grid = np.flip(np.reshape(density, grid_x.shape), axis=0)

		# Define spatial information (transform and CRS)
		transform = from_origin(upper_left_x, upper_left_y, resolution, resolution)  # Adjust according to your grid
		crs = acled_data.crs

		# Specify the output raster file name
		output_raster = "ACLED/"+country+"_ACLED.tif"

		# Write the density map to a raster file
		with rasterio.open(
		    output_raster,
		    "w",
		    driver="GTiff",
		    width=density_grid.shape[1],
		    height=density_grid.shape[0],
		    count=1,
		    dtype=np.float32,
		    crs=crs,
		    transform=transform,
		) as dst:
		    dst.write(density_grid, 1)

		print("Density map raster created successfully:", output_raster)
		'''
		
		# Code to compute the ACLED variable
		acled_raster = "ACLED/"+country+"_ACLED.tif"

		acled_counts = np.zeros(feat_num)

		with rasterio.open(acled_raster) as src:
			transform = src.transform
			acled_array = src.read(1)

			for index,row in buffers.iterrows(): 
				polygon = row['geometry']

				poly_mask = geometry_mask([polygon], out_shape=acled_array.shape, transform=transform, invert=False)

				masked_data = np.ma.masked_array(acled_array, poly_mask)
				if(np.ma.count(masked_data)==0):
					row,col=rowcol(transform, polygon.centroid.x, polygon.centroid.y)
					acled_counts[index]=np.nan_to_num(acled_array[row,col], nan=0)
				else:
					acled_counts[index]=np.nanmean(masked_data)

		light_df['Events']=acled_counts
		
		print('ACLED')
		
		light_df.to_csv(dest_folder+country+'_vars_PSU_'+buffer_str+'_2.csv')
		
