import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


DOCTOR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `mediall_doctor` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `source_profile_id` BIGINT UNSIGNED NULL,
    `source_user_id` BIGINT UNSIGNED NULL,
    `email` VARCHAR(254) NOT NULL,
    `phone` VARCHAR(20) NOT NULL DEFAULT '',
    `full_name` VARCHAR(150) NOT NULL DEFAULT '',
    `birth_year` SMALLINT UNSIGNED NULL,
    `country` VARCHAR(100) NOT NULL DEFAULT '',
    `avatar` VARCHAR(255) NOT NULL DEFAULT '',
    `is_verified` TINYINT(1) NOT NULL DEFAULT 0,
    `specialties` VARCHAR(255) NOT NULL DEFAULT '',
    `position` VARCHAR(150) NOT NULL DEFAULT '',
    `workplace` VARCHAR(255) NOT NULL DEFAULT '',
    `introduction` LONGTEXT NOT NULL,
    `training_history` LONGTEXT NOT NULL,
    `years_experience` SMALLINT UNSIGNED NULL,
    `video_consultation_fee` DECIMAL(12,2) NULL,
    `message_consultation_fee` DECIMAL(12,2) NULL,
    `work_schedule_type` VARCHAR(20) NOT NULL DEFAULT 'office',
    `custom_work_start` TIME NULL,
    `custom_work_end` TIME NULL,
    `weekend_off` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `mediall_doctor_source_profile_uniq` (`source_profile_id`),
    KEY `mediall_doctor_email_idx` (`email`),
    KEY `mediall_doctor_specialties_idx` (`specialties`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


CUSTOMER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS `mediall_cus` (
    `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    `source_profile_id` BIGINT UNSIGNED NULL,
    `source_user_id` BIGINT UNSIGNED NULL,
    `email` VARCHAR(254) NOT NULL,
    `phone` VARCHAR(20) NOT NULL DEFAULT '',
    `full_name` VARCHAR(150) NOT NULL DEFAULT '',
    `birth_year` SMALLINT UNSIGNED NULL,
    `country` VARCHAR(100) NOT NULL DEFAULT '',
    `avatar` VARCHAR(255) NOT NULL DEFAULT '',
    `address` VARCHAR(255) NOT NULL DEFAULT '',
    `is_member` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `mediall_cus_source_profile_uniq` (`source_profile_id`),
    KEY `mediall_cus_email_idx` (`email`),
    KEY `mediall_cus_phone_idx` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
"""


def required_env(name):
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def main():
    connection = pymysql.connect(
        host=required_env("DB_HOST"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=required_env("DB_USER"),
        password=required_env("DB_PASSWORD"),
        database=required_env("DB_NAME"),
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TABLE_NAME
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME IN ('mediall', 'mediall_doctor')
                """,
                (required_env("DB_NAME"),),
            )
            existing_tables = {row[0] for row in cursor.fetchall()}
            if "mediall" in existing_tables and "mediall_doctor" not in existing_tables:
                cursor.execute("RENAME TABLE `mediall` TO `mediall_doctor`")

            cursor.execute(DOCTOR_TABLE_SQL)
            cursor.execute(CUSTOMER_TABLE_SQL)
        connection.commit()

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT TABLE_NAME, COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME IN ('mediall_doctor', 'mediall_cus')
                GROUP BY TABLE_NAME
                ORDER BY TABLE_NAME
                """,
                (required_env("DB_NAME"),),
            )
            for table_name, column_count in cursor.fetchall():
                print(f"{table_name}: {column_count} columns")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    main()
