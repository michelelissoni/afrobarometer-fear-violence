##########################################################################################################
#
# Rscript table_viewer.R OUT_INDEX [SIG_THRES]
#
# This script takes the OUT_INDEX of an outcome variable as a command line argument and prints the Latex 
# table showcasing the results of all its models. A second optional argument (SIG_THRES) sets the 
# significance threshold (default: 0.05).
#
# OUT_INDEX values:
#	1: Q54a Fear
#	2: Q54a Experience
#	3: Q54b Fear
#	4: Q54b Experience
#	5: Q54c Fear
#	6: Q54c Experience 
# 
##########################################################################################################

library(dplyr)
library(tidyr)
library(stringr)

args <- commandArgs(trailingOnly=TRUE)

if(length(args)==0){
	stop("Provide an OUT_INDEX value")
}

out_index <- as.integer(args[1])
if(length(args)==1){
	sig_thres <- 0.05
}else{
	sig_thres <- as.numeric(args[2])
}


# Result files
pvalue_EA_arr <- readRDS("Results/pvalues_EA_bj.Rda")
pvalue_Resp_arr <- readRDS("Results/pvalues_Resp_bj.Rda")
coef_EA_arr <- readRDS("Results/coefs_EA_bj.Rda")
coef_Resp_arr <- readRDS("Results/coefs_Resp_bj.Rda")
auc_arr <- readRDS("Results/auc_bj.Rda")

all_pvalue_EA_arr <- readRDS("Results/pvalues_EA_bj_allcountries.Rda")
all_pvalue_Resp_arr <- readRDS("Results/pvalues_Resp_bj_allcountries.Rda")
all_coef_EA_arr <- readRDS("Results/coefs_EA_bj_allcountries.Rda")
all_coef_Resp_arr <- readRDS("Results/coefs_Resp_bj_allcountries.Rda")
all_auc_arr <- readRDS("Results/auc_bj_allcountries.Rda")

outcomes <- c("Q54A FEAR", "Q54A EXPERIENCE", "Q54B FEAR", "Q54B EXPERIENCE", "Q54C FEAR", "Q54C EXPERIENCE")

outcome <- outcomes[out_index]

df_len <- dim(pvalue_Resp_arr)[1]

# Names and descriptions of the variables
vars <- c("Q0: female gender?",
          "Q1: age",
          "Q3: country direction right?",
          "Q4b: living conditions good?",
          "Q5: govt discrimination (wealth)",
          "Q7a: how long without food?",
          "Q10a: freedom of speech",
          "Q43a: corruption decreased?",
          "Q56: media freedom",
          "Q81: ethnic power",
          "Q82a: govt discrimination (ethnicity)",
          "Q84a: people discrimination (wealth)",
          "Q84b: people discrimination (religion)",
          "Q84c: people discrimination (ethnicity)",
          "Q88: traditional leaders serve people?",
          "Q96c: household of farmers?",
          "Q97: level of education",
          "Q98b: govt discrimination (religion)",
          "Rural area?",
          "Temperature Ecological Zone",
          "Moisture Ecological Zone",
          "Nighttime lights",
          "RFE24: rainfall anomaly",
          "LST24: temperature anomaly",
          "NDVI24: vegetation anomaly",
          "ACLED density")

# Storing all the data into a dataframe
df <- data.frame(
  variables = vars,
  nigeria_signif = rep(0,df_len),
  nigeria_EA = coef_EA_arr[,4,out_index],
  nigeria_Resp = coef_Resp_arr[,4,out_index],
  pnigeria_EA = pvalue_EA_arr[,4,out_index],
  pnigeria_Resp = pvalue_Resp_arr[,4,out_index],
  ethiopia_signif = rep(0,df_len),
  ethiopia_EA = coef_EA_arr[,2,out_index],
  ethiopia_Resp = coef_Resp_arr[,2,out_index],
  pethiopia_EA = pvalue_EA_arr[,2,out_index],
  pethiopia_Resp = pvalue_Resp_arr[,2,out_index],
  southafrica_signif = rep(0,df_len),
  southafrica_EA = coef_EA_arr[,3,out_index],
  southafrica_Resp = coef_Resp_arr[,3,out_index],
  psouthafrica_EA = pvalue_EA_arr[,3,out_index],
  psouthafrica_Resp = pvalue_Resp_arr[,3,out_index],
  kenya_signif = rep(0,df_len),
  kenya_EA = coef_EA_arr[,1,out_index],
  kenya_Resp = coef_Resp_arr[,1,out_index],
  pkenya_EA = pvalue_EA_arr[,1,out_index],
  pkenya_Resp = pvalue_Resp_arr[,1,out_index],
  all_signif = rep(0,df_len),
  all_EA = all_coef_EA_arr[,out_index],
  all_Resp = all_coef_Resp_arr[,out_index],
  pall_EA = all_pvalue_EA_arr[,out_index],
  pall_Resp = all_pvalue_Resp_arr[,out_index],
  order = c(21,22,16,6,10,7,19,17,20,15,14,9,11,13,18,24,23,12,25,4,5,8,1,2,3,26)
)

# Distinguishing significant and non-significant coefficients

df$kenya_signif <- as.integer(df$pkenya_Resp<sig_thres)+as.integer(df$pkenya_EA<sig_thres)*2
df$ethiopia_signif <- as.integer(df$pethiopia_Resp<sig_thres)+as.integer(df$pethiopia_EA<sig_thres)*2
df$southafrica_signif <- as.integer(df$psouthafrica_Resp<sig_thres)+as.integer(df$psouthafrica_EA<sig_thres)*2
df$nigeria_signif <- as.integer(df$pnigeria_Resp<sig_thres)+as.integer(df$pnigeria_EA<sig_thres)*2
df$all_signif <- as.integer(df$pall_Resp<sig_thres)+as.integer(df$pall_EA<sig_thres)*2

# Ordering the data and discarding superfluous columns
df <- df %>% arrange(order) %>% dplyr::select(-c(order,pnigeria_EA,pnigeria_Resp,pethiopia_EA,pethiopia_Resp,psouthafrica_EA,psouthafrica_Resp,pkenya_EA,pkenya_Resp,pall_EA,pall_Resp))

print(df)

# Function that highlights the significant coefficients in different colors, depending on their signs
format_func <- function(x, indices){
  x_string <- as.character(signif(x,2))
  x_string_neg <- paste0("\\cellcolor{ProcessBlue}{",x_string,"}")
  x_string_pos <- paste0("\\cellcolor{RedOrange}{",x_string,"}")
  x_string_zero <- rep(paste0("\\cellcolor{lightgray}{}"),length(x_string))
  
  x_string[x>0 & indices] <- x_string_pos[x>0 & indices] 
  x_string[x<0 & indices] <- x_string_neg[x<0 & indices]
  x_string[x==0] <- x_string_zero[x==0]
  
  
  return (x_string)
}

countries <- c('kenya','ethiopia','nigeria','southafrica','all')

#Applying the function to the data
for(country in countries){
  df[[paste0(country,'_Resp')]] <- format_func(df[[paste0(country,'_Resp')]],df[[paste0(country,'_signif')]]==1 | df[[paste0(country,'_signif')]]==3)
  df[[paste0(country,'_EA')]] <- format_func(df[[paste0(country,'_EA')]],df[[paste0(country,'_signif')]]==2 | df[[paste0(country,'_signif')]]==3)
}

# Keeping only the data that is to be printed
df <- df %>% dplyr::select(-c(kenya_signif, ethiopia_signif, nigeria_signif, southafrica_signif, all_signif))


mat <- as.matrix(df)

# Creating a printable table
table_str <- capture.output(write.table(df, row.names=F, col.names=F, sep=" & ", eol="\\\\\n\\noalign{\\gdef\\vline{\\vrule width 1.5pt\\global\\let\\vline\\xvline}}\n\\hhline{|~|-|-|-|-|-|-|-|-|-|-|-|}\n & ", quote=FALSE))
table_str <- str_replace_all(table_str, "RFE24", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{5}{*}{Environment} & RFE24")
table_str <- str_replace_all(table_str, " & Q4b", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{3}{*}{Economy} & Q4b")
table_str <- str_replace_all(table_str, " & Q84a", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{7}{*}{Discrimination} & Q84a")
table_str <- str_replace_all(table_str, " & Q3", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{3}{*}{Trust} & Q3")
table_str <- str_replace_all(table_str, " & Q10a", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{2}{*}{Democracy} & Q10a")
table_str <- str_replace_all(table_str, " & Q0", "\\\\Xhline{4\\\\arrayrulewidth}\n\\\\multirow{6}{*}{Other} & Q0")


cat(outcome,'LATEX TABLE','\n')
cat('\n')

# Printing the table
cat('\\begin{tabular}{?l|l?cc?cc?cc?cc?cc?}','\n')
cat('\\Xhline{4\\arrayrulewidth}','\n')
cat(paste0('\\multicolumn{12}{?c?}{\\textbf{',outcome,'}}\\\\'),'\n')
cat('\\Xhline{4\\arrayrulewidth}','\n')
cat('\\multicolumn{2}{?c?}{\\textbf{Variable}} & \\multicolumn{2}{c?}{\\textbf{Nigeria}} & \\multicolumn{2}{c?}{\\textbf{Ethiopia}} & \\multicolumn{2}{c?}{\\textbf{South Africa}} & \\multicolumn{2}{c?}{\\textbf{Kenya}} & \\multicolumn{2}{c?}{\\textbf{All countries}} \\\\','\n')
cat('\\hline','\n')
cat('\\multicolumn{1}{?c|}{Driver} & \\multicolumn{1}{c?}{Name} &  \\multicolumn{1}{c}{PSU} & \\multicolumn{1}{c?}{Resp} &  \\multicolumn{1}{c}{PSU} & \\multicolumn{1}{c?}{Resp}&  \\multicolumn{1}{c}{PSU} & \\multicolumn{1}{c?}{Resp}&  \\multicolumn{1}{c}{PSU} & \\multicolumn{1}{c?}{Resp}&  \\multicolumn{1}{c}{PSU} & \\multicolumn{1}{c?}{Resp} \\\\','\n')
cat(table_str[-c(14,15,23,24,44,45,53,54,59,60,77,78,79)], sep='\n')
cat('\\Xhline{4\\arrayrulewidth}','\n')
cat('\\end{tabular}','\n')

