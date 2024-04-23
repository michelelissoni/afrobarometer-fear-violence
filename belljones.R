##########################################################################################################
#
# This script contains two functions that operate the Bell-Jones model.
# 
##########################################################################################################

library(dplyr)
library(lme4)
library(pROC)

######################################################################################
#
# belljones_vars
#
#	This function splits the explanatory variables into higher-scale averages and 
#	lower-scale residuals, creating the inputs for the Bell-Jones model.
#
#	Arguments:
#		x - the dataframe containing the original data
#		variables - a vector containing the list of explanatory variables,
#			    indicating the names of the columns that contain them.
#		scales - a vector, the same length as "variables", indicating the 
#			 scale at which each variable was sampled.
#		scale_list - a vector containing the scales that the Bell-Jones model
#			     should consider.
#		index_list - a vector, the same length as "scale_list", indicating 
#		             the columns containing the grouping factors associated
#			     with each scale. The first element should be an empty 
#			     string.
#
#	Returns:
#		data - the new dataframe.
#		variables - a vector containing the new list of variables.
#		scales - a vector containing the corresponding list of scales.
# 
######################################################################################

belljones_vars <- function(x, variables, scales, scale_list, index_list){
  
  # Looping over the higher scales
  for(j in 2:length(scale_list)){
    scale <- scale_list[j]
    scale_prev <- scale_list[j-1]
    index <- index_list[j]
    
    vars_prev <- variables[scales==scale_prev] # The variables sampled at the previous scale (immediately lower than this one)
    
    vars_prev_new <- paste0(vars_prev, "_", scale_prev) # The names of the residual variables
    
    prev_means <- x[,c(vars_prev, index)] %>% # The averages at the present scale.
      group_by_at(index) %>%
      summarise(across(.cols=all_of(vars_prev), \(x) mean(x, na.rm = TRUE)))
    
    # The residuals at the previous scale
    x <- x %>%
      rename_with(~vars_prev_new, .cols=all_of(vars_prev)) %>%
      merge(prev_means, by=index)
    
    x[,vars_prev_new] <- x[,vars_prev_new]-x[,vars_prev]
    
    # Adding the newly named variables, and their scales, to the list.
    variables <- c(vars_prev_new, variables)
    scales[scales==scale_prev] <- scale
    scales <- c(rep(scale_prev,length(vars_prev_new)),scales)
    
    # Concluding the loop, so that all variable names now also indicate their scale.
    if(j==length(scale_list)){
      
      x <- x %>%
        rename_with(~paste0(variables[scales==scale], "_", scale), .cols=all_of(variables[scales==scale])) 
      
      variables[scales==scale] <- paste0(variables[scales==scale], "_", scale)
    }
  }
  return(list("data"=x, "variables"=variables, "scales"=scales))
}

######################################################################################
#
# belljones_model
#
#	This function loops over the outcome variables and for each one fits the 
#	Bell-Jones model and returns the results.
#
#	Arguments:
#		x - the dataframe containing the original data
#		outcome_values - a named list. The keys should be names of the
#				 columns containing the various outcome variable data. 
#		                 The values should be vectors containing the values 
#		                 for which the binary outcome variable should be set
#		                 to 1.
#		variables - a vector containing the list of explanatory variables,
#			    indicating the names of the columns that contain them.
#		scales - a vector, the same length as "variables", indicating the 
#			 scale at which each variable was sampled.
#		scale_list - a vector containing the scales that the Bell-Jones model
#			     should consider.
#		index_list - a vector, the same length as "scale_list", indicating 
#		             the columns containing the grouping factors associated
#			     with each scale. The first element should be an empty 
#			     string.
#		other_indices - a vector of other grouping factors for which only
#		                random effects should be added to the model, without
#				splitting the variables. Default: NULL
#		
#		var_excepts - a vector containing the names of the variables that 
#		              are already known not to be significant. For these,
#		              the coefficients and standard errors will be set to 0
#		              the p-values to 1. Default: none.
#
#		weights - weights for the various data instances. Default: 
#		          equal weights for all
#
#	Returns:
#		coefficients - a list, whose keys are the scales and whose value for
#		               each scale is a R x Q array, where R is the number of
#		               explanatory variables and Q the number of outcome
#		               variables, containing for each outcome the value of the
#		               coefficient.
#		stderrs - a list, with the same format, containing the coefficients'
#		         standard errors.
#		pvalues - a list, with the same format, containing the coefficients'
#		          p-values.
#		aucs - a 1D array containing, for each outcome variable, the Area Under
#		       Curve of the regression model.
#		randvars - a Q x I array, where I is the number of upper-level scales, 
#		           containing the variance explained by the 
#		           upper-level random effects (the variance explained by the 
#		           fixed effects is equal to pi^2/3 ~ 3.29.
#		randeffs - a list, whose keys are the outcome variables, containing
#		           for each such variable a dataframe detailing the values of 
#		           the random effect terms.		
#
# 
######################################################################################


belljones_model <- function(data, outcome_values, variables, scales, scale_list, index_list, other_indices=NULL, var_excepts=c(), weights=NULL){

	outcomes <- names(outcome_values)

	# Lists of output
	coef_arrays <- list() # Coefficients
	pvalue_arrays <- list() # P-values
	stderr_arrays <- list() # Standard errors

	# Creating the array contained in these lists at each scale
	for(scale in scale_list){

		coef_arrays[[scale]] <- array(dim=c(length(variables), length(outcomes)))
		stderr_arrays[[scale]] <- array(dim=c(length(variables), length(outcomes)))
		pvalue_arrays[[scale]] <- array(dim=c(length(variables), length(outcomes)))
		
	}

	auc_arr <- array(dim=c(length(outcomes))) # AUC array
	rand_effs <- list() # Random effects list

	# A dataframe to gather the results.	
	vars_df0 <- data.frame(variables=all_vars, scale=scales)

	# Excluding the var_except variables that known not to be significant
	scales <- scales[ !variables %in% var_excepts]
	variables <- variables[ !variables %in% var_excepts]
	
	# Setting the coefficients, standard errors and p-values for the 
	# var_except variables
	for(var_except in var_excepts){
		for(scale in scale_list){
			vars_df0[vars_df0$variables==var_except, paste0('Coef_', scale)]=0
			vars_df0[vars_df0$variables==var_except, paste0('Stderr_', scale)]=0
			vars_df0[vars_df0$variables==var_except, paste0('Pvalue_', scale)]=1
		}
	}

	# Creating the correct variables for the Bell-Jones model
	a <- belljones_vars(data, variables, scales, scale_list, index_list)

	all_data <- a$data
	vars_bj  <- a$variables
	scales <- a$scales

	# Standardizing the variables: helps the model converge
	all_data_scaled <- all_data %>% mutate_at(vars_bj, ~(scale(.) %>% as.vector))
	
	# Adding the other_indices to the index list
	index_list <- c(index_list,other_indices)
	
	ranvar_arr <- array(dim=c(length(index_list)-1, length(outcomes))) # Random effect variances

	# Formula
	func_string <- paste("OUT",'~',paste(vars_bj, collapse=" + "),paste(' + (1 |',index_list[2:length(index_list)],')', collapse=''))

	# Looping over the outcome variables
	for(j in 1:length(outcomes)){
	
		outcome <- outcomes[j]
		pos_values <- outcome_values[[outcome]] # Values for which the outcome is set to 1

		vars_df <- vars_df0
		
		# Creating the binary outcome variable
		all_data_scaled$OUT <- ifelse(all_data_scaled[[outcome]] %in% pos_values, 1, 0)
		
		# Default weights
		if(is.null(weights)){
			weights <-  rep(1.0, nrow(all_data))
		}

		# Fitting the model
		full_model <- glmer(as.formula(func_string),data=all_data_scaled, family=binomial(link="logit"), control=glmerControl(optCtrl=list(maxfun=200000)), weight=weights, nAGQ=0)
	
		# Regression results
		pvalues <- summary(full_model)$coefficients[,4]
		stderrs <- summary(full_model)$coefficients[,2]
		coefficients <- summary(full_model)$coefficients[,1]

		# Recording the results
		for(i in 1:length(all_vars)){
		  
			variable <- all_vars[i]
			
			for(scale in scale_list){
				variable_bj <- paste0(variable,'_',scale)
		  
		  		if(variable_bj %in% vars_bj){
				  	vars_df[vars_df$variables==variable, paste0('Coef_',scale)] <- unname(coefficients[variable_bj])
				  	vars_df[vars_df$variables==variable, paste0('Stderr_',scale)] <- unname(stderrs[variable_bj])
				  	vars_df[vars_df$variables==variable, paste0('Pvalue_',scale)] <- unname(pvalues[variable_bj])
				}else{
				  	vars_df[vars_df$variables==variable, paste0('Coef_',scale)] <- 0
				  	vars_df[vars_df$variables==variable, paste0('Stderr_',scale)] <- 0
				  	vars_df[vars_df$variables==variable, paste0('Pvalue_',scale)] <- 1
				}
			}
			
		}
			
		# Inserting the results into the arrays and lists that will be returned by the function
		for(scale in scale_list){
		
			coef_array <- coef_arrays[[scale]]
			stderr_array <- stderr_arrays[[scale]]
			pvalue_array <- pvalue_arrays[[scale]]
			
			coef_array[,j] <- vars_df[[paste0('Coef_',scale)]]
			stderr_array[,j] <- vars_df[[paste0('Stderr_',scale)]]
			pvalue_array[,j] <- vars_df[[paste0('Pvalue_',scale)]]
			
			coef_arrays[[scale]] <- coef_array
			stderr_arrays[[scale]] <- stderr_array
			pvalue_arrays[[scale]] <- pvalue_array
		}

		for(q in 2:length(index_list)){
			
			index <- index_list[q]
			ranvar <- unname(attr(summary(full_model)$varcor[[index]], "stddev"))^2
			ranvar_arr[q-1,j] <- ranvar
			
		}
		
		rand_effs[[outcome]]=as.data.frame(ranef(full_model))
		
		# Calculating the AUC
		actual_labels <- all_data_scaled$OUT
		predicted_probs <- predict(full_model, newdata=all_data_scaled, type="response")
		roc_curve <- roc(actual_labels, predicted_probs)

		auc_value <- auc(roc_curve)
		
		auc_arr[j] <- auc_value
		
	}
	
	return(list("coefficients"=coef_arrays, "stderrs"=stderr_arrays, "pvalues"=pvalue_arrays, "aucs"=auc_arr, "randvars"=ranvar_arr, "randeffs"=rand_effs))
}
