import importlib
import configManager
config = importlib.import_module(configManager.configName)
import normClass as nc
import agentClass as ac
import bargainClass as bc
import time
import numpy as np
import pandas as pd
np.random.seed(1)

# Initialization functions: ================================= ================================= ================================= ================================= ================================= ================================= ================================= =================================
# This is for loading the behavior of agents once they've stabilized from some initial conditions
#   You need to run simulations until stable state to determine what that state is, but once
#     you've done that, you can load it in for different experiments instead of rerunning
# Note that this is hard-coded with column names and populations and won't work for different 
#   simulations if you change those
def loadInitialInputs(filename, timeStep, aliceNorm, bobNorm, theta):
	df = pd.read_excel(filename)
	bobs = df.loc[df.ID % 2 == 0]
	alices = df.loc[df.ID % 2 == 1]
	bobs = bobs.loc[bobs.timeStep == timeStep]
	alices = alices.loc[alices.timeStep == timeStep]

	for bob in bobNorm.population:
		myBob = bobs.loc[bobs.ID == bob.ID]
		bob.inputVector = [myBob.privateActivity1_time_input.item(), myBob.publicActivity_time_input.item()]
		if theta:
			bob.agreedUponTransfer = myBob.theta.item()

	for alice in aliceNorm.population:
		myAlice = alices[alices.ID == alice.ID]
		alice.inputVector = [myAlice.privateActivity1_time_input.item(), myAlice.publicActivity_time_input.item()]
		if theta:
			alice.agreedUponTransfer = myAlice.theta.item()



# Startup / bargain functions: ================================= ================================= ================================= ================================= ================================= ================================= ================================= =================================
def generateInputCombinations(n):
	inputBlock = np.random.random((n, config.numActivities*config.numInputs*2))
	

	t0 = time.time()
	# If agents are allowed to do nothing:
	if "leisure" in config.outputTypes:
		# This is a horrendous for loop. Sue me, I'm tired
		allCols = []
		for inputIndex, inputCols in zip(range(config.numInputs*2), np.split(inputBlock, config.numInputs*2, axis = 1)):
			if inputIndex == config.inputTypes.index("time") or inputIndex == (config.inputTypes.index("time") + config.numInputs):
				overOne = np.sum(inputCols, axis = 1) > 1
				inputCols[overOne] = np.true_divide(inputCols[overOne], np.sum(inputCols[overOne], axis = 1)[:,np.newaxis])
			else:
				inputCols = np.true_divide(inputCols, np.sum(inputCols, axis = 1)[:,np.newaxis])
			allCols.append(inputCols)
		inputBlock = np.hstack(allCols)
		inputBlock = inputBlock.round(config.inputStep)

		timeIndex = config.inputTypes.index("time")

		leisureBob = (1 - np.sum(inputBlock[:, timeIndex : timeIndex + config.numActivities], axis = 1))*config.totalTime
		leisureAlice = (1 - np.sum(inputBlock[:, timeIndex + config.numActivities*config.numInputs : timeIndex + config.numActivities + config.numActivities*config.numInputs], axis = 1))*config.totalTime
		leisureColumns = np.column_stack((leisureBob, leisureAlice))

		print(time.time() - t0)

	else:
		inputBlock = np.hstack([np.true_divide(inputCols, np.sum(inputCols, axis = 1)[:,np.newaxis]) for inputCols in np.split(inputBlock, config.numInputs*2, axis = 1)])
		inputBlock = inputBlock.round(config.inputStep)
		leisureColumns = np.column_stack((np.repeat(-1,n),np.repeat(-1,n)))

	return [inputBlock, leisureColumns]



def checkForStop(norms, limit, timeStep, timeStart, timeBlock):

	lastM = np.vstack([norm.lastNormMatrix for norm in norms])
	currentM = np.vstack([norm.normMatrix for norm in norms])

	if np.all(lastM != None):
		print(lastM, "\n")
		print(currentM, "\n")

		changeM = np.divide(np.abs(np.subtract(currentM, lastM)), lastM).flatten()

		print(np.round(changeM,3), "\n")

		meanM = np.nanmean(np.abs(changeM[np.isfinite(changeM)]))
		maxM = np.nanmax(np.abs(changeM[np.isfinite(changeM)]))
		medM = np.nanmedian(np.abs(changeM[np.isfinite(changeM)]))
		print("Mean change: ", meanM)
		print("Median change: ", medM)

		# if (changeM[np.isfinite(changeM)] <= limit).all():
		# 	return True

		if timeStep >= timeStart and timeStep % timeBlock == 0:
			inputString = "Mean change: " + str(round(meanM, 4)) +  ", median change: " + str(round(medM, 4)) + ", max change: " + str(round(maxM, 4)) +  ". Keep going? y/n      "
			keepGoing = input(inputString)

			if keepGoing.lower() == "y":
				return False
			else:
				return True



		




# Agent functions: ================================= ================================= ================================= ================================= ================================= ================================= ================================= =================================
# For now let's just have the weight be the same everywhere.
# Figure out how to apply specific weights some other time (maybe pass a list of dicts that have the activity and the input type and the intended weight)
def generateNormWeights(weight, justTheta):
	if config.thetaMin != None:
		nw = np.zeros(len(config.inputTypes)*len(config.activities)+1) # We just have ONE transfer type and it's capital
	else:
		nw = np.zeros(len(config.inputTypes)*len(config.activities)) # Indicating unitary model being used

	i = 0
	for activity in config.activities:
		for inputType in config.inputTypes:
			if inputType in activity["inputTypes"]:
				if justTheta:
					nw[i] = 0
				else:
					nw[i] = weight
			i += 1

	# For theta:
	if config.thetaMin != None: # Indicating unitary model being used
		nw[i] = weight
	return nw




# Activity functions: ================================= ================================= ================================= ================================= ================================= ================================= ================================= =================================

# Frequency-dependent gardening: Vanilla flavor. Select the relevant norm
# population, modify the price without worrying about mobility brackets.
def calculateFDPrice(norm, activityIndex):
	# Norm matrix is set up with rows as inputs and columns as agents -- rows are in order of agent.inputVector per activity + transfers
	#   Find the FD activity row and sum it

	# Get activity index AND time index -- NOTE, here we assume time = yield. If you wanted an output function SEPARATE from a payoff function,
	#   then you'd calculate output and sum that instead of just grabbing the time spent by agents. You'd also want to grab the resources of each
	#   agent in the case that some are more productive than others, etc.

	activityTimeIndex = (activityIndex*len(config.inputTypes)) + config.inputTypes.index("time")

	totalYield = np.sum(norm.normMatrix[activityTimeIndex, :])

	pLocal = config.pGlobal*np.exp(-1*config.a*totalYield)

	print("Total yield: ", totalYield)
	print("pLocal: ", pLocal)

	return pLocal


def FDPayoff(agent, inputVector, activity):
	time = inputVector[:, config.inputTypes.index("time")]
	try:
		price = agent.activityParams[activity["name"] + "_wage"]
	except:
		print("No price information for agent ", agent.ID)
	output = price*time
	return output








# Frequency-dependent activity with mobility bins.
def calculateFDPriceBins(norm, activityIndex):

	activityTimeIndex = (activityIndex*len(config.inputTypes)) + config.inputTypes.index("time")
	valueVector = norm.normMatrix[activityTimeIndex, :]
	# print(valueVector)
	bindices = np.digitize(valueVector, config.bins)
	# print(bindices)
	# binYields = [np.sum(valueVector[np.where(bindices == binNumber)]) for binNumber in range(len(config.bins))]

	# print("Yield:",binYields)

	# min(config.a, binNumber)
	binPrices = [config.pGlobal*np.exp(-1 * min(config.a, (binNumber/len(config.bins))) * np.sum(valueVector[np.where(bindices == binNumber)]) ) for binNumber in range(len(config.bins))]

	return binPrices








def cudevillePrivate(agent, inputVector, activity):
	
	# activityParams = activity["activityParams"] 
	time = inputVector[:, config.inputTypes.index("time")]

	try:
		wage = agent.activityParams[activity["name"] + "_wage"]
	except:
		print("No wage information for agent ", agent.ID)

	output = wage*time
	return output


def cudevillePublic(ID, inputVector, activity):
	
	activityParams = activity["activityParams"] 
	time = inputVector[:, config.inputTypes.index("time")]
	a = activityParams["a"]
	output = a*time
	return output







