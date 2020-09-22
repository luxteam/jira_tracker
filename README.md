# Jira tracking

Send new tasks by epics to slack.

### How to use

Add configuration.

Copy **config_example.py** file to **config.py** and update constants.

- **project** is project name in jira
- **webhook_test** is webhook url where error notifications will be sent
- **webhook_url** is main webhook url, where main tickets reports will be sent
- **jira_host** is your jira main url
- **jira_username** username of user that will be used
- **jira_token** jira access token
- **known_tickets_file** file where sent tickent will be stored
- **loading_epics** epics that will be used to load tickets list (tickets only with that epics will be loaded)

Then run **slackJiraTracker.py**. Tasks will be checked per 10 minutes.
