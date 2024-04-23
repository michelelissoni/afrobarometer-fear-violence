##########################################################################################################
#
# This script performs the regressions over the data for the individual countries and stores the results
# (coefficients, standard errors, p-values, random effects and random effect variances) in files.
# 
##########################################################################################################

library(dplyr)
library(lme4)
library(pROC)

source("belljones.R")

country_list <- list(
		'kenya'=list(
			'acronym'='KEN',
			'var_excepts'=c()),
		'ethiopia'=list(
			'acronym'='ETH',
			'var_excepts'=c()),
		'southafrica'=list(
			'acronym'='SAF',
			'var_excepts'=c('Q81')),
		'nigeria'=list(
			'acronym'='NIG',
			'var_excepts'=c('AEZ_Temp'))
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

# Lists and arrays containing the results of the model for each country
coef_arrays <- list() # Coefficients
pvalue_arrays <- list() # P-values
stderr_arrays <- list() # Standard errors

for(scale in scale_list){

	coef_arrays[[scale]] <- array(dim=c(length(all_vars), length(countries), length(outcomes)))
	pvalue_arrays[[scale]] <- array(dim=c(length(all_vars), length(countries), length(outcomes)))
	stderr_arrays[[scale]] <- array(dim=c(length(all_vars), length(countries), length(outcomes)))
	
}

auc_arr <- array(dim=c(length(countries), length(outcomes))) # Area Under Curve
ranvar_arr <- array(dim=c(length(countries), length(scale_list)-1, length(outcomes))) # Random effect variances

# Looping over the countries
for(n in 1:length(countries)){

	startTime <- Sys.time() 
		
	country <- countries[n]
	country_acronym <- country_list[[country]]$acronym
	var_excepts <- country_list[[country]]$var_excepts
	
	folder <- paste0('Afrobarometer/',country_acronym,'/')

	# Retrieving the data

	for(i in 1:length(scale_list)){
		scale <- scale_list[i]
		index <- index_list[i]
		
		file_list <- vars_list[[scale]]$files
		
		
		for(q in 1:length(file_list)){
		
			file <- file_list[q]
			file_data <- read.csv(paste0(folder, country, file))
			
			# Distinguishing the EZ temperature and moisture classes
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

	# Fitting the Bell-Jones model	
	bj_results <- belljones_model(all_data, outcome_values, all_vars, all_scales, scale_list, index_list, var_excepts=var_excepts)
		
	# Recording the results
	for(scale in scale_list){
	
		coef_array <- coef_arrays[[scale]]
		stderr_array <- stderr_arrays[[scale]]
		pvalue_array <- pvalue_arrays[[scale]]
		
		coef_array[,n,] <- bj_results$coefficients[[scale]]
		stderr_array[,n,] <- bj_results$stderrs[[scale]]
		pvalue_array[,n,] <- bj_results$pvalues[[scale]]
		
		coef_arrays[[scale]] <- coef_array
		stderr_arrays[[scale]] <- stderr_array
		pvalue_arrays[[scale]] <- pvalue_array
	}
	
	ranvar_arr[n,,] <- bj_results$randvars
	
	auc_arr[n,] <- bj_results$aucs
	
	randeffs <- bj_results$randeffs
	
	# Saving the random effect values
	for(outcome in outcomes){
		saveRDS(randeffs[[outcome]], file=paste0('Results/ranef/ranef_',country_acronym,'_',outcome,'.Rda'))	
	}
	
	cat(country, as.numeric(Sys.time())-as.numeric(startTime),'\n')
		
}

# Saving the regression results
for(scale in scale_list){
			
	coef_array <- coef_arrays[[scale]]
	stderr_array <- stderr_arrays[[scale]]
	pvalue_array <- pvalue_arrays[[scale]]
	
	saveRDS(pvalue_array, file=paste0("Results/pvalues_",scale,"_bj.Rda"))
	saveRDS(stderr_array, file=paste0("Results/stderrs_",scale,"_bj.Rda"))
	saveRDS(coef_array, file=paste0("Results/coefs_",scale,"_bj.Rda"))
}

saveRDS(ranvar_arr, file="Results/ranvar_bj.Rda")
saveRDS(auc_arr, file="Results/auc_bj.Rda")
