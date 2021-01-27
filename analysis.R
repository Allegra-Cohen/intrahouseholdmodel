library('ggplot2')
library('dplyr')
library(openxlsx)
library('gridExtra')
source('multiplot.R')
library('xtable')

loadData <- function() {
  
  alldf = data.frame()
  for (suffix in c("0pt15", "0pt2", "0pt25", "0pt3", "0pt4", "0pt5", "0pt6", "0pt7", "0pt8", "0pt9", "1pt0", "1pt1")){  
    for (i in seq(1, 12)) {
      df = as.data.frame(readWorkbook(paste0("CM", i, "_", suffix, ".xlsx"), colNames = T))
      df$agentGender = rep(c("M", "F"),nrow(df)/2)
      
      # Need to add "initial conditions"/starting positions at t = 0 and bump all t by one:
      df$timeStep = df$timeStep + 1
      
      dfdup <- df[df$timeStep == 1,]
      dfdup$timeStep = 0
      dfdup$capital = 0
      dfdup$public.good = 0
      dfdup$bargainingPower = NA
      dfdup$theta = NA
      dfdup$utility = NA
      dfdup$privateActivity1_time_input[dfdup$agentGender == "M"] = 0.8
      dfdup$publicActivity_time_input[dfdup$agentGender == "M"] = 0.2
      dfdup$privateActivity1_time_input[dfdup$agentGender == "F"] = 0.2
      dfdup$publicActivity_time_input[dfdup$agentGender == "F"] = 0.8
      df = rbind(dfdup, df)
      
      df$origin = paste0("CM",i)
      if (nchar(suffix) == 5){
        df$wage = as.double(paste0(substr(suffix,1,1), ".", substr(suffix, nchar(suffix) - 1, nchar(suffix)))) 
      } else {
        df$wage = as.double(paste0(substr(suffix,1,1), ".", substr(suffix, nchar(suffix), nchar(suffix))))
      }
      df$uniqueID = paste0(df$ID,df$origin,suffix) # This is only used for grouping in plots
      df$uniqueHHID = paste0(df$hhID,df$origin,suffix)
      
      if (!("theta_nWeight" %in% colnames(df))) {
        df$theta_nWeight = NA
      }
      
      if  (!("aliceWage" %in% colnames(df))) { # Didn't have this in 1.1 files
        df$aliceWage = 1.1
      }
      
      # df$convergencePoint = NA
      # df$convergencePoint[df$agentGender == "F"] = findConvergencePoint(varianceEveryN(df[df$agentGender == "F",], 10),10)
      # df$convergencePoint[df$agentGender == "M"] = findConvergencePoint(varianceEveryN(df[df$agentGender == "M",], 10),10)
      # 
      alldf = rbind(df, alldf)
    } 
  }
  
  originType <- case_when(
    alldf$origin %in% c("CM1", "CM3", "CM5", "CM11") ~ 1,
    alldf$origin %in% c("CM7", "CM8", "CM9", "CM12") ~ 2,
    alldf$origin %in% c("CM2", "CM4", "CM6", "CM10") ~ 3,
  )
  #alldf$originType = factor(originType, labels = c("IM (Individual-based model)", "UM (Unitary household-based model)", "IHM (Intra-household model)"))
  alldf$originType = factor(originType, labels = c("IM", "UM", "IHM"))
  
  experiment <- case_when(
    alldf$origin %in% c("CM1", "CM2", "CM7") ~ 1,
    alldf$origin %in% c("CM3", "CM4", "CM8") ~ 3,
    alldf$origin %in% c("CM5", "CM6", "CM9") ~ 4,
    alldf$origin %in% c("CM10", "CM11", "CM12") ~ 2,
  )
  alldf$experiment = factor(experiment, labels = c("No Norms, Moderate Preferences", "CM (Conformist Males)", "MP (Moderate Preferences)", "Norms, Opposite Preferences"))
  #alldf$experiment = factor(experiment, labels = c("No Norms, Moderate Preferences", "Conformist Males", "Moderate Males", "Norms, Opposite Preferences"))
  alldf$utility = NA # Because you reported the utilities wrong when you ran the code, dumbass
  return(alldf)
}

householdContribution <- function(df) {
  hhC <- df %>%
    group_by(uniqueHHID, timeStep) %>%
    summarize(
      hhContribution = sum(publicActivity_time_input),
      aliceContribution = publicActivity_time_input[agentGender == "F"]/sum(publicActivity_time_input),
      timeStep = timeStep,
      uniqueID = uniqueID
    )
  return(hhC)
}

df <- loadData()
#hhC = householdContribution(df)
#df2 <- merge(hhC, df, by = intersect(names(hhC), names(df)))

apdf <- df %>% group_by(origin, wage, uniqueID, agentGender) %>%
  mutate(lag3 = (privateActivity1_time_input - lag(privateActivity1_time_input, 3))/(1 - lag(privateActivity1_time_input, 3)),
         lag1 = (privateActivity1_time_input - lag(privateActivity1_time_input, 1))/(1 - lag(privateActivity1_time_input, 1)),
         lag5 = (privateActivity1_time_input - lag(privateActivity1_time_input, 5))/(1 - lag(privateActivity1_time_input, 5)),
         totalChange = privateActivity1_time_input[timeStep == 150] - privateActivity1_time_input[timeStep == 26],
         totalThetaChange = theta[timeStep == 150] - theta[timeStep == 26])
#totalHHCChange = hhContribution[timeStep == 150] - hhContribution[timeStep = 26])

apdf = as.data.frame(apdf)

apdf = apdf[apdf$experiment != "No Norms, Moderate Preferences" & apdf$experiment != "Norms, Opposite Preferences",]
