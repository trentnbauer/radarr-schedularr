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
START_DATE = os.environ.get("START_DATE")  # Format: DD/MM
END_DATE = os.environ.get("END_DATE")      # Format: DD/MM

# Basic Validation
if not all([RADARR_URL, API_KEY, LIST_NAME, START_DATE, END_DATE]):
    print("❌ Error: Missing configuration variables. Check docker-compose.yml.")
    sys.exit(1)

# --- HEARTBEAT ---
def run_heartbeat():
    with open("/tmp/healthy", "w") as f:
        f.write(str(time.time()))

# --- RADARR API HELPERS ---
def get_list_id(url, headers):
    try:
        res = requests.get(f"{url}/api/v3/importlist", headers=headers)
        res.raise_for_status()
        target = next((i for i in res.json() if i['name'].lower() == LIST_NAME.lower()), None)
        if not target:
            print(f"❌ Error: List '{LIST_NAME}' not found in Radarr.")
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
        return

    print(f"⚙️ Mismatch detected! {action} list '{LIST_NAME}'...")
    target['enabled'] = enable_state
    
    try:
        put_url = f"{url}/api/v3/importlist/{target['id']}"
        requests.put(put_url, json=target, headers=headers).raise_for_status()
        print(f"✅ Success! List '{LIST_NAME}' has been {action}.")
    except Exception as e:
        print(f"❌ Update Failed: {e}")

# --- DATE LOGIC (UPDATED FOR DD/MM) ---
def check_season_status():
    now = datetime.now()
    current_year = now.year
    
    # We combine USER DATE + CURRENT YEAR to create a full timestamp
    # Input: "01/12" -> Becomes "01/12/2025"
    try:
        d_start = datetime.strptime(f"{START_DATE}/{current_year}", "%d/%m/%Y")
        d_end = datetime.strptime(f"{END_DATE}/{current_year}", "%d/%m/%Y")
    except ValueError as e:
        print(f"❌ Date Format Error: Ensure config uses DD/MM (e.g., 01/12). Error: {e}")
        sys.exit(1)

    if d_start > d_end:
        # New Year Wrap (e.g. 01/12 to 02/01)
        if now < d_start and now > d_end:
            return False
        return True
    else:
        # Standard Range
        return d_start <= now <= d_end

# --- MAIN LOOP ---
def daily_enforcement():
    print(f"☀️ Daily Check ({datetime.now().strftime('%Y-%m-%d %H:%M')}): Verifying list state...")
    should_be_active = check_season_status()
    
    status_text = "ACTIVE" if should_be_active else "INACTIVE"
    print(f"🧐 Verdict: List should be {status_text} (Window: {START_DATE} to {END_DATE})")
    
    set_list_state(should_be_active)

if __name__ == "__main__":
    print("🚀 Container Starting...")
    
    daily_enforcement()

    scheduler = BlockingScheduler()
    scheduler.add_job(run_heartbeat, 'interval', minutes=1)
    scheduler.add_job(daily_enforcement, CronTrigger(hour=8, minute=0))
    
    print(f"⏰ Scheduler active. Next check at 08:00 AM.")
    
    try:
        run_heartbeat()
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass

