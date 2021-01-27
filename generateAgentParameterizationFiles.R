

# This file is to generate agent parameterization files to ensure that all the
#   parameterizations across experiments are consistent where necessary. I could have done
#   this by setting a seed in Python, but random processes work weirdly on UF's HiperGator
#   and I figured this way is much safer.

numFemales = 100
numMales = 100

# Random conformity file
male = runif(100, min=0.3, max=0.7)
female = runif(100, min=0.3, max=0.7)
df1 = data.frame("male" = male, "female" = female)

# Conformist file
male = runif(100, min=2.5, max=3.0)
female = runif(100, min=2.5, max=3.0)
df2 = data.frame("male" = male, "female" = female)


# Random/moderate preference file
male = runif(100, min=0.3, max=0.7)
female = runif(100, min=0.3, max=0.7)
df3 = data.frame("male" = male, "female" = female)


# Opposite/complementary preference file
male1 = runif(50, min=0.7, max=1.0)
female1 = runif(50, min=0.05, max=0.3)

male2 = runif(50, min=0.05, max=0.3)
female2 = runif(50, min=0.7, max=1.0)

male = c(male1, male2)
female = c(female1, female2)
df4 = data.frame("male" = male, "female" = female)

initialTransfer = runif(100, min = 0.1, max = 0.6)

write.csv(df1, "moderateConformity.csv")
write.csv(df2, "highConformity.csv")
write.csv(df3, "moderatePreferences.csv")
write.csv(df4, "oppositePreferences.csv") 
write.csv(initialTransfer, "initialTransfer.csv") 
