import os
import time
import json
import datetime
import operator
import traceback

import config
from webhookHandler import send
from jiraHandler import JiraClient

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

def getKnownTicketsDict():
    known_tickets_file = config.known_tickets_file

    if os.path.exists(known_tickets_file):
        with open(known_tickets_file, 'r') as f:
            known_tickets = json.load(f)
    else:
        known_tickets = {}
    return known_tickets

def addKnownIssuesFromTicketsDict(slack_report_dict):
    known_tickets_file = config.known_tickets_file

    if os.path.exists(known_tickets_file):
        with open(known_tickets_file, 'r') as f:
            known_issues = json.load(f)
    else:
        known_issues = {}

    for ticket, summary in slack_report_dict.items():
        # if not ticket in known_issues:
        known_issues[ticket] = summary

    with open(known_tickets_file, 'w') as f:
        json.dump(known_issues, f, indent=2)

def createJiraReport():
    logging.info('Start creating report')
    slack_report_dict = {}

    known_tickets_dict = getKnownTicketsDict()

    jira_client = JiraClient(
        config.jira_host,
        config.jira_username,
        config.jira_token,
        config.loading_epics,
        known_tickets_dict.keys()
    )

    jira_tickets, closed_tickets_dict = jira_client.getJiraTicketsAndClosedTicketsDict(config.project)

    addKnownIssuesFromTicketsDict(closed_tickets_dict)

    for ticket, summary in jira_tickets.items():
        if ticket not in known_tickets_dict:
            slack_report_dict[ticket] = summary
        else:
            logging.info("Ticket {} is in known_issues".format(ticket))

    slack_report = {}

    if slack_report_dict:
        slack_report["attachments"] = [createSlackReport(slack_report_dict)]

    logging.info('Report created')
    return slack_report, slack_report_dict


def createSlackReport(json):
    report = {}
    report["title"] = "Jira tracker"

    tickets = []

    for ticket in json:
        message = "*Epic*: {}\n*Reporter*: {}\n*Priority*: {}\n*Status*: {}\n*Link*: {}\n".format(
            json[ticket]['epic'],
            json[ticket]['reporter'],
            json[ticket]['priority'],
            json[ticket]['status'],
            json[ticket]['link']
        )
        tickets.append({
            "title": "[{}] {}".format(json[ticket]['key'], json[ticket]['summary']),
            "value": message,
            "short": False
        })

    report["color"] = "#00ffff"
    report["fields"] = tickets
    report["footer"] = "Jira API"
    report["footer_icon"] = "https://platform.slack-edge.com/img/default_application_icon.png"

    return report

def sendDirectMessage(text):
    report = {}
    report["attachments"] = [{
        'title': 'JIRA tracker notification',
        'text': text
    }]
    send(config.webhook_test, payload=report)


def monitoring():

    while True:
        try:
            logging.info("\n"*3)
            slack_report, slack_report_dict = createJiraReport()
            if slack_report:
                logging.info("Send request with report")
                response = send(config.webhook_url, payload=slack_report)
                logging.info('Sent with response: {}'.format(response))
                if response == 'ok':
                    logging.info("Response is ok, add tasks to known tasks")
                    addKnownIssuesFromTicketsDict(slack_report_dict)
            else:
                logging.info("Report is empty")
            time.sleep(600)
        except:
            sendDirectMessage(str(traceback.format_exc()))
            logging.error(traceback.format_exc())
            time.sleep(600)



if __name__ == "__main__":
    logging.info("Start JIRA TRACKER bot")
    monitoring()
