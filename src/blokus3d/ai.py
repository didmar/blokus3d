#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
AI-related functions
"""

# XXX take penalty into account, in a smart way:
# threshold based on number of remaining blocks ?
# threshold based on the number of variations that can be played
# for each block (a block which can only be placed in one way
# might to interesting to play immediately)

from numpy.core import hstack, vstack
from numpy.core.numeric import array, argsort, mean
from numpy.core.fromnumeric import argmax
from matplotlib.mlab import find
from itertools import imap, ifilter, izip

from blokus3d.utils import randomFromList, fst, snd, randint, unik

randomMove = lambda gs : randomFromList(gs.legalMoves())

# Fitness functions

def relativeBaseScoreFitness(gs):
    scores = gs.baseScores()
    currentPlayer = (gs.nextPlayer-1) % gs.nbPlayers
    # Remove player score from the scores
    bestOpponentScore = max(hstack([scores[:currentPlayer],\
                            scores[currentPlayer+1:]]))
    return scores[currentPlayer] - bestOpponentScore

def libertiesFitness(gs):
    """Each legal cube amounts to its square height"""
    return sum(cube[2]**2 for cube in \
               gs.libertyCubes([(gs.nextPlayer-1) % gs.nbPlayers]))

def penaltyFitness(gs):
    return -gs.penalty()[(gs.nextPlayer-1) % gs.nbPlayers]

def mixtureFitness(weightedFitFuns):
    """Meta-fitness function that make a mix between several"""
    return lambda gs: sum(weight*fitFun(gs) \
                           for (weight,fitFun) in weightedFitFuns)

def bestMoves(gs, fitFun, moves=None):
    """Select the best legal moves according to
       a one-step fitness function"""
    if moves == None:
        moves = gs.legalMoves()
    if moves == []:
        return [None], None
    fitnesses = array([fitFun(gs.clone().playMove(move)) \
                       for move in moves])
    bestFitness = max(fitnesses)
    # TODO should use argsort instead
    selectedMoves = map(moves.__getitem__,find(fitnesses==bestFitness))
    return selectedMoves, bestFitness

# Heuristics based on fitness functions

def oneStepHeuristic(gs, fitFuns, verbose=False):
    """Find the move that maximize the fitness
       after this move."""
    moves = gs.legalMoves()
    for fitFun in fitFuns:
        moves, fitness = bestMoves(gs, fitFun)
        if verbose:
            print "best %s : %d (%d moves)" \
                    % (str(fitFun), fitness, len(moves))
        if len(moves)==1:
            return moves[0]
    return moves[0]

mixtureOneStepHeuristic = lambda gs, weightedFitFuns:\
        oneStepHeuristic(gs, [mixtureFitness(weightedFitFuns)])

def threeHeuristicsMC(gs, verbose=False):
    """Find the best move according to three heuristics,
       then evaluate each in depth with Monte-Carlo method"""
    lm = gs.legalMoves()
    if lm == []:
        yield None
        raise StopIteration
    if verbose:
        print "Picking a best next move according to each criterion"
    moves = map(lambda fitFun: fst(fst(bestMoves(gs,fitFun,moves=lm))),\
                [relativeBaseScoreFitness,\
                 libertiesFitness,\
                 penaltyFitness])
    # Some moves might be the same
    moves = unik(moves)
    if verbose:
        print "Candidate moves are :",moves
    assert moves != []
    if len(moves)==1:
        yield moves[0]
        raise StopIteration
    if verbose:
        print "Now performing MC evaluation"
    for move in monteCarloHeuristic(gs,moves=moves):
        yield move

# Meta-heuristic

# TODO add depth so it can be maximini...maximinimax !
def minimax(gs, fitFun):
    # Get the legal moves and return immediately if there are only one
    moves = gs.legalMoves()
    lnMoves = len(moves)
    if lnMoves==1:
        yield moves[0]
        raise StopIteration
    # Get the one-step fitness for each possible move
    fitnesses = []
    nextGss = []
    for move in moves:
        nextGs = gs.clone().playMove(move)
        fitnesses.append(fitFun(nextGs))
        nextGss.append(nextGs)
    bestMovesOrder = argsort(fitnesses)[::-1]
    bestSoFar = moves[bestMovesOrder[0]]
    yield bestSoFar
    # Find the one-step that minimize the opponent fitness (second step)
    leastBestEnemyFitness = snd(bestMoves(nextGss[bestMovesOrder[0]].clone(),fitFun))
    for num,idx in enumerate(bestMovesOrder):
        print "processing move %d/%d (fitness %d)" % (num+1,lnMoves,fitnesses[idx])
        bestEnemyFitness = snd(bestMoves(nextGss[idx].clone(),fitFun))
        if bestEnemyFitness < leastBestEnemyFitness:
            bestSoFar = moves[idx]
            leastBestEnemyFitness = bestEnemyFitness
            print "new least best enemy fitness : %d" % leastBestEnemyFitness
        # TODO the yield is only here to avoid blocking on timeLimit,
        # must be removed when timeLimit works asynchronously
        yield bestSoFar

# Some other functions

def monteCarloScores(gs, maxDepth=None):
    # Copy the game state, so we can keep the original
    gs = gs.clone()
    depth = 0
    while not gs.isOver() and (maxDepth==None or depth<maxDepth):
        lm = gs.legalMoves()
        if lm != []:
            choice = randint(len(lm))
            gs.playMove(lm[choice])
            depth += 1
        else:
            gs.playMove(None) # passing move
    return gs.finalScores()

def monteCarloHeuristic(gs, moves=None, maxDepth=None, verbose=False):
    """Determines the best move using a Monte-Carlo estimation
       of the final scores"""
    if moves==None:
        moves = gs.legalMoves()
    nextStates = map(lambda move : gs.clone().playMove(move), moves)
    relativeScoreGrid = [[] for _ in xrange(len(moves))]
    for trial in xrange(1000000):
        for m in xrange(len(moves)):
            scores = nextStates[m].monteCarloScores(\
                        gs,maxDepth=maxDepth)
            if verbose:
                print "trial %d, move %d/%d, scores : %s" \
                      % (trial+1, m+1, len(moves), scores)
            relativeScoreGrid[m].append(scores)
        # for each move, compute the margin of each winning trial
        winningMargin = [ map(lambda z : z[1][-1]-z[1][-2], \
            ifilter(lambda y: y[0][-1]==gs.nextPlayer, \
            izip(imap(argsort,x),x))) \
            for x in relativeScoreGrid ]
        choice = argmax(map(mean,winningMargin))
        if verbose:
            print "best move so far is %d, mean margin = %f (wins %d/%d)" \
                  % (choice+1, mean(winningMargin[choice]), \
                     len(winningMargin[choice]), trial+1)
        yield moves[choice]

def bruteForceTree(gs, root=(None,[]), saveGs=False, depth=2):
    if depth <= 0:
        return root
    knownMoves = []
    if root[0]!=None:
        # Get the next player moves already registered
        # through children nodes
        if len(root[1]) > 0 and root[1][0]['move'] != None:
            knownMoves = vstack(node[0]['move'] for node in root[1])
    # Get the legal moves of the next player
    lm = gs.legalMoves()
    if lm == []:
        lm = [None]
    else:
        # Filter moves that are already known
        lm = [move for move in lm if move not in knownMoves]
    # Add nodes for those which are new
    for move in lm:
        dic = {'player':gs.nextPlayer,'move':move}
        root[1].append( (dic,[]) )
    # Evaluate each move and perform recursion
    for i,node in enumerate(root[1]):
        # Play the move
        move = node[0]['move']
        nextGs = gs.clone().playMove(move)
        if saveGs:
            node[0]['gs'] = nextGs
        # Evaluate the scores
        node[0]['baseScores'] = nextGs.baseScores()
        node[0]['penalty'] = nextGs.penalty()
        # Recursion
        nextGs.bruteForceTree(root=node,saveGs=saveGs,depth=depth-1)
        # DEBUG
        if depth==2:
            print "done node %d/%d" % (i,len(root[1]))
    return root

# def bruteForceArray(gs,maxDepth,depth=0,arr=None,nbNodes=[]):
#     """same as bruteForceTree but using an array to represent the tree
#     m1 scores
#     m2 scores
#     m3 scores
#     m1m1 scores
#     m1m2 scores
#     m2m1 scores
#     m3m1 scores
#     m3m2 scores
#     m1m1m1 scores
#     ...
#     nbNodes = [3,2,1,2,...]
#     """
#     if depth >= maxDepth:
#         return
#     # Get the legal moves of the current player == depth
#     lm = gs.legalMoves(depth)
#     if lm == []:
#         lm = [None]
#     nbNodes.append(len(lm))
#     if depth==0:
#         # Estimate the necessary array size :
#         # assuming that the nb of moves decrease by a half with each turn
#         arr = empty(( sum(int(nbNodes*(1/d)) for d in xrange(1,maxDepth+1)), 5+nbPlayers ),dtype=int16)
#     offset = 0 # TODO calculer offset
#     for i in xrange(len(lm)):
#         if move != None:
#             arr[offset+i,:3] = lm[i][0]
#             arr[offset+i,3]  = lm[i][1]
#             arr[offset+i,4]  = lm[i][2]
#         else:
#             arr[offset+i,3] = -1    # blkId = -1 means passing
#         # Evaluate each move and perform recursion
#         nextGs = gs.clone().playMove(player,lm[i])
#         # Evaluate the scores
#         arr[offset+i,5:(5+nbPlayers)] = nextGs.baseScores()
#         arr[offset+i,(5+nbPlayers):(5+nbPlayers*2)] = nextGs.penalty()
#         # Recursion
#         #nextGs.bruteForceArray(arr=arr,nbNodes=nbNodes,maxDepth=maxDepth)
