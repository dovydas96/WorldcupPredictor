import pandas as pd
import trueskill as ts
import math
import itertools



team_rankings = pd.read_csv("sofifa.csv")
world_cup_results = pd.read_csv("world_cup_results.csv")
world_cup_teams = pd.read_csv("world_cup_teams.csv")

teams = world_cup_teams[["country_name"]]
real_games = world_cup_results
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "African Cup of Nations")]
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "AFF Championship")]
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "AFC Asian Cup")]
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "Gold Cup")]
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "CCCF Championship")]
#real_games = world_cup_results[(world_cup_results["TOURNAMENT"] != "UNCAF Cup")]
#real_games = real_games[(real_games["TOURNAMENT"] != "Friendly")]
real_games = real_games[(real_games["TOURNAMENT"].isin(["FIFA World Cup","FIFA World Cup qualification"]))]

country_list = [x[0] for x in teams.values]
country_list.append("Korea Republic")
real_games["MATCH_DATE"] = pd.to_datetime(real_games["MATCH_DATE"])
real_games = real_games.loc[real_games["MATCH_DATE"] > "01-01-2014"]
real_games.insert(2,'result',"NaN")

world_cup_elo = {}

print(real_games.to_string())
for index, row in real_games.iterrows():

    if not row["HOME_TEAM"] in world_cup_elo:
        world_cup_elo[row["HOME_TEAM"]] = ts.Rating(25)

    if not row["AWAY_TEAM"] in world_cup_elo:
        world_cup_elo[row["AWAY_TEAM"]] = ts.Rating(25)

    if int(row["HOME_SCORE"]) > int(row["AWAY_SCORE"]):

        result = ts.rate_1vs1(world_cup_elo[row["HOME_TEAM"]], world_cup_elo[row["AWAY_TEAM"]])
        world_cup_elo[row["HOME_TEAM"]], world_cup_elo[row["AWAY_TEAM"]] = result
        if row["TOURNAMENT"] == "FIFA World Cup":
            world_cup_elo[row["AWAY_TEAM"]] = ts.Rating(world_cup_elo[row["AWAY_TEAM"]].mu - 3,
                                                        world_cup_elo[row["AWAY_TEAM"]].sigma)
            world_cup_elo[row["HOME_TEAM"]] = ts.Rating(world_cup_elo[row["HOME_TEAM"]].mu + 3,
                                                        world_cup_elo[row["HOME_TEAM"]].sigma)

    if int(row["HOME_SCORE"]) < int(row["AWAY_SCORE"]):

        # if row["AWAY_TEAM"] in world_cup_elo:
        #
        result = ts.rate_1vs1(world_cup_elo[row["AWAY_TEAM"]], world_cup_elo[row["HOME_TEAM"]])
        world_cup_elo[row["AWAY_TEAM"]], world_cup_elo[row["HOME_TEAM"]] = result
        if row["TOURNAMENT"] == "FIFA World Cup":
            world_cup_elo[row["AWAY_TEAM"]] = ts.Rating(world_cup_elo[row["AWAY_TEAM"]].mu+3,
                                                        world_cup_elo[row["AWAY_TEAM"]].sigma)
            world_cup_elo[row["HOME_TEAM"]] = ts.Rating(world_cup_elo[row["HOME_TEAM"]].mu-3,
                                                        world_cup_elo[row["HOME_TEAM"]].sigma)



    if int(row["HOME_SCORE"]) == int(row["AWAY_SCORE"]):


        result = ts.rate_1vs1(world_cup_elo[row["AWAY_TEAM"]], world_cup_elo[row["HOME_TEAM"]],drawn=True)
        world_cup_elo[row["AWAY_TEAM"]], world_cup_elo[row["HOME_TEAM"]] = result

        if row["TOURNAMENT"] == "FIFA World Cup":
            world_cup_elo[row["AWAY_TEAM"]] = ts.Rating(world_cup_elo[row["AWAY_TEAM"]].mu + .5,
                                                        world_cup_elo[row["AWAY_TEAM"]].sigma)
            world_cup_elo[row["HOME_TEAM"]] = ts.Rating(world_cup_elo[row["HOME_TEAM"]].mu + .5,
                                                        world_cup_elo[row["HOME_TEAM"]].sigma)

world_cup_elo = dict((key, value) for key, value in world_cup_elo.items() if key in country_list)
for c in sorted(world_cup_elo, key=world_cup_elo.get, reverse=True):
    print(c, world_cup_elo[c])


team1 = world_cup_elo["Argentina"]
team2 = world_cup_elo["Iceland"]

BETA = 75
delta_mu = team1.mu - team2.mu
sum_sigma = team1.sigma ** 2 + team2.sigma ** 2
size = 1
denom = math.sqrt((BETA) + sum_sigma)
ts = ts.global_env()
print(ts.cdf(delta_mu / denom))



