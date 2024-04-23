##########################################################################################################
#
# This script extracts the Afrobarometer outcome and explanatory variables from the raw data,
# ensures they only have valid values (masking the invalid ones) and writes the result to a CSV file.
# 
##########################################################################################################

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# Countries, acronyms and Afrobarometer Excel data files

country_acronyms = {
    'nigeria': 'NIG',
    'ethiopia': 'ETH',
    'southafrica': 'SAF',
    'kenya': 'KEN'
    }
    
countries = list(country_acronyms.keys())

afrob_files = {
    'nigeria': 'NIG_R8.Data.wtd.final_1JUN23.xlsx',
    'ethiopia': 'ETH_R8.Data.wtd.final_31May23.xlsx',
    'kenya': 'KEN_R8.Data.wtd.final_31May23.xlsx',
    'southafrica': 'SAF_R8.Data.wtd.final_1JUN23.xlsx'
    }
    
# Selecting the Afrobarometer variables from the list of all possible answers

valid_qs=[
    #"Respondent number",
    #"Urban or rural Primary Sampling Unit",
    #"Town/Village",
    #"EA Number",
    #"EA Unique Number",
    #"GPS Latitude in EA",
    #"GPS Longitude in EA",
    #"EA-SVC-A. Electricity grid in the PSU/EA",
    #"EA-SVC-B. Piped water system in the PSU/EA",
    #"EA-SVC-C. Sewage system in the PSU/EA",
    #"EA-SVC-D. Mobile phone service in the PSU/EA",
    #"EA-SVC-E.  Borehole or tubewell in PSU/EA",
    #"EA-FAC-A. Post office in the PSU/EA",
    #"EA-FAC-B. School in the PSU/EA",
    #"EA-FAC-C. Police station in the PSU/EA",
    #"EA-FAC-D. Health Clinic in the PSU/EA",
    #"EA-FAC-E. Market stalls in the PSU/EA",
    #"EA-FAC-F. Bank or money services in the PSU/EA",
    #"EA-FAC-G. Paid transport in the PSU/EA",
    #"EA-SEC-A. Police in the PSU/EA",
    #"EA-SEC-B. Soldiers/army in the PSU/EA",
    #"EA-SEC-C. Roadblocks by police/army in the PSU/EA",
    #"EA-SEC-D. Customs checkpoints in the PSU/EA",
    #"EA-SEC-E. Roadblocks by private security/local community in the PSU/EA",
    #"EA-ROAD-A. Road surface at start point",
    #"EA-ROAD-B. Road surface last 5 km",
    #"EA-ROAD-C. Road condition last 5 km",
    #"Reason for Unsuccessful Call Household 1",
    #"Reason for Unsuccessful Call Household 1 (Verbatim)",
    #"Reason for Unsuccessful Call Household 2",
    #"Reason for Unsuccessful Call Household 2 (Verbatim)",
    #"Reason for Unsuccessful Call Household 3",
    #"Reason for Unsuccessful Call Household 4",
    #"Reason for Unsuccessful Call Household 5",
    #"Reason for Unsuccessful Call Household 6",
    #"Reason for Unsuccessful Call Household 7",
    #"Reason for Unsuccessful Call Household 8",
    #"Reason for Unsuccessful Call Household 9",
    #"Reason for Unsuccessful Call Household 10",
    #"Reason for Unsuccessful Call Household 11",
    "Q0. This interview, gender",
    #"Number of adults in household",
    #"Number of calls",
    #"Date of interview",
    #"Time interview started",
    "Q1. Age", # 999
    #"Q2. Language spoken in home",
    #"Q2other. Language spoken in home (verbatim)",
    "Q3. Overall direction of the country",
    #"Q4a. Country’s present economic condition",
    "Q4b. Your present living conditions",
    "Q5. Treated unfairly by government based on economic status",
    #"Q6a. Country’s economic condition compared to 12 months ago",
    #"Q6b. Country’s economic condition in 12 months’ time",
    "Q7a. How often gone without food",
    #"Q7b. How often gone without water",
    #"Q7c. How often gone without medical care",
    #"Q7d. How often gone without cooking fuel",
    #"Q7e. How often gone without cash income",
    #"Q8a. How often felt unsafe walking in neighbourhood",
    #"Q8b. How often feared crime in home",
    #"Q9. Discuss politics",
    "Q10a. Freedom to say what you think",
    #"Q10b. Freedom to join any political organization",
    #"Q10c. Freedom to choose who to vote for",
    #"Q11a. Attend a community meeting",
    #"Q11b. Join others to raise an issue",
    #"Q11c. Attend a demonstration or protest march",
    #"Q12a. Contact local government councillor",
    #"Q12b. Contact MP",
    #"Q12c Contact political party official",
    #"Q12d. Contact traditional leader",
    #"Q13. Voting in the most recent countryal election",
    #"Q14. Freeness and fairness of the last countryal election",
    #"Q15a. Last countryal election: attend a campaign rally",
    #"Q15b. Last countryal election: work for a candidate or party",
    #"Q15c. Last countryal election: contacted by political party rep",
    #"Q15d. Which party contacted: 1st response",
    #"Q15d. Which party contacted: 2nd response",
    #"Q15d. Which party contacted: 3rd response",
    #"Q15d. Which party contacted: 4th response",
    #"Q15d. Which party contacted: 5th response",
    #"Q15d. Which parties contacted: Other (verbatim)",
    #"Q16a. Last countryal election: media covers all candidates fairly",
    #"Q16b. Last countryal election: offered food, gift or money for vote",
    #"Q17a. Last countryal election: votes not accurately counted",
    #"Q17b. Last countryal election: people voted more than once",
    #"Q17c. Last countryal election: powerful find out your vote",
    #"Q17d. Last countryal election: fear political intimidation or violence",
    #"Q18a. Last countryal election: police or soldiers assist people to cast ballot",
    #"Q18b. Last countryal election: voter intimidation",
    #"Q18c. Last countryal election: announced results reflect counted results",
    #"Q19a. Government bans organizations vs join any", 
    #"Q19b. Media free to publish vs government control", 
    #"Q20a. Reject one-party rule",
    #"Q20b. Reject military rule",
    #"Q20c. Reject one-man rule",
    #"Q21. Support for democracy",
    #"Q22. Govt gets things done vs govt accountable to citizens", 
    #"Q23. Listen to wisdom of elders vs fresh ideas from young people", 
    #"Q24. Choose leaders through elections vs other methods", 
    #"Q25. Political parties divisive vs many parties needed", 
    #"Q26. Elected officials  follow constituent demands vs follow own ideas", 
    #"Q27. Elected leaders empower most capable vs help people left behind", 
    #"Q28. Experts make most important decisions vs no need for experts", 
    #"Q29. President monitored by parliament vs free to act on own", 
    #"Q30. President free to act vs obey the laws and courts", 
    #"Q31. Election winner pursues preferred policies vs compromise w/others", 
    #"Q32. Popular govt free to do whatever people want vs always follow the law", 
    #"Q33. Media checks government vs avoid negative reporting", 
    #"Q34. Presidential two term limit vs no term limits", 
    #"Q35a. Minimum age for presidential candidate",
    #"Q35b. Suggested minimum age for presidential candidate",
    #"Q35c. Maximum age for presidential candidate",
    #"Q35d. Suggested maximum age for presidential candidate",
    #"Q36. Extent of democracy",
    #"Q37. Satisfaction with democracy",
    #"Q38a. MPs listen",
    #"Q38b. Local government councillors listen",
    #"Q38c. Traditional leaders listen",
    #"Q39a. Tax authorities have right to enforce taxes",
    #"Q39b. Government information for official use only",
    #"Q40a. How often party competition leads to conflict",
    #"Q40b. How often president ignores laws",
    #"Q40c. How often president ignores parliament",
    #"Q40d. How often careful what you say",
    #"Q40e. How often people treated unequally",
    #"Q40f. How often officials unpunished",
    #"Q40g. How often ordinary people unpunished",
    #"Q41a. Trust president",
    #"Q41b. Trust parliament/countryal assembly",
    #"Q41c. Trust countryal electoral commission",
    #"Q41d. Trust your elected local government council",
    #"Q41e. Trust the ruling party",
    #"Q41f. Trust opposition political parties",
    #"Q41g. Trust police",
    #"Q41h. Trust army",
    #"Q41i. Trust courts of law",
    #"Q41j. Trust tax/revenue office",
    #"Q41k. Trust traditional leaders",
    #"Q41l. Trust religious leaders",
    #"Q42a. Corruption: office of the Presidency",
    #"Q42b. Corruption: Members of Parliament",
    #"Q42c. Corruption: Civil servants",
    #"Q42d. Corruption: local government councillors",
    #"Q42e. Corruption: Police",
    #"Q42f. Corruption: Judges and Magistrates",
    #"Q42g. Corruption: Tax officials",
    #"Q42h. Corruption:Traditional leaders",
    #"Q42i. Corruption: Religious leaders",
    "Q43a. Level of corruption",
    #"Q43b. Ordinary people can report corruption without fear",
    #"Q44a. Contact with public school",
    #"Q44b. Difficulty to obtain public school services",
    #"Q44c. Pay bribe for public school services",
    #"Q44d. Contact with public clinic or hospital",
    #"Q44e. Difficulty to obtain medical care",
    #"Q44f. Pay bribe for medical care",
    #"Q44g. Tried to obtain identity document",
    #"Q44h. Difficulty to obtain identity document",
    #"Q44i. Pay bribe for identity document",
    #"Q44j. Requested assistance from the police",
    #"Q44k. Difficulty to obtain police assistance",
    #"Q44l. Pay bribe to receive police assistance",
    #"Q44m. Contact with police in other situations",
    #"Q44n. Pay bribe to avoid problem with police",
    #"Q45. Higher taxes w/more services vs lower taxes w/fewer services",
    #"Q46a. Difficulty to find out what taxes or fees to pay",
    #"Q46b. Difficulty to find out how government uses tax revenues",
    #"Q46c. Taxes for ordinary people: too little, too much, or right amount",
    #"Q46d. Taxes for the rich: too little, too much, or right amount",
    #"Q47a. Government should ensure informal sector pays taxes",
    #"Q47b. Fair for rich to pay higher taxes",
    #"Q47c. Taxes used by government for the well-being of citizens",
    #"Q47d. How often people avoid paying taxes",
    #"Q48pt1. Most important problems - 1st response",
    #"Q48pt1other. MIP - 1st response (verbatim)",
    #"Q48pt2. Most important problems - 2nd response",
    #"Q48pt2other. MIP - 2nd response (verbatim)",
    #"Q48pt3. Most important problems - 3rd response",
    #"Q48pt3other. MIP - 3rd response (verbatim)",
    #"Q49a. Support more taxes for youth programs",
    #"Q49b. Priorities for investment in youth programs",
    #"Q50a. Handling managing the economy",
    #"Q50b. Handling improving living standards of the poor",
    #"Q50c. Handling creating jobs",
    #"Q50d. Handling keeping prices stable",
    #"Q50e. Handling narrowing income gaps",
    #"Q50f. Handling reducing crime",
    #"Q50g. Handling improving basic health services",
    #"Q50h. Handling addressing educational needs",
    #"Q50i. Handling providing water and sanitation services",
    #"Q50j. Handling fighting corruption",
    #"Q50k. Handling maintaining roads and bridges",
    #"Q50l. Handling providing a reliable supply of electricity",
    #"Q50m. Handling preventing or resolving violent conflict",
    #"Q50n. Handling addressing the needs of young people",
    #"Q50o. Handling protecting rights, promoting opportunities for disabled",
    #"Q51a. Performance: President",
    #"Q51b. Performance: MP/countryal Assembly rep",
    #"Q51c. Performance: local government councillor",
    #"Q51d. Performance: traditional leader",
    #"Q52a. Who responsible: MPs do jobs",
    #"Q52b. Who responsible: president does job",
    #"Q53a. Elections ensure voters' views are reflected",
    #"Q53b. Elections enable voters to remove leaders from office",
    #"Q53c. Negative consequences if communities don't vote for ruling party",
    "Q54a. Feared violence in neighbourhood", # OUTCOME VARIABLE
    "Q54b. Feared violence during public protest", # OUTCOME VARIABLE
    "Q54c. Feared violence by extremists", # OUTCOME VARIABLE
    #"Q55a. Radio news",
    #"Q55b. Television news",
    #"Q55c. Newspaper news",
    #"Q55d. Internet news",
    #"Q55e. Social media news",
    "Q56. How free is news media",
    #"Q57a. Spread false information: government officials",
    #"Q57b. Spread false information: politicians and political parties",
    #"Q57c. Spread false information: news media and journalists",
    #"Q57d. Spread false information: social media users",
    #"Q57e. Spread false information: activists and interest groups",
    #"Q58a. Govt can prohibit sharing: news or information that is false",
    #"Q58b. Govt can prohibit sharing: news, information, or opinions that the government disapproves of",
    #"Q58c. Govt can prohibit sharing: criticism of president",
    #"Q58d. Govt can prohibit sharing: hate speech",
    #"Q59a. Heard about social media",
    #"Q59b. Social media: makes people more informed",
    #"Q59c. Social media: makes people more likely to believe false news",
    #"Q59d. Social media: helps people have more impact on politics",
    #"Q59e. Social media: makes people more intolerant",
    #"Q59f. Effects of social media on society",
    #"Q60. Unrestricted access to the Internet vs regulated access",
    #"Q61. Allow free movement in region vs limit cross-border movement",
    #"Q62. Difficulty to move across borders",
    #"Q63. Finance development from own resources vs use external loans",
    #"Q64a. Strict spending requirements on external loans vs govt decides",
    #"Q64b. Strict democracy conditions on external loans vs govt decides",
    #"Q65a. Know if country receives assistance from China",
    #"Q65b. Government required to repay China for loans",
    #"Q65c. Government borrowed too much money from China",
    #"Q65d.China puts more or less conditions on assistance",
    #"Q66. Open trade for development vs protect local producers",
    #"Q67. Only countryals trade vs allow foreigners to trade",
    #"Q68. Diverse communities stronger vs similar communities stronger", 
    #"Q69a. Best country model for development",
    #"Q69aother. Best country model for development (verbatim)",
    #"Q69b. China's influence on economy",
    #"Q70a. Influence of organization: African Union",
    #"Q70b. Influence of organization: regional alliance (EAC)",
    #"Q70c. Influence of organization: United countrys agencies",
    #"Q70d. Influence of country: former colonial power (Britain)",
    #"Q70e. Influence of country: China",
    #"Q70f. Influence of country: United States",
    #"Q70g. Influence of country: regional superpower",
    #"Q70h. Influence of country: Russia",
    #"Q71. Most important intercountryal language",
    #"Q71other. Most important intercountryal language (verbatim)",
    #"Q72a. Heard about climate change",
    #"Q72b. Climate change: affecting country",
    #"Q73. Free to move when public security threatened vs impose curfews",
    #"Q74. Government should monitor private communication vs right to privacy",
    #"Q75. Absolute freedom of religion vs government regulates what is said",
    "Q81. Ethnic community, cultural group or tribe",
    #"Q81other. Ethnic community, cultural group or tribe (verbatim)",
    "Q82a. Ethnic group treated unfairly by government",
    #"Q82b. Ethnic or countryal identity", 
    #"Q82c. Comfortable speaking mother tongue in public",
    #"Q82d. Comfortable wearing  traditional or cultural dress in public",
    #"Q83. Most people can be trusted",
    "Q84a. Unfair treatment by other people based on economic status",
    "Q84b. Unfair treatment by other people based on religion",
    "Q84c. Unfair treatment by other people based on ethnicity",
    #"Q85. More that unites or more that divides people",
    #"Q86a. Neighbours: people of different religion",
    #"Q86b. Neighbours: people of different ethnicity",
    #"Q86c. Neighbours: homosexuals",
    #"Q86d. Neighbours: immigrants and foreign workers",
    #"Q86e. Neighbours: people who support a different political party",
    #"Q87a. Influence of traditional leaders: governing local community",
    #"Q87b. Influence of traditional leaders: allocating land",
    #"Q87c. Influence of traditional leaders: votes",
    #"Q87d. Influence of traditional leaders: solving disputes",
    #"Q87e. Traditional leaders more or less influence",
    "Q88. Who traditional leaders serve", 
    #"Q89a. Traditional leaders advise on vote vs stay out of politics", 
    #"Q89b. Traditional leaders in competition with elected leaders vs cooperation", 
    #"Q90. Traditional leaders bad or good for democracy",
    #"Q91a. Close to political party",
    #"Q91b. Which party",
    #"Q91bother. Which party (verbatim)",
    #"Q92a. Own radio",
    #"Q92b. Own television",
    #"Q92c. Own motor vehicle, car or motorcycle",
    #"Q92d. Own computer",
    #"Q92e. Own bank account",
    #"Q92f. Own mobile phone",
    #"Q92g. Mobile phone access to internet",
    #"Q92h. How often use a mobile phone",
    #"Q92i. How often use the internet",
    #"Q93a. Source of water for household use",
    #"Q93b. Location of toilet or latrine",
    #"Q94a. Electric connection from mains",
    #"Q94b. Electricity available from mains",
    #"Q94c. Other source of electricity: available",
    #"Q94d. Other source of electricity: type",
    #"Q94e. Other source of electricity: owner",
    #"Q95a. Employment status",
    #"Q95b. Required to pay an income tax",
    "Q95c. Occupation of respondent",
    #"Q95cother. Occupation of respondent (verbatim)",
    #"Q95d. Employer of respondent",
    #"Q96a. Who decides how money is used",
    #"Q96b. Head of household", 
    "Q96c. Occupation of head of household",
    "Q97. Education of respondent",
    "Q98b. Religious group treated unfairly by government",
    #"Q100. Perceived survey sponsor",
    #"Time interview ended",
    #"Length of interview",
    #"Q101.  Gender of respondent",
    #"Q102.  Race of respondent",
    #"Q103. Language of interview",
    #"Q104. Type of shelter of respondent",
    #"Q105. Roof of respondent’s home",
    #"Q106. Others present",
    #"Q107a. Check with others",
    #"Q107b. Influence by others",
    #"Q107c. Approached by community/party representatives",
    #"Q107d. Feel threatened",
    #"Q107e. Physically threatened",
    #"Q108. Proportion difficulty answering",
    #"Q110a. Respondent friendly",
    #"Q110b. Respondent interested",
    #"Q110c. Respondent cooperative",
    #"Q110d. Respondent patient",
    #"Q110e. Respondent at ease",
    #"Q110f. Respondent honest",
    #"Q112. Interviewer Number",
    #"Q113. Interviewer’s age",
    #"Q114. Interviewer’s gender",
    #"Q115. Interviewer rural or urban",
    #"Q116. Interviewer's home language",
    #"Q117. Interviewer's ethnic group or tribe",
    #"Q118. Interviewer's education",
    #"Q119. Other spoken languages_first",
    #"Q119. Other spoken languages_second",
    #"Q119. Other spoken languages_third",
    #"Q119. Other spoken languages_fourth",
    #"Q119. Other spoken languages_fifth",
    #'within country weighting factor, weights to EA level ("old AB withinwt")',
    #'within country weighting factor, weights to HH level ("new AB withinwt")'
]

# Leaving only the question number in the list of variables

for i in range(0,len(valid_qs)):
	valid_qs[i]=valid_qs[i].split('. ')[0]

# Other relevant columns

other_cols=[
    "Respondent number",
    "EA Unique Number",
    'within country weighting factor, weights to EA level ("old AB withinwt")',
    'within country weighting factor, weights to HH level ("new AB withinwt")',
    "GPS Latitude in EA",
    "GPS Longitude in EA",
]

# Ethnic Power Relations rankings

epr_dict={'kenya': {
    1: np.nan,
    4: np.nan,
    300: 4,
    301: 2,
    302: 2,
    303: 2,
    304: 4,
    305: 3,
    306: 4,
    307: 4,
    308: 3,
    309: 2,
    310: 1,
    311: 2,
    312: 4
    },
    'southafrica': {
    700: 4,
    701: 4,
    702: 4,
    703: 4,
    704: 4,
    705: 4,
    706: 4,
    707: 4,
    708: 4,
    709: 4,
    710: 4,
    711: 4,
    712: 4
    },
    'nigeria': {
    620: 4,
    621: 3,
    622: 3,
    623: 2,
    624: 2,
    625: 4,
    626: 2,
    627: 2,
    628: 2,
    629: 2,
    630: 2,
    631: 2,
    632: 2,
    633: 2,
    634: 2,
    635: 2,
    636: 2,
    637: 2,
    638: 2,
    639: 2,
    640: 2,
    641: 2,
    642: 2,
    643: 2,
    644: 2
    },
    'ethiopia': {
    1340: 4,
    1341: 3,
    1342: 3,
    1343: 4,
    1344: 1,
    1345: 3,
    1346: 3,
    1347: 3,
    1348: 3,
    1349: 3,
    1350: 3,
    1351: 3,
    1352: 3,
    1353: 3,
    1354: 3,
    1355: 3,
    1356: 2,
    1357: 2,
    1358: 2,
    1359: 3,
    1360: 3
    }
}

# Valid values for the variables 

valid_values=dict()
valid_values['Q0']=[1,2]
valid_values['Q1']=range(18,130)
valid_values["Q3"]=[1,2]
valid_values["Q4b"]=[1,2,3,4,5]
valid_values["Q5"]=[0,1,2,3]
valid_values["Q7a"]=[0,1,2,3,4]
valid_values["Q10a"]=[1,2,3,4]
valid_values["Q43a"]=[1,2,3,4,5]
valid_values["Q54a"]=[0,1,2]
valid_values["Q54b"]=[0,1,2]
valid_values["Q54c"]=[0,1,2]
valid_values["Q56"]=[0,1,2,3]
valid_values["Q81"]=[1,2,3,4]
valid_values["Q82a"]=[0,1,2,3]
valid_values["Q84a"]=[0,1,2,3]
valid_values["Q84b"]=[0,1,2,3]
valid_values["Q84c"]=[0,1,2,3]
valid_values["Q88"]=[1,2,3]
valid_values["Q96c"]=[0,1]
valid_values["Q97"]=[0,1,2,3,4,5,6,7,8,9]
valid_values["Q98b"]=[0,1,2,3]

# Looping through the countries

for country in countries:

	folder='Afrobarometer/'+country_acronyms[country]+'/'

	db = pd.read_excel(folder+afrob_files[country]) # Afrobarometer dataframe

	# Distinguishing the columns containing the answers to the questions from the other columns;
	# renaming the columns so that their naming is the same regardless of country and doesn't contain spaces

	q_cols=[]
	q_cols2=[]

	for col in db.columns[0:]:

		if(col[0]=='Q'):
			q_cols.append(col)
			q_cols2.append(col.split('. ')[0])

	q_cols=["This interview, gender"]+q_cols # Renaming the gender question Q0
	q_cols2=["Q0"]+q_cols2

	# Dataframe containing only the columns with the responses

	db1=db.loc[:,q_cols]
	db1.columns=q_cols2

	db1=db1.loc[:,valid_qs]

	other_data=db.loc[:,other_cols]
	other_data['one']=1

	# Creating the variable distinguishing farmer from non-farmer heads of household

	db1.loc[db1.loc[:,'Q96c']==97,'Q96c']=db1.loc[db1.loc[:,'Q96c']==97,'Q95c'] 
	db1=db1.drop('Q95c', axis=1)

	db1.loc[db1.loc[:,'Q96c']>12,'Q96c']=np.nan
	db1.loc[(db1.loc[:,'Q96c']!=3) & (db1.loc[:,'Q96c']!=np.nan),'Q96c']=0
	db1.loc[db1.loc[:,'Q96c']==3,'Q96c']=1

	# Ranking the Respondents' ethnic groups according to Ethnic Power Relations data

	db1.loc[db1.loc[:,'Q81']>=9990,'Q81']=np.nan

	ethnic_power=epr_dict[country]
	max_ethnic=max(list(ethnic_power.keys()))

	if(country=='southafrica'):
		db1.loc[db1.loc[:,'Q81']>max_ethnic,'Q81']=4
	else:
		db1.loc[db1.loc[:,'Q81']>max_ethnic,'Q81']=2

	for key, value in ethnic_power.items():
		db1.loc[db1.loc[:,'Q81']==key,'Q81']=value

	# Masking responses that are not valid (e.g. "Don't know" answers)

	for key, value_list in valid_values.items():
		if(key in db1.columns):
			masked_col=db1.loc[:,key].mask(~np.isin(db1.loc[:,key],value_list))
			db1=db1.drop(key, axis=1)
			db1[key]=masked_col

	# Inserting the remaining columns into the dataframe

	db1['Respondent']=other_data['Respondent number']
	db1['EA_Num']=other_data['EA Unique Number']
	db1['EA_weight']=other_data['within country weighting factor, weights to EA level ("old AB withinwt")']
	db1['HH_weight']=other_data['within country weighting factor, weights to HH level ("new AB withinwt")']
	db1['Latitude']=other_data["GPS Latitude in EA"]
	db1['Longitude']=other_data["GPS Longitude in EA"]

	# Setting the "Don't know" answers of the outcome variables to zero

	db1.loc[db1['Q54a'].isna(), 'Q54a']=0
	db1.loc[db1['Q54b'].isna(), 'Q54b']=0
	db1.loc[db1['Q54c'].isna(), 'Q54c']=0

	# Saving the data to a CSV

	db1.to_csv(folder+country+'_afrob_vars.csv')
