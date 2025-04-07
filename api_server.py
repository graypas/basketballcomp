from flask import Flask, request, jsonify
from flask_cors import CORS
from compare_players import list_games, get_stats, extract_player_stats, extract_team_stats
from playerDefine import Player
from game import calculate_player_stats
from utils import validate_date, safe_float
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route("/games", methods=["GET"])
def get_games():
    try:
        date = request.args.get("date")
        date = validate_date(date)
        game_ids = list_games(date)
        return jsonify({"games": game_ids})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/players", methods=["GET"])
def get_players():
    try:
        game_id = request.args.get("game_id")
        player_df, _ = get_stats(game_id)

        if "MIN" not in player_df.columns:
            raise ValueError("Player data is missing the 'MIN' column")

        player_df["MIN"] = player_df["MIN"].apply(safe_float)
        players = player_df[player_df["MIN"] > 0][["PLAYER_NAME", "TEAM_ABBREVIATION"]].drop_duplicates()
        return jsonify({"players": players.to_dict(orient="records")})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/compare", methods=["POST"])
def compare_players():
    try:
        data = request.get_json()
        game_id = data["game_id"]
        name1, team1 = data["player1"], data["team1"]
        name2, team2 = data["player2"], data["team2"]

        player_df, team_df = get_stats(game_id)

        stats1 = extract_player_stats(name1, team1, game_id, player_df)
        stats2 = extract_player_stats(name2, team2, game_id, player_df)

        team1_stats, opp1_stats = extract_team_stats(team1, game_id, team_df)
        team2_stats, opp2_stats = extract_team_stats(team2, game_id, team_df)

        p1 = Player(name1, team1, stats1)
        p2 = Player(name2, team2, stats2)

        calculate_player_stats(p1, team1_stats, opp1_stats)
        calculate_player_stats(p2, team2_stats, opp2_stats)

        return jsonify({
            "player1": {"name": p1.name, "stats": p1.stats},
            "player2": {"name": p2.name, "stats": p2.stats}
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/season-averages", methods=["GET"])
def season_averages():
    try:
        player_name = request.args.get("player")
        season = request.args.get("season", "2023")
        season_type = request.args.get("type", "Regular Season")

        player_info = players.find_players_by_full_name(player_name)
        if not player_info:
            raise ValueError(f"Player '{player_name}' not found.")

        player_id = player_info[0]["id"]
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season, season_type_all_star=season_type)
        df = gamelog.get_data_frames()[0]

        if df.empty:
            raise ValueError(f"No games found for {player_name} in {season} {season_type}.")

        stats = df.mean(numeric_only=True).to_dict()
        return jsonify({
            "player": player_name,
            "season": season,
            "averages": stats
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
