import importlib
import configManager
config = importlib.import_module(configManager.configName)
import agentClass as ac
import bargainClass as bc
import runtimeFunctions as rf
import itertools
import numpy as np


class Norm():
	def __init__(self, name, population, distanceFunction):
		self.name = name
		self.population = population
		self.distanceFunction = distanceFunction # This is a string that can be used to call one of the many distance functions that will eventually live in a norm class instance.
		self.normMatrix = None
		self.lastNormMatrix = None

		# Make sure agents in the norm know they're in the norm
		# Can augment this in future to change membership
		for agent in self.population:
			agent.norms.append(self)


	def getDistance(self, inputBlock, fixedTheta):
		return getattr(self, self.distanceFunction)(inputBlock, fixedTheta)


	def getMatrix(self):
		if self.normMatrix is not None:
			self.lastNormMatrix = self.normMatrix.copy()

		agreedTheta = np.array(self.population[0].agreedUponTransfer)
		
		if agreedTheta == None: # This indicates we're using this code for a unitary model
			normMatrix = np.array(self.population[0].inputVector)
			for agent in self.population[1:]:
				column = np.array(agent.inputVector)
				normMatrix = np.column_stack((normMatrix, column))
		else:
			normMatrix = np.concatenate((np.array(self.population[0].inputVector), np.array([agreedTheta])))
			for agent in self.population[1:]:
				agreedTheta = np.array([agent.agreedUponTransfer])
				column = np.concatenate((np.array(agent.inputVector), agreedTheta))
				normMatrix = np.column_stack((normMatrix, column))

		# Now you have a matrix where rows are inputs to activities AND, at the bottom, transfers, and columns are agents in the population who committed those inputs and transfers in their last bargain.
		self.normMatrix = normMatrix



	def euclideanDistance(self, inputBlock, fixedTheta):

		if fixedTheta == None:
			agentBlock = inputBlock
		else:
			agentBlock = np.column_stack((inputBlock, np.repeat(fixedTheta, len(inputBlock[:,0]))))
		
		# Now you have a matrix where columns are components and rows are possible bargains.
		# self.normMatrix has columns of agents and rows of components.
		# However, it doesn't matter much because you're taking some statistic of the matrix anyways, which will get you a vector
		#   where each index is a component and the value is the statistic (here it's mean.)
		mu = self.normMatrix.mean(1) # Take average of each row (along the columns of agents, so for each input/transfer)

		# Now you need to operate on agentBlock to create a new column which has normative distance for each bargain. 
		#   So you need to take each row, subtract each of mu's elements from each of the row's elements, and square that.
		# Now you have a matrix where rows are still bargains, and columns are the distance from the norm for each component.
		# You'll pass that back to the agent function which will weight each component and add them up for each bargain
		#   to get a final, single distance number.

		return np.square((agentBlock - mu))


	def returnTopQuartileMean(self, attributeName, resourceType):
		if resourceType in config.nonInputTypes:
			sortedAgents = sorted(self.population, key=lambda x: x.nonInputResources[config.nonInputTypes.index(resourceType)], reverse=True)
		else:
			sortedAgents = sorted(self.population, key=lambda x: x.resources[config.inputTypes.index(resourceType)], reverse=True)

		quartileCutoff = len(sortedAgents)//4

		topQuartileAgents = sortedAgents[0:quartileCutoff]

		return np.mean([getattr(agent, attributeName) for agent in topQuartileAgents])


# TODO: 

	# def getSortedMatrix(self, resourceToSortBy, isInput):

	# 	# Definitely a cleaner way of doing this, I'll come back to it

	# 	if isInput:
	# 		resourceIndex = config.inputTypes.index(resourceToSortBy)
	# 		agreedTheta = self.minMaxScaling(np.array(self.population[0].agreedUponTransfer))

	# 		normMatrix = np.concatenate((np.array(self.population[0].inputVector), agreedTheta, np.array(self.population[0].resources[resourceIndex])))
	# 		for agent in self.population[1:]:
	# 			agreedTheta = np.array(agent.agreedUponTransfer)
	# 			column = np.concatenate((np.array(agent.inputVector), agreedTheta, np.array(agent.resources[resourceIndex])))
	# 			normMatrix = np.column_stack((normMatrix, column))
	# 	else:

	# 		resourceIndex = config.nonInputTypes.index(resourceToSortBy)
	# 		agreedTheta = np.array(self.population[0].agreedUponTransfer)
	# 		normMatrix = np.concatenate((np.array(self.population[0].inputVector), agreedTheta, np.array([self.population[0].nonInputResources[resourceIndex]])))
	# 		for agent in self.population[1:]:
	# 			agreedTheta = np.array(agent.agreedUponTransfer)
	# 			column = np.concatenate((np.array(ag ent.inputVector), agreedTheta, np.array([agent.nonInputResources[resourceIndex]])))
	# 			normMatrix = np.column_stack((normMatrix, column))

	# 	# Now you have a matrix where rows are inputs to activities AND, at the bottom, transfers, and columns are agents in the population who committed those inputs and transfers in their last bargain.

	# 	normMatrix = normMatrix.T[(-normMatrix).T[:,-1].argsort()].T # Best ones are at the beginning

	# 	self.normMatrix = normMatrix




	# def topQuartile(self, agentResourceVector, proposedTransferVector):
	# 	# Take the first 1/4 columns
	# 	numAgents = len(self.normMatrix[1,:])//4 # Get a number you can use
	# 	useMe = self.normMatrix[:,0:numAgents][:-1,:] # Don't use the column you used to sort
	# 	agentResourceVector = np.array(agentResourceVector)
	# 	proposedTransferVector = np.array(proposedTransferVector)

	# 	agentVector = np.concatenate((agentResourceVector, proposedTransferVector))
	# 	mu = useMe.mean(1) # Take average of each row (along the columns of agents, so for each input/transfer)

	# 	return (agentVector - mu)**2






















