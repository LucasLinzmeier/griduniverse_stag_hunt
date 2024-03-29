import logging
import random
from bisect import bisect
from random import randint

from dallinger.experiments import Griduniverse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__file__)


class Offspring(object):
    """Generate genome from the last generation.
    If there is no last generation (m=0), the genome is
    generated using random methods tailored to the
    types of variables we are randomizing.
    """

    MAX_SCORE = 7.0

    def __init__(self, id, parents, scores, mutation_rate):
        self.id = id
        self.mutation_rate = mutation_rate
        self.parents = parents
        self.scores = scores

    def get_genome(self):
        """Run genome logic"""
        if bool(self.parents):
            weights = self.generate_weights(self.scores)
            options = self.weighted_rand(self.parents, weights)
            return self.mutate(options)
        return self.randomize_genome()

    def randomize_genome(self):
        """Generate random genome for generation 1"""
        return {
            "time_per_round": int(random.gauss(100, 15)),
            "num_food": int(random.gauss(12, 2)),
            "respawn_food": bool(random.getrandbits(1)),
            "rows": int(random.gauss(40, 5)),
            "columns": int(random.gauss(40, 5)),
            "block_size": int(random.gauss(7, 3)),
            "background_animation": bool(random.getrandbits(1)),
            "padding": int(randint(0, 3)),
            "visibility": int(random.gauss(1000, 20)),
            "walls_density": float(random.betavariate(2, 2)),
            "walls_contiguity": float(random.betavariate(2, 2)),
            "walls_visible": bool(random.getrandbits(1)),
            "motion_speed_limit": float(random.gauss(12, 5)),
            "motion_auto": bool(random.getrandbits(1)),
        }

    def mutate(self, genome):
        """Mutate genes based on the mutation_rate"""
        for gene in genome.keys():
            if random.random() <= self.mutation_rate:
                logger.info("Mutation! Changing {}".format(gene))
                if type(genome[gene]) is bool:
                    genome[gene] = bool(random.getrandbits(1))
                elif genome[gene] == "time_per_round":
                    int(random.gauss(100, 15))
                elif genome[gene] == "rows" or genome[gene] == "columns":
                    int(random.gauss(40, 5))
                elif genome[gene] == "block_size":
                    int(random.gauss(7, 3))
                elif genome[gene] == "padding":
                    int(randint(0, 3))
                elif genome[gene] == "visibility":
                    int(random.gauss(1000, 20))
                elif (
                    genome[gene] == "walls_density"
                    or genome[gene] == "walls_contiguity"
                ):
                    float(random.betavariate(2, 2))
                elif genome[gene] == "motion_speed_limit":
                    float(random.gauss(12, 5))
                elif genome[gene] == "num_food":
                    int(random.gauss(12, 2))
        return genome

    def generate_weights(self, scores):
        """Generate probability of survival"""
        logger.info("Weights are selected based on parent survival.")
        weights = []
        fitness_denom = 0

        for player, value in enumerate(self.parents):
            fitness_denom += float(scores[player]) / self.MAX_SCORE

        for player, value in enumerate(self.parents):
            score_decimal = float(scores[player]) / self.MAX_SCORE
            prob_survival = float(score_decimal) / float(fitness_denom)
            logger.info("Survival %: {}".format(100.0 * float(prob_survival)))
            weights.append(prob_survival)
        return weights

    def weighted_rand(self, values, weights):
        """Generate random value using weighted probabilities"""
        total = 0
        weightList = []
        for weight in weights:
            total += weight
            weightList.append(total)
        randomPoint = random.random() * total
        randomIndex = bisect(weightList, randomPoint)
        return values[randomIndex]


class Evolve(object):
    """The n x m iteractive evolutionary algorithm"""

    TIME_PER_ROUND = 5.00
    STEP_RATE = 0.3

    def __init__(self, n, m, bot=False, mutation_rate=0.1):
        """Run experiment loop"""
        logger.info(
            "Begin {0} x {1} experiment, bot={2}, mutation_rate={3}.".format(
                n, m, bot, mutation_rate
            )
        )
        self.n = n
        self.m = m
        self.bot = bot
        self.mutation_rate = mutation_rate
        self.recruiter = "bots" if bot else "None"
        self.bot_policy = "AdvantageSeekingBot" if bot else "None"
        self.run(n, m)

    def player_feedback(self, currPay, lastPay, feedback):
        """Generate feedback based on dollars earned.

        This requires a check to see how fun the game is based on
        fixed amounts of money in the beginning, relative to the
        time_per_round variable. After that, the comparison becomes
        relative to a percentage of the last round's fun rating. The
        STEP_RATE variable is the percent required to bump up a rating.
        """
        logger.info("Current Pay: {0}. Last Payout {1}.".format(currPay, lastPay))
        low = 0.015 * self.TIME_PER_ROUND
        high = 0.08 * self.TIME_PER_ROUND
        if lastPay == 0:
            if currPay <= low:
                return 1
            elif currPay >= high:
                return 5
            else:
                return 3
        if (currPay / lastPay) - 1 >= self.STEP_RATE:
            return feedback + 1
        elif abs(currPay - lastPay) / lastPay < self.STEP_RATE:
            return feedback
        else:
            if feedback == 0:
                return feedback
            else:
                return feedback - 1

    def run(self, players, generations):
        """Run evolutionary algorithm"""
        lastPay = 0
        feedback = 0
        new_parents = {"genome": {}, "scores": {}}
        for generation in range(generations):
            parents = new_parents
            for player in range(players):
                logger.info(
                    "Running player {0} for generation {1}.".format(
                        player + 1, generation + 1
                    )
                )
                logger.info("Parents: {}.".format(parents))
                spawn = Offspring(
                    player,
                    parents["genome"].values(),
                    parents["scores"],
                    self.mutation_rate,
                )
                child = spawn.get_genome()
                data = experiment.run(
                    mode="debug",
                    webdriver_type="chrome",
                    fun_survey=True,
                    recruiter=self.recruiter,
                    bot_policy=self.bot_policy,
                    max_participants=1,
                    num_dynos_worker=1,
                    verbose=True,
                    show_chatroom=False,
                    time_per_round=self.TIME_PER_ROUND,
                    num_food=child["num_food"],
                    respawn_food=child["respawn_food"],
                    rows=child["rows"],
                    columns=child["columns"],
                    block_size=child["block_size"],
                    background_animation=child["background_animation"],
                    padding=child["padding"],
                    visibility=child["visibility"],
                    motion_speed_limit=child["motion_speed_limit"],
                    motion_auto=child["motion_auto"],
                )
                if self.bot:
                    if player - 1 in new_parents["scores"]:
                        feedback = new_parents["scores"][player - 1]
                    currPay = experiment.average_payoff(data)
                    # Use custom feedback from the script with bots
                    new_parents["scores"][player] = self.player_feedback(
                        currPay, lastPay, feedback
                    )
                    lastPay = currPay
                else:
                    # Use the real feedback from the database with real players
                    new_parents["scores"][player] = experiment.player_feedback(data)[2]
                logger.info("Fun rating: {}.".format(new_parents["scores"][player]))
                new_parents["genome"][player] = child
        logger.info("Final generation: {}".format(new_parents))


experiment = Griduniverse()
Evolve(2, 2, bot=True, mutation_rate=0.1)
