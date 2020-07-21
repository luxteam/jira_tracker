import time
import config
import requests
import datetime
from jira import JIRA


# create jira client connection
def createJiraClient():
	jira_options = {'server': config.jira_host}
	return JIRA(options=jira_options, basic_auth=(config.jira_username, config.jira_token))


def getIssuesListFronJQL(jql):
	jira_client = createJiraClient()
	issue_dict = jira_client.search_issues(jql, maxResults=100, json_result=True)

	issues_keys = []
	for i in issue_dict['issues']:
		issues_keys.append(i['key'])

	startAt = 100
	while len(issue_dict['issues']) == 100:
		issue_dict = jira_client.search_issues(jql, startAt=startAt, maxResults=100, json_result=True)
		for i in issue_dict['issues']:
			issues_keys.append(i['key'])
		startAt += 100

	jira_client.close()
	return issues_keys


def getIssueInfo(ticket):
	response = requests.get("{}/rest/api/2/issue/{}".format(config.jira_host, ticket), auth=(config.jira_username, config.jira_token))
	issueInfo = response.json()
	return issueInfo


# return all jira tickets with epic bug
def getJiraBugIssues(project):
	jql = "project = {} AND 'Epic Link' = STVCIS-973".format(project)
	issues_list = getIssuesListFronJQL(jql)
	report = {}
	for issue in issues_list:
		issueInfo = getIssueInfo(issue)

		if issueInfo['key'] != "STVCIS-973" and issueInfo['fields']['status']['name'] != 'Closed':
			try:
				issue_url = 'https://adc.luxoft.com/jira/browse/{}'.format(issueInfo['key'])
			except:
				issue_url = 'unknown'

			issue_dict = {'key': issueInfo['key'], 'summary': issueInfo['fields']['summary'], \
				'priority': issueInfo['fields']['priority']['name'], 'status': issueInfo['fields']['status']['name'], \
				'reporter': issueInfo['fields']['reporter']['displayName'], 'link': issue_url}

			report[issueInfo['key']] = issue_dict

	return report




