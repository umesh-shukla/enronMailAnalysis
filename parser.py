"""
Parsing Logic: 
We essentially capture lines starting with following strings in each mail text file: 
1. 'Message-ID': Message-ID on top of each mail text file is unique and is used as a primary key in DB
2. 'Subject': Subject-line of a mail. In few mails it's empty. A Mail is marked as a reply, 
	if it's subject starts with 're:' or 'Re:'. 
3. 'Date': Sender's date-time. 
4. 'From': Sender. There are some instances where this field was empty, but we still store details
	of that mail as other details of that mail could still be of an importance. 
5. 'To': Recepients of that mail. Mail IDs present in TO:' field are considered as receivers
	'CC' and 'BCC' list are not considered. 
6. 'Sent': This field is used to determine original mail sent time in response time calculations. 

Assumptions: 
1. If Message-ID is not present, we ignore that mail text as file. I haven't found a single case where
	Message-ID wasn't present. 
2. Original mail was sent in the same time-zone. 
	Based on what I've read about Enron mails, this assumption is correct. 
3.  For response time calculations, only those mails considered which have '----- Original Message -----'
	present in the mail text file. There are few mails where original mail doesn't follow this logic, 
	but we ignore such mails. 
4. We assume that all the mails present in a mail-thread of a mail text file are also present
	in the file system i.e. if a mail contains 5 previous mails (4 previous replies and original mail), 
	then all those 5 mails are also present in the system. While this assumption is not true sometimes
	in the given corpus, it was needed to come up with an uniform logic which is also easy to maintain 
"""

import re
import datetime
import time 

class Parser(): 
	def __init__(self): 
		self.name = 'Parser'

	# Regex matcher to pick only selected lines from a message file
	def processLine(self, line): 
		return re.match( r'^(Subject|Message-ID|Date|From|To|Sent):\s*(.*)', line)
	
	def fillBlankDetails(self, mail_info, keys):
		for key in keys:
			if key not in mail_info:
				mail_info[key] = ''
	# Date string parser
	def parseDate(self, text):
		for fmt in ('%d %b %Y %H:%M:%S', '%b %d, %Y %I:%M %p', '%B %d, %Y %I:%M %p'):
			try:
				return datetime.datetime.strptime(text, fmt)
			except ValueError:
				pass
		raise ValueError('no valid date format found')
    
    # This is the main routine to process and clean the raw mail data
	def processRawMailInfo(self, rawMailInfo): 
		processedMailInfo = {}
		
		# if Message ID is not present, ignore this mail's data
		if 'Message-ID' not in rawMailInfo: 
			return processedMailInfo 
	
		# Fill blank details for keys not present 
		keys = ['To', 'From', 'Subject', 'Message-ID', 'Date', 'Sent']
		self.fillBlankDetails(rawMailInfo, keys)
		
		# sender
		processedMailInfo['Sender'] = rawMailInfo['From']
	
		# receiver 
		pattern = re.compile("\s*,\s*")
		receivers = pattern.split(rawMailInfo['To'])
		
		# Remove any duplicate mail-ids from list
		processedMailInfo['Receivers'] = list(set(receivers)) 
	
		# label -- broadcast or direct
		if len(receivers) > 1: 
			processedMailInfo['Label'] = 'Broadcast'
		else: 
			processedMailInfo['Label'] = 'Direct'
	
		# Sender Date and time calculations
		datePattern = re.compile('\w+\W+(\d+\s+\w+\s+\d+)\s+(\d+:\d+:\d+)\s+-(\d\d)')
		dateInfo = rawMailInfo['Date']
		matchedObj = re.match(datePattern, dateInfo)
		utcOffset = None
		if matchedObj:
			mail_date = matchedObj.group(1)
			mail_time = matchedObj.group(2)
			utcOffset = matchedObj.group(3)
			processedMailInfo['Date'] = mail_date
			processedMailInfo['TimeStamp'] = time.mktime(self.parseDate(mail_date+' '+mail_time).timetuple())\
												- 3600*int(utcOffset)
		else:
			processedMailInfo['TimeStamp'] = 0
		matchedObj
		# Response time calculation. 
		# The Assumption is that original mail was sent in the same time-zone
		# Based on what I've read about Enron mails, this assumption is correct. 
		datePattern = re.compile('\w+\W+(\w+\sutcOffset+\d+,\s+\d+\s+\d+:\d+\s+\w+)')
		sentInfo = rawMailInfo['Sent']
		matchedObj = re.match(datePattern, sentInfo)
		if matchedObj:
			orig_mail_time = matchedObj.group(1)
			origTime = time.mktime(self.parseDate(orig_mail_time).timetuple())
			if utcOffset:
				origTime = origTime - 3600*int(utcOffset)
			processedMailInfo['ResponseTime'] = processedMailInfo['TimeStamp'] - origTime
		
		# msg_id 
		processedMailInfo['msg_id'] = re.match(r'<(\d+.\d+).\w+.\w+@\w+>', rawMailInfo['Message-ID']).group(1)
	
		# ifResponse, Original Subject
		if rawMailInfo['Subject'].startswith('Re:') or rawMailInfo['Subject'].startswith('RE:'):
			processedMailInfo['if_response'] = True
			processedMailInfo['Subject'] = rawMailInfo['Subject'][4:]
		else:
			processedMailInfo['if_response'] = False
			processedMailInfo['Subject'] = rawMailInfo['Subject']
	
		# Fill blank details for keys not present 
		keys = ['Sender', 'Receivers', 'Subject', 'Message-ID', 'if_response', 'Label', 'Date', 'TimeStamp', 'ResponseTime']
		self.fillBlankDetails(processedMailInfo, keys)
		if processedMailInfo['ResponseTime'] == '':
			processedMailInfo['ResponseTime'] = 0.0
		
		return processedMailInfo
	
	# File parser routine exposed to from the clients	
	def parseEnronFile(self, fileName): 
		multiLineToList = False 
		toStr = ''
		rawMailInfo = {}
		
		with open(fileName, 'rb') as f:
			for line in f: 
				line = line.strip()
				# logic to reconstruct the 'TO:' string since text files have 
				# mail receivers spanning across multiple lines
				if re.match(r'^(To): (.*),$', line): 
					toStr = toStr + line
					multiLineToList = True
					continue
				elif multiLineToList: 
					toStr = toStr + line
					if line.endswith(',') == True:
						continue
					else: 
						line = toStr
						print line
						multiLineToList = False

				matchObj = self.processLine(line)
				if matchObj and matchObj.group(1) not in rawMailInfo:
					rawMailInfo[matchObj.group(1)] = matchObj.group(2)
		
		# Process raw data collected from each mail and clean it to store in DB
		return self.processRawMailInfo(rawMailInfo)
			