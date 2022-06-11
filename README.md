# gerrit-stats

Utility for collecting productivity statistics for the Gerrit code review tool

## Usage

1. Open the settings of your own profile in Gerrit at the HTTP Credentials section and generate a one-time password to access the API;

2. Create a *config.json* file based on the attached *config.json.tmpl* template and fill in the required details;

3. After running the script, the *gerrit-stats.csv* file will be created containing statistics on the commits of the listed accounts in the given branch, collected over the selected period of time;




