# enronMailAnalysis
This repo processes Enron Mail corpus files and stores them in mySQL DB for various queries. 
 
## Parsing Logic: 
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

## Assumptions: 
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
	

## MySQL DB Schema: 
We've kept mySQL scheme generic enough so that other common queries can also be made in performance-optimzied manner. 
Two tables are being maintained which have following schema:

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


## SQL Queries: 

1. How many emails did each person receive each day?
select distinct(Receiver), date, count(MailID) from EnronTeam \
								where receiver != '' \
								group by date, Receiver \
								order by date, Receiver
								
2. Identify the person (or people) who received the largest number of direct emails
select Receiver, count(MailID) from EnronTeam \
								where Label = 'Direct' and receiver != '' \
								group by Receiver having count(MailID) = \
								(select max(Y.MailCount) from (select Receiver, count(MailID) as MailCount from EnronTeam \
								where Label = 'Direct' and receiver != '' \
								group by Receiver) Y)
								
3. The person (or people) who sent the largest number of broadcast emails
select Sender, count(MailID) from EnronTeam \
								where Label = 'Broadcast' \
								group by Sender having count(MailID) = \
								(select max(Y.MailCount) from (select Sender, count(MailID) as MailCount from EnronTeam \
								where Label = 'Broadcast' group by Sender) Y)
								
4. Find the five emails with the fastest response times
select MailID, subject, ResponseTime from EnronMails \
								where ResponseTime > 0 and ifResponse = 1 \
								order by ResponseTime limit 5
								