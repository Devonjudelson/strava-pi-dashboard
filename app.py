from __future__ import annotations
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import requests
from flask import Flask, jsonify, render_template, request


from services.strava_client import StravaClient


app = Flask(__name__)
strava = StravaClient()

TIMEZONE = ZoneInfo("America/New_York")
METERS_PER_MILE = 1609.344
RUN_TYPES = {"Run", "TrailRun", "VirtualRun"}


def get_today_bounds() -> tuple[int, int]:
    """Return Unix timestamps for the start and end of today."""

    today = datetime.now(TIMEZONE).date()

    start = datetime.combine(
        today,
        time.min,
        tzinfo=TIMEZONE,
    )

    end = start + timedelta(days=1)

    return int(start.timestamp()), int(end.timestamp())


def meters_to_miles(meters: float) -> float:
    return meters / METERS_PER_MILE


def calculate_pace(
    distance_meters: float,
    moving_time_seconds: int,
) -> str | None:
    """Calculate average minutes per mile."""

    distance_miles = meters_to_miles(distance_meters)

    if distance_miles <= 0:
        return None

    seconds_per_mile = moving_time_seconds / distance_miles

    minutes = int(seconds_per_mile // 60)
    seconds = round(seconds_per_mile % 60)

    if seconds == 60:
        minutes += 1
        seconds = 0

    return f"{minutes}:{seconds:02d}"


def format_run(activity: dict) -> dict:
    """Convert a Strava activity into dashboard-friendly data."""

    distance_meters = activity.get("distance", 0)
    moving_time_seconds = activity.get("moving_time", 0)

    return {
        "id": activity.get("id"),
        "name": activity.get("name", "Run"),
        "start_time": activity.get("start_date_local"),
        "distance_miles": round(
            meters_to_miles(distance_meters),
            2,
        ),
        "pace_per_mile": calculate_pace(
            distance_meters,
            moving_time_seconds,
        ),
        "average_heart_rate": (
            round(activity["average_heartrate"])
            if activity.get("average_heartrate") is not None
            else None
        ),
        "moving_time_seconds": moving_time_seconds,
        "gear_id": activity.get("gear_id"),
        "route_polyline": (
            activity.get("map", {}).get("summary_polyline")
        ),
    }
    
def format_shoe(shoe: dict) -> dict:
    distance_meters = shoe.get("distance", 0)

    return {
        "id": shoe.get("id"),
        "name": shoe.get("name", "Unnamed Shoe"),
        "primary": shoe.get("primary", False),
        "distance_miles": round(
            meters_to_miles(distance_meters),
            1,
        ),
    }


@app.route("/")
def home():
    return render_template("dashboard.html")
    """return 
        <h1>Strava Dashboard</h1>
        <p>Server is running!</p>

        <ul>
            <li>
                <a href="/api/athlete">
                    Test athlete profile
                </a>
            </li>
            <li>
                <a href="/api/today">
                    Test today's runs
                </a>
            </li>
        </ul>
    """
@app.route("/shoes")
def shoe_dashboard():
    return render_template("shoes.html")

@app.route("/weekly")
def weekly_dashboard():
    return render_template("weekly.html")

@app.route("/api/shoes")
def shoes():
    try:
        athlete_data = strava.get_athlete()

        athlete_shoes = athlete_data.get("shoes", [])

        shoes = [
            format_shoe(shoe)
            for shoe in athlete_shoes
        ]

        shoes.sort(
            key=lambda shoe: shoe["distance_miles"],
            reverse=True,
        )

        return jsonify({
            "success": True,
            "shoe_count": len(shoes),
            "shoes": shoes,
        })

    except requests.exceptions.HTTPError as error:
        return jsonify({
            "success": False,
            "error": error.response.text,
        }), error.response.status_code

@app.route("/api/athlete")
def athlete():
    try:
        athlete_data = strava.get_athlete()

        return jsonify({
            "connected": True,
            "id": athlete_data.get("id"),
            "first_name": athlete_data.get("firstname"),
            "last_name": athlete_data.get("lastname"),
        })

    except requests.exceptions.HTTPError as error:
        return jsonify({
            "connected": False,
            "error": error.response.text,
        }), error.response.status_code


@app.route("/api/today")
def todays_runs():
    try:
        after, before = get_today_bounds()

        activities = strava.get_activities(
            after=after,
            before=before,
        )

        runs = [
            format_run(activity)
            for activity in activities
            if activity.get("sport_type") in RUN_TYPES
        ]

        runs.sort(
            key=lambda run: run.get("start_time") or ""
        )

        return jsonify({
            "success": True,
            "date": datetime.now(TIMEZONE).date().isoformat(),
            "run_count": len(runs),
            "runs": runs,
        })
        


    except requests.exceptions.HTTPError as error:
        return jsonify({
            "success": False,
            "error": error.response.text,
        }), error.response.status_code

    except requests.exceptions.RequestException as error:
        return jsonify({
            "success": False,
            "error": f"Could not connect to Strava: {error}",
        }), 500
@app.route("/api/weekly")
def weekly_mileage():
    try:
        now = datetime.now().astimezone()

        monday = now - timedelta(days=now.weekday())
        monday = monday.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        activities = strava.get_activities(
            after=int(monday.timestamp())
        )

        running_types = {
            "Run",
            "TrailRun",
            "VirtualRun",
        }

        runs = [
            activity
            for activity in activities
            if activity.get("sport_type") in running_types
            or activity.get("type") == "Run"
        ]

        daily_mileage = {
            day: 0
            for day in [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        }

        for run in runs:
            start_date = run.get("start_date_local")

            if not start_date:
                continue

            run_date = datetime.fromisoformat(
                start_date.replace("Z", "+00:00")
            )

            day_name = run_date.strftime("%A")
            distance_miles = meters_to_miles(
                run.get("distance", 0)
            )

            daily_mileage[day_name] += distance_miles

        formatted_days = [
            {
                "day": day,
                "miles": round(miles, 2),
            }
            for day, miles in daily_mileage.items()
        ]

        total_miles = sum(
            day["miles"]
            for day in formatted_days
        )

        return jsonify({
            "success": True,
            "week_start": monday.strftime("%B %d, %Y"),
            "total_miles": round(total_miles, 2),
            "run_count": len(runs),
            "days": formatted_days,
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500
        
        
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True,
    )
    
