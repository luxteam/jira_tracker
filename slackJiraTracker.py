import os
import time
import json
import datetime
import operator
import traceback

import config
from webhookHandler import send
from jiraHandler import getJiraTickets


def createJiraReport():

	slack_report_dict = {}

	known_tickets_file = "current_issues.json"

	if os.path.exists(known_tickets_file):
		with open(known_tickets_file, 'r') as f:
			known_issues = json.load(f)
	else:
		known_issues = {}

	jira_tickets = getJiraTickets(config.project)

	for ticket, summary in jira_tickets.items():
		if not ticket in known_issues:
			slack_report_dict[ticket], known_issues[ticket] = summary, summary

	with open(known_tickets_file, 'w') as f:
		json.dump(known_issues, f)

	slack_report = {}

	if slack_report_dict:
		slack_report["attachments"] = [createSlackReport(slack_report_dict)]

	return slack_report


def createSlackReport(json):
	report = {}
	report["title"] = "Jira tracker"

	tickets = []

	for ticket in json:
		message = "*Epic*: {}\n*Reporter*: {}\n*Priority*: {}\n*Status*: {}\n*Link*: {}\n".format(json[ticket]['epic'], json[ticket]['reporter'], json[ticket]['priority'], \
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

	while True:
		try:
			slack_report = createJiraReport()
			if slack_report:
				send(config.webhook_test, payload=slack_report)
			time.sleep(600)
		except Exception as ex:
			sendDirectMessage(str(ex))
			#traceback.print_exc()


if __name__ == "__main__":
	monitoring()
	
