# code by Oliver Haimson and John Schomberg
# last revised Jan. 2 2014

import os
# set this next line to wherever on your computer you keep the data file
os.chdir("/Users/oliverhaimson/Dropbox/Yelp epidemiology project/data")

import sys
import string
import urllib

import re
import datetime
from datetime import datetime, date, timedelta

from numpy import *
import numpy

# get list of restaurants from bizlist
# for each restaurant, find it in phoenixviolations csv
#       - in progress. right now we find about 40% of restaurants - can improve algorithm later
# open up the URL and grab (create variables for) dates & number of  violations
# for each restaurant and each date, search in Yelp dataset to get
#    number of violations in past X months
# get average time between Yelp violations - haven't done this yet 
# calculate correlation coefficient between Yelp data and health code data

# Yelp business data
bizData = []
IDs = []
names = []
addresses = []
url = []

# health code business data
indexInHC = []
namesHC = []
addressesHC = []
urlHC = []
source = []

# health code violation data
dateHC = []
numViolHC = []
IDsHC = []

# Yelp review violation data
dateY = []
IDsY = []
starsY = []

# Yelp review full data
dateYY = []
IDsYY = []
starsYY = []
reviewYY = []

numViolY = []
avgViol = []
avgStars = []

kw_list = ["sick"] # not actual dictionary - work in progress
data_kws = []
timeLen = 6 # number of months
trialNumber = 1000

def removeNonRestaurants():
    global bizData, indexInHC
    data = open("bizList.txt", "rU")
    for line in data:
        if "Restaurant" in line or "Food" in line or "Bar" in line:
            bizData.append(line)
    indexInHC = [0]*len(bizData)

def getRestaurantNames():
    global bizData, IDs, names, addresses
    for line in bizData:
        lineSplit = line.split("\":")
        IDs.append(lineSplit[1][2:-16])
        names.append(lineSplit[7][2:-17].lower())
        addresses.append(lineSplit[2].split("\\")[0][2:].lower())

def getPhoenixData():
    global namesHC, addressesHC, urlHC
    healthcode = open("phoenixviolations.csv", "rU")
    for line in healthcode:
        lineSplit = line.split(",")
        namesHC.append(lineSplit[2].lower())
        addressesHC.append(lineSplit[3].lower())
        urlHC.append(lineSplit[1])

def removePunctuation():
    global names, namesHC, addresses, addressesHC
    for i in range(len(names)):
        for punct in string.punctuation:
            names[i] = names[i].replace(punct,"")
            addresses[i] = addresses[i].replace(punct,"")
    for i in range(len(namesHC)):
        for punct in string.punctuation:
            namesHC[i] = namesHC[i].replace(punct,"")
            addressesHC[i] = addressesHC[i].replace(punct,"")
            
def findRestaurantInPhoenixData():
    global indexInHC, names, namesHC, addresses, addressesHC, source
    source = ["1"]*len(names)
    ind = 0
    for i in range(len(names)):
        for j in range(len(namesHC)):
            if (names[i] in namesHC[j]) and (addresses[i] in addressesHC[j]):
                indexInHC[ind] = addressesHC.index(addressesHC[j])
                source[ind] = "found"
        ind += 1

def exportRestaurantMatches():
    global indexInHC, names, namesHC, addresses, addressesHC, source
    namesHC[0] = "1"
    addressesHC[0] = "1"
    namesHCList = [0]*len(names)
    addressesHCList = [0]*len(names)
    i = 0
    for num in indexInHC:
        namesHCList[i] = namesHC[num]
        addressesHCList[i] = addressesHC[num]
        i += 1
    file = open("names3.csv", "wb")
    for x in range(len(names)):
        file.write(names[x] + ",")
        file.write(namesHCList[x] + ",")
        file.write(addresses[x] + ",")
        file.write(addressesHCList[x] + ",")
        file.write(source[x] + "\n")

def readURL():
    global indexInHC, url, urlHC, dateHC, numViolHC, IDsHC
    url = [0]*len(indexInHC)
    for i in range(len(indexInHC)):
        url[i] = urlHC[indexInHC[i]]
    c = 0
    for u in url[:trialNumber]:
        # scrape data from Maricopa site if we have a url for that restaurant
        # (currently ignores restaurants where we don't have a match between
        # Yelp dataset and Maricopa dataset)
        if len(u) > 0:
            try:
                html = urllib.urlopen(u).readlines()
                for line in html:
                    if "navigatedFrom=inspectionResultsDrillDown" in line:
                        # get the date and number of violations
                        linesplit = line.split(">")
                        date = linesplit[3][:-3]
                        dateObject = datetime.strptime(date, ('%m/%d/%Y'))
                        dateObject = datetime.date(dateObject)
                        dateHC.append(dateObject)
                        numViolHC.append(linesplit[8][:-6])
                        IDsHC.append(IDs[c])
            except IOError:
                print("IO error")
                print(u)
        c+=1
    for i in range(len(numViolHC)):
        if numViolHC[i] == "&nbsp;":
            numViolHC[i] = "0"
        numViolHC[i] = int(numViolHC[i])

def parseReviewData():
    global IDsYY, starsYY, dateYY, reviewYY
    data = open("fullData.txt")
    for line in data:
        lineSplit = line.split("\":")
        IDsYY.append(lineSplit[-1][2:-3])
        starsYY.append(int(lineSplit[7][1]))
        date = lineSplit[8][2:-8]
        dateObject = datetime.strptime(date, ('%Y-%m-%d'))
        dateObject = datetime.date(dateObject)
        dateYY.append(dateObject)
        # several scenarios so that we capture the full review
        if lineSplit[10] != " \"review\", \"business_id":
            review = lineSplit[9] + lineSplit[10]
        if lineSplit[11] != lineSplit[-1]:
            review = lineSplit[9] + lineSplit[10]
        if len(lineSplit) > 13:
            review = lineSplit[9] + lineSplit[10] + lineSplit[11]
        if len(lineSplit) > 14:
            review = lineSplit[9] + lineSplit[10] + lineSplit[11] + lineSplit[12]
        else:
            review = lineSplit[9]
        reviewYY.append(review)

# find out how many Yelp violations within timeLen months prior to date

def findYelpViolations():
    global kw_list, dateY, IDsY, starsY, reviewYY, dateYY, starsYY, IDSYY
    for i in range(0,len(reviewYY)):
        for kw in kw_list:
            if kw in reviewYY[i]:
                dateY.append(dateYY[i])
                starsY.append(starsYY[i])
                IDsY.append(IDsYY[i])
                #print(IDsY[-1])
                #print(review)
                #print(" ")
                break

def calculateTotals(index, dateEnd, dateBegin):
    global IDsHC, IDsYY, starsYY, dateYY
    totalReviews = 0
    totalStars = 0
    for i in range(0,len(IDsYY)):
        if IDsYY[i]==IDsHC[index]:
            if dateYY[i] < dateEnd and dateYY[i] > dateBegin:
                totalReviews += 1
                totalStars += starsYY[i]
    return (totalReviews, totalStars)

def matchYelpViolToHCViol():
    global dateHC, dateY, numViolY, IDsHC, IDsY, starsY, avgViol, avgStars
    numViolY = [0]*len(dateHC)
    avgViol = [0.0]*len(dateHC)
    avgStars = [0.0]*len(dateHC)
    for i in range(0,len(dateHC)):
        #### CHANGE CODE SOMEWHERE AROUND HERE
        dateEnd = dateHC[i]
        # average of 30.4375 days in a month * timeLen months
        dateBegin = dateHC[i] - timedelta(days = 30.4375*timeLen)
        [totalReviews, totalStars] = calculateTotals(i, dateEnd, dateBegin)
        totalReviews = float(totalReviews)
        for j in range(0,len(IDsY)):
            if IDsY[j]==IDsHC[i]:
                if dateY[j] < dateEnd and dateY[j] > dateBegin:
                    # Yelp violation occurred in 6 months prior to HC violation date
                    numViolY[i] += 1
        if totalReviews != 0: 
            avgViol[i] = float(numViolY[i]) / totalReviews
            avgStars[i] = float(totalStars) / totalReviews
    
def calculateCorrelation():
    global numViolHC, avgViolY
    c = corrcoef(numViolHC, numViolY)
    print(c)



        
removeNonRestaurants()
getRestaurantNames()
getPhoenixData()
removePunctuation()
findRestaurantInPhoenixData()
#exportRestaurantMatches()
readURL()
parseReviewData()
findYelpViolations()
matchYelpViolToHCViol()
calculateCorrelation()

