import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)


def expected_score(rating_a, rating_b):
    """Returns the expected score for a game between the specified players
	http://footballdatabase.com/methodology.php
    """
    W_e = 1.0 / (1 + 10 ** ((rating_b - rating_a) / elo_width))
    return W_e


def get_k_factor(row, goals=0):
    """Returns the k-factor for updating Elo.
    http://footballdatabase.com/methodology.php
    """
    k_factor = 30

    if row["TOURNAMENT"] == "FIFA World Cup":
        k_factor = 60

    elif row["TOURNAMENT"] == "UEFA Euro":
        k_factor = 50

    elif row["TOURNAMENT"] == "Copa America":
        k_factor = 50

    elif row["TOURNAMENT"] == "Friendly":
        k_factor = 20

    if not goals or goals == 1:
        return k_factor

    if goals == 2:
        return k_factor * 1.5

    return k_factor * ((11 + goals) / 8)


def calculate_new_elos(rating_a, rating_b, score_a, goals,rpw):
    """Calculates and returns the new Elo ratings for two players.
    score_a is 1 for a win by player A, 0 for a loss by player A, or 0.5 for a draw.
    """

    e_a = expected_score(rating_a, rating_b)
    e_b = 1. - e_a
    if goals > 0:
        a_k = get_k_factor(row, goals)
        b_k = get_k_factor(row)
    else:
        a_k = get_k_factor(row)
        b_k = get_k_factor(row, goals)

    new_rating_a = rating_a + a_k * (score_a - e_a)
    score_b = 1. - score_a
    new_rating_b = rating_b + b_k * (score_b - e_b)
    return new_rating_a, new_rating_b


def getWinner(row):

    epsilon = 1e-15
    if int(row["HOME_SCORE"]) > int(row["AWAY_SCORE"]):  # Home Win
        return row['HOME_TEAM'], row['AWAY_TEAM'], 1 - epsilon
    elif int(row["HOME_SCORE"]) < int(row["AWAY_SCORE"]):  # Away Win
        return row['HOME_TEAM'], row['AWAY_TEAM'], epsilon
    elif int(row["HOME_SCORE"]) == int(row["AWAY_SCORE"]):  # Tie
        return row['HOME_TEAM'], row['AWAY_TEAM'], 0.5

def defineWinner(row):
    if row["HOME_SCORE"] > row["AWAY_SCORE"]:
        row['result'] = 1#'Home win'
    elif row["AWAY_SCORE"] > row["HOME_SCORE"]:
        row['result'] = 0#'Away win'
    elif row["HOME_SCORE"] == row["AWAY_SCORE"]:
        row['result'] = 0.5#'Tie'
    else: # For when scores are missing, etc (should be none)
        row['result'] = None
    return row


def get_mean(continents, team):
    try:
        if (continents[continents['official_name_en'].astype(str).str.contains(team)].Continent.values[0]) == "EU":
            return 1500

        elif (continents[continents['official_name_en'].astype(str).str.contains(team)].Continent.values[0]) == "SA":
            return 1450

        elif (continents[continents['official_name_en'].astype(str).str.contains(team)].Continent.values[0]) == "NA":
            return 1300

        elif (continents[continents['official_name_en'].astype(str).str.contains(team)].Continent.values[0]) == "OC":
            return 1300

        elif (continents[continents['official_name_en'].astype(str).str.contains(team)].Continent.values[0]) == "AS":
            return 1300

        else:
            return 1250

    except:
        return 1250


elo_width = 150.
world_cup_results = pd.read_csv("world_cup_results.csv")
world_cup_teams = pd.read_csv("world_cup_teams.csv")
teams = world_cup_teams[["country_name"]]
continents = pd.read_csv("countries and continents.csv")
real_games = world_cup_results
country_list = [x[0] for x in teams.values]
country_list.append("Korea Republic")
real_games["MATCH_DATE"] = pd.to_datetime(real_games["MATCH_DATE"])
real_games = real_games.loc[real_games["MATCH_DATE"] > "01-01-2014"]
real_games.insert(1, 'result', "NaN")
real_games = real_games.apply(defineWinner, axis=1)

print(continents[continents['official_name_en'].astype(str).str.contains('Egypt')].Continent.values[0])
print("Training...")
world_cup_elo = {}

for index, row in real_games.iterrows():
    if not row["HOME_TEAM"] in world_cup_elo:
        world_cup_elo[row["HOME_TEAM"]] = get_mean(continents, row["HOME_TEAM"])

    if not row["AWAY_TEAM"] in world_cup_elo:
        world_cup_elo[row["AWAY_TEAM"]] = get_mean(continents, row["AWAY_TEAM"])


    (ht_id, at_id, score) = getWinner(row)
    # update elo score
    ht_elo_before = world_cup_elo[row["HOME_TEAM"]]
    at_elo_before = world_cup_elo[row["AWAY_TEAM"]]
    world_cup_elo[row["HOME_TEAM"]], world_cup_elo[row["AWAY_TEAM"]] = calculate_new_elos(ht_elo_before, at_elo_before,
                                                                                          score, row['HOME_SCORE'] - row['AWAY_SCORE'], row)
#
world_cup_elo = dict((key, value) for key, value in world_cup_elo.items() if key in country_list)
# for c in sorted(world_cup_elo, key=world_cup_elo.get, reverse=True):
#     print(c, world_cup_elo[c])


print("Predicting...")
samples = pd.read_csv("world_cup_fixtures.csv")
#samples = real_games.loc[real_games["MATCH_DATE"] > "01-01-2017"]
loss = 0
expected_list = []
epsilon = 1e-15

y_true = []
y_predicted = []
groups = dict.fromkeys(world_cup_elo.keys(),0)
#
# for row in samples.itertuples():
#     ht_elo = world_cup_elo[row.home_team_name]
#     at_elo = world_cup_elo[row.away_team_name]
#     w_expected = expected_score(ht_elo, at_elo)
#     if w_expected >= .7:
#         groups[row.home_team_name] += 3
#     elif .4 <= w_expected and w_expected < .7:
#         groups[row.home_team_name] += 1
#         groups[row.away_team_name] += 1
#     elif w_expected <= .4:
#         groups[row.away_team_name] += 3
# i=0
# correct = 0
# incorrect = 1
# while i < len(y_true):
#     if float(y_predicted[i] == y_true[i]):
#         correct += 1
#     else:
#         incorrect +=1
#
#     i += 1


# for c in sorted(groups, key=groups.get, reverse=True):
#     print(c, groups[c])

# groupA = [("Uruguay",groups["Uruguay"]), ("Russia",groups["Russia"]), ("Saudi Arabia",groups["Saudi Arabia"]), ("Egypt",groups["Egypt"])]
# print(groupA)
# groupB = [("Spain",groups["Spain"]), ("Portugal",groups["Portugal"]), ("Iran",groups["Iran"]), ("Morocco",groups["Morocco"])]
# print(sorted(groupB,key=lambda x: x[1],reverse=True))
# groupC = [("France",groups["France"]), ("Denmark",groups["Denmark"]), ("Peru",groups["Peru"]), ("Australia",groups["Australia"])]
# print(sorted(groupC,key=lambda x: x[1],reverse=True))
# groupD = [("Croatia",groups["Croatia"]), ("Argentina",groups["Argentina"]), ("Nigeria",groups["Nigeria"]), ("Iceland",groups["Iceland"])]
# print(sorted(groupD,key=lambda x: x[1],reverse=True))
# groupE = [("Brazil",groups["Brazil"]), ("Switzerland",groups["Switzerland"]), ("Serbia",groups["Serbia"]), ("Costa Rica",groups["Costa Rica"])]
# print(sorted(groupE,key=lambda x: x[1],reverse=True))
# groupF = [("Sweden",groups["Sweden"]), ("Mexico",groups["Mexico"]), ("Korea Republic",groups["Korea Republic"]), ("Germany",groups["Germany"])]
# print(sorted(groupF,key=lambda x: x[1],reverse=True))
# groupG = [("Belgium",groups["Belgium"]), ("England",groups["England"]), ("Tunisia",groups["Tunisia"]), ("Panama",groups["Panama"])]
# print(sorted(groupG,key=lambda x: x[1],reverse=True))
# groupH = [("Colombia",groups["Colombia"]), ("Japan",groups["Japan"]), ("Senegal",groups["Senegal"]), ("Poland",groups["Poland"])]
# print(sorted(groupH,key=lambda x: x[1],reverse=True))
#

# winners = []
# knockout = [("Uruguay","Portugal"), ("France","Argentina"), ("Brazil","Sweden"),("Belgium","Poland"),("Spain","Russia"),("Croatia","Peru"),("Germany","Switzerland"),("Colombia","England")]
# for matches in knockout:
#     ht_elo = world_cup_elo[matches[0]]
#     at_elo = world_cup_elo[matches[1]]
#     w_expected = expected_score(ht_elo, at_elo)
#     if w_expected > .50:
#         winners.append(matches[0])
#     else:
#         winners.append(matches[1])
#
# print(winners)


winners = []
knockout = [("Uruguay","France"),("Belgium","Brazil"),("Croatia","Russia"),("Sweden","England")]
for matches in knockout:
    ht_elo = world_cup_elo[matches[0]]
    at_elo = world_cup_elo[matches[1]]
    w_expected = expected_score(ht_elo, at_elo)
    if w_expected > .50:
        winners.append((matches[0],w_expected))
    else:
        winners.append((matches[1], 1-  w_expected))

print(winners)


winners = []
knockout = [("France","Brazil"),("Croatia","England")]
for matches in knockout:
    ht_elo = world_cup_elo[matches[0]]
    at_elo = world_cup_elo[matches[1]]
    w_expected = expected_score(ht_elo, at_elo)
    if w_expected > .50:
        winners.append((matches[0],w_expected))
    else:
        winners.append((matches[1],1 - w_expected))

print(winners)

winners = []
knockout = [("Brazil","England")]
for matches in knockout:
    ht_elo = world_cup_elo[matches[0]]
    at_elo = world_cup_elo[matches[1]]
    w_expected = expected_score(ht_elo, at_elo)
    if w_expected > .50:
        winners.append((matches[0], w_expected))
    else:
        winners.append((matches[1], 1 - w_expected))

print(winners)


