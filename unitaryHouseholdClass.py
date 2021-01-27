import importlib
import configManager
config = importlib.import_module(configManager.configName)
import runtimeFunctions as rf
import time
import math 
import numpy as np
np.set_printoptions(linewidth=300)



class Household():

	def __init__(self, agent1, agent2, inputColumns, leisureColumns):

		self.agent1 = agent1
		self.agent2 = agent2
		self.n = len(inputColumns[:,0])
		self.currentIndex = -1
		self.inputColumns = inputColumns

		self.output = np.zeros((self.n, len(config.outputTypes)))

		self.outputFilled = False

		self.temporaryMatrix = np.zeros((self.n, len(self.inputColumns[0,:]) + len(config.outputTypes) + 1))


		if "leisure" in config.outputTypes:
			leisureIndex = config.outputTypes.index("leisure")
			self.output[:,leisureIndex] = leisureColumns[:,0]



	def getOutput(self, activityIndex):
		# You have been given an index, which corresponds to the activity associated with the input vector, described in config.activities. This will tell you which function to use.
		# activity = config.activities[activityIndex]
		activity = config.activities[activityIndex]

		blockLength = config.numInputs*config.numActivities
		inputVector1 = self.inputColumns[:, np.arange(activityIndex, blockLength, config.numInputs)]*self.agent1.resources
		inputVector2 = self.inputColumns[:, np.arange(activityIndex + blockLength, blockLength*2, config.numInputs)]*self.agent2.resources


		if activity["public"]:
			inputVector = np.add(inputVector1, inputVector2)
			outputVector = getattr(rf, activity["outputFunction"])(None, inputVector, activity) 

		else:
			outputVector1 = getattr(rf, activity["outputFunction"])(self.agent1, inputVector1, activity)
			outputVector2 = getattr(rf, activity["outputFunction"])(self.agent2, inputVector2, activity)	
			outputVector = np.add(outputVector1, outputVector2)

		outputIndex = activity["outputIndex"]

		self.output[:, outputIndex] = np.add(self.output[:, outputIndex], outputVector)





	def assembleOutput(self):

		# For loop for activities because you have to call the functions explicitly, sorry.
		if not self.outputFilled:
			np.column_stack([self.getOutput(activityIndex) for activityIndex in np.arange(len(config.activities))])
			self.outputFilled = True


		# This is a bit sloppy -- Agent 1 and Agent 2 should have the same weights, but regardless you use the preferences associated with Agent 1. 
		#   This is a weird little thing that comes from not having an explicit Household class.
		# Option one (no norms):
		# util = np.sum(np.sqrt(self.output)*self.agent1.typeWeights, axis = 1)
		# Option two (norms):
		totalDistance = self.agent1.getNormativeDistance(self.inputColumns[:, 0: config.numActivities*config.numInputs], None) + self.agent2.getNormativeDistance(self.inputColumns[:, config.numActivities*config.numInputs: config.numActivities*config.numInputs*2], None)
		util = np.sum(np.sqrt(self.output)*self.agent1.typeWeights, axis = 1) * np.exp(-1*totalDistance)

		self.temporaryMatrix = np.column_stack((self.inputColumns, self.output, util))




	def findBestPortfolio(self):
		
		self.assembleOutput()
		bestPortfolio = self.temporaryMatrix[np.where(self.temporaryMatrix[:,-1] == np.max(self.temporaryMatrix[:,-1]))]

		portfolioInfo = {"util": bestPortfolio[0,-1]}

		self.agent1.inputVector = bestPortfolio[0, 0 : config.numInputs*config.numActivities]
		self.agent2.inputVector = bestPortfolio[0, config.numInputs*config.numActivities : config.numInputs*config.numActivities*2]
		self.agent1.agreedUponTransfer = None
		self.agent2.agreedUponTransfer = None


		outputStart = config.numInputs*config.numActivities 
		for outputIndex, outputType in enumerate(config.outputTypes):

			agentTypeOutput = bestPortfolio[0, outputStart + outputIndex]

			if outputType in config.inputTypes:
				self.agent1.resources[outputIndex] += agentTypeOutput
				self.agent2.resources[outputIndex] += agentTypeOutput

			elif outputType in config.nonInputTypes:
				self.agent1.nonInputResources[outputIndex] += agentTypeOutput
				self.agent2.nonInputResources[outputIndex] += agentTypeOutput


		# I don't remove spent resources because you always have the time available to you. If activities cost money (like planting a crop), you'd remove resources here.

		return [bestPortfolio, portfolioInfo]






























