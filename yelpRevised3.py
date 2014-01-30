# code by Oliver Haimson and John Schomberg
# last revised Nov. 7 2013

import os
# set this next line to wherever on your computer you keep the data file
os.chdir("/Users/oliverhaimson/Dropbox/Yelp epidemiology project/data")

import re
import datetime
from datetime import datetime, date, timedelta
import collections
from collections import defaultdict

# define global variables

filename = "fullData.txt"
kw_list = ["sick"]
# number of days between violations that signifies a cluster:
clusterThreshold = 180
# time increment determines how often we want to start new clusters:
timeIncrement = 90

data_kws = []
businessIDs = []
dates = []
reviews = []
stars = []
repeatViolations = []
IDs = []
names = []


def findViolations(filename):
    # use these global variables in this function
    global kw_list 
    global data_kws
    global businessIDs
    # read data into Python
    data = open(filename, "rU")
    # find reviews that include keywords
    for line in data: 
        for kw in kw_list:
            if kw in line:
                data_kws.append(line)
                # if we have already added it to the list, we don't need to keep checking for
                # keywords in that review, otherwise it may end up on our list twice
                break
    for line in data_kws:
        lineSplit = line.split("\":")
        businessIDs.append(lineSplit[-1][2:-3])
            

def removeNonRestaurants():
    global data_kws
    global businessIDs
    bizData = open("bizList.txt", "rU")
    for line in bizData:
        for j in businessIDs:
            if j in line and "Restaurant" not in line and "Food" not in line and "Bar" not in line:
                businessIDs.remove(j)
                for k in data_kws:
                    if j in k:
                        data_kws.remove(k)
                

def separateFields():
    global data_kws, businessIDS, dates, reviews, stars
    for line in data_kws:
        lineSplit = line.split("\":")
        date = lineSplit[8][2:-8]
        dateObject = datetime.strptime(date, ('%Y-%m-%d'))
        dateObject = datetime.date(dateObject)
        dates.append(dateObject)
        # may not capture the whole review - part of it may be split into [10]
        reviews.append(lineSplit[9])
        stars.append(lineSplit[7][1])


def findRepeatViolations():
    global businessIDs
    global repeatViolations
    # add business ID to list if there is more than one violation
    repeatViolations = [[x, y] for x, y in collections.Counter(businessIDs).items() if y > 1]

        
def findTimeBetweenViolations():
    global repeatViolations
    global businessIDs
    global dates
    global clusterThreshold
    for bizIndex in range(0, len(repeatViolations)):
        # find indeces in businessIDs list that match up with repeat violations
        indeces = [x for x, y in enumerate(businessIDs) if y==repeatViolations[bizIndex][0]]
        # sort dates, then determine time between each violation
        datesList = []
        for index in indeces:
            datesList.append(dates[index])
        datesList = sorted(datesList)
        findClusters(datesList, bizIndex)
        

def findClusters(datesList, bizIndex):
    global clusterThreshold
    global repeatViolations
    repeatViolations[bizIndex].append([])
    repeatViolations[bizIndex].append([])
    end = datetime.date(datetime.today())
    begin = end - timedelta(days = clusterThreshold)
    while end > min(datesList):
        violationCount = 0
        for date in datesList:
            if date < end and date > begin:
                violationCount += 1
        if violationCount > 1:
            repeatViolations[bizIndex][2].append([[begin],[end]])
            repeatViolations[bizIndex][3].append(violationCount)
        end -= timedelta(days = timeIncrement)
        begin -= timedelta(days = timeIncrement)


def matchBusinessIDsToNames():
    global IDs
    global names
    global businessIDs
    global repeatViolations
    biz = []
    bizData = open("bizList.txt", "rU")
    # find businesses in the list who have repeat violations
    for line in bizData:
        for i in repeatViolations:
            if i[0] in line:
                biz.append(line)
    for line in biz:
        lineSplit = line.split("\":")
        IDs.append(lineSplit[1][2:-16])
        names.append(lineSplit[7][2:-17])
    # add business name to the repeatViolations matrix
    for line in repeatViolations:
        for j in range(0,len(IDs)):
            if line[0] == IDs[j]:
                line.append(names[j])           


def outputBusinessesWithMultipleViolations():
    global repeatViolations
    global clusterThreshold
    file = open ("results.txt", "wb")
    for bizIndex in repeatViolations:
        file.write("Business ID: "  + str(bizIndex[0]) + "\n")
        file.write("Business name: " + str(bizIndex[4]) + "\n")
        file.write("Total violations: " + str(bizIndex[1]) + "\n")
        for i in range(0, len(bizIndex[3])):
            file.write("Number of violations between " + str(bizIndex[2][i][0][0]) + " and " + str(bizIndex[2][i][1][0]) + ": " + str(bizIndex[3][i]) + "\n")
        file.write("\n")
    file = open ("results.csv", "wb")
    file.write("business, violations\n")
    for bizIndex in repeatViolations:
        file.write(str(bizIndex[4]) + ",")
        file.write(str(bizIndex[1]) + "\n")

        
    
findViolations(filename)
removeNonRestaurants()
separateFields()
findRepeatViolations()
findTimeBetweenViolations()
matchBusinessIDsToNames()
outputBusinessesWithMultipleViolations()






