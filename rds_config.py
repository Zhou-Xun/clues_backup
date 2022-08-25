#!/usr/bin/python
#config file containing credentials for rds mysql instance

#import boto3
import json

"""
Init database
"""
#db_config = get_secret()
#print(db_config)

db_config   = {
    "mysql_host":"clues.cemnk6uitgq7.us-east-2.rds.amazonaws.com", 
    "mysql_user":"admin", 
    "mysql_password":"G78F4DN*kMeG*QTRwExj", 
    "mysql_db":"CLUES_DEV",
    "mysql_port":"3306"
    }

db_host     = db_config['mysql_host']
db_user     = db_config['mysql_user']
db_password = db_config['mysql_password']
db_name     = db_config['mysql_db']
db_port     = db_config['mysql_port']


#db_host     = "clues.cemnk6uitgq7.us-east-2.rds.amazonaws.com"
#db_user     = "admin"
#db_password = "G78F4DN*kMeG*QTRwExj"
#db_name     = "CLUES"
#db_port     = 3306