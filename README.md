# ENVIRONMENTAL OR SOCIOECONOMIC? COMPARING DRIVERS OF FEAR AND EXPERIENCE OF VIOLENCE IN FOUR SUB-SAHARAN COUNTRIES

Master of Arts, Department of Geography, CU Boulder  
Michele Lissoni  
___

This repository contains the code and some of the data used in my thesis work, whose goal was to model the drivers
of individual fear and experience of violence as measured by the [Afrobarometer](https://www.afrobarometer.org/) Round 8 opinion surveys in Nigeria,
Ethiopia, South Africa and Kenya.  

The scripts in this repository are written in a mix of Python and R. Most are designed to be operated from the 
command line, but the thesis figures are produced using Jupyter Notebooks and R Markdowns. Two Jupyter Notebook for 
preprocessing the data run inside an ArcGIS Pro project file (ArcGIS Pro operates only on Windows OS).

The respondent-level Afrobarometer Round 8 data used in the study are not made available, in compliance with the 
Afrobarometer data policy, but they can be requested at https://www.afrobarometer.org/contact-us/data-requests/.

## GLOSSARY 

### Countries
 
| Country | COUNTRY_ACRONYM | COUNTRY_STRING | 
|---|---|---|
| Nigeria | NIG            | nigeria |
| Ethiopia | ETH            | ethiopia |
| South Africa | SAF            | southafrica |
| Kenya | KEN            | kenya | 

### Outcome variables

|OUTCOME_CODE|OUT_INDEX|Violence type|Outcome type|
|---|---|---|---|
|Q54aF|1|Communal|Fear|
|Q54aE|2|Communal|Experience|
|Q54bF|3|Political|Fear|
|Q54bE|4|Political|Experience|
|Q54cF|5|Armed|Fear|
|Q54cE|6|Armed|Experience|

### Spatial scales

|SCALE||
|---|---|
|Resp|Respondent|
|EA|Primary Sampling Unit (PSU)|

### PSU Buffers 

**PERCENT_AREA**: 200, 300, 400, 500, 750, 1000  
**KM_DISTANCE**: 1, 2, 5, 10, 20, 50   

## INSTRUCTIONS FOR REPLICATION

The results of the regressions are included in the repository (skip to the end to see how to create the figures and tables
describing them), but you can follow these instructions to replicate them step by step.

### Pre-processing the Afrobarometer respondent-level data

1. Request Afrobarometer Round 8 data. Save the Excel spreadsheets that will be sent to you in the 
   *Afrobarometer/[COUNTRY\_ACRONYM]/* directory. 
   
2. Run the *afrobarometer.py* Python script. This will strip the Afrobarometer data from the questions that were
   not used in this study and remove the invalid values, saving the results to the files 
   *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_afrob\_vars.csv*.
   
3. Run the *miss\_forest.R* R script. This will impute the missing values, saving the results to the files
   *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_afrob\_imp.csv*.

### Pre-processing the non-Afrobarometer (environmental) PSU-level data
This part is optional as the processed data are already provided.  

4. Run the *sample\_PSU.py* Python script with no command line arguments. This will retrieve the values of the 
   rainfall (TAMSAT), land surface temperature and vegetation (MODIS), nighttime lights
   (VIIRS) and ACLED variables and save them to the files 
   *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_vars\_PSU\_poly\_2.csv* (included in the repository).  
   
   NOTE: several variables are retrieved through the Google Earth Engine Python API. You will therefore need a 
   Google Earth Engine project. You will also have to upload manually the PSU polygons 
   (*GIS/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_R8\_PSU\_polys\_2.shp*, included in the repository) to your GEE assets beforehand.
   
5. Open the ArcGIS Pro project *ArcGIS/arcgis1.aprx* and run the *ArcGIS/urban\_rural.ipynb* Jupyter Notebook from
   inside the project to obtain the urban-rural binary variable, saved in the files
   *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_Urb\_Rur.csv* (included in the repository).  
   
   NOTE: the *urb\_rur.xlsx* file contains the analysis that estimated the optimal threshold distinguishing urban and
   rural PSU on the basis of the percentage of built area.
   
6. Carrying out spatial joins using a GIS software (no code was written for this operation), find in which ecological 
   zone (the shapefiles *Ecological\_areas/[COUNTRY\_ACRONYM]/mst\_thz\_COUNTRY\_STRING\_poly.shp* divide each country into 
   ecological zones; the attribute *gridcode* contains this information) each PSU polygon falls. Save the information
   to the files *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_AEZ\_PSU.csv* (included in the repository).
   
### Random-effects multi-level model regressions
The results of these regressions are included in the repository provided. The R functions operating the model are stored in 
the *belljones.R* file.  

7. Run the *multi\_scale\_bj.R* R script to carry out the regression on the individual countries. The results,
   distinguished by scale, are saved in the *Results/* directory in the files:
   
   | | |
   |---|---|
   |*coefs\_[SCALE]\_bj.Rda*	| Coefficients| 
   |*stderrs\_[SCALE]\_bj.Rda*	|Standard errors|
   |*pvalues\_[SCALE]\_bj.Rda*	|P-values|
   |*ranvar\_bj.Rda*		|Variance explained by the random effects|
   |*auc\_bj.Rda*			|Area Under Curve|

   
   The values of the random effect terms for each regression are saved in the files 
   *Results/ranef/ranef\_[COUNTRY\_ACRONYM]\_[OUTCOME\_CODE].Rda*.
   
9. Run the *all\_countries\_bj.R* R script with no command line arguments to carry out the regression on the data for all 	
   four countries aggregated. The results, distinguished by scale, are saved in the *Results/* directory in the files:
   
   | | |
   |---|---|
   |*coefs\_[SCALE]\_bj\_allcountries.Rda*	| Coefficients| 
   |*stderrs\_[SCALE]\_bj\_allcountries.Rda*	|Standard errors|
   |*pvalues\_[SCALE]\_bj\_allcountries.Rda*	|P-values|
   |*ranvar\_bj\_allcountries.Rda*		|Variance explained by the random effects|
   |*auc\_bj\_allcountries.Rda*			|Area Under Curve|
   
   The values of the random effect terms for each regression are saved in the files 
   *Results/ranef/ranef\_allcountries\_[OUTCOME\_CODE].Rda*.

### Regressions to test other spatial units
The results of these regressions are included in the repository.  

9. Open the ArcGIS Pro project *ArcGIS/arcgis1.aprx* and run the *ArcGIS/PSU\_buffers.ipynb* Jupyter Notebook from
   inside the project to create the percentage and fixed distance buffers around the PSUs, saved in the 
   *GIS/[COUNTRY\_ACRONYM]/* directories, respectively in the files *[COUNTRY\_ACRONYM]\_R8\_PSU\_[PERCENT\_AREA]\_buffers.shp*
   and *[COUNTRY\_ACRONYM]\_R8\_PSU\_[KM\_DISTANCE]km\_buffers.shp* (included in the repository).
   
10. Run the *sample\_PSU.py* Python script with the command line arguments *-p* and *-k*. This will retrieve, 
    respectively for the percentage and fixed distance buffers, the values of the rainfall, land surface
    temperature, vegetation, nighttime lights and ACLED variables and save them to the files 
    *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_vars\_PSU\_[PERCENT\_AREA]\_2.csv* and
    *Afrobarometer/[COUNTRY\_ACRONYM]/[COUNTRY\_STRING]\_vars\_PSU\_[KM\_DISTANCE]km\_2.csv*.
    
11. Run the *all\_countries\_bj.R* R script with the command line arguments *-p* and *-k* to carry out the regressions for 
    the percentage and fixed distance buffers respectively and save the AUC values respectively to the files 
    *Results/auc\_bj\_all\_countries\_percents.Rda* and *Results/auc\_bj\_allcountries\_kms.Rda*.

### Analyse the results and plot the figures

12. Use the *maps.ipynb* Jupyter Notebook to plot the maps of the environmental dynamics variables (which use the TIFFs
    generated using the *environmentals.ipynb* Jupyter Notebook and saved in the *Maps/* directory), of the ecological
    zone variables (which use the TIFFs stored in the *Ecological\_areas/[COUNTRY\_ACRONYM]/* directories) and of the 
    ACLED variable (which uses TIFFs generated using code found in *sample\_PSU.py* and saved in the *ACLED/* directory).
    
13. Use the *data\_statistics.Rmd* R Markdown to generate all the other figures and the Latex table containing the number of
    regression models in which each variable was significant.
14. Run the *table_viewer.R* with the appropriate [OUT_INDEX] command line arguments to print the Latex tables showing
    the regression results for the outcome variables.
