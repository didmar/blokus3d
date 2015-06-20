#!/usr/bin/env python
#-*- coding:utf-8 -*-

from blokus3d.viewer import findMove3d
from blokus3d.mcts import UCT
from blokus3d.gamestate import saveLegalMovesDic, GameSettings
from blokus3d.match import match
from blokus3d.ai import libertiesFitness, relativeBaseScoreFitness, \
                        penaltyFitness, minimax, mixtureFitness, \
                        mixtureOneStepHeuristic, oneStepHeuristic
from blokus3d.utils import randomFromList, timeLimit

# Create game settings for 2 players

nbPlayers = 2
gameSettings = GameSettings(nbPlayers)

# Let's define some AIs

randomMove = lambda gs: randomFromList(gs.legalMoves())

oneStepLibertiesFirst = lambda gs: oneStepHeuristic(gs, [\
                    libertiesFitness, \
                    relativeBaseScoreFitness, \
                    penaltyFitness])

mixture1 = lambda gs: mixtureOneStepHeuristic(gs, [\
                    (0.25,libertiesFitness), \
                    (0.75,relativeBaseScoreFitness)])

mixture2 = lambda gs: mixtureOneStepHeuristic(gs, [\
                    (0.5,libertiesFitness), \
                    (0.5,relativeBaseScoreFitness)])

mixture3 = lambda gs: mixtureOneStepHeuristic(gs, [\
                    (0.75,libertiesFitness), \
                    (0.25,relativeBaseScoreFitness)])

mixture4 = lambda gs: mixtureOneStepHeuristic(gs, [\
                    (0.4,libertiesFitness), \
                    (0.4,relativeBaseScoreFitness), \
                    (0.1,penaltyFitness)])

mixture5 = lambda gs: mixtureOneStepHeuristic(gs, [\
                    (0.3,libertiesFitness), \
                    (0.3,relativeBaseScoreFitness), \
                    (0.2,penaltyFitness)])

minimax1 = lambda gs : timeLimit(10, \
                minimax(gs,mixtureFitness([\
                    (0.3,libertiesFitness), \
                    (0.3,relativeBaseScoreFitness), \
                    (0.2,penaltyFitness)])))

minimax2 = lambda gs : timeLimit(10, \
                minimax(gs,mixtureFitness([\
                    (0.5,libertiesFitness), \
                    (0.5,relativeBaseScoreFitness), \
                    (0.0,penaltyFitness)])))

minimax3 = lambda gs : timeLimit(10, minimax(gs,libertiesFitness))

uct = lambda gs: UCT(gameSettings, gs, 5)

# Uncomment to test AIs against each other
#from blokus3d.match import runCompetition
#players = [randomMove, oneStepLibertiesFirst]
#runCompetition(gameSettings, players)

# Choose an opponent (AI) and play against it
human = lambda gs: findMove3d(gs)
opponent = mixture1
endGs = match(gameSettings, [human, opponent], \
              verbose=True, \
              askConfirmation=False, \
              saveCache=False)
endGs.showScores()

saveLegalMovesDic()

print "Press ESC to quit"
findMove3d(endGs, viewOnly=True)
