from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from datetime import datetime
from .models import SystemEarnings, MonthlyEarnings

def snapshot_monthly_earnings():
    now = datetime.now()
    system = SystemEarnings.load()

    MonthlyEarnings.objects.create(
        year=now.year,
        month=now.month,
        total_volume=system.total_volume,
        total_transactions=system.total_transactions,
        total_successful_transactions=system.total_successful_transactions,
        total_failed_transactions=system.total_failed_transactions,
        total_earnings=system.total_earnings,
    )

    # Reset system earnings for next month
    system.total_volume = 0
    system.total_transactions = 0
    system.total_successful_transactions = 0
    system.total_failed_transactions = 0
    system.total_earnings = 0
    system.save()

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # ✅ Register the job manually — don't use @register_job
    scheduler.add_job(
        snapshot_monthly_earnings,
        trigger="cron",
        day=1,
        hour=0,
        minute=0,
        id="monthly_snapshot",
        name="Monthly Earnings Snapshot",
        replace_existing=True,
    )

    scheduler.start()
