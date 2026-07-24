import os
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
load_dotenv(BASE_DIR / ".env")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mediall_en.settings")

import django  # noqa: E402

django.setup()

from accounts.models import DoctorProfile, PatientProfile  # noqa: E402


DOCTOR_UPSERT_SQL = """
INSERT INTO `mediall_doctor` (
    `source_profile_id`, `source_user_id`, `email`, `phone`, `full_name`,
    `birth_year`, `country`, `avatar`, `is_verified`, `specialties`,
    `position`, `workplace`, `introduction`, `training_history`,
    `years_experience`, `video_consultation_fee`, `message_consultation_fee`,
    `work_schedule_type`, `custom_work_start`, `custom_work_end`,
    `weekend_off`, `created_at`, `updated_at`
) VALUES (
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s
)
ON DUPLICATE KEY UPDATE
    `source_user_id` = VALUES(`source_user_id`),
    `email` = VALUES(`email`),
    `phone` = VALUES(`phone`),
    `full_name` = VALUES(`full_name`),
    `birth_year` = VALUES(`birth_year`),
    `country` = VALUES(`country`),
    `avatar` = VALUES(`avatar`),
    `is_verified` = VALUES(`is_verified`),
    `specialties` = VALUES(`specialties`),
    `position` = VALUES(`position`),
    `workplace` = VALUES(`workplace`),
    `introduction` = VALUES(`introduction`),
    `training_history` = VALUES(`training_history`),
    `years_experience` = VALUES(`years_experience`),
    `video_consultation_fee` = VALUES(`video_consultation_fee`),
    `message_consultation_fee` = VALUES(`message_consultation_fee`),
    `work_schedule_type` = VALUES(`work_schedule_type`),
    `custom_work_start` = VALUES(`custom_work_start`),
    `custom_work_end` = VALUES(`custom_work_end`),
    `weekend_off` = VALUES(`weekend_off`),
    `updated_at` = VALUES(`updated_at`)
"""


CUSTOMER_UPSERT_SQL = """
INSERT INTO `mediall_cus` (
    `source_profile_id`, `source_user_id`, `email`, `phone`, `full_name`,
    `birth_year`, `country`, `avatar`, `address`, `is_member`, `created_at`,
    `updated_at`
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
    `source_user_id` = VALUES(`source_user_id`),
    `email` = VALUES(`email`),
    `phone` = VALUES(`phone`),
    `full_name` = VALUES(`full_name`),
    `birth_year` = VALUES(`birth_year`),
    `country` = VALUES(`country`),
    `avatar` = VALUES(`avatar`),
    `address` = VALUES(`address`),
    `is_member` = VALUES(`is_member`),
    `updated_at` = VALUES(`updated_at`)
"""


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def mysql_connection():
    return pymysql.connect(
        host=required_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=required_env("DB_USER"),
        password=required_env("DB_PASSWORD"),
        database=required_env("DB_NAME"),
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
    )


def naive_datetime(value):
    return value.replace(tzinfo=None) if value and value.tzinfo else value


def user_email(user):
    return (user.email or user.username).strip()


def doctor_values(profile):
    account = profile.account
    user = account.user
    return (
        profile.pk,
        user.pk,
        user_email(user),
        account.phone,
        profile.full_name,
        profile.birth_year,
        profile.country,
        str(profile.avatar or ""),
        profile.is_verified,
        profile.specialties,
        profile.position,
        profile.workplace,
        profile.introduction,
        profile.training_history,
        profile.years_experience,
        profile.video_consultation_fee,
        profile.message_consultation_fee,
        profile.work_schedule_type,
        profile.custom_work_start,
        profile.custom_work_end,
        profile.weekend_off,
        naive_datetime(profile.created_at),
        naive_datetime(profile.updated_at),
    )


def customer_values(profile):
    account = profile.account
    user = account.user
    return (
        profile.pk,
        user.pk,
        user_email(user),
        account.phone,
        profile.full_name,
        profile.birth_year,
        profile.country,
        str(profile.avatar or ""),
        profile.address,
        profile.is_member,
        naive_datetime(profile.created_at),
        naive_datetime(profile.updated_at),
    )


def main():
    doctors = list(
        DoctorProfile.objects.select_related("account__user").order_by("pk")
    )
    customers = list(
        PatientProfile.objects.select_related("account__user").order_by("pk")
    )

    connection = mysql_connection()
    try:
        with connection.cursor() as cursor:
            cursor.executemany(DOCTOR_UPSERT_SQL, [doctor_values(item) for item in doctors])
            cursor.executemany(
                CUSTOMER_UPSERT_SQL,
                [customer_values(item) for item in customers],
            )
        connection.commit()

        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM `mediall_doctor`")
            doctor_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM `mediall_cus`")
            customer_count = cursor.fetchone()[0]
        print(f"Doctors synced: {len(doctors)}; remote rows: {doctor_count}")
        print(f"Customers synced: {len(customers)}; remote rows: {customer_count}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
