import requests
import sys
import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# --- CONFIGURATION ---
# We fetch these from the Docker Environment Variables
RADARR_URL = os.environ.get("RADARR_URL")
API_KEY = os.environ.get("RADARR_API_KEY")
LIST_NAME = os.environ.get("LIST_NAME")
ON_CRON = os.environ.get("ON_CRON") import requests
import sys
import os
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# --- CONFIGURATION ---
RADARR_URL = os.environ.get("RADARR_URL")
API_KEY = os.environ.get("RADARR_API_KEY")
LIST_NAME = os.environ.get("LIST_NAME")
ON_CRON = os.environ.get("ON_CRON") 
OFF_CRON = os.environ.get("OFF_CRON")

# Basic Validation
if not all([RADARR_URL, API_KEY, LIST_NAME]):
    print("Error: Missing mandatory env vars. Check docker-compose.yml")
    sys.exit(1)

if not ON_CRON and not OFF_CRON:
    print("Error: No schedule provided. Set ON_CRON or OFF_CRON.")
    sys.exit(1)

# --- HEARTBEAT FUNCTION ---
def run_heartbeat():
    """Updates a file timestamp so Docker knows we are alive"""
    with open("/tmp/healthy", "w") as f:
        f.write(str(time.time()))

def toggle_list(enable_state):
    action = "ENABLING" if enable_state else "DISABLING"
    print(f"⏰ Triggered: {action} list '{LIST_NAME}'...")
    
    url = RADARR_URL.rstrip("/")
    headers = {"X-Api-Key": API_KEY}
    
    try:
        # 1. Get All Lists
        res = requests.get(f"{url}/api/v3/importlist", headers=headers)
        if res.status_code == 401:
            print("❌ Error: API Key Rejected.")
            return
        res.raise_for_status()
        all_lists = res.json()
        
        # 2. Find Specific List
        target = next((i for i in all_lists if i['name'].lower() == LIST_NAME.lower()), None)
        
        if not target:
            print(f"❌ Error: List '{LIST_NAME}' not found.")
            return

        # 3. Update Status
        if target['enabled'] == enable_state:
            print(f"ℹ️ No change needed. List is already {'Enabled' if enable_state else 'Disabled'}.")
            return

        target['enabled'] = enable_state
        
        # 4. Push Update
        put_url = f"{url}/api/v3/importlist/{target['id']}"
        requests.put(put_url, json=target, headers=headers).raise_for_status()
        print(f"✅ Success! List '{LIST_NAME}' is now {action}.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    # 1. Add Heartbeat (Runs every 1 minute)
    scheduler.add_job(run_heartbeat, 'interval', minutes=1)
    print("❤️ Heartbeat started.")

    # 2. Add Schedules
    if ON_CRON:
        print(f"📅 Scheduler: Will ENABLE '{LIST_NAME}' at [{ON_CRON}]")
        scheduler.add_job(toggle_list, CronTrigger.from_crontab(ON_CRON), args=[True])

    if OFF_CRON:
        print(f"📅 Scheduler: Will DISABLE '{LIST_NAME}' at [{OFF_CRON}]")
        scheduler.add_job(toggle_list, CronTrigger.from_crontab(OFF_CRON), args=[False])

    print(f"🚀 Container started. Watching clock for list: {LIST_NAME}...")
    
    try:
        # Write one heartbeat immediately so the container starts 'healthy'
        run_heartbeat()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
OFF_CRON = os.environ.get("OFF_CRON")

# Basic Validation
if not all([RADARR_URL, API_KEY, LIST_NAME]):
    print("Error: Missing mandatory env vars. Check docker-compose.yml")
    sys.exit(1)

if not ON_CRON and not OFF_CRON:
    print("Error: No schedule provided. Set ON_CRON or OFF_CRON.")
    sys.exit(1)

def toggle_list(enable_state):
    action = "ENABLING" if enable_state else "DISABLING"
    print(f"⏰ Triggered: {action} list '{LIST_NAME}'...")
    
    # Clean URL
    url = RADARR_URL.rstrip("/")
    headers = {"X-Api-Key": API_KEY}
    
    try:
        # 1. Get All Lists
        res = requests.get(f"{url}/api/v3/importlist", headers=headers)
        if res.status_code == 401:
            print("❌ Error: API Key Rejected.")
            return
        res.raise_for_status()
        all_lists = res.json()
        
        # 2. Find Specific List
        target = next((i for i in all_lists if i['name'].lower() == LIST_NAME.lower()), None)
        
        if not target:
            print(f"❌ Error: List '{LIST_NAME}' not found.")
            return

        # 3. Update Status
        if target['enabled'] == enable_state:
            print(f"ℹ️ No change needed. List is already {'Enabled' if enable_state else 'Disabled'}.")
            return

        target['enabled'] = enable_state
        
        # 4. Push Update
        put_url = f"{url}/api/v3/importlist/{target['id']}"
        requests.put(put_url, json=target, headers=headers).raise_for_status()
        print(f"✅ Success! List '{LIST_NAME}' is now {action}.")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    scheduler = BlockingScheduler()

    if ON_CRON:
        print(f"📅 Scheduler: Will ENABLE '{LIST_NAME}' at [{ON_CRON}]")
        scheduler.add_job(toggle_list, CronTrigger.from_crontab(ON_CRON), args=[True])

    if OFF_CRON:
        print(f"📅 Scheduler: Will DISABLE '{LIST_NAME}' at [{OFF_CRON}]")
        scheduler.add_job(toggle_list, CronTrigger.from_crontab(OFF_CRON), args=[False])

    print(f"🚀 Container started. Watching clock for list: {LIST_NAME}...")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass