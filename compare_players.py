from nba_api.stats.endpoints import scoreboardv2, boxscoretraditionalv2
from playerDefine import Player
from utils import safe_float, validate_date
import pandas as pd
from tabulate import tabulate

def choose_players(player_df):
    player_df["MIN"] = player_df["MIN"].apply(safe_float)
    active_players = player_df[player_df["MIN"] > 0][["PLAYER_NAME", "TEAM_ABBREVIATION"]].drop_duplicates().reset_index(drop=True)

    print("\nPlayers in this game:")
    for i, row in active_players.iterrows():
        print(f"{i + 1}. {row['PLAYER_NAME']} ({row['TEAM_ABBREVIATION']})")

    def get_index(prompt):
        while True:
            try:
                i = int(input(prompt)) - 1
                if 0 <= i < len(active_players):
                    return active_players.iloc[i]
                else:
                    print("Invalid selection.")
            except:
                print("Enter a valid number.")

    p1 = get_index("Choose Player 1 by number: ")
    p2 = get_index("Choose Player 2 by number: ")
    return (p1["PLAYER_NAME"], p1["TEAM_ABBREVIATION"]), (p2["PLAYER_NAME"], p2["TEAM_ABBREVIATION"])


def list_games(date):
    scoreboard = scoreboardv2.ScoreboardV2(game_date=date)
    games = scoreboard.get_data_frames()[1]
    game_options = {}
    print("\nAvailable Games:")
    for i, row in games.iterrows():
        game_id = row["GAME_ID"]
        team = row["TEAM_ABBREVIATION"]
        matchup = game_options.setdefault(game_id, [])
        matchup.append(team)
    for i, (gid, teams) in enumerate(game_options.items()):
        print(f"{i+1}. {teams[0]} vs {teams[1]} ({gid})")
    return list(game_options.keys())

def get_stats(game_id):
    boxscore = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
    return boxscore.get_data_frames()

def extract_player_stats(player_name, team_abbr, game_id, player_df):
    row = player_df[
        (player_df["PLAYER_NAME"] == player_name) & 
        (player_df["TEAM_ABBREVIATION"] == team_abbr) & 
        (player_df["GAME_ID"] == game_id)
    ]
    if row.empty:
        raise ValueError(f"No stats found for {player_name} on {team_abbr}")
    return row.iloc[0].to_dict()

def extract_team_stats(team_abbr, game_id, team_df):
    team = team_df[
        (team_df["TEAM_ABBREVIATION"] == team_abbr) & 
        (team_df["GAME_ID"] == game_id)
    ]
    opp = team_df[
        (team_df["TEAM_ABBREVIATION"] != team_abbr) & 
        (team_df["GAME_ID"] == game_id)
    ]
    if team.empty or opp.empty:
        raise ValueError(f"Missing team/opponent stats for {team_abbr}")
    return team.iloc[0].to_dict(), opp.iloc[0].to_dict()

def compare(player_obj1, player_obj2):
    print("\n" + "="*40)
    print(f"Comparing {player_obj1.name} vs {player_obj2.name}")
    print("="*40)

    context_stats = [
        "MIN", "PTS", "FGA", "FGM", "FG3A", "FG3M",
        "FTA", "FTM", "AST", "TO", "REB", "STL", "BLK"
    ]

    advanced_stats = [
        "TS%", "eFG%", "USG%", "Box Creation", "Pass Rating",
        "Offensive Load", "Offensive Rating", "Defensive Rating"
    ]

    def build_table(keys):
        rows = []
        for key in keys:
            val1 = player_obj1.stats.get(key, "–")
            val2 = player_obj2.stats.get(key, "–")
            rows.append([key, val1, val2])
        return rows

    print("\nBasic Stats:")
    print(tabulate(build_table(context_stats), headers=["Metric", player_obj1.name, player_obj2.name], tablefmt="fancy_grid"))

    print("\nAdvanced Stats:")
    print(tabulate(build_table(advanced_stats), headers=["Metric", player_obj1.name, player_obj2.name], tablefmt="fancy_grid"))

def main():
    try:
        # VALID DATE
        while True:
            try:
                date = validate_date(input("Enter game date (YYYY-MM-DD): "))
                break
            except ValueError as e:
                print(f"Invalid date: {e}")

        # LIST GAMES
        game_ids = list_games(date)

        # VALID GAME NUMBER
        while True:
            try:
                choice = int(input("\nSelect a game number: ")) - 1
                game_id = game_ids[choice]
                break
            except (IndexError, ValueError):
                print("Invalid choice. Please enter a valid game number.")

        name1, team1, name2, team2 = None, None, None, None
        player_df = get_stats(game_id)[0]
        (name1, team1), (name2, team2) = choose_players(player_df)


        team_df, player_df = get_stats(game_id)[1], get_stats(game_id)[0]

        stats1 = extract_player_stats(name1, team1, game_id, player_df)
        stats2 = extract_player_stats(name2, team2, game_id, player_df)

        team1_stats, opp1_stats = extract_team_stats(team1, game_id, team_df)
        team2_stats, opp2_stats = extract_team_stats(team2, game_id, team_df)

        p1 = Player(name1, team1, stats1)
        p2 = Player(name2, team2, stats2)

        from game import calculate_player_stats
        calculate_player_stats(p1, team1_stats, opp1_stats)
        calculate_player_stats(p2, team2_stats, opp2_stats)

        compare(p1, p2)

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    main()
