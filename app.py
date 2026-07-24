from flask import Flask, jsonify
import requests

from services.strava_client import StravaClient


app = Flask(__name__)
strava = StravaClient()


@app.route("/")
def home():
    return """
        <h1>Strava Dashboard</h1>
        <p>Server is running!</p>
        <p><a href="/api/athlete">Test Strava connection</a></p>
    """


@app.route("/api/athlete")
def athlete():
    try:
        athlete_data = strava.get_athlete()

        return jsonify({
            "connected": True,
            "id": athlete_data.get("id"),
            "first_name": athlete_data.get("firstname"),
            "last_name": athlete_data.get("lastname"),
            "city": athlete_data.get("city"),
            "state": athlete_data.get("state"),
            "profile": athlete_data.get("profile"),
        })

    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code

        return jsonify({
            "connected": False,
            "error": f"Strava returned HTTP {status_code}",
            "details": error.response.text,
        }), status_code

    except Exception as error:
        return jsonify({
            "connected": False,
            "error": str(error),
        }), 500


if __name__ == "__main__":
    app.run(debug=True)