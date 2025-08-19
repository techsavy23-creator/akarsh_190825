import tempfile
from .models import StoreStatus,  ReportStatus , StoreStatusLog , StoreReport , Store
from django.utils import timezone 
import pytz
from datetime import datetime, timedelta
import csv
import os
from django.conf import settings

def trigger_report_combined(report):
    csv_data = []

    # Only generate report for first 200 stores (can remove [:200] later)
    stores = Store.objects.all()[:200]
    for store in stores:
        data = generate_report_data(store)
        csv_data.append(data)

    generate_csv_file(report, csv_data)
    return report


def generate_report_data(store):
    now = datetime.now(pytz.UTC)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)

    tz = pytz.UTC
    if store.timezone_str:
        try:
            tz = pytz.timezone(store.timezone_str)
        except Exception:
            pass

    logs = StoreStatusLog.objects.filter(store=store).order_by("timestamp")

    # Initialize counters
    uptime_last_hour = downtime_last_hour = 0
    uptime_last_day = downtime_last_day = 0
    uptime_last_week = downtime_last_week = 0

    for log in logs:
        if not log.timestamp:
            continue

        ts = log.timestamp.astimezone(tz)

        # Last hour
        if ts >= one_hour_ago:
            if log.status == "active":
                uptime_last_hour += 1
            else:
                downtime_last_hour += 1

        # Last day
        if ts >= one_day_ago:
            if log.status == "active":
                uptime_last_day += 1
            else:
                downtime_last_day += 1

        # Last week
        if ts >= one_week_ago:
            if log.status == "active":
                uptime_last_week += 1
            else:
                downtime_last_week += 1

    return {
        "store_id": store.store_id,
        "uptime_last_hour_minutes": uptime_last_hour,
        "uptime_last_day_hours": round(uptime_last_day / 60.0, 2),
        "uptime_last_week_hours": round(uptime_last_week / 60.0, 2),
        "downtime_last_hour_minutes": downtime_last_hour,
        "downtime_last_day_hours": round(downtime_last_day / 60.0, 2),
        "downtime_last_week_hours": round(downtime_last_week / 60.0, 2),
    }


def generate_csv_file(report, csv_data):
    if not csv_data:
        return None

    # Ensure reports directory exists
    reports_dir = os.path.join(settings.MEDIA_ROOT, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    file_path = os.path.join(reports_dir, f"{report.id}.csv")

    # Write CSV
    with open(file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_data[0].keys())
        writer.writeheader()
        writer.writerows(csv_data)

    # Save relative path to report model
    report.report_url.name = f"reports/{report.id}.csv"
    report.status = ReportStatus.COMPLETED
    report.save()

    return file_path


def get_last_one_hour_data(store, utc_time, current_day, current_time):
    last_one_hour_data = {"uptime" : 0 , "downtime" : 0 , "unit" : "minutes"}
    # checking if store is open in last one hour
    is_store_open = store.timings.filter(day=current_day,start_time__lte=current_time,end_time__gte=current_time).exists()
    if not is_store_open:
        return last_one_hour_data
    last_one_hour_logs = store.status_logs.filter(timestamp__gte=utc_time - datetime.timedelta(hours=1)).order_by('timestamp')
    # checking if store is open in last one hour and last log status is active
    if last_one_hour_logs:
        last_one_hour_log_status = last_one_hour_logs[0].status
        if last_one_hour_log_status == StoreStatus.ACTIVE:
            last_one_hour_data["uptime"] = 60
        else:
            last_one_hour_data["downtime"] = 60

    return last_one_hour_data
    

def get_last_one_day_data(store, utc_time, current_day, current_time):
    """
    Compute uptime/downtime in the last 24 hours using actual elapsed time
    instead of just counting logs.
    """
    last_one_day_data = {"uptime": 0.0, "downtime": 0.0, "unit": "hours"}

    start_time = utc_time - datetime.timedelta(days=1)
    logs = (
        store.status_logs.filter(timestamp__gte=start_time, timestamp__lte=utc_time)
        .order_by("timestamp")
    )

    # If no logs at all → store considered fully down
    if not logs.exists():
        last_one_day_data["downtime"] = 24
        return last_one_day_data

    # Ensure we include a boundary at start_time
    first_log = logs.first()
    if first_log.timestamp > start_time:
        # Assume previous state is same as first log
        logs = list(logs)
        fake_log = type(first_log)(status=first_log.status, timestamp=start_time)
        logs.insert(0, fake_log)
    else:
        logs = list(logs)

    # Walk through logs, add elapsed time to uptime/downtime
    for i in range(len(logs) - 1):
        log, next_log = logs[i], logs[i + 1]
        duration = (next_log.timestamp - log.timestamp).total_seconds() / 3600.0  # hours

        # Only count time if within store's business hours
        if store.timings.filter(
            day=log.timestamp.weekday(),
            start_time__lte=log.timestamp.time(),
            end_time__gte=log.timestamp.time(),
        ).exists():
            if log.status == StoreStatus.ACTIVE:
                last_one_day_data["uptime"] += duration
            else:
                last_one_day_data["downtime"] += duration

    # Handle time from last log until now
    last_log = logs[-1]
    duration = (utc_time - last_log.timestamp).total_seconds() / 3600.0
    if store.timings.filter(
        day=last_log.timestamp.weekday(),
        start_time__lte=last_log.timestamp.time(),
        end_time__gte=last_log.timestamp.time(),
    ).exists():
        if last_log.status == StoreStatus.ACTIVE:
            last_one_day_data["uptime"] += duration
        else:
            last_one_day_data["downtime"] += duration

    return last_one_day_data


def get_last_one_week_data(store, utc_time, current_day, current_time):
    last_one_week_data = {"uptime" : 0 , "downtime" : 0, "unit" : "hours"}
    one_week_ago = current_day - 7 if current_day > 0 else 0
    # checking if store is open in last one week
    is_store_open = store.timings.filter(day__gte=one_week_ago,day__lte=current_day,start_time__lte=current_time,end_time__gte=current_time).exists()
    if not is_store_open:
        return last_one_week_data
    # getting all the logs in last one week
    last_one_week_logs = store.status_logs.filter(timestamp__gte=utc_time - datetime.timedelta(days=7)).order_by('timestamp')
    for log in last_one_week_logs:
        # checkig if log is in store business hours
        log_in_store_business_hours = store.timings.filter(
            day=log.timestamp.weekday(),
            start_time__lte=log.timestamp.time(),
            end_time__gte=log.timestamp.time()
            ).exists()
        # checking if log is in store business hours and status is active
        if not log_in_store_business_hours:
            continue
        if log.status == StoreStatus.ACTIVE:
            last_one_week_data["uptime"] += 1
        else:
            last_one_week_data["downtime"] += 1
    
    return last_one_week_data