import json
from sys import stdout
from base64 import b64encode
from urllib.request import urlopen, Request

saveName = "gerrit-stats.csv"
bugTags = ["fix:", "exceptfix:", "exeptfix:", "crashfix:"]

def isBugfix(subject):
    subject = subject.lower()
    for tag in bugTags:
        if subject.find(tag) >= 0:
            return True
    return False

def loadJson(path):
    file = open(path, "r")
    cfg = json.loads(file.read())
    file.close()
    return cfg

cfg = loadJson("config.json")
api = cfg["api"]
authUsername = cfg["auth"]["username"].strip()
authPassword = cfg["auth"]["password"].strip()

def fetchData(url):
    request = Request(url)
    base64string = b64encode(f"{authUsername}:{authPassword}".encode('ascii')).decode('ascii')
    request.add_header("Authorization", f"Basic {base64string}")
    response = urlopen(request)
    data = response.read().decode("utf-8").split("\n")[1]
    return json.loads(data)

projects = cfg["projects"]

def getProject(subject):
    for project in projects:
        if subject.find(project) >= 0:
            return project
    return "Other:"

branch = cfg["branch"]
timeSince = cfg["time"]["since"]
timeUntil = cfg["time"]["until"]
authors = cfg["authors"]

stats = {}
changesData = {}

def pr(str):
    stdout.write(str)

pr("\nFetching data: [")
for author in authors:
    pr(".")
    projectsData = {}
    stats[author] = projectsData
    url = f"{api}/a/changes/?q=owner:{author}+status:merged+branch:{branch}+since:{timeSince}+until:{timeUntil}"
    commits = fetchData(url)
    for commit in commits:
        subject = commit["subject"]
        changeId = commit["id"]
        projectId = getProject(subject)
        changesData[changeId] = projectId
        if projectId not in projectsData:
            projectsData[projectId] = {}
        type = "bug" if isBugfix(subject) else "commit"
        typeData = projectsData[projectId]
        if type not in typeData:
            typeData[type] = 0
        typeData[type] += 1

maxDot = len(changesData) / 30
curDot = 0
for changeId, projectId in changesData.items():
    if curDot > maxDot:
        pr(".")
        curDot = 0
    else:
        curDot += 1
    url = f"{api}/a/changes/{changeId}/comments"
    changes = fetchData(url)
    for comments in changes.values():
        for comment in comments:
            if "in_reply_to" in comment:
                continue
            username = comment["author"]["username"]
            if username not in stats:
                continue
            #message = comment["message"] TODO check messages for significance
            projectsData = stats[username]
            if projectId not in projectsData:
                projectsData[projectId] = {}
            typeData = projectsData[projectId]
            if "comment" not in typeData:
                typeData["comment"] = 0
            typeData["comment"] += 1

file = open(saveName, "w")
for author in authors:
    projectsData = stats[author]
    file.write(f"{author};commit;bug;comment\n")
    for projectId, statsData in projectsData.items():
        commit = statsData.get("commit", 0)
        bug = statsData.get("bug", 0)
        comment = statsData.get("comment", 0)
        file.write(f"{projectId};{commit};{bug};{comment}\n")
    file.write(";;;\n")
file.close()

pr(f"]\nFile '{saveName}' has been saved.\n")


# TODO split interval to months
# TODO count rewiewed commits not only commit count