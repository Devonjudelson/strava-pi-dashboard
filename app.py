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

def get_week_bounds(
    week_start: str | None = None,
) -> tuple[datetime, datetime]:
    """Return the Monday and next Monday for a selected week."""

    if week_start:
        monday_date = datetime.strptime(
            week_start,
            "%Y-%m-%d",
        ).date()

        monday = datetime.combine(
            monday_date,
            time.min,
            tzinfo=TIMEZONE,
        )
    else:
        now = datetime.now(TIMEZONE)

        monday = (
            now - timedelta(days=now.weekday())
        ).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    next_monday = monday + timedelta(days=7)

    return monday, next_monday

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

@app.route("/api/weekly")
def weekly_mileage():
    try:
        requested_week = request.args.get("week_start")

        monday, next_monday = get_week_bounds(
            requested_week
        )

        activities = strava.get_activities(
            after=int(monday.timestamp()),
            before=int(next_monday.timestamp()),
            per_page=100,
        )

        runs = [
            activity
            for activity in activities
            if (
                activity.get("sport_type") in RUN_TYPES
                or activity.get("type") == "Run"
            )
        ]

        daily_mileage = {
            day: 0.0
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

            daily_mileage[day_name] += meters_to_miles(
                run.get("distance", 0)
            )

        formatted_days = [
            {
                "day": day,
                "short_day": day[:3],
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
            "week_start": monday.date().isoformat(),
            "week_end": (
                next_monday - timedelta(days=1)
            ).date().isoformat(),
            "week_label": (
                f"{monday.strftime('%b %d')} – "
                f"{(next_monday - timedelta(days=1)).strftime('%b %d')}"
            ),
            "total_miles": round(total_miles, 2),
            "run_count": len(runs),
            "days": formatted_days,
        })

    except ValueError:
        return jsonify({
            "success": False,
            "error": (
                "week_start must use YYYY-MM-DD format."
            ),
        }), 400

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

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500
        
@app.route("/api/weekly-history")
def weekly_history():
    try:
        current_monday, next_monday = get_week_bounds()

        first_monday = (
            current_monday - timedelta(weeks=9)
        )

        activities = strava.get_activities(
            after=int(first_monday.timestamp()),
            before=int(next_monday.timestamp()),
            per_page=200,
        )

        weeks = []

        for index in range(10):
            week_start = (
                first_monday + timedelta(weeks=index)
            )

            week_end = week_start + timedelta(days=7)

            weeks.append({
                "week_start": week_start,
                "week_end": week_end,
                "miles": 0.0,
                "run_count": 0,
            })

        for activity in activities:
            is_run = (
                activity.get("sport_type") in RUN_TYPES
                or activity.get("type") == "Run"
            )

            if not is_run:
                continue

            start_date = activity.get("start_date_local")

            if not start_date:
                continue

            activity_date = datetime.fromisoformat(
                start_date.replace("Z", "+00:00")
            )

            activity_monday = (
                activity_date
                - timedelta(days=activity_date.weekday())
            ).replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

            week_index = (
                activity_monday.date()
                - first_monday.date()
            ).days // 7

            if 0 <= week_index < len(weeks):
                weeks[week_index]["miles"] += (
                    meters_to_miles(
                        activity.get("distance", 0)
                    )
                )

                weeks[week_index]["run_count"] += 1

        formatted_weeks = []

        for week in weeks:
            formatted_weeks.append({
                "week_start": (
                    week["week_start"]
                    .date()
                    .isoformat()
                ),
                "label": week[
                    "week_start"
                ].strftime("%b %d"),
                "full_label": (
                    f"{week['week_start'].strftime('%b %d')}"
                    " – "
                    f"{(week['week_end'] - timedelta(days=1)).strftime('%b %d')}"
                ),
                "miles": round(week["miles"], 2),
                "run_count": week["run_count"],
                "current_week": (
                    week["week_start"].date()
                    == current_monday.date()
                ),
            })

        return jsonify({
            "success": True,
            "weeks": formatted_weeks,
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

    except Exception as error:
        return jsonify({
            "success": False,
            "error": str(error),
        }), 500

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

        
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True,
    )
    
