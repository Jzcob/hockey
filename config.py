import requests
import discord
import json

jacob = 920797181034778655
dev_server_dev_channel = 1165858822183735316
allowed_channels = [dev_server_dev_channel]
mgr_channel = 1168943605205962912
mod_logs = 1169386959303626772
hockey_discord_server = 1165854570195472516
owner = 1165854743281799218
logs = 1168944556927103067

color = 0xffffff
error_channel = 1166019404870463558
footer = "Bot created by @jzcob"

def checkForTeam(team: str) -> None:
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    response = requests.get(url)
    x = json.loads(response.text)
    y = 0
    team = team.lower()

    for i in x['teams']:
        teamName = x['teams'][y]['teamName']
        teamName = teamName.lower()
        teamAbbreviation = x['teams'][y]["abbreviation"]
        teamAbbreviation = teamAbbreviation.lower()
        teamFullName = x['teams'][y]["name"]
        teamFullName = teamFullName.lower()
        if teamName == team or teamAbbreviation == team or teamFullName == team:
            teamID = x['teams'][y]['id']
            return teamID
        else:
            y += 1
    else:
        teamID = None
        return teamID

def checkForTeamName(team: str) -> None:
    url = "https://statsapi.web.nhl.com/api/v1/teams"
    response = requests.get(url)
    x = json.loads(response.text)
    y = 0
    team = team.lower()
    
    for i in x['teams']:
        teamName = x['teams'][y]['teamName']
        teamName = teamName.lower()
        teamAbbreviation = x['teams'][y]["abbreviation"]
        teamAbbreviation = teamAbbreviation.lower()
        teamFullName = x['teams'][y]["name"]
        teamFullName = teamFullName.lower()
        if teamName == team or teamAbbreviation == team or teamFullName == team:
            teamName = x['teams'][y]['name']
            return teamName
        else:
            y += 1
    else:
        teamName = None
        return teamName