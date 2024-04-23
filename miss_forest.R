##########################################################################################################
#
# This script performs an imputation using the missForest algorithm (Stekhoven and Bühlmann, 2012) to 
# replace the invalid values of the Afrobarometer data (e.g. "Don't know" answers) with valid ones.
# It writes the result to a new CSV file.
#
# WARNING: missForest will not always output the same result. However, the impact of the differences
#          on the results are largely negligible.
# 
##########################################################################################################

library(missForest)
library(dplyr)

countries <- c('kenya','ethiopia','southafrica', 'nigeria')

country_acronyms <- list(
	'kenya'='KEN',
	'ethiopia'='ETH',
	'southafrica'='SAF',
	'nigeria'='NIG'
	)

# Valid values for each variable

valid_values_list <- list(
	'Q0'=c(1,2),
	'Q1'=18:129,
	"Q3"=c(1,2),
	"Q4b"=c(1,2,3,4,5),
	"Q5"=c(0,1,2,3),
	"Q7a"=c(0,1,2,3,4),
	"Q10a"=c(1,2,3,4),
	"Q43a"=c(1,2,3,4,5),
	"Q56"=c(0,1,2,3),
	"Q81"=c(1,2,3,4),
	"Q82a"=c(0,1,2,3),
	"Q84a"=c(0,1,2,3),
	"Q84b"=c(0,1,2,3),
	"Q84c"=c(0,1,2,3),
	"Q88"=c(1,2,3),
	"Q96c"=c(0,1),
	"Q97"=c(0,1,2,3,4,5,6,7,8,9),
	"Q98b"=c(0,1,2,3)
	)

# Looping across countries

for(country in countries){

	country_acronym <- country_acronyms[[country]]
	
	folder <- paste0('Afrobarometer/',country_acronym,'/')
	file <- paste0(folder,country,'_afrob_vars.csv')

	country_data <- read.csv(file, header=TRUE) # Data file (with missing values)

	# Only the explanatory variables are used for the imputation
	X <- select(country_data, -c(X, Respondent, EA_Num, EA_weight, HH_weight, Latitude, Longitude, Q54a, Q54b, Q54c))

	X_imp <- missForest(X, verbose=TRUE) # MissForest imputation

	# All the values are integers, hence the new ones are rounded
	X_imp_rd <-X_imp$ximp %>%
	  mutate(across(where(is.numeric), round, digits=0))
	  
	# On rare occasions, the MissForest algorithm produces values that are different from the valid ones.
	# These are turned into the closest valid values.	  
	for(question in names(valid_values_list)){
		valid_values <- valid_values_list[[question]]
		closest_valid_values <- sapply(X_imp_rd[[question]], function(x) {
	  		closest_value <- valid_values[which.min(abs(x - valid_values))]
	  		return(closest_value)
		})
		
		X_imp_rd[[question]] <- closest_valid_values
	}
	
	# Writing to the new data file
	write.csv(cbind(X_imp_rd, select(country_data, c(Respondent, EA_Num, EA_weight, HH_weight, Latitude, Longitude, Q54a, Q54b, Q54c))), paste0(folder,country,"_afrob_imp.csv"))
	
	cat(country,'\n')
}
