import time
import requests
import datetime
import time

import logging

from jira import JIRA

def isTaskEpic(issue_info):
    try:
        return issue_info['issuetype']['name'].lower() == 'epic'
    except:
        return False

def isTaskClosed(issue_info):
    try:
        return issue_info['fields']['status']['name'].lower() == 'closed'
    except:
        return False

def getTaskStatus(issue_info):
    try:
        return issue_info['fields']['status']['name']
    except:
        return "unknown"

def findFieldIdByName(issue_info, name):
    # print(json.dumps(issue_info, indent=2))
    for field_id, field_name in issue_info['names'].items():
        if field_name == name:
            return field_id
    return None

class JiraClient:
    """Jira Client for loading data from jira REST api"""
    def __init__(self, jira_host, jira_username, jira_token, loading_epics, known_tickets_list):
        self.EPIC_LINKS = {}
        self.issues_info = {}
        self.jira_host = jira_host
        self.jira_username = jira_username
        self.jira_token = jira_token
        self.loading_epics = loading_epics
        self.known_tickets_list = known_tickets_list

    # create jira client connection
    def createJiraClient(self):
        jira_options = {'server': self.jira_host}
        return JIRA(options=jira_options, basic_auth=(self.jira_username, self.jira_token))


    def getIssuesListFronJQL(self, jql):
        logging.info('GET ISSUES BY JQL = {}'.format(jql))
        jira_client = self.createJiraClient()

        issues_keys = []
        startAt = 0
        while True:
            issue_dict = jira_client.search_issues(jql, startAt=startAt, maxResults=100, json_result=True)
            issues_keys = [ *issues_keys, *[i['key'] for i in issue_dict['issues']] ]
            if len(issue_dict['issues']) < 100:
                break
            startAt += 100

        jira_client.close()
        logging.info('Loaded {} issues'.format(len(issues_keys)))
        return issues_keys

    def getEpicNameByEpicTicket(self, epic_key):
        # logging.info("Get Epic Name By Epic Ticket {}".format(epic_key))
        if not epic_key:
            return 'unknown'
        if epic_key in self.EPIC_LINKS:
            return self.EPIC_LINKS[epic_key]
        epic_info = self.getIssueInfo(epic_key)
        epic_name_id = findFieldIdByName(epic_info, 'Epic Name')
        epic = epic_info['fields'][epic_name_id]
        return epic

    def getEpicNameByTicket(self, ticket):
        # logging.info("Get epic name from ticket {}".format(ticket))
        if not ticket:
            return 'unknown'
        if ticket in self.EPIC_LINKS:
            return self.EPIC_LINKS[ticket]
        issueInfo = self.getIssueInfo(ticket)
        epic_field_key = findFieldIdByName(issueInfo, 'Epic Link')
        epic_key = issueInfo['fields'][epic_field_key]
        epic_name = self.getEpicNameByEpicTicket(epic_key)
        # logging.info("Got epic name {}".format(epic_name))
        if epic_name == 'unknown':
            parent_key = ""
            if 'parent' in issueInfo['fields'].keys():
                parent_key = issueInfo['fields']['parent']['key']
                # logging.info("Got parent key {}".format(parent_key))
                epic_name = getEpicNameByTicket(parent_key)
                # logging.info("Got epic name {}".format(epic_name))
        self.EPIC_LINKS[ticket] = epic_name

        return epic_name

    def getIssueInfo(self, ticket):
        if ticket in self.issues_info:
            return self.issues_info[ticket]

        request_url = "{}/rest/api/2/issue/{}?expand=names".format(self.jira_host, ticket)
        # if expand:
        #     request_url += "?expand={}".format(','.join(expand))
        response = requests.get(request_url, auth=(self.jira_username, self.jira_token))
        issueInfo = response.json()
        self.issues_info[ticket] = issueInfo
        logging.info("Get issue info: {} {} by url = {}".format(ticket, getTaskStatus(issueInfo), request_url))
        return issueInfo


    def getJiraTicketsAndClosedTicketsDict(self, project):
        epic_links_query = ' OR '.join(['\'Epic Link\' = \'{}\''.format(epic) for epic in self.loading_epics])
        jql = "project = {} AND {}".format(project, epic_links_query)
        issues_list = self.getIssuesListFronJQL(jql)
        report = {}
        closed_tickets_dict = {}
        for i, issue in enumerate(issues_list, 1):
            if issue in self.known_tickets_list:
                logging.info("Issue {} {}/{} is in known issues list".format(issue, i, len(issues_list)))
                continue

            try:
                issueInfo = self.getIssueInfo(issue)
            except :
                time.sleep(20)
                logging.error(traceback.format_exc())
                issueInfo = self.getIssueInfo(issue)

            try:
                epic = self.getEpicNameByTicket(issue)
            except:
                time.sleep(20)
                logging.error(traceback.format_exc())
                epic = self.getEpicNameByTicket(issue)

            if isTaskEpic(issueInfo):
                logging.info("Ticket {} {} is epic".format(issue, getTaskStatus(issueInfo)))
                continue

            try:
                issue_url = '{}/browse/{}'.format(self.jira_host, issueInfo['key'])
            except:
                issue_url = 'unknown'

            issue_dict = {
                'key': issueInfo['key'],
                'summary': issueInfo['fields']['summary'],
                'epic': epic,
                'priority': issueInfo['fields']['priority']['name'],
                'status': issueInfo['fields']['status']['name'],
                'reporter': issueInfo['fields']['reporter']['displayName'],
                'link': issue_url
            }

            if isTaskClosed(issueInfo):
                closed_tickets_dict[issue] = issue_dict
            else:
                logging.info("Add ticket: {} {}".format(issue, getTaskStatus(issueInfo)))
                report[issueInfo['key']] = issue_dict

        return report, closed_tickets_dict




