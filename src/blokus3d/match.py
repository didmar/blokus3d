#!/usr/bin/env python
#-*- coding:utf-8 -*-

from numpy.core import mean
from numpy.core.numeric import array
from matplotlib.pylab import find
from itertools import cycle

from blokus3d.gamestate import saveLegalMovesDic, GameState

def scoresStats(scoresList):
    scoresList = array(scoresList)
    nbPlayers = scoresList.shape[1]
    print "Player | wins loses (ties) meanWinMargin meanLossMargin"
    for player in xrange(nbPlayers):
        otherPlayer = (player+1) % nbPlayers
        winning = find(scoresList[:,player] > scoresList[:,otherPlayer])
        losing  = find(scoresList[:,player] < scoresList[:,otherPlayer])
        wins,loses = len(winning),len(losing)
        ties = scoresList.shape[0]-wins-loses
        meanWinningMargin = mean(sum(scoresList[winning],1))
        meanLosingMargin  = mean(sum(scoresList[losing],1))
        print "     %c | %d %d (%d) +%f -%f" % \
            (chr(65+player), wins, loses, ties, \
             meanWinningMargin, meanLosingMargin)

def match(settings, playersFun, verbose=False, askConfirmation=False, recordUnder=None,\
          startFrom=None, saveCache=True, stopAfterTurn=None):
    """Make matches between human or artificial players
       using decision functions. Returns the final score."""
    assert len(playersFun) == settings.nbPlayers
    gs = startFrom if startFrom != None else GameState.initState(settings)
    if recordUnder != None:
        turn = 1
    while not gs.isOver():
        if verbose:
            print "Player %c turn" % chr(65+gs.nextPlayer)
        gs.playMove(playersFun[gs.nextPlayer](gs))
        if recordUnder != None:
            gs.save(recordUnder+str(turn))
            turn += 1
        if saveCache:
            saveLegalMovesDic()
        if verbose:
            print gs
        if askConfirmation:
            raw_input("Press ENTER to continue")
        if verbose:
            print '-'*60
        if stopAfterTurn:
            if turn > stopAfterTurn:
                print "Stopping after turn %d" % (turn-1)
                return gs
    return gs

def competitor(settings, playersFun):
    """A generator that make matches between players, cycling through
       the possible order so it makes the evaluation fair"""
    assert len(playersFun) == settings.nbPlayers
    if len(playersFun) != 2:
        print "Only works for 2 players right now !!!"
        raise StopIteration
    # We will cycle through the possible order of players
    # TODO generate that for any player number
    orderGen = cycle([[0,1],[1,0]])
    while True:
        order = next(orderGen)
        yield match(settings, map(playersFun.__getitem__, order), saveCache=False).finalScores()[order]

def runCompetition(settings, playersFun):
    gen = competitor(settings, playersFun)
    results = []
    nbMatchs = 3
    for i in xrange(nbMatchs):
        res = next(gen)
        print "Match %d/%d result: %s" % (i+1, nbMatchs, res)
        results.append(res)
    scoresStats(results)
