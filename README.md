# Email Jamf Advanced Mobile Device Search as a CSV


## Purpose
This script does the following:
* Downloads Jamf Advanced Mobile Device Search and converts to a CSV
* Emails CSV to a specified email address

Note this version uses Sendgrid SMTP Relay for the outgoing email account.
Additionally, "search_id" refers to the ID of the Advanced Search you are downloading.

### Configure .env as follows:
```xml
jss = "https://myJamfInstance.jamfcloud.com"
api_user = "jamf_user"
api_pw = "jamf_user_credentials"
tmp_path = "/tmp/"
email_api_user = "apikey"
email_api_key = "apikey_string"
email_recipient = "email.recipient@email.com"
smtp_server = "smtp.sendgrid.net"
smtp_server_port = "587"
search_id = "12"
```
