import numpy as np
import importlib
import configManager
config = importlib.import_module(configManager.configName)
import normClass as nc
import agentClass as ac
import bargainClass as bc
import runtimeFunctions as rf
import time 
import csv
import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate
from collections import OrderedDict
import multiprocessing
from functools import partial
import itertools


def run(agents, norms):
	columnNames = ["timeStep"] + agents[0].reportStats()[0] + ["utility"] + ["aliceWage"]
	
	dataList = []
	config.pGlobal = config.initialAlicePrice

	for t in range(config.timeSteps):
		print("TIME: ", t)
		t0 = time.time()

		for norm in norms:
			norm.getMatrix()

			# # FOR FDOs (frequency-dependent outcomes):
			# if norm.name == "allAlices":
			# 	aIndex = [aIndex for aIndex, activity in enumerate(config.activities) if activity["name"] == "privateActivity1"][0]
			# 	# pLocal = rf.calculateFDPrice(norm, aIndex) # Option A
			# 	binPrices = rf.calculateFDPriceBins(norm, aIndex) # Option B

			# # For spousal threshold:
			# if norm.name == "allBobs":
			# 	normSpousalThreshold = norm.returnTopQuartileMean("spousalThreshold", "capital")

		config.changeLocalPrice(agents, config.pGlobal) # Change the local price based on uniformly increasing global price (no FDOs)

		# FOR FDOs:
		## config.changeLocalPrice(agents, pLocal) # Option A: Change the local price based on "yield"
		# config.changeLocalPriceBins(agents, binPrices, aIndex) # Option B: Change the local price based on "yield" and mobility bin
		
		for a in range(0, config.agentNumber,2):

			# Tiny agent learning I didn't do much with:
			# agents[a].adjustAttribute("spousalThreshold", normSpousalThreshold)

			# You CAN do this just once for one simulation, but you need more than 100,000 bargains to create uniqueness in agent trajectories. It doesn't add too much time where it is.
			inputCombinations = rf.generateInputCombinations(100000)
			inputColumns, leisureColumns = inputCombinations[0], inputCombinations[1] # Remember that if "leisure" isn't in config outputs, leisureColumns is basically None
			t1 = time.time()
			bargain = bc.Bargain(agents[a], agents[a+1], inputColumns, leisureColumns)
			bestBargain = bargain.findBestBargain()
			
			stats0 = [t] + agents[a].reportStats()[1] + [bestBargain[1]["bobUtil"]] + [config.pGlobal]
			stats1 = [t] + agents[a+1].reportStats()[1] + [bestBargain[1]["aliceUtil"]] + [config.pGlobal]
			dataList.append(stats0)
			dataList.append(stats1)

		print("That took: ", time.time() - t0)

	# print(tabulate(pd.DataFrame(np.array(dataList), columns = columnNames)[["timeStep", "ID", "privateActivity1_wage", "capital", "public good", "capital_hWeight", "public good_hWeight", "privateActivity1_time_input", "publicActivity_time_input", "theta"]], headers='keys', tablefmt='psql'))

	return pd.DataFrame(np.array(dataList), columns = columnNames)



initials = config.generatePopulationsAndNorms(config.agentNumber)
agents = initials[0]
norms = initials[1]
loadStart = 23
t0 = time.time()
df = run(agents, norms)
df.to_excel("CM_IHM_testOutput.xlsx", index = False)
print("Total time: ", time.time() - t0)





