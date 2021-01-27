import numpy as np
import importlib
import configManager
config = importlib.import_module(configManager.configName)
import normClass as nc
import agentClass as ac
import bargainClass as bc
import individualClass as ic
import unitaryHouseholdClass as uhc
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
import random

def run(agents, norms, origin, wageIncrease):
	columnNames = ["timeStep"] + agents[0].reportStats()[0] + ["utility"] + ["aliceWage"]
	
	dataList = []
	config.pGlobal = config.initialAlicePrice

	for t in range(0, endSim):
		print("TIME: ", t)
		t0 = time.time()

		for norm in norms:
			norm.getMatrix()

		# ========= WAGE CHANGE ======= ============== ============== ============== ============== ============== ============== ============== =======
		if t == wageTime:
			config.pGlobal += wageIncrease


		# NOTE! ==== ! ==== !
		# Because it's slow otherwise, I waited until wage change to make the "CM" males conformist, using the code below. 
		#   This should be uncommented for any simulations matching the "CM" conditions in the associated paper. This is also why the associated config files don't use
		#	the highConformity.csv file.
		# newConformity = pd.read_csv("highConformity.csv")["male"]
		# i = 0
		# for agent in agents:
		# 	if agent.ID % 2 == 0:
		# 		agent.normWeights = rf.generateNormWeights(newConformity[i], False)
		# 		i += 1
		# == ! == ! == ! == !

		config.changeLocalPrice(agents, config.pGlobal) # Change the local price based on uniformly increasing global price (no FDOs)
		# ======= ============== ============== ============== ============== ============== ============== ============== ======= ======= ============== 

		
		for a in range(0, config.agentNumber,2):

			# You CAN do this just once for one simulation, but you need more than 100,000 bargains to create uniqueness in agent trajectories. It doesn't add too much time where it is.
			inputCombinations = rf.generateInputCombinations(100000)
			inputColumns, leisureColumns = inputCombinations[0], inputCombinations[1] # Remember that if "leisure" isn't in config outputs, leisureColumns is basically None
			
			if origin == "framework": # IHM
				bargain = bc.Bargain(agents[a], agents[a+1], inputColumns, leisureColumns)
				bestBargain = bargain.findBestBargain()		
				stats0 = [t] + agents[a].reportStats()[1] + [bestBargain[1]["bobUtil"]] + [config.pGlobal]
				stats1 = [t] + agents[a+1].reportStats()[1] + [bestBargain[1]["aliceUtil"]] + [config.pGlobal]

			elif origin == "unitaryHousehold": # UM
				householdPortfolio = uhc.Household(agents[a], agents[a+1], inputColumns, leisureColumns)
				bestPortfolio = householdPortfolio.findBestPortfolio()
				stats0 = [t] + agents[a].reportStats()[1] + [bestPortfolio[1]["util"]] + [config.pGlobal]
				stats1 = [t] + agents[a+1].reportStats()[1] + [bestPortfolio[1]["util"]] + [config.pGlobal]

			else: # Individual (IM)
				portfolio1 = ic.Portfolio(agents[a], inputColumns[:, 0: config.numActivities*config.numInputs], leisureColumns[0])
				portfolio2 = ic.Portfolio(agents[a + 1], inputColumns[:, config.numActivities*config.numInputs: config.numActivities*config.numInputs*2], leisureColumns[1])
				bestPortfolio1 = portfolio1.findBestPortfolio()
				bestPortfolio2 = portfolio2.findBestPortfolio()
				stats0 = [t] + agents[a].reportStats()[1] + [bestPortfolio1[1]["util"]] + [config.pGlobal]
				stats1 = [t] + agents[a+1].reportStats()[1] + [bestPortfolio2[1]["util"]] + [config.pGlobal]


			dataList.append(stats0)
			dataList.append(stats1)

		print("That took: ", time.time() - t0)

	# print(tabulate(pd.DataFrame(np.array(dataList), columns = columnNames)[["timeStep", "ID", "privateActivity1_wage", "capital", "public good", "capital_hWeight", "public good_hWeight", "privateActivity1_time_input", "publicActivity_time_input", "theta"]], headers='keys', tablefmt='psql'))

	return pd.DataFrame(np.array(dataList), columns = columnNames)


endSim = 150
wageTime = 25

def wrapNrun(wageIncrease, filename):

	initials = config.generatePopulationsAndNorms(config.agentNumber)
	agents = initials[0]
	norms = initials[1]

	t0 = time.time()
	df = run(agents, norms, "framework",  wageIncrease)
	df.to_excel(filename, index = False)
	print("Total time: ", time.time() - t0)

wrapNrun(0.3, "MP_IHM_0pt4.xlsx")














