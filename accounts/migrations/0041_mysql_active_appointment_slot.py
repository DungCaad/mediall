from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0040_featuredpostgroup_blogpost_featured_group"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveConstraint(
                    model_name="doctorappointment",
                    name="unique_doctor_appointment_time_slot",
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE accounts_doctorappointment
                        ADD COLUMN active_slot_guard TINYINT
                            GENERATED ALWAYS AS (
                                CASE WHEN status <> 'rejected' THEN 1 ELSE NULL END
                            ) STORED,
                        ADD UNIQUE KEY unique_doctor_appointment_time_slot (
                            doctor_id, appointment_date, time_slot, active_slot_guard
                        )
                    """,
                    reverse_sql="""
                        ALTER TABLE accounts_doctorappointment
                        DROP INDEX unique_doctor_appointment_time_slot,
                        DROP COLUMN active_slot_guard
                    """,
                ),
            ],
        ),
    ]
