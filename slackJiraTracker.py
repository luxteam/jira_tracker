import os
import time
import json
import datetime
import operator

import config
from webhookHandler import send
from jiraHandler import getJiraBugIssues


def createJiraReport(project="STVCIS", diff=True):

	slack_report_json = {}

	current_issues_json = "current_issues.json"

	if os.path.exists(current_issues_json):
		with open(current_issues_json, 'r') as f:
			current_issues = json.load(f)
	else:
		current_issues = {}


	all_jira_issues = getJiraBugIssues(project)

	if diff:
		for issue in all_jira_issues:
			if not issue in current_issues:
				slack_report_json[issue] = all_jira_issues[issue]
				current_issues[issue] = all_jira_issues[issue]
		with open(current_issues_json, 'w') as f:
			json.dump(current_issues, f)
	else:
		slack_report_json = all_jira_issues

	slack_report = {}

	if slack_report_json:
		slack_report["attachments"] = [createSlackReport(slack_report_json)]

	return slack_report


def createSlackReport(json):
	report = {}
	report["title"] = "Jira issues"

	tickets = []

	for ticket in json:
		message = "*Reporter*: {}\n*Priority*: {}\n*Status*: {}\n*Link*: {}\n".format(json[ticket]['reporter'], json[ticket]['priority'], \
			json[ticket]['status'], json[ticket]['link'])
		tickets.append({"title": "[{}] {}".format(json[ticket]['key'], json[ticket]['summary']) , "value": message, "short": False})

	report["color"] = "#00ffff"
	report["fields"] = tickets
	report["footer"] = "Jira API"
	report["footer_icon"] = "https://platform.slack-edge.com/img/default_application_icon.png"

	return report


def sendDirectMessage(text):
	report = {}
	report["attachments"] = [{'text': text}]
	send(config.webhook_test, payload=report)


def monitoring():

	sendDirectMessage("Jira issue tracking was started!")	

	while True:
		try:
			weekday = datetime.datetime.today().weekday()
			now = datetime.datetime.now()

			if weekday in range(0, 5) and now.hour == 7 and now.minute == 0:
				send(config.webhook_url, payload=createJiraReport(diff=False))
				time.sleep(600)
			
			slack_report = createJiraReport()
			if slack_report:
				send(config.webhook_url, payload=slack_report)
			time.sleep(60)
		except Exception as ex:
			sendDirectMessage(str(ex))


if __name__ == "__main__":
	monitoring()
	
