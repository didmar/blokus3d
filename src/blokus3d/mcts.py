# Modified by Didier Marin.
# Original description :
#
# This is a very simple implementation of the UCT Monte Carlo Tree Search algorithm in Python 2.7.
# The function UCT(rootstate, itermax, verbose = False) is towards the bottom of the code.
# It aims to have the clearest and simplest possible code, and for the sake of clarity, the code
# is orders of magnitude less efficient than it could be made, particularly by using a
# state.GetRandomMove() or state.DoRandomRollout() function.
#
# Example GameState classes for Nim, OXO and Othello are included to give some idea of how you
# can write your own GameState use UCT in your 2-player game. Change the game to be played in
# the UCTPlayGame() function at the bottom of the code.
#
# Written by Peter Cowling, Ed Powley, Daniel Whitehouse (University of York, UK) September 2012.
#
# Licence is granted to freely use and distribute for any sensible/legal purpose so long as this
# comment remains in any distributed code.
#
# For more information about Monte Carlo Tree Search check out our web site at www.mcts.ai

from numpy.core import hstack
from math import sqrt, log
import random

from blokus3d.move import moveIndex

class Node(object):
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, gameSettings, move = None, parent = None, state = None):
        self.gameSettings = gameSettings
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.untriedMoves = state.legalMoves() # future child nodes
        # the only part of the state that the Node needs later
        self.playerJustMoved = (state.nextPlayer-1) % gameSettings.nbPlayers

    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied
            so we have lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits
            to vary the amount of exploration versus exploitation.
        """
        key = lambda c: c.wins/c.visits + sqrt(2*log(self.visits)/c.visits)
        s = sorted(self.childNodes, key = key)[-1]
        return s

    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(self.gameSettings, move = m, parent = self, state = s)
        i = moveIndex(self.untriedMoves,m)
        self.untriedMoves = self.untriedMoves[:i]+self.untriedMoves[i+1:]
        self.childNodes.append(n)
        return n

    def Update(self, result):
        """ Update this node - one additional visit and result additional wins.
            result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" \
            + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
            s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for _ in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
            s += str(c) + "\n"
        return s

def UCT(gameSettings, rootstate, itermax, verbose=False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts),
        with game results in the range [0.0, 1.0]."""

    rootnode = Node(gameSettings, state = rootstate)

    for _ in xrange(itermax):
        node = rootnode
        state = rootstate.clone()

        # Select
        # while node is fully expanded and non-terminal
        while node.untriedMoves == [] and node.childNodes != []:
            node = node.UCTSelectChild()
            state.playMove(node.move)

        # Expand
        # if we can expand (i.e. state/node is non-terminal)
        if node.untriedMoves != []:
            m = random.choice(node.untriedMoves)
            state.playMove(m)
            node = node.AddChild(m,state) # add child and descend tree

        # Rollout
        # while state is non-terminal
        while not state.isOver():
            state.playMove(random.choice(state.legalMoves()))

        # Backpropagate
        # backpropagate from the expanded node and work back to the root node
        while node != None:
            scores = state.finalScores()
            bestOpponentScore = max(hstack([scores[:node.playerJustMoved],\
                                    scores[node.playerJustMoved+1:]]))
            diffScore = scores[node.playerJustMoved] - bestOpponentScore
            # state is terminal. Update node with result
            # from POV of node.playerJustMoved
            node.Update( diffScore )
            node = node.parentNode

    # Output some information about the tree - can be omitted
    if verbose:
        print rootnode.TreeToString(0)
        print rootnode.ChildrenToString()

    # return the move that was most visited
    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move
