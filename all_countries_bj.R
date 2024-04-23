##########################################################################################################
#
# Rscript all_countries_bj.R [-k] [-p] 
#
# This script performs the regressions over the aggregated data for all the countries and stores the results
# (coefficients, standard errors, p-values, random effects and random effect variances) in files.
#
# Depending on the arguments provided to the script in the command line, the operation can be performed
# over different spatial units:
#
# 	no arguments: the operation is performed over the PSU polygons, all results are saved
#	
#	-k: the script loops over the fixed-distance buffers, only the AUCs are saved
#
#	-p: the script loops over the percent-area buffers, only the AUCs are saved
# 
##########################################################################################################

library(dplyr)
library(lme4)
library(pROC)

source("belljones.R")

# Command line arguments 
args <- commandArgs(trailingOnly=TRUE)

if(length(args)==0){
	in_string <- NULL
	out_string <- NULL
	buff_list <- c('poly')
	print_string <- ''
	len_loop <- 1
	get_all <- TRUE
}else if(args[1]=='-k'){
	in_string <- 'km'
	print_string <- 'km'
	out_string <- '_kms'
	buff_list <- c(1,2,5,10,20,50)
	len_loop <- length(buff_list)
	get_all <- FALSE
}else if(args[1]=='-p'){
	in_string <- NULL
	print_string <- '%'
	out_string <- '_percents'
	buff_list <- c(200,300,400,500,750,1000)
	len_loop <- length(buff_list)
	get_all <- FALSE	
}

country_list <- list(
		'kenya'=list(
			'acronym'='KEN'),
		'ethiopia'=list(
			'acronym'='ETH'),
		'southafrica'=list(
			'acronym'='SAF'),
		'nigeria'=list(
			'acronym'='NIG')
		)

countries <- names(country_list)

# Outcome variables and values for which they will be set to 1
outcome_values <- list('Q54aF'=c(1,2), 'Q54aE'=c(2), 'Q54bF'=c(1,2), 'Q54bE'=c(2), 'Q54cF'=c(1,2), 'Q54cE'=c(2))
outcomes <- names(outcome_values)

# List of variables
vars_list <- list(
	'Resp'=list( # Respondent scale
		'variables'=c( # Variable names
			"Q0",
			"Q1",
			"Q3",
			"Q4b",
			"Q5",
			"Q7a",
			"Q10a",
			"Q43a",
			"Q56",
			"Q81",
			"Q82a",
			"Q84a",
			"Q84b",
			"Q84c",
			"Q88",
			"Q96c",
			"Q97",
			"Q98b"
			),
		'files'= c('_afrob_imp.csv'), # Data source
		'index'=''
		),	
	'EA'=list( # PSU scale
		'variables'=c("Urb_Rur", "AEZ_Temp", "AEZ_Mois", "nighttime", "rfe_anoms", "LST_anoms", "NDVI_anoms", "Events"), # Variable names
		'files'=c('_Urb_Rur.csv', # Urban-rural variable
			  '_AEZ_PSU.csv', # Ecological zone variables
			  '_vars_PSU_poly_2.csv' # Other variables 
			  ),
		'index'='EA_Num' # Grouping factor
		)
	)

# Filling the lists of variables, scales and indices
all_vars <- c()
all_scales <- c()
scale_list <- names(vars_list)
index_list <- c()

for(scale in scale_list){
	vars_vector <- vars_list[[scale]]$variables
	vars_index <- vars_list[[scale]]$index
	
	all_vars <- c(all_vars, vars_vector)
	all_scales <- c(all_scales, rep(scale, length(vars_vector)))
	
	index_list <- c(index_list, vars_index)
}

auc_arr <- array(dim=c(len_loop,length(outcomes)))

# Looping over the spatial units
for(k in 1:len_loop){

	file_str <- paste0(buff_list[k],in_string)

	vars_list[['EA']][['files']][3] <- paste0('_vars_PSU_',file_str,'_2.csv') # Data source for each spatial unit
	
	# Aggregating the data from the four countries
	for(n in 1:length(countries)){

		country <- countries[n]
		country_acronym <- country_list[[country]]$acronym

		folder <- paste0('Afrobarometer/',country_acronym,'/')

		for(i in 1:length(scale_list)){
			scale <- scale_list[i]
			index <- index_list[i]
			
			file_list <- vars_list[[scale]]$files
			
			
			for(q in 1:length(file_list)){
			
				file <- file_list[q]
				file_data <- read.csv(paste0(folder, country, file))
				
				if(file=='_AEZ_PSU.csv'){					
					file_data <- file_data %>%
						mutate(AEZ_Temp=floor(AEZ_Num/100), AEZ_Mois=AEZ_Num %% 100)					
				}
				
				if(q==1 & i==1){					
					all_data <- file_data
				}else{					
					all_data <- merge(all_data, file_data, by=index)
				}
			}				
		}
		
		for(outcome in outcomes){
			outcome_q <- gsub('.{1}$', '', outcome)
			all_data[[outcome]] <- all_data[[outcome_q]]
		}

		all_data[['Country']] <- country_acronym
		
		for(index in index_list){
			all_data[[index]] <- paste0(all_data[[index]],country_acronym)
		}
		
		if(n==1){
			all_countries_data <- all_data[c(all_vars, index_list[2:length(index_list)], 'Country', outcomes)]
		}else{
			all_countries_data <- rbind(all_countries_data, all_data[c(all_vars, index_list[2:length(index_list)], 'Country', outcomes)])
		}
	}

	# Fitting the Bell-Jones model
	bj_results <- belljones_model(all_countries_data, outcome_values, all_vars, all_scales, scale_list, index_list, other_indices=c('Country'))

	auc_arr[k,] <- bj_results$aucs
	
	cat(paste0(buff_list[k],print_string),'\n')
}

# Saving the AUC results
out_file <- paste0('Results/auc_bj_allcountries',out_string,'.Rda')

saveRDS(auc_arr, file=out_file)

# If the spatial units is the PSU polygons, all the other results are also saved
if(get_all){

	for(outcome in outcomes){
			saveRDS(bj_results$randeffs[[outcome]], file=paste0('Results/ranef/ranef_allcountries_',outcome,'.Rda'))	
		}

	for(scale in scale_list){
				
		coef_array <- bj_results$coefficients[[scale]]
		stderr_array <- bj_results$stderrs[[scale]]
		pvalue_array <- bj_results$pvalues[[scale]]
		
		saveRDS(pvalue_array, file=paste0("Results/pvalues_",scale,"_bj_allcountries.Rda"))
		saveRDS(coef_array, file=paste0("Results/coefs_",scale,"_bj_allcountries.Rda"))
		saveRDS(stderr_array, file=paste0("Results/stderrs_",scale,"_bj_allcountries.Rda"))
	}

	saveRDS(bj_results$randvars, file="Results/ranvar_bj_allcountries.Rda")
}
