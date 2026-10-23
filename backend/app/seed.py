import datetime
from sqlalchemy.orm import Session
from app.models.wellness import (
    Patient,
    Habit,
    WellnessPlan,
    WellnessGoal,
    HabitLog,
    Measurement,
    DriftEvent,
)
from app.db.database import engine, Base


def init_db():
    """Create all tables in the database if they don't already exist."""
    Base.metadata.create_all(bind=engine)


def seed_database(db: Session) -> dict:
    """
    Repeatable synthetic seed data initialization.
    Does not duplicate records if run multiple times.
    Never deletes existing user data.
    
    Populates 6 fictional patient scenarios:
    1. Eleanor Vance: Type 2 diabetes with previously reviewed wellness plan.
    2. Marcus Chen: Hypertension with daily logging instructions.
    3. Liam O'Connor: Sleep consistency improvement.
    4. Aisha Patel: Physical activity habit building.
    5. Sarah Jenkins: Incomplete wellness profile (Sparse data, baseline onboarding).
    6. Robert Taylor: Declining habit adherence across multiple consecutive weeks (Drift).
    """
    init_db()

    # 1. Habits Seed (Master Habit Catalog)
    habits_data = [
        {"code": "post_meal_walk", "name": "Post-Meal Brisk Walk", "category": "activity", "default_unit": "min", "description": "Helps blunt post-prandial glycemic excursions."},
        {"code": "hydration_intake", "name": "Hydration Target", "category": "hydration", "default_unit": "L", "description": "Daily balanced cellular hydration."},
        {"code": "glucose_check", "name": "Blood Glucose Log", "category": "medication", "default_unit": "log", "description": "Pre-prandial or post-prandial glucose tracking."},
        {"code": "bp_check", "name": "Resting Blood Pressure Check", "category": "medication", "default_unit": "mmHg", "description": "Seated resting blood pressure measurement."},
        {"code": "dash_nutrition", "name": "Low-Sodium DASH Meal", "category": "nutrition", "default_unit": "meals", "description": "Dietary Approaches to Stop Hypertension guidelines."},
        {"code": "sleep_schedule", "name": "Consistent Sleep Schedule", "category": "sleep", "default_unit": "hours", "description": "Retiring and waking within consistent 30-min window."},
        {"code": "wind_down_ritual", "name": "Evening Digital Wind-Down", "category": "mindfulness", "default_unit": "min", "description": "Blue light cessation 45 mins before rest."},
        {"code": "aerobic_cardio", "name": "Zone 2 Aerobic Exercise", "category": "activity", "default_unit": "min", "description": "Cardiorespiratory endurance training at 65-75% max HR."},
        {"code": "baseline_survey", "name": "Baseline Wellness Assessment", "category": "mindfulness", "default_unit": "survey", "description": "Initial lifestyle assessment and questionnaire."},
    ]

    habit_map = {}
    for h in habits_data:
        existing = db.query(Habit).filter(Habit.code == h["code"]).first()
        if not existing:
            habit_obj = Habit(**h)
            db.add(habit_obj)
            db.flush()
            habit_map[h["code"]] = habit_obj
        else:
            habit_map[h["code"]] = existing

    # 2. Patients Seed
    patients_data = [
        # Scenario 1: Type 2 diabetes with a previously reviewed wellness plan
        {
            "synthetic_identifier": "SYNTH-T2D-8841",
            "display_name": "Eleanor Vance",
            "age": 54,
            "gender": "Female",
            "primary_condition": "Type 2 Diabetes Mellitus",
            "condition_severity": "Moderate",
            "condition_notes": "Requires post-meal glycemic management and consistent hydration tracking.",
            "secondary_conditions": [
                {"name": "Stage 1 Essential Hypertension", "severity": "Managed", "diagnosed_year": 2024}
            ],
            "profile_completeness": 94,
            "data_quality_rating": "High Quality",
            "preferences": {"dietary": "Mediterranean-leaning", "preferred_walk_time": "morning"},
            "plan_name": "Metabolic Stabilization & Glycemic Guard v3",
            "plan_status": "Active",
            "plan_version": "v3.0",
            "goals": [
                {"habit": "post_meal_walk", "title": "20-minute Post-Breakfast Brisk Walk", "target_value": 20, "target_unit": "min", "priority": "high", "recommended_time": "08:30 AM", "completed_today": True},
                {"habit": "hydration_intake", "title": "Hydration Target (2.5L)", "target_value": 2.5, "target_unit": "L", "priority": "medium", "recommended_time": "Throughout day", "completed_today": True},
                {"habit": "glucose_check", "title": "Pre-Dinner Blood Glucose Log", "target_value": 1, "target_unit": "log", "priority": "high", "recommended_time": "06:30 PM", "completed_today": False},
            ],
            "measurements": [
                {"measurement_type": "hba1c", "value": 7.1, "unit": "%", "days_ago": 14},
                {"measurement_type": "fasting_glucose", "value": 128.0, "unit": "mg/dL", "days_ago": 1},
            ],
            "log_pattern": "moderate", # ~75% completion
        },
        # Scenario 2: Hypertension with logging instructions
        {
            "synthetic_identifier": "SYNTH-HTN-4219",
            "display_name": "Marcus Chen",
            "age": 48,
            "gender": "Male",
            "primary_condition": "Hypertension (Stage 1)",
            "condition_severity": "Managed",
            "condition_notes": "Prescribed lifestyle protocol with strict home blood pressure monitoring and DASH dietary tracking.",
            "secondary_conditions": [],
            "profile_completeness": 98,
            "data_quality_rating": "High Quality",
            "preferences": {"tracking_reminder": "07:00 AM", "activity_preference": "cycling"},
            "plan_name": "Cardiovascular Resilience & DASH Protocol",
            "plan_status": "Active",
            "plan_version": "v2.1",
            "goals": [
                {"habit": "bp_check", "title": "Morning Resting Blood Pressure Check", "target_value": 1, "target_unit": "log", "priority": "high", "recommended_time": "07:15 AM", "completed_today": True},
                {"habit": "dash_nutrition", "title": "Low-Sodium DASH Meals (< 2000mg Na)", "target_value": 3, "target_unit": "meals", "priority": "high", "recommended_time": "Mealtimes", "completed_today": True},
                {"habit": "aerobic_cardio", "title": "30-Min Zone 2 Aerobic Cycling", "target_value": 30, "target_unit": "min", "priority": "medium", "recommended_time": "05:30 PM", "completed_today": True},
            ],
            "measurements": [
                {"measurement_type": "systolic_bp", "value": 126.0, "unit": "mmHg", "days_ago": 0},
                {"measurement_type": "diastolic_bp", "value": 82.0, "unit": "mmHg", "days_ago": 0},
            ],
            "log_pattern": "high", # ~95% completion
        },
        # Scenario 3: Sleep consistency improvement
        {
            "synthetic_identifier": "SYNTH-SLP-3301",
            "display_name": "Liam O'Connor",
            "age": 36,
            "gender": "Male",
            "primary_condition": "Circadian Rhythm Dysregulation",
            "condition_severity": "Moderate",
            "condition_notes": "Difficulty maintaining regular sleep-wake windows; high cognitive load evening work.",
            "secondary_conditions": [],
            "profile_completeness": 88,
            "data_quality_rating": "High Quality",
            "preferences": {"target_bedtime": "10:30 PM", "wind_down_style": "audiobook"},
            "plan_name": "Circadian Restoration & Sleep Regularity",
            "plan_status": "Active",
            "plan_version": "v1.2",
            "goals": [
                {"habit": "sleep_schedule", "title": "7.5+ Hours Sleep in Consistent Window", "target_value": 7.5, "target_unit": "hours", "priority": "high", "recommended_time": "10:30 PM", "completed_today": False},
                {"habit": "wind_down_ritual", "title": "Digital Screen Cutoff at 09:45 PM", "target_value": 45, "target_unit": "min", "priority": "medium", "recommended_time": "09:45 PM", "completed_today": False},
            ],
            "measurements": [
                {"measurement_type": "average_sleep", "value": 6.8, "unit": "hours", "days_ago": 2},
            ],
            "log_pattern": "moderate",
        },
        # Scenario 4: Physical activity habit building
        {
            "synthetic_identifier": "SYNTH-ACT-7714",
            "display_name": "Aisha Patel",
            "age": 42,
            "gender": "Female",
            "primary_condition": "Metabolic Syndrome Prevention",
            "condition_severity": "Mild",
            "condition_notes": "Sedentary occupational profile; aiming to integrate incremental physical activity.",
            "secondary_conditions": [],
            "profile_completeness": 92,
            "data_quality_rating": "High Quality",
            "preferences": {"schedule": "lunchtime walk, weekend swim"},
            "plan_name": "Progressive Daily Activity Escalator",
            "plan_status": "Active",
            "plan_version": "v1.0",
            "goals": [
                {"habit": "aerobic_cardio", "title": "30-Minute Midday Movement / Brisk Walk", "target_value": 30, "target_unit": "min", "priority": "high", "recommended_time": "12:30 PM", "completed_today": True},
                {"habit": "hydration_intake", "title": "Hydration Target (2.0L)", "target_value": 2.0, "target_unit": "L", "priority": "medium", "recommended_time": "Throughout day", "completed_today": True},
            ],
            "measurements": [
                {"measurement_type": "resting_heart_rate", "value": 72.0, "unit": "bpm", "days_ago": 1},
            ],
            "log_pattern": "high",
        },
        # Scenario 5: Incomplete wellness profile
        {
            "synthetic_identifier": "SYNTH-NEW-1092",
            "display_name": "Sarah Jenkins",
            "age": 39,
            "gender": "Female",
            "primary_condition": "Early Metabolic Syndrome Risk",
            "condition_severity": "Under Review",
            "condition_notes": "New onboarding patient. Intake lifestyle questionnaire pending completion.",
            "secondary_conditions": [],
            "profile_completeness": 42,
            "data_quality_rating": "Sparse",
            "preferences": {},
            "plan_name": "Baseline Habit Foundation v1",
            "plan_status": "Under Review",
            "plan_version": "v0.5",
            "goals": [
                {"habit": "baseline_survey", "title": "Complete Intake Lifestyle Survey", "target_value": 1, "target_unit": "survey", "priority": "high", "recommended_time": "Anytime", "completed_today": False},
                {"habit": "hydration_intake", "title": "Baseline Water Intake Log", "target_value": 2.0, "target_unit": "L", "priority": "medium", "recommended_time": "Daily", "completed_today": True},
            ],
            "measurements": [],
            "log_pattern": "sparse", # Only 3 days of logs
        },
        # Scenario 6: Declining habit adherence across multiple consecutive weeks (Wellness Drift)
        {
            "synthetic_identifier": "SYNTH-DFT-9905",
            "display_name": "Robert Taylor",
            "age": 61,
            "gender": "Male",
            "primary_condition": "Type 2 Diabetes & Chronic Fatigue",
            "condition_severity": "Moderate",
            "condition_notes": "Previously established solid adherence that has noticeably eroded over the past 3 weeks.",
            "secondary_conditions": [
                {"name": "Dyslipidemia", "severity": "Managed", "diagnosed_year": 2022}
            ],
            "profile_completeness": 96,
            "data_quality_rating": "High Quality",
            "preferences": {"morning_routine": "coffee first", "barrier": "work stress"},
            "plan_name": "Comprehensive Glycemic & Vitality Regimen",
            "plan_status": "Active",
            "plan_version": "v2.0",
            "goals": [
                {"habit": "post_meal_walk", "title": "20-minute Post-Meal Walk", "target_value": 20, "target_unit": "min", "priority": "high", "recommended_time": "07:30 PM", "completed_today": False},
                {"habit": "glucose_check", "title": "Daily Fasting Glucose Log", "target_value": 1, "target_unit": "log", "priority": "high", "recommended_time": "07:00 AM", "completed_today": False},
                {"habit": "hydration_intake", "title": "Daily Water Intake (2.5L)", "target_value": 2.5, "target_unit": "L", "priority": "medium", "recommended_time": "All day", "completed_today": False},
            ],
            "measurements": [
                {"measurement_type": "fasting_glucose", "value": 142.0, "unit": "mg/dL", "days_ago": 2},
                {"measurement_type": "weight", "value": 89.5, "unit": "kg", "days_ago": 7},
            ],
            "log_pattern": "declining_drift", # Clear multi-week decline: 85% baseline -> 58% recent
            "drift_event": {
                "baseline_adherence": 85.0,
                "current_adherence": 58.0,
                "percentage_point_change": -27.0,
                "observation_window": "Past 14 days vs prior 28-day baseline",
                "status": "Active",
                "flag_reason": "Adherence dropped 27 percentage points below established baseline. Evening walk and glucose logs missed on 9 of the last 14 days.",
                "recovery_suggestion": "Temporarily shorten evening walk to 10 minutes and shift blood glucose log to immediately after morning coffee.",
            },
        },
    ]

    today = datetime.date.today()
    seeded_count = 0

    for p_info in patients_data:
        patient = db.query(Patient).filter(Patient.synthetic_identifier == p_info["synthetic_identifier"]).first()
        if not patient:
            patient = Patient(
                synthetic_identifier=p_info["synthetic_identifier"],
                display_name=p_info["display_name"],
                age=p_info["age"],
                gender=p_info["gender"],
                primary_condition=p_info["primary_condition"],
                condition_severity=p_info["condition_severity"],
                condition_notes=p_info.get("condition_notes"),
                secondary_conditions=p_info.get("secondary_conditions", []),
                profile_completeness=p_info["profile_completeness"],
                data_quality_rating=p_info["data_quality_rating"],
                preferences=p_info.get("preferences", {}),
                is_synthetic=True,
            )
            db.add(patient)
            db.flush()
            seeded_count += 1

            # Create Wellness Plan
            plan = WellnessPlan(
                patient_id=patient.id,
                plan_name=p_info["plan_name"],
                version=p_info["plan_version"],
                status=p_info["plan_status"],
                description=f"Synthetic protocol tailored for {patient.primary_condition}.",
            )
            db.add(plan)
            db.flush()

            # Create Goals
            for g in p_info["goals"]:
                habit_obj = habit_map.get(g["habit"])
                if habit_obj:
                    goal = WellnessGoal(
                        plan_id=plan.id,
                        habit_id=habit_obj.id,
                        title=g["title"],
                        target_value=g.get("target_value"),
                        target_unit=g.get("target_unit"),
                        priority=g.get("priority", "medium"),
                        recommended_time=g.get("recommended_time"),
                        is_completed_today=g.get("completed_today", False),
                        start_date=today - datetime.timedelta(days=30),
                    )
                    db.add(goal)

            # Create Measurements
            for m in p_info.get("measurements", []):
                measurement = Measurement(
                    patient_id=patient.id,
                    measurement_type=m["measurement_type"],
                    value=m["value"],
                    unit=m["unit"],
                    recorded_at=datetime.datetime.utcnow() - datetime.timedelta(days=m["days_ago"]),
                    context_notes="Synthetic clinical observation",
                )
                db.add(measurement)

            # Create Drift Event if specified
            if "drift_event" in p_info:
                d = p_info["drift_event"]
                drift = DriftEvent(
                    patient_id=patient.id,
                    baseline_adherence=d["baseline_adherence"],
                    current_adherence=d["current_adherence"],
                    percentage_point_change=d["percentage_point_change"],
                    observation_window=d["observation_window"],
                    status=d["status"],
                    flag_reason=d["flag_reason"],
                    recovery_suggestion=d["recovery_suggestion"],
                )
                db.add(drift)

            # Populate Dated Habit Logs (Scenario-driven)
            pattern = p_info.get("log_pattern", "moderate")
            walk_habit = habit_map.get("post_meal_walk")
            hydration_habit = habit_map.get("hydration_intake")
            glucose_habit = habit_map.get("glucose_check")
            bp_habit = habit_map.get("bp_check")

            if pattern == "sparse":
                # Only 3 days of logs
                for day_offset in range(1, 4):
                    log_d = today - datetime.timedelta(days=day_offset)
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=hydration_habit.id,
                        log_date=log_d,
                        is_completed=(day_offset % 2 == 1),
                        numeric_value=1.5 if day_offset % 2 == 1 else 0.8,
                        unit="L",
                    ))

            elif pattern == "declining_drift":
                # 35 days of history: Days 35-15 (Baseline: ~85-90%), Days 14-0 (Decline: ~40-50%)
                for day_offset in range(0, 35):
                    log_d = today - datetime.timedelta(days=day_offset)
                    if day_offset >= 14:
                        # Baseline period (high adherence)
                        completed_walk = (day_offset % 7 != 0) # 6 out of 7 days
                        completed_glucose = (day_offset % 8 != 0)
                        completed_hydration = (day_offset % 6 != 0)
                    else:
                        # Recent decline period (low adherence, consecutive missed logs)
                        completed_walk = (day_offset in [1, 5, 10]) # only 3 in 14 days
                        completed_glucose = (day_offset in [2, 6, 11])
                        completed_hydration = (day_offset % 3 == 0)

                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=walk_habit.id,
                        log_date=log_d,
                        is_completed=completed_walk,
                        numeric_value=20.0 if completed_walk else 0.0,
                        unit="min",
                        user_reported_barrier="Fatigue / prolonged workday" if not completed_walk and day_offset < 14 else None,
                    ))
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=glucose_habit.id,
                        log_date=log_d,
                        is_completed=completed_glucose,
                        numeric_value=1.0 if completed_glucose else 0.0,
                        unit="log",
                    ))
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=hydration_habit.id,
                        log_date=log_d,
                        is_completed=completed_hydration,
                        numeric_value=2.5 if completed_hydration else 1.2,
                        unit="L",
                    ))

            elif pattern == "high":
                # High adherence across 21 days (~95%)
                for day_offset in range(0, 21):
                    log_d = today - datetime.timedelta(days=day_offset)
                    habit_target = bp_habit if bp_habit else walk_habit
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=habit_target.id,
                        log_date=log_d,
                        is_completed=(day_offset != 7), # missed only 1 day
                        numeric_value=1.0,
                        unit="log",
                    ))
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=hydration_habit.id,
                        log_date=log_d,
                        is_completed=True,
                        numeric_value=2.5,
                        unit="L",
                    ))

            else: # moderate
                # Standard 14 days of logs (~75%)
                for day_offset in range(0, 14):
                    log_d = today - datetime.timedelta(days=day_offset)
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=walk_habit.id,
                        log_date=log_d,
                        is_completed=(day_offset % 4 != 0),
                        numeric_value=20.0 if day_offset % 4 != 0 else 0.0,
                        unit="min",
                    ))
                    db.add(HabitLog(
                        patient_id=patient.id,
                        habit_id=hydration_habit.id,
                        log_date=log_d,
                        is_completed=(day_offset % 3 != 0),
                        numeric_value=2.5 if day_offset % 3 != 0 else 1.0,
                        unit="L",
                    ))

    db.commit()
    total_patients = db.query(Patient).count()
    total_habits = db.query(Habit).count()
    total_logs = db.query(HabitLog).count()

    return {
        "status": "success",
        "newly_seeded_patients": seeded_count,
        "total_patients": total_patients,
        "total_habits": total_habits,
        "total_habit_logs": total_logs,
    }


if __name__ == "__main__":
    from app.db.database import SessionLocal
    db = SessionLocal()
    try:
        res = seed_database(db)
        print(f"Seed completed: {res}")
    finally:
        db.close()
