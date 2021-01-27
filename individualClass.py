import importlib
import configManager
config = importlib.import_module(configManager.configName)
import runtimeFunctions as rf
import time
import math 
import numpy as np
np.set_printoptions(linewidth=300)



class Portfolio():

	def __init__(self, agent, inputColumns, leisureColumns):

		self.agent = agent
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
		activity = config.activities[activityIndex]

		blockLength = config.numInputs*config.numActivities
		inputVector = self.inputColumns[:, np.arange(activityIndex, blockLength, config.numInputs)]*self.agent.resources

		outputVector = getattr(rf, activity["outputFunction"])(self.agent, inputVector, activity)
		outputIndex = activity["outputIndex"]

		self.output[:, outputIndex] = np.add(self.output[:, outputIndex], outputVector)






	def assembleOutput(self):

		# For loop for activities because you have to call the functions explicitly, sorry.
		if not self.outputFilled:
			np.column_stack([self.getOutput(activityIndex) for activityIndex in np.arange(len(config.activities))])
			self.outputFilled = True

		util = np.sum(np.sqrt(self.output)*self.agent.typeWeights, axis = 1) * np.exp(-1*self.agent.getNormativeDistance(self.inputColumns[:, 0: config.numActivities*config.numInputs], None))

		self.temporaryMatrix = np.column_stack((self.inputColumns, self.output, util))




	def findBestPortfolio(self):
		
		self.assembleOutput()
		bestPortfolio = self.temporaryMatrix[np.where(self.temporaryMatrix[:,-1] == np.max(self.temporaryMatrix[:,-1]))]

		portfolioInfo = {"util": bestPortfolio[0,-1]}

		self.agent.inputVector = bestPortfolio[0, 0 : config.numInputs*config.numActivities]
		self.agent.agreedUponTransfer = None


		outputStart = config.numInputs*config.numActivities 
		for outputIndex, outputType in enumerate(config.outputTypes):

			agentTypeOutput = bestPortfolio[0, outputStart + outputIndex]

			if outputType in config.inputTypes:
				self.agent.resources[outputIndex] += agentTypeOutput

			elif outputType in config.nonInputTypes:
				self.agent.nonInputResources[outputIndex] += agentTypeOutput


		# I don't remove spent resources because you always have the time available to you. If activities cost money (like planting a crop), you'd remove resources here.

		return [bestPortfolio, portfolioInfo]






























