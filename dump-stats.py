import json, sys, urllib2, base64

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
authUsername = cfg["auth"]["username"]
authPassword = cfg["auth"]["password"]

def fetchData(url):
    request = urllib2.Request(url)
    base64string = base64.encodestring('%s:%s' % (authUsername, authPassword)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    response = urllib2.urlopen(request)
    data = response.read().split("\n")[1]
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
    sys.stdout.write(str)

pr("\nFetching data: [")
for author in authors:
    pr(".")
    projectsData = {}
    stats[author] = projectsData
    url = "{u}/a/changes/?q=owner:{a}+status:merged+branch:{b}+since:{ts}+until:{tu}".format(u=api, a=author, b=branch, ts=timeSince, tu=timeUntil)
    commits = fetchData(url)
    for commit in commits:
        subject = commit["subject"]
        changeId = commit["id"]
        projectId = getProject(subject)
        changesData[changeId] = projectId
        if not projectsData.has_key(projectId):
            projectsData[projectId] = {}
        type = "bug" if isBugfix(subject) else "commit"
        typeData = projectsData[projectId]
        if not typeData.has_key(type):
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
    url = "{u}/a/changes/{c}/comments".format(u=api, c=changeId)
    changes = fetchData(url)
    for comments in changes.values():
        for comment in comments:
            if comment.has_key("in_reply_to"):
                continue
            author = comment["author"]["email"]
            if not stats.has_key(author):
                continue
            #message = comment["message"] TODO check messages for significance
            projectsData = stats[author]
            if not projectsData.has_key(projectId):
                projectsData[projectId] = {}
            typeData = projectsData[projectId]
            if not typeData.has_key("comment"):
                typeData["comment"] = 0
            typeData["comment"] += 1

file = open(saveName, "w")
for author in authors:
    projectsData = stats[author]
    file.write("{};commit;bug;comment\n".format(author))
    for projectId, statsData in projectsData.items():
        commit = statsData.get("commit", 0)
        bug = statsData.get("bug", 0)
        comment = statsData.get("comment", 0)
        file.write("{p};{cmt};{bug};{cmn}\n".format(p=projectId, cmt=commit,bug=bug, cmn=comment))
    file.write(";;;\n")
file.close()

pr("]\nFile '{}' has been saved.\n".format(saveName))
