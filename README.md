# THIS PROJECT WAS VIBE CODED BY GEMINI
sorry not sorry. I don't know Python, so I'm sure there are more efficient ways to do this. It seems to work though

# This will automate enabling / disabling your Radarr lists
Please refer to the example compose file for a Halloween and Christmas schedule. These 2 look for lists named "halloween" and "christmas" - pretty straight forward.
Personally, I am using [maintainerr](https://maintainerr.info/) to automate deleting content, but setting Clean Library Level to "remove movie and delete files" will delete any movies added by the automated lists when they are disabled.


##  Environment Variables

| Variable | Required | Description | Example |
| :--- | :---: | :--- | :--- |
| `RADARR_URL` | ✅ | The full URL to your Radarr instance. | `http://192.168.1.50:7878` |
| `RADARR_API_KEY` | ✅ | Your API Key found in Radarr > Settings > General. | `c28565be288...` |
| `LIST_NAME` | ✅ | The **exact name** of the Import List you want to control. NOT case sensitive. | `Christmas` |
| `START_DATE` | ✅ | The day the list should turn **ON**. <br> **Format:** `DD/MM` | `01/12` (1st Dec) |
| `END_DATE` | ✅ | The day the list should turn **OFF**. <br> **Format:** `DD/MM` | `02/01` (2nd Jan) |
| `TZ` | ❌ | (Optional) Your Timezone. Determines when the "Daily Check" runs (default 8 AM). | `Australia/Melbourne` |

##  How It Works

The container runs a Python script that acts as a **State Enforcer**. It does not just toggle the list once; it ensures the list is always in the correct state for the current date.

1.  **On Startup:** The script immediately calculates if "Today" falls between `START_DATE` and `END_DATE`.
    * **Inside Window:** Forces the list to **Enable**.
    * **Outside Window:** Forces the list to **Disable**.
2.  **Daily Check:** Every morning at **08:00 AM**, it runs the check again to catch any dates that rolled over during the night.
3.  **New Year Logic:** It automatically handles date ranges that cross the New Year (e.g., Dec 1st to Jan 2nd).

You will need a seperate container per list - please refer to the example compose file.

##  Healthcheck

This container includes a built-in **Heartbeat** mechanism for Docker.

* The script updates a file at `/tmp/healthy` every 60 seconds.
* Docker checks this file to ensure the scheduler hasn't frozen.
* If the script hangs, Docker will mark the container as `unhealthy`.

You can use something like [Autoheal](https://github.com/willfarrell/docker-autoheal) to automate recovering the container

## 🛠 Development

To build this image locally:

```bash
docker build -t radarr-schedularr .
