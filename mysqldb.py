"""
mySqlDB class exposes insert and query APIs to Enron Tables . The schema of Enron Mail database 
tables is as follows:

				EnronTeam Table 
+----------+--------------+------+-----+---------+-------+
| Field    | Type         | Null | Key | Default | Extra |
+----------+--------------+------+-----+---------+-------+
| MailID   | varchar(150) | NO   | PRI | NULL    |       |
| Date     | date         | NO   |     | NULL    |       |
| Sender   | varchar(150) | NO   |     | NULL    |       |
| Receiver | varchar(150) | NO   | PRI | NULL    |       |
| Label    | varchar(150) | YES  |     | NULL    |       |
+----------+--------------+------+-----+---------+-------+

				EnronMails Table
+--------------+--------------+------+-----+---------+-------+
| Field        | Type         | Null | Key | Default | Extra |
+--------------+--------------+------+-----+---------+-------+
| MailID       | varchar(150) | NO   | PRI | NULL    |       |
| EpochTime    | int(11)      | NO   |     | NULL    |       |
| Subject      | varchar(150) | YES  |     | NULL    |       |
| IfResponse   | varchar(150) | YES  |     | NULL    |       |
| ResponseTime | double       | YES  |     | NULL    |       |
+--------------+--------------+------+-----+---------+-------+
"""

import mysql.connector

class MySqlDB(): 
	def __init__(self): 
		# TODO: Use config for credentials
		self.cnx = mysql.connector.connect(user='root', 
				 	password='shukla', 
				 	host='127.0.0.1', 
				 	database='slack')
		self.cursor = self.cnx.cursor()
		self.insertCommand = {
								'EnronTeam': 'insert into EnronTeam(MailID, Date, Sender, Receiver, Label)\
												 values (%s, %s, %s, %s, %s)' , 
								'EnronMails': 'insert into EnronMails(MailID, EpochTime, Subject, IfResponse, ResponseTime)\
												 values (%s, %s, %s, %s, %s)'
							 }
		
	def insert(self, tableName, rowVals):
		self.cursor.execute(self.insertCommand[tableName], rowVals)
		self.cnx.commit()
		
	def query(self, query):
		self.cursor.execute(query)
		return self.cursor.fetchall()
		