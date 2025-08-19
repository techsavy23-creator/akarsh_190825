import csv
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from store.main.models import Store, StoreTiming, StoreStatusLog, StoreStatus


class Command(BaseCommand):
    help = "Load CSV data into the database (stores, timings, status logs)."

    def add_arguments(self, parser):
        parser.add_argument("--stores", type=str, help="Path to stores CSV (data.csv)")
        parser.add_argument("--timings", type=str, help="Path to timings CSV (Menu_hours.csv)")
        parser.add_argument("--status", type=str, help="Path to status logs CSV (store_status.csv)")

    def handle(self, *args, **options):
        if options["stores"]:
            self.load_stores(options["stores"])
        if options["timings"]:
            self.load_timings(options["timings"])
        if options["status"]:
            self.load_status_logs(options["status"])

    # -------------------
    # Load Stores
    # -------------------
    def load_stores(self, filepath):
        self.stdout.write(self.style.MIGRATE_HEADING(f"📂 Loading Stores from {filepath}"))
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                store_id = row["store_id"].strip()
                timezone = row.get("timezone_str") or "UTC"
                Store.objects.update_or_create(
                    store_id=store_id,
                    defaults={"timezone_str": timezone}
                )
        self.stdout.write(self.style.SUCCESS("✅ Stores loaded successfully"))

    # -------------------
    # Load Timings
    # -------------------
    def load_timings(self, filepath):
        self.stdout.write(self.style.MIGRATE_HEADING(f"📂 Loading Store Timings from {filepath}"))
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                store_id = row["store_id"].strip()

                store, _ = Store.objects.get_or_create(
                    store_id=store_id,
                    defaults={"timezone_str": "UTC"}
                )

                StoreTiming.objects.create(
                    store=store,
                    day=int(row["day"]),
                    start_time=row["start_time_local"],
                    end_time=row["end_time_local"],
                )
        self.stdout.write(self.style.SUCCESS("✅ Store timings loaded successfully"))

    # -------------------
    # Load Status Logs
    # -------------------
    def load_status_logs(self, filepath):
        self.stdout.write(self.style.MIGRATE_HEADING(f"📂 Loading Store Status Logs from {filepath}"))

        # cache stores in memory
        stores = {s.store_id: s for s in Store.objects.all()}

        # ✅ logs_to_create must be inside the function
        logs_to_create = []

        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                store_id = row["store_id"].strip()

                store = stores.get(store_id)
                if not store:
                    store = Store.objects.create(store_id=store_id, timezone_str="UTC")
                    stores[store_id] = store

                status_str = row["status"].lower().strip()
                status = StoreStatus.ACTIVE if status_str in ("active", "1") else StoreStatus.INACTIVE

                timestamp = parse_datetime(row["timestamp_utc"])

                logs_to_create.append(StoreStatusLog(
                    store=store,
                    status=status,
                    timestamp=timestamp
                ))

                # print progress every 50k
                if i % 50000 == 0:
                    self.stdout.write(f"Processed {i} rows...")

        # ✅ bulk insert after loop
        if logs_to_create:
            StoreStatusLog.objects.bulk_create(logs_to_create, batch_size=5000)

        self.stdout.write(self.style.SUCCESS(f"✅ {len(logs_to_create)} logs loaded successfully"))