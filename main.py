import requests
import sys
import os
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

# --- CONFIGURATION ---
RADARR_URL = os.environ.get("RADARR_URL")
API_KEY = os.environ.get("RADARR_API_KEY")
LIST_NAME = os.environ.get("LIST_NAME")

# format: "MM-DD", e.g., "12-01"
START_DATE = os.environ.get("START_DATE") 
END_DATE = os.environ.get("END_DATE")

# Basic Validation
if not all([RADARR_URL, API_KEY, LIST_NAME, START_DATE, END_DATE]):
    print("Error: Missing config. Check docker-compose.yml")
    sys.exit(1)

# --- HEARTBEAT ---
def run_heartbeat():
    with open("/tmp/healthy", "w") as f:
        f.write(str(time.time()))

# --- CORE LOGIC ---
def get_list_id(url, headers):
    try:
        res = requests.get(f"{url}/api/v3/importlist", headers=headers)
        res.raise_for_status()
        target = next((i for i in res.json() if i['name'].lower() == LIST_NAME.lower()), None)
        if not target:
            print(f"❌ Error: List '{LIST_NAME}' not found.")
            return None
        return target
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return None

def set_list_state(enable_state):
    action = "ENABLING" if enable_state else "DISABLING"
    url = RADARR_URL.rstrip("/")
    headers = {"X-Api-Key": API_KEY}
    
    target = get_list_id(url, headers)
    if not target: return

    if target['enabled'] == enable_state:
        print(f"ℹ️ State Check: List '{LIST_NAME}' is already {action} (Correct).")
        return

    print(f"⚙️ changing state: {action} list '{LIST_NAME}'...")
    target['enabled'] = enable_state
    try:
        put_url = f"{url}/api/v3/importlist/{target['id']}"
        requests.put(put_url, json=target, headers=headers).raise_for_status()
        print(f"✅ Success! List is now {action}.")
    except Exception as e:
        print(f"❌ Update Failed: {e}")

def check_season_status():
    """
    Determines if we are currently INSIDE the active window.
    """
    now = datetime.now()
    current_year = now.year
    
    # Parse config dates (append current year)
    # We assume the config is "12-01", so we make it "2025-12-01"
    d_start = datetime.strptime(f"{current_year}-{START_DATE}", "%Y-%m-%d")
    d_end = datetime.strptime(f"{current_year}-{END_DATE}", "%Y-%m-%d")

    # Handle "Over the New Year" (e.g. Dec 1 to Jan 2)
    if d_start > d_end:
        # If today is Jan 1, we compare against Start(Last Year) and End(This Year)
        # If today is Dec 20, we compare against Start(This Year) and End(Next Year)
        if now < d_start and now > d_end:
            # We are in the middle gap (e.g. June), so NOT active
            return False
        return True
    else:
        # Standard range (e.g. June 1 to July 1)
        return d_start <= now <= d_end

if __name__ == "__main__":
    print("🚀 Container Starting...")
    
    # 1. IMMEDIATE STARTUP CHECK
    # This fixes your "Started on the 2nd" issue
    should_be_active = check_season_status()
    print(f"📅 Date Check: Today is {datetime.now().strftime('%m-%d')}. Active Window: {START_DATE} to {END_DATE}.")
    print(f"🧐 Verdict: List should be {'ACTIVE' if should_be_active else 'INACTIVE'}.")
    
    set_list_state(should_be_active)

    # 2. SCHEDULE FUTURE TRIGGERS
    scheduler = BlockingScheduler()
    scheduler.add_job(run_heartbeat, 'interval', minutes=1)

    # Parse Months/Days for Cron
    s_m, s_d = START_DATE.split("-")
    e_m, e_d = END_DATE.split("-")

    # Schedule Enable (Runs every year on Start Date at 08:00)
    scheduler.add_job(set_list_state, CronTrigger(month=s_m, day=s_d, hour=8), args=[True])
    print(f"⏰ Scheduled: Enable every year on {START_DATE} at 08:00")

    # Schedule Disable (Runs every year on End Date at 08:00)
    scheduler.add_job(set_list_state, CronTrigger(month=e_m, day=e_d, hour=8), args=[False])
    print(f"⏰ Scheduled: Disable every year on {END_DATE} at 08:00")
    
    try:
        run_heartbeat()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
