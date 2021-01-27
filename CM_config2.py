import normClass as nc
import agentClass as ac
import bargainClass as bc
import runtimeFunctions as rf
import itertools
import time
from collections import OrderedDict
import numpy as np
import pandas as pd

# Notes:  = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == 
#	This is the "moderate preferences" condition setup for the unitary household model (UM)    
# = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = == = 

# AGENT SECTION ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== 

def generateAgents(ID, hhID, preference, conformity, initialTheta, totalTime):

	resources = [totalTime]
	nonInputResources = [0]*len(nonInputTypes)
	
	normWeights = rf.generateNormWeights(conformity, False)
	typeWeights = [preference, 1 - preference]

	initialInputVector1 = [0.8, 0.2]
	initialInputVector2 = [0.2, 0.8]

	spousalThreshold = None
	initialTransfer = initialTheta
	leisureWeight = None
	alpha = None

	activityParams1 = OrderedDict([("privateActivity1_wage", initialBobPrice)])
	activityParams2 = OrderedDict([("privateActivity1_wage", initialAlicePrice)])

	agentType = None

	agent1 = ac.Agent(ID, hhID, agentType, resources, nonInputResources, typeWeights, normWeights, initialInputVector1, initialTransfer, activityParams1, spousalThreshold, alpha)
	agent2 = ac.Agent(ID + 1, hhID, agentType, resources, nonInputResources, typeWeights, normWeights, initialInputVector2, initialTransfer, activityParams2, spousalThreshold, alpha)

	return [agent1, agent2]


def changeAgentWage(agents, newWageBob, newWageAlice):
	for agent in agents:
		if agent.ID % 2 == 0:
			agent.activityParams["privateActivity1_wage"] = newWageBob
		else:
			agent.activityParams["privateActivity1_wage"] = newWageAlice




def changeLocalPrice(agents, newPriceAlice):
	for agent in agents:
		if agent.ID % 2 == 1:
			agent.activityParams["privateActivity1_wage"] = newPriceAlice



def changeLocalPriceBins(agents, binPrices, activityIndex):
	for agent in agents:
		if agent.ID % 2 == 1:
			# Find your bin
			activityTimeIndex = (activityIndex*len(inputTypes)) + inputTypes.index("time")
			binIndex = np.digitize(agent.inputVector[activityTimeIndex], bins)
			binPrice = binPrices[binIndex]
			agent.activityParams["privateActivity1_wage"] = binPrice



# POPULATION SECTION ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== 

def generatePopulationsAndNorms(agentNumber):

	agents = []
	alicePop = []
	bobPop = []

	preferencesFile = pd.read_csv("moderatePreferences.csv")
	conformityFile = pd.read_csv("moderateConformity.csv")

	i = 0
	for agentIndex in range(0, agentNumber, 2):
		# For random moderate preferences and conformity, it doesn't matter if you snag male or female, so just take the first n of either and assign it to a household.
		ba = generateAgents(agentIndex, agentIndex, preferencesFile["male"][i], conformityFile["male"][i], None, totalTime)
		bob, alice = ba[0], ba[1]

		agents = agents + [bob, alice]
		bobPop = bobPop + [bob]
		alicePop = alicePop + [alice]

		i += 1


	aliceNorm = nc.Norm("allAlices", alicePop, "euclideanDistance")
	bobNorm = nc.Norm("allBobs", bobPop, "euclideanDistance")

	norms = [aliceNorm, bobNorm]

	return [agents, norms]






# ACTIVITY SECTION ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== 

inputTypes = ["time"]  # Capital, time, land. Can be used for input-transfers AND resourceVectors.
numInputs = len(inputTypes)

outputTypes = ["capital", "public good"]
nonInputTypes = [ot for ot in outputTypes if ot not in inputTypes]
# Capital, land, goods, units of services. Can either be added to existing resources OR just used for utility calculation (e.g. one unit of "massage" costs money and does not return resources, but increases the utility of an agent during the time step.)
# We can consider how to do long-term investments like education, etc. later.
# We make an unfortunate assumption that all TRANSFERS are of CAPITAL after an activity is performed -- otherwise it gets too complicated for one small little PhD student to deal with.
# We'd like to be able to have input-transfers (ex. labor) and output-transfers (ex. subsistence crops, capital)


totalTime = 10

initialBobPrice = 0.6
initialAlicePrice = 0.1
pGlobal = 0.1
a = 0.2
bins = np.arange(0,1,0.1)

# This is cash crops for Bob and gardening for Alice:						
private1 = {"name": "privateActivity1", "public": False, "outputFunction": "cudevillePrivate", "inputTypes": ["time"], "outputType": "capital", "agentParams": {}, "activityParams": {}}
# This is housework:
public1 = {"name": "publicActivity", "public": True, "outputFunction": "cudevillePublic", "inputTypes": ["time"], "outputType": "public good", "agentParams": {}, "activityParams": {"a": 1}}
activities = [private1, public1]

spousalInterest = None
spousalThresholdBonus = None
alpha = None

for activity in activities:
	activity["outputIndex"] = outputTypes.index(activity["outputType"])

numActivities = len(activities)
isPublic = [activity["public"] for activity in activities]
publicIndices = np.array(list(itertools.chain.from_iterable(itertools.repeat(x, numInputs) for x in isPublic)))



# RUNTIME SECTION ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== 
inputStep = 2 # How many decimals for the matrix?
thetaMin, thetaMax, thetaStep = None, None, None
convergenceLoops = 10

timeSteps = 20
agentNumber = 200

# ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== ===== 
