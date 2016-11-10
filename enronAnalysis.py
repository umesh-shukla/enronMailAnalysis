"""
Main file which takes input directory of Enron Mail files as input and processes
all the sub-directories and loads the result in mySQL DB. 
It also queries DB for the specific questions that were asked in coding challenge. 
"""

import os
import sys
import datetime
import time 
from parser import Parser
from mysqldb import MySqlDB 

# Add new rows for every mail file to mySQL DB
def writeToDB(parsedObj): 
	db = MySqlDB()
	
	# Insert into EnronTeam Table
	for receiver in parsedObj['Receivers']:
		db.insert('EnronTeam', (parsedObj['msg_id'], datetime.datetime.strptime(parsedObj['Date'],'%d %b %Y').strftime('%Y-%m-%d'), \
		parsedObj['Sender'], receiver, parsedObj['Label']))
		
	# Insert into EnronMails Table
	db.insert('EnronMails', (parsedObj['msg_id'], parsedObj['TimeStamp'], \
	parsedObj['Subject'], parsedObj['if_response'], parsedObj['ResponseTime']))

	
def queryDB(queryKey): 
	# Table holding all queries
	queryTable = {
					# Q1: How many emails did each person receive each day?
					'Query1': """select distinct(Receiver), date, count(MailID) from EnronTeam \
								where receiver != '' \
								group by date, Receiver \
								order by date, Receiver""",
								 
					# Q2.1: who received the largest number of direct emails 
					'Query2.1': """select Receiver, count(MailID) from EnronTeam \
								where Label = 'Direct' and receiver != '' \
								group by Receiver having count(MailID) = \
								(select max(Y.MailCount) from (select Receiver, count(MailID) as MailCount from EnronTeam \
								where Label = 'Direct' and receiver != '' \
								group by Receiver) Y)""", 
								
					# Q2.2:  who sent the largest number of broadcast emails
					'Query2.2': """select Sender, count(MailID) from EnronTeam \
								where Label = 'Broadcast' \
								group by Sender having count(MailID) = \
								(select max(Y.MailCount) from (select Sender, count(MailID) as MailCount from EnronTeam \
								where Label = 'Broadcast' group by Sender) Y)""", 
								
					# Q3: Find the five emails with the fastest response times
					'Query3': """select MailID, subject, ResponseTime from EnronMails \
								where ResponseTime > 0 and ifResponse = 1 \
								order by ResponseTime limit 5"""
				 }
				 
	db = MySqlDB()
	return db.query(queryTable[queryKey])

# Main function
if __name__ == "__main__":

	if len(sys.argv) != 2:
		print("Usage Error: python enronAnalysis.py $input_dir")
		exit(-1)
	
	# input directory
	mainDir = sys.argv[1]
	
	# Go through all the sub-dirs and parse text files in them
	for root, subdirs, files in os.walk(mainDir):
		for fileName in files:
			if fileName.endswith(".txt") == False: 
				continue
			
			filePath = os.path.join(root, fileName)
			p = Parser()
			parsedObj = p.parseEnronFile(filePath)
			
			# Now that parsing is complete, store results in DBWriter
			writeToDB(parsedObj)
	
	# In practice, below queries will come from front end, but we'll query here itself
	# for demo purposes.
	rows = queryDB('Query3')
	
	# print all rows in result
	for r in rows:
		print r
	


