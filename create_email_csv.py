#!/usr/bin/env python3

# this script creates a .CSV in /tmp from a Jamf Advanced Mobile Device Search via API and sends it as an attachment to the email

import os 
import requests
import sys  
import base64  
import json  
import datetime 
import xml.etree.ElementTree as Xet
import pandas as pd 
import smtplib 
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv 
load_dotenv()



def init_variables():
	jss = os.environ.get("jss")
	api_user = os.environ.get("api_user")
	api_pw = os.environ.get("api_pw")
	tmp_path = os.environ.get("tmp_path")
	email_api_user = os.environ.get("email_api_user")
	email_api_key = os.environ.get("email_api_key")
	email_recipient = os.environ.get("email_recipient")
	smtp_server = os.environ.get("smtp_server")
	smtp_server_port = os.environ.get("smtp_server_port")
	search_id = os.environ.get("search_id")
	
	return jss, api_user, api_pw, tmp_path, email_api_user, email_api_key, email_recipient, smtp_server, smtp_server_port, search_id
	

def generate_auth_token():
	# generate api token
	global api_token
	
	credentials = api_user + ":" + api_pw
	credentials_bytes = credentials.encode('ascii')
	base64_bytes = base64.b64encode(credentials_bytes)
	encoded_credentials = base64_bytes.decode('ascii')
	
	# api call details
	jss_token_url = jss + "/api/v1/auth/token"
	payload = {}
	
	headers = {
		'Authorization': 'Basic ' + encoded_credentials
	}
	
	response = requests.request("POST", jss_token_url, headers=headers, data=payload)
	check_response_code(response, jss_token_url)
	# parse the json from the request
	response_data_dict = json.loads(response.text)
	api_token = response_data_dict['token']
	

def get_advanced_search(search_id, tmp_xml_filename):
	# define api endpoint
	api_url = jss + f"/JSSResource/advancedmobiledevicesearches/id/{search_id}"
	
	# make api call
	payload = {}
	headers = {
		'Authorization': 'Bearer ' + api_token
	}
	response = requests.request("GET", api_url, headers=headers, data=payload)
	check_response_code(response, api_url)
	reply = response.text
	print(reply, file=open(tmp_path + tmp_xml_filename, "w+"))
	return reply
	
		
def check_response_code(response_code: str, api_call: str):
	response_code = str(response_code)
	response_code = response_code[11:14]
	if response_code != "200" and response_code != "201":
		print(f"ERROR: response returned for {api_call} [{response_code}]")
		print(f"ERROR: response returned [{response_code}]")
		print(response_code)
		sys.exit(1)
	else:
		print(f"INFO: http response for {api_call} [{response_code}]")
		


def define_now():
	now = str(datetime.datetime.now())
	now = now.split(".", 1)
	now_formatted = str(now[0])
	char_to_replace = {':': '', ' ': '-'}
	for key, value in char_to_replace.items():
		now_formatted = now_formatted.replace(key, value)
		
	return now_formatted


def convert_xml_to_csv(xml_file, csv_file_name):
	cols = ["ID", "Name", "Display Name", "UDID", "Activation Lock Enabled"]
	rows = []
	csv_output_path = tmp_path + csv_file_name
	tmp_xml_file = tmp_path + xml_file
	# Parsing the XML file
	xmlparse = Xet.parse(tmp_xml_file)
	root = xmlparse.getroot()
	for i in root.findall('.//mobile_device'):
		id = i.find("id").text
		name = i.find("name").text
		display_name = i.find("Display_Name").text
		udid = i.find("udid").text
		activation_lock_enabled = i.find("Activation_Lock_Enabled").text
		
		rows.append({"ID": id,
					"Name": name,
					"Display Name": display_name,
					"UDID": udid,
					"Activation Lock Enabled": activation_lock_enabled })
		
	df = pd.DataFrame(rows, columns=cols)
	df.to_csv(csv_output_path)
	os.remove(tmp_xml_file)
	
	# clean up CSV (remove automatically-created, first column)
	f=pd.read_csv(csv_output_path)
	keep_col = cols
	new_f = f[keep_col]
	new_f.to_csv(csv_output_path, index=False)
	

def send_email(csv_file_name, smtp_server, smtp_server_port):
	
	csv_file = tmp_path + csv_file_name
	subject = f"Advanced Mobile Device Search Results"
	fromEmail = "mason.peralta@jamf.com"
	toEmail = email_recipient
	
	msg = MIMEMultipart('alternative')
	s = smtplib.SMTP(smtp_server, smtp_server_port)
	s.login(email_api_user, email_api_key)

	msg['Subject'] = subject
	msg['From'] = fromEmail
	body = "This is the daily Advanced Mobile Device API pull delivered as a .CSV file."
	
	content = MIMEText(body, 'plain')
	msg.attach(content)
	
	# add .csv attachment to message
	f = open(csv_file)
	attachment = MIMEText(f.read())
	attachment.add_header('Content-Disposition', 'attachment', filename=csv_file)
	msg.attach(attachment)
	
	s.sendmail(fromEmail, toEmail, msg.as_string())
	print(f"SUCCESS: email sent with attachment ({csv_file_name}) to {toEmail}")
	# delete .csv from /tmp
	os.remove(csv_file)
	
	
def define_filenames(search_id, now_formatted):
	xml_file = f"advanced_search_{search_id}.xml"
	csv_file = f"advanced_search_{search_id}_" + now_formatted + ".csv"
	return xml_file, csv_file
	
		
if __name__ == "__main__":
	jss, api_user, api_pw, tmp_path, email_api_user, email_api_key, email_recipient, smtp_server, smtp_server_port, search_id = init_variables()
	now_formatted = define_now()
	generate_auth_token()
	xml_file, csv_file = define_filenames(search_id, now_formatted)
	xml_data = get_advanced_search(search_id, xml_file)
	convert_xml_to_csv(xml_file, csv_file)
	send_email(csv_file, smtp_server, smtp_server_port)
	
