# Store Monitoring System

This project is a backend system that monitors the uptime/downtime of restaurants (stores) in the US. It processes raw data (store hours, status, timezones) and generates reports about store performance.

# Problem : 
A system monitors several restaurants in the US and needs to monitor if the store is online or not. All restaurants are supposed to be online during their business hours. Due to some unknown reasons, a store might go inactive for a few hours. Restaurant owners want to get a report of the how often this happened in the past.   



# Features
1)Store management (add/list stores)
2)Load CSV data (store hours, timezones, statuses)
3)Track store uptime and downtime
4)Generate CSV reports with uptime/downtime summaries
5)REST API built using Django + Django REST Framework 

#Tech Stack
1)Backend: Django, Django REST Framework
2)Database: SQLite (default, can be replaced with Postgres/MySQL)
3)Language: Python 3.12
4)Other: Git for version control

#Structure 
Store-Monitoring-System-master/
│── store/
│   ├── main/                # Main Django app
│   │   ├── models.py        # Database models
│   │   ├── views.py         # API endpoints
│   │   ├── serializers.py   # Data serializers
│   │   ├── helper.py        # Report logic
│   │   └── management/
│   │       └── commands/    # Custom commands to load CSV
│   └── ...
│── media/reports/           # Generated reports (CSV files)
│── manage.py                # Django management file


# Step by step logic for last one day (uptime and downtime):
- Initialize a dictionary last_one_day_data with keys "uptime", "downtime", and "unit". The values for "uptime" and "downtime" are set to 0, and "unit" is set to "hours".

- Calculate one_day_ago as the day of the week one day before the current_day. If current_day is 0 (Monday), set one_day_ago to 6 (Sunday).
- Check if the store is open during the last one day (one_day_ago to current_day) at the current time (current_time). 
- This is done by querying the store.timings to see if there is any entry that matches the conditions for day and time.
- If the store is not open during the last one day, return the initialized last_one_day_data.
- If the store is open during the last one day, query the store.status_logs to get all the logs within the last one day (utc_time - 1 day to utc_time) and order them by timestamp.
- Loop through each log in last_one_day_logs:
- Check if the log's timestamp falls within the store's business hours on that day (log_in_store_business_hours). This is done by querying the store.timings to see if there is any entry that matches the conditions for day and time.
- If the log is not within the store's business hours, skip it and move to the next log.
- If the log's status is "active", increment the "uptime" value in last_one_day_data by 1 hour.
- If the log's status is not "active", increment the "downtime" value in last_one_day_data by 1 hour.
- Same logic has been followed for last one hour and last one week uptime and downtime.


# APIs :

1) Trigger Report
   curl --request GET \
  --url http://localhost:8000/store/9200325206334396031/trigger_report/ \
  --header 'Content-Type: application/json' \
  --data '	'
   
3) Get Report
   curl --request POST \
  --url http://localhost:8000/store/get_report/ \
  --header 'Content-Type: application/json' \
  --data '{
	"report_id": 74
	
#Output CSV Format

store_id,
uptime_last_hour_minutes,
uptime_last_day_hours,
uptime_last_week_hours,
downtime_last_hour_minutes,
downtime_last_day_hours,
downtime_last_week_hours
