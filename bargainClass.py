import importlib
import configManager
config = importlib.import_module(configManager.configName)
import runtimeFunctions as rf
import time
import math 
import numpy as np
np.set_printoptions(linewidth=300)


class Bargain():

	def __init__(self, bob, alice, inputColumns, leisureColumns):

		self.alice = alice
		self.bob = bob

		self.n = len(inputColumns[:,0])
		self.currentIndex = -1
		self.inputColumns = inputColumns

		self.aliceOutput = np.zeros((self.n, len(config.outputTypes)))
		self.bobOutput = np.zeros((self.n, len(config.outputTypes)))

		self.outputFilled = False

		# Temporary for use with each theta
		self.aliceWithTransfer = np.zeros((self.n, len(config.outputTypes)))
		self.bobWithTransfer = np.zeros((self.n, len(config.outputTypes)))
		self.temporaryMatrix = np.zeros((self.n, len(self.inputColumns[0,:]) + len(config.outputTypes)*4 + 2))


		# Okay, so I don't actually use leisure because it makes a slow model even slower. If you wanted to, you could. 
		if "leisure" in config.outputTypes:
			leisureIndex = config.outputTypes.index("leisure")
			self.bobOutput[:,leisureIndex] = leisureColumns[:,0]
			self.bobWithTransfer[:,leisureIndex] = leisureColumns[:,0]
			self.aliceOutput[:,leisureIndex] = leisureColumns[:,1]
			self.aliceWithTransfer[:,leisureIndex] = leisureColumns[:,1]



	def getOutput(self, activityIndex):
		# You have been given an index, which corresponds to the activity associated with the input vector, described in config.activities. This will tell you which function to use.
		activity = config.activities[activityIndex]

		blockLength = config.numInputs*config.numActivities
		inputVector1 = self.inputColumns[:, np.arange(activityIndex, blockLength, config.numInputs)]*self.bob.resources
		inputVector2 = self.inputColumns[:, np.arange(activityIndex + blockLength, blockLength*2, config.numInputs)]*self.alice.resources


		if activity["public"]:
			inputVector = np.add(inputVector1, inputVector2)
			outputVector = getattr(rf, activity["outputFunction"])(None, inputVector, activity) 
			outputVector1, outputVector2 = outputVector, outputVector.copy()

		else:
			outputVector1 = getattr(rf, activity["outputFunction"])(self.bob, inputVector1, activity)
			outputVector2 = getattr(rf, activity["outputFunction"])(self.alice, inputVector2, activity)	

		outputIndex = activity["outputIndex"]

		self.bobOutput[:, outputIndex] = np.add(self.bobOutput[:, outputIndex], outputVector1)
		self.aliceOutput[:, outputIndex] = np.add(self.aliceOutput[:, outputIndex], outputVector2)






	def assembleOutput(self, fixedTheta):

		# For loop for activities because you have to call the functions explicitly, sorry.
		#     Only fill Alice and Bob's outputs once per bargain (that is, once for all thetas).
		# 	  If you're reusing the bargain, you can reuse the last output.
		# 	  We DON'T include transfer operations here because the matrix gets enormous and it takes longer to store than to just recalculate.
		if not self.outputFilled:
			np.column_stack([self.getOutput(activityIndex) for activityIndex in np.arange(len(config.activities))])
			self.outputFilled = True

		# This is temporary for each theta, so you don't have to keep calculating basic outputs
		self.aliceWithTransfer, self.bobWithTransfer = self.aliceOutput.copy(), self.bobOutput.copy()

		# Deal with transfers now:
		# ASSUMPTION: All thetas are of capital type. This is a bad assumption (we'd like labor (input) transfers, clothing transfers, land transfers, etc.)
		if fixedTheta > 0:
			self.aliceWithTransfer[:, config.outputTypes.index("capital")] = np.add(self.aliceWithTransfer[:, config.outputTypes.index("capital")], self.bobWithTransfer[:, config.outputTypes.index("capital")]*fixedTheta)
			self.bobWithTransfer[:, config.outputTypes.index("capital")] = self.bobWithTransfer[:, config.outputTypes.index("capital")]*(1 - fixedTheta)

		else:
			fixedTheta = np.abs(fixedTheta)
			self.bobWithTransfer[:, config.outputTypes.index("capital")] = np.add(self.bobWithTransfer[:, config.outputTypes.index("capital")], self.aliceWithTransfer[:, config.outputTypes.index("capital")]*fixedTheta)
			self.aliceWithTransfer[:, config.outputTypes.index("capital")] = self.aliceWithTransfer[:, config.outputTypes.index("capital")]*(1 - fixedTheta)
		



		# If you care about what your spouse is doing with their time, add that to the withTransfer matrices.
		if config.spousalInterest != None:
			activityIndex = config.activities.index(config.spousalInterest)
			timeIndex = config.inputTypes.index("time")
			bobBonus = self.inputColumns[:, activityIndex + timeIndex].copy()
			aliceBonus = self.inputColumns[:, config.numInputs*config.numActivities + activityIndex + timeIndex].copy()

			if self.alice.spousalThreshold != None:
				bobBonus[bobBonus >= self.alice.spousalThreshold] = config.spousalThresholdBonus
				bobBonus[bobBonus < self.alice.spousalThreshold] = 1
			else:
				bobBonus.fill(1)

			if self.bob.spousalThreshold != None:
				aliceBonus[aliceBonus >= self.bob.spousalThreshold] = config.spousalThresholdBonus
				aliceBonus[aliceBonus < self.bob.spousalThreshold] = 1
			else:
				aliceBonus.fill(1)
		else:
			bobBonus, aliceBonus = 1, 1


		# TWO UTILITY OPTIONS: Multiplication or addition

		# Weight the outputs by type and then multiply them, and then add norms:
		# bobHUtil = np.product(np.sqrt(self.bobWithTransfer*self.bob.typeWeights), axis = 1) * np.exp(-1*self.bob.getNormativeDistance(self.inputColumns[:, 0: config.numActivities*config.numInputs], fixedTheta))
		# aliceHUtil = np.product(np.sqrt(self.aliceWithTransfer*self.alice.typeWeights), axis = 1) * np.exp(-1*self.alice.getNormativeDistance(self.inputColumns[:, config.numActivities*config.numInputs: config.numActivities*config.numInputs*2], fixedTheta))

		bobHUtil = bobBonus*np.sum(np.sqrt(self.bobWithTransfer)*self.bob.typeWeights, axis = 1) * np.exp(-1*self.bob.getNormativeDistance(self.inputColumns[:, 0: config.numActivities*config.numInputs], fixedTheta))
		aliceHUtil = aliceBonus*np.sum(np.sqrt(self.aliceWithTransfer)*self.alice.typeWeights, axis = 1) * np.exp(-1*self.alice.getNormativeDistance(self.inputColumns[:, config.numActivities*config.numInputs: config.numActivities*config.numInputs*2], fixedTheta))

		self.temporaryMatrix = np.column_stack((self.inputColumns, self.bobOutput, self.aliceOutput, self.bobWithTransfer, self.aliceWithTransfer, bobHUtil, aliceHUtil))




	def findMatchingRows(self, agentIndex, row):
		
		startIndex = agentIndex*config.numInputs*config.numActivities
		allAgentInputs = self.inputColumns[:, startIndex:startIndex + config.numInputs*config.numActivities]
		maskedInputs = allAgentInputs[:, config.publicIndices]
		maskedRow = row[startIndex:startIndex + config.numInputs*config.numActivities][config.publicIndices]
		options = self.temporaryMatrix[np.where((maskedInputs == maskedRow).all(axis=1))]

		return options






	def findEquilibrium(self):

		bestAliceOption = self.temporaryMatrix[np.where(self.temporaryMatrix[:,-1] == np.max(self.temporaryMatrix[:,-1]))][0] # We'll have some redundancies here
		
		for i in range(config.convergenceLoops):
			# "If you do that, then I'll do this"
			#     Grab Alice's proposed input, get Bob's best bargain
			bobOptions = self.findMatchingRows(1, bestAliceOption)
			bestBobOption = bobOptions[np.where(bobOptions[:, -2] == np.max(bobOptions[:,-2]))][0]
			aliceOptions = self.findMatchingRows(0, bestBobOption)
			bestAliceOption = aliceOptions[np.where(aliceOptions[:, -1] == np.max(aliceOptions[:,-1]))][0]

		return bestAliceOption




	def findBestBargain(self):
		
		self.assembleOutput(0)
		thetaMatrix = np.hstack((0, self.findEquilibrium())) # Separate spheres case
		for fixedTheta in np.arange(config.thetaMin, config.thetaMax, config.thetaStep):
			# Set up the matrix for this theta
			self.assembleOutput(fixedTheta)

			# Find the Cournot-Nash equilibrium for this theta and add it
			convergedBargain = self.findEquilibrium()
			thetaOutput = np.hstack((fixedTheta, convergedBargain))
			thetaMatrix = np.row_stack((thetaMatrix, thetaOutput))


		# Find the best bargain over all thetas using the objective function:
		separateSpheres = thetaMatrix[0,:]
		valid = thetaMatrix[(thetaMatrix[:,-1] >= separateSpheres[-1]) & (thetaMatrix[:,-2] >= separateSpheres[-2])]

		self.bob.bargainingPower = separateSpheres[-2]
		self.alice.bargainingPower = separateSpheres[-1]
		
		if valid.size == 0:
			return separateSpheres
		else:
			objectiveResult = (valid[:,-1] - separateSpheres[-1]) * (valid[:,-2] - separateSpheres[-2])
			valid = np.column_stack((valid, objectiveResult))
			bestBargain = valid[np.where(valid[:,-1] == np.max(valid[:,-1]))]

		bargainInfo = {"bobUtil": bestBargain[0,-3], "aliceUtil": bestBargain[0,-2]}



		self.bob.inputVector = bestBargain[0, 1 : 1 + config.numInputs*config.numActivities]
		self.alice.inputVector = bestBargain[0, 1 + config.numInputs*config.numActivities: 1 + config.numInputs*config.numActivities*2]
		self.bob.agreedUponTransfer = bestBargain[0,0]
		self.alice.agreedUponTransfer = bestBargain[0,0]


		outputStart = 1 + config.numInputs*config.numActivities*2 + len(config.outputTypes)*2 # Transfer index + resource-activity columns for Bob and alice + output columns for Bob and alice --> transfer columns is what you want
		for outputIndex, outputType in enumerate(config.outputTypes):

			bobTypeOutput = bestBargain[0, outputStart + outputIndex]
			aliceTypeOutput = bestBargain[0, outputStart + len(config.outputTypes) + outputIndex]

			if outputType in config.inputTypes:
				self.bob.resources[outputIndex] += bobTypeOutput
				self.alice.resources[outputIndex] += aliceTypeOutput

			elif outputType in config.nonInputTypes:
				self.bob.nonInputResources[outputIndex] += bobTypeOutput
				self.alice.nonInputResources[outputIndex] += aliceTypeOutput


		# I don't remove spent resources because you always have the time available to you. If activities cost money (like planting a crop), you'd remove resources here.

		return [bestBargain, bargainInfo]






























