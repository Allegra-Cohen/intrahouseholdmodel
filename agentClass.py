import importlib
import configManager
config = importlib.import_module(configManager.configName)
import normClass as nc
import bargainClass as bc
import runtimeFunctions as rf
import math
import itertools
import time
import numpy as np

class Agent():
	def __init__(self, ID, householdID, agentType, resources, nonInputResources, typeWeights, normWeights, initialInputVector, initialTransfer, activityParams, spousalThreshold, alpha):
		self.ID = ID
		self.householdID = householdID
		self.agentType = agentType

		self.resources = resources # This is a LIST that corresponds by index to config.inputTypes
		self.nonInputResources = nonInputResources
		self.typeWeights = typeWeights # This is a LIST that has weights/preferences for output types as corresponding to config.outputTypes
		self.normWeights = normWeights # This is a LIST that has weights for the components used to calculate distance from a norm 
		
		self.inputVector = initialInputVector  # This is a vector which tells us how much of each input goes to which activities [input_1-to-activity-a, input_2-to-activity-a, input_1-to-activity-b, ...] 
		self.agreedUponTransfer = initialTransfer # This is the transfer arrangement agreed upon by the agent and the agent's spouse
		self.norms = []

		self.activityParams = activityParams # This should be an ordered dict so it writes out properly
		self.spousalThreshold = spousalThreshold

		self.bargainingPower = None

		self.alpha = alpha

	def reportStats(self):
		if config.thetaMin == None: # Indicating unitary model being used ==> taking out theta norm weight
			columnNames = ["ID", "hhID", "agentType"] + list(self.activityParams.keys()) + config.inputTypes + config.nonInputTypes + [output + "_hWeight" for output in config.outputTypes] + [activity["name"] + "_" + inputType + "_nWeight" for activity in config.activities for inputType in config.inputTypes] + [activity["name"] + "_" + inputType + "_input" for activity in config.activities for inputType in config.inputTypes] + ["theta", "spousalThreshold", "bargainingPower"]
		else:
			columnNames = ["ID", "hhID", "agentType"] + list(self.activityParams.keys()) + config.inputTypes + config.nonInputTypes + [output + "_hWeight" for output in config.outputTypes] + [activity["name"] + "_" + inputType + "_nWeight" for activity in config.activities for inputType in config.inputTypes] + ["theta_nWeight"] + [activity["name"] + "_" + inputType + "_input" for activity in config.activities for inputType in config.inputTypes] + ["theta", "spousalThreshold", "bargainingPower"]
		stats = [self.ID, self.householdID, self.agentType] + list(self.activityParams.values()) + list(self.resources) + list(self.nonInputResources) + list(self.typeWeights) + list(self.normWeights) + list(self.inputVector) + [self.agreedUponTransfer, self.spousalThreshold, self.bargainingPower]
		return [columnNames, stats]
		

	def adjustAttribute(self, attributeName, normAttribute):
		currentAttribute = getattr(self, attributeName)
		adjustedAttribute = min(1, max(0, (currentAttribute + self.alpha*(normAttribute - currentAttribute)))) # Straight from Beal Cohen (2019)
		setattr(self, attributeName, adjustedAttribute)


	def getNormativeDistance(self, inputBlock, fixedTheta):
		
		if len(self.norms) == 0:
			return 0

		else:
			distances = np.zeros(len(inputBlock[:,0]))

			for norm in self.norms:
				distance = np.sum(np.multiply(norm.getDistance(inputBlock, fixedTheta), np.array(self.normWeights)[:,np.newaxis].T), axis = 1)
				distances = np.add(distances, distance)

			# We add up the distances if there are multiple norms -- this assumes that norms have equal weight to an agent, which is a bad
			#   assumption but it's very easy to fix.
			return distances # Now we have a vector that we can column stack to be distances for each bargain








