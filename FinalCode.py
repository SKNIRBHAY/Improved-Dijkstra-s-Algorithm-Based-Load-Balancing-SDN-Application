#!/usr/bin/env python

import requests
import json
import unicodedata
from subprocess import Popen, PIPE
import time
import networkx as nx
from sys import exit
import os


# Parses JSON Data To Find all the host information
def hostInformation(data):
	global switch #Store all hosts IP address and the MAC of the switch to which it is connected
	global deviceMAC # All hosts IP addresses and corresponding MAC addresses
	global hostPorts # ALL hosts IP, Last octet of the MAC of switch to which it is connected and the port number to which it is connected 
	switchDPID = ""
	for i in data['devices']:
		if(i['ipv4']):
			ip = i['ipv4'][0].encode('ascii','ignore')
			mac = i['mac'][0].encode('ascii','ignore')
			deviceMAC[ip] = mac
			for j in i['attachmentPoint']:
				for key in j:
					temp = key.encode('ascii','ignore')
					if(temp=="switch"):
						switchDPID = j[key].encode('ascii','ignore')
						switch[ip] = switchDPID
					elif(temp=="port"):
						portNumber = j[key]
						switchShort = switchDPID.split(":")[7]
						hostPorts[ip+ "::" + switchShort] = str(portNumber)
	print("\n\nSwitch: " + str(switch))
	print("\n\ndeviceMAC: " + str(deviceMAC))
	print("\n\nhostPort: " + str(hostPorts))


# Parses JSON Data To Find all the link information

def linksInformation(data,s):
	global switchLinks
	global linkPorts
	global G
	global linkLatency

	links=[]
	count = 0;
	for i in data:
		src = i['src-switch'].encode('ascii','ignore')
		dst = i['dst-switch'].encode('ascii','ignore')

		srcPort = str(i['src-port'])
		dstPort = str(i['dst-port'])

		latency = str(i['latency'])

		srcTemp = src.split(":")[7]
		dstTemp = dst.split(":")[7]

		G.add_edge(int(srcTemp,16), int(dstTemp,16))

		tempSrcToDst = srcTemp + "::" + dstTemp
		tempDstToSrc = dstTemp + "::" + srcTemp

		portSrcToDst = str(srcPort) + "::" + str(dstPort)
		portDstToSrc = str(dstPort) + "::" + str(srcPort)

		linkPorts[tempSrcToDst] = portSrcToDst
		linkPorts[tempDstToSrc] = portDstToSrc

		linkLatency[tempSrcToDst] = latency
		linkLatency[tempDstToSrc] = latency

		if (src==s):
			links.append(dst)
		elif (dst==s):
			links.append(src)
		else:
			continue

	switchID = s.split(":")[7]
	switchLinks[switchID]=links
	print("The Graph: ")
	print(list(G.edges()))
	print("\n\nThe switchLinks: "),
	print(switchLinks)
	print("\n\nThe linkPort: "),
	print(linkPorts)
	print("\n\nThe linkLatency: "),
	print(linkLatency)

# Parses JSON Data To Find the list of all shortest paths from source to destination

def findSwitchRoute():
	global path
	pathKey = ""
	nodeList = []
	src = int(switch[h2].split(":",7)[7],16)
	dst = int(switch[h1].split(":",7)[7],16)
	#temp = nx.all_shortest_paths(G, source=src, target=dst, weight=None)

	for currentPath in nx.all_shortest_paths(G, source=src, target=dst, weight=None):
		for node in currentPath:
			tmp = ""
			if node < 17:
				pathKey = pathKey + "0" + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:0" + str(hex(node)).split("x",1)[1]
			else:
				pathKey = pathKey + str(hex(node)).split("x",1)[1] + "::"
				tmp = "00:00:00:00:00:00:00:" + str(hex(node)).split("x",1)[1]
			nodeList.append(tmp)

		pathKey=pathKey.strip("::")
		path[pathKey] = nodeList
		pathKey = ""
		nodeList = []

	print("\n\nThe path: "),
	print(path);

############################################################
# Computation of total switch latency in all shortest paths

def totalPathLatency():
	global path;
	url = "http://192.168.56.101:8080/wm/core/switch/all/flow/json"
	getResponse(url,"findSwitchLatency")
	findLinkLatency()
	print("\n\nThe total PathLatency: ", pathLatency)

########################################################################
# Computation of total latency offered by the links in the shortest path
def findLinkLatency():
	global linkLatency
	global pathLatency

	for key in pathLatency:
		temp1 = key.split('::')
		length = len(temp1) 
		count = 1
		for i in temp1:
			temp2 = i + '::' + temp1[count]
			pathLatency[key] = str(int(pathLatency[key]) + int(linkLatency[temp2]))
			count += 1
			if count == length:
				break

###########################################################
# Calculate the total switch latency 
def findSwitchLatency(data):
	global path
	global pathLatency
	global tempLatency
	for key in path:
		for switch in path[key]:
			tempSec = int(data[switch]['flows'][0]['duration_sec'])
			tempByte = int(data[switch]['flows'][0]['byte_count'])
			if tempByte == 0: tempByte = 1;
			tempLatency += 100 * (tempSec/tempByte)
		pathLatency[key] = tempLatency
		tempLatency = 0


##########################################################			
# Computation total transmission rate in a path

def costComputaion(data,key):
	global cost
	port = linkPorts[key]
	port = port.split("::")[0]
	for i in data:
		if i['port']==port:
			cost = cost + (int)(i['bits-per-second-tx'])

#########################################################
# Computation total transmission rate in a path

def getLinkCost():
	global portKey
	global cost
	global linkPorts

	for key in path:
		start = switch[h2]
		src = switch[h2]
		srcShortID = src.split(":")[7]
		mid = path[key][1].split(":")[7]
		for link in path[key]:
			temp = link.split(":")[7]

			if srcShortID==temp:
				continue
			else:
				portKey = srcShortID + "::" + temp
				portNumber = linkPorts[portKey].split("::")[0]
				stats = "http://192.168.56.101:8080/wm/statistics/bandwidth/" + src + "/" + portNumber +"/json"
				getResponse(stats,"costComputaion")
				srcShortID = temp
				src = link
		portKey = start.split(":")[7] + "::" + mid + "::" + switch[h1].split(":")[7]
		finalLinkTX[key] = cost
		cost = 0
		portKey = ""
	print("finalLinkTX: "),
	print(finalLinkTX)

####################################################
# Setting up of Flow Rule 
####################################################
def systemCommand(cmd):
	terminalProcess = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	terminalOutput, stderr = terminalProcess.communicate()

###################################################
# creating and pushing the flow rules 
def flowRule(currentNode, flowCount, inPort, outPort, staticFlowURL):
	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    	"name":"flow" + str(flowCount),
	    	"cookie":"0",
	    	"priority":"32768",
	    	"in_port":inPort,
		"eth_type": "0x0800",
		"ipv4_src": h2,
		"ipv4_dst": h1,
		"eth_src": deviceMAC[h2],
		"eth_dst": deviceMAC[h1],
	    	"active":"true",
	    	"actions":"output=" + outPort
	       }

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

	flowCount = flowCount + 1

	flow = {
		'switch':"00:00:00:00:00:00:00:" + currentNode,
	    	"name":"flow" + str(flowCount),
	    	"cookie":"0",
	    	"priority":"32768",
		"in_port":outPort,
		"eth_type": "0x0800",
		"ipv4_src": h1,
		"ipv4_dst": h2,
		"eth_src": deviceMAC[h1],
		"eth_dst": deviceMAC[h2],
	    	"active":"true",
	    	"actions":"output=" + inPort
	       }

	jsonData = json.dumps(flow)

	cmd = "curl -X POST -d \'" + jsonData + "\' " + staticFlowURL

	systemCommand(cmd)

########################################
# Pushing the flow rules into the switches in the path
def addFlow():
	global LBType
	#print "KAAM CHALU HAI"

	Deleting Flow
	cmd = "curl -X DELETE -d \'{\"name\":\"flow1\"}\' http://192.168.56.101:8080/wm/staticflowpusher/json"
	systemCommand(cmd)

	cmd = "curl -X DELETE -d \'{\"name\":\"flow2\"}\' http://192.168.56.101:8080/wm/staticflowpusher/json"
	systemCommand(cmd)

	flowCount = 1
	staticFlowURL = "http://192.168.56.101/wm/staticflowpusher/json"
	
	if(LBType == 1):
		count = 1
		for key in finalLinkTX:
			if count == 1:
				maximum = int(finalLinkTX[key])
				maxKey = key
				count = 2
			else:
				current = int(finalLinkTX[key])
				if current >= maximum:
					maximum = current
					maxKey = key
		shortestPath = maxKey
	if(LBType == 2):
		shortestPath = min(pathLatency, key=pathLatency.get)
	print("\n\nBest Shortest Path: ",shortestPath)

	currentNode = shortestPath.split("::",2)[0]
	nextNode = shortestPath.split("::")[1]

	# Port Computation

	port = linkPorts[currentNode+"::"+nextNode]
	outPort = port.split("::")[0]
	inPort = hostPorts[h2+"::"+switch[h2].split(":")[7]]

	flowRule(currentNode,flowCount,inPort,outPort,staticFlowURL)

	flowCount = flowCount + 2

	bestPath = path[shortestPath]
	previousNode = currentNode

	for currentNode in range(0,len(bestPath)):
		if previousNode == bestPath[currentNode].split(":")[7]:
			continue
		else:
			port = linkPorts[bestPath[currentNode].split(":")[7]+"::"+previousNode]
			inPort = port.split("::")[0]
			outPort = ""
			if(currentNode+1<len(bestPath) and bestPath[currentNode]==bestPath[currentNode+1]):
				currentNode = currentNode + 1
				continue
			elif(currentNode+1<len(bestPath)):
				port = linkPorts[bestPath[currentNode].split(":")[7]+"::"+bestPath[currentNode+1].split(":")[7]]
				outPort = port.split("::")[0]
			elif(bestPath[currentNode]==bestPath[-1]):
				outPort = str(hostPorts[h1+"::"+switch[h1].split(":")[7]])

			flowRule(bestPath[currentNode].split(":")[7],flowCount,str(inPort),str(outPort),staticFlowURL)
			flowCount = flowCount + 2
			previousNode = bestPath[currentNode].split(":")[7]


########################################
# Method To Get REST Data In JSON Format
def getResponse(url,choice):

	response = requests.get(url)

	if(response.ok):
		jData = json.loads(response.content)
		if(choice=="deviceInfo"):
			hostInformation(jData)
		elif(choice=="linksInformation"):
			linksInformation(jData,switch[h2])
		elif(choice=="costComputaion"):
			costComputaion(jData,portKey)
		elif(choice=="findSwitchLatency"):
			findSwitchLatency(jData)
	else:
		response.raise_for_status()

###################################
# Method To Perform Load Balancing
def loadbalance():
	global LBType
	linkURL = "http://192.168.56.101:8080/wm/topology/links/json"
	getResponse(linkURL,"linksInformation")
	findSwitchRoute()
	if(LBType == 1):
		getLinkCost()
	if(LBType == 2):
		totalPathLatency()
	addFlow()


########## Main ###############
# Stores H1 and H2 from user
global h1,h2,h3

h1 = ""
h2 = ""

print "Enter the source host"
h1 = int(input())
print("\nEnter the destination host")
h2 = int(input())

h1 = "10.0.0." + str(h1)
h2 = "10.0.0." + str(h2)

while(1):
	print("\nWhich Scheem of load balancing do you want? (Tx 'or' NW/EW/Latency): ")
	print("1. Band width scheme \n2. NW/EW scheme\n")
	print("Press 1 or 2: ", end='')
	LBType = int(input())
	if(LBType == 1 or LBType == 2):
		break
	else:
		print("Wrong entry, try again !!! \n")
		continue

##############################
while True:
	print "######################################################################### SHRI GANESHAE NAMAH !!! #########################################################################"
	# Stores Info About H3 And H4's Switch
	switch = {}

	# Mac of H3 And H4
	deviceMAC = {}

	# Stores Host Switch Ports
	hostPorts = {}

	# Stores Switch To Switch Path
	path = {}

	# Switch Links

	switchLinks = {}

	# Stores Link Ports
	linkPorts = {}

	# Stores the dictionary of links and their latency
	linkLatency = {} 

	# Stores the sum of switch latencys of all switches in a path
	pathLatency = {}

	# Temporarilly Stores the latency of a switch
	tempLatency = 0

	# Stores Final Link Rates
	finalLinkTX = {}

	# Store Port Key For Finding Link Rates
	portKey = ""

	# Stores Link Cost
	cost = 0

	# Store total Link Latency
	totalLatency = 0

	# Graph
	G = nx.Graph()

	try:
		#############################################
		# Enables Statistics Like B/W, etc
		enableStats = "http://192.168.56.101:8080/wm/statistics/config/enable/json"
		requests.put(enableStats)
		# Device Info (Switch To Which The Device Is Connected & The MAC Address Of Each Device)
		url = "http://192.168.56.101:8080/wm/device/"
		getResponse(url,"deviceInfo")
		# Load Balancing
		loadbalance()
		os.system('clear')

	except KeyboardInterrupt:
		print("Error Found !!! Please retry...")
		break
		exit()
