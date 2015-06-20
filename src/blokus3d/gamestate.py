#!/usr/bin/env python
#-*- coding:utf-8 -*-
"""
Module containing the logic of the game
"""

from numpy.core import vstack
from numpy.core.numeric import array, zeros, fromiter
from numpy.core.numerictypes import int8, int16
from matplotlib.pylab import flatten
from itertools import ifilter, product
import copy as cp
import os
import pickle

from blokus3d.utils import emptyIter, fold, unik
from blokus3d.block import nbBlocks, adjacentCoords, containsCube, blocksVar,\
    blockVarWithOrigin, argsortBlocks, blocks, includesCube

class GameSettings(object):

    def __init__(self, nbPlayers):
        self.nbPlayers = nbPlayers
        self.boardSize = (5, 4, 2*nbPlayers if nbPlayers < 4 else 8)
        self.xycoords = list(product(xrange(self.boardSize[0]),xrange(self.boardSize[1])))

class GameState(object):

    def __init__(self, settings, playerBlocks, board, nextPlayer=0, firstToPass=None):
        self.nbPlayers = settings.nbPlayers
        self.boardSize = settings.boardSize
        self.xycoords = settings.xycoords
        assert len(playerBlocks)==self.nbPlayers
        self.settings = settings
        self.playerBlocks = playerBlocks
        self.board = board
        self.nextPlayer = nextPlayer # next player to play
        self.firstToPass = firstToPass

    @classmethod
    def initState(cls, settings):
        """Returns a new GameState that corresponds to
           the beginning of the game"""
        return GameState( \
            settings,
            list(range(nbBlocks) for _ in xrange(settings.nbPlayers)), \
            cls.initBoard(settings.boardSize))

    @classmethod
    def initBoard(cls, boardSize):
        return [[[] for _ in xrange(boardSize[1])] for _ in xrange(boardSize[0])]

    def __uniqueid__(self):
        # Create an order of players such that
        # the nextPlayer is 0
        order = fromiter((player % self.nbPlayers \
                    for player in xrange(self.nextPlayer, self.nextPlayer+4)),\
                    dtype=int8)
        remainingBlocks = sum( \
            (p*(2**nbBlocks) \
             + sum(2**b for b in self.playerBlocks[p])) \
            for p in order)
        board = tuple(tuple(tuple(order[h] for h in c)\
                    for c in l) for l in self.board)
        return (remainingBlocks, board)

    def height(self,xy):
        assert len(xy)==2
        assert xy[0]>=0 and xy[0] < self.boardSize[0]
        assert xy[1]>=0 and xy[1] < self.boardSize[1]
        return len(self.board[xy[0]][xy[1]])

    def heightMap(self):
        return tuple(tuple(self.height([x,y]) \
                for y in xrange(self.boardSize[1])) \
                for x in xrange(self.boardSize[0]))

    def emptyCoords(self,coords):
        """Returns True iff the coordinates are within the board
           and empty of any cube"""
        assert len(coords)==3
        return coords[0] >= 0 and coords[0] < self.boardSize[0] and coords[1] >= 0 \
               and coords[1] < self.boardSize[1] and coords[2] < self.boardSize[2] \
               and coords[2] >= self.height(coords[:2])

    def adjToPlayers(self,players):
        """Returns the coordinates of grounded (not floating)
           empty cubes adjacent to given players' cubes"""
        # Get liberty cubes
        L = self.libertyCubes(players)
        if L==[]:
            return L
        # Remove all the "floating" cubes
        # XXX maybe there's a cleaner way, using an iterator ?
        L.reverse()
        x, y, z = L[-1][0], L[-1][1], L[-1][2]
        newL = [ L.pop() ]
        while len(L) > 0:
            e = L.pop()
            if x==e[0] and y==e[1]:
                assert e[2] > z
            else:
                newL.append(e)
                x, y, z = e[0], e[1], e[2]
        return newL

    def libertyCubes(self,players):
        """Return the coordinates of empty cubes
           adjacent to given players' cubes"""
        L = []
        for (x,y) in self.xycoords:
            for z in xrange(self.height([x,y])):
                if self.board[x][y][z] in players:
                    L.extend(filter(lambda coords : \
                        self.emptyCoords(coords), \
                        adjacentCoords+array([x,y,z])))
        # remove duplicates
        L = unik(L)
        return L

    def doesFit(self,blk,xyz):
        """Returns whether a block fits at a particular position
        on the board, checking that it not over some empty space,
        but not that its adjacent to another block."""
        assert blk.shape[1] == 3
        assert len(xyz) == 3
        blkWithOrigin = vstack([blk,array([0,0,0])])
        for cube in blkWithOrigin:
            if not (self.emptyCoords(xyz+cube) \
                    and (self.height(xyz[:2]+cube[:2])==xyz[2]+cube[2] \
                         or containsCube(blkWithOrigin, \
                                            cube-array([0,0,1])))):
                return False
        return True

    def blockVarsThatFit(self,blkId,coords):
        return filter(lambda i: self.doesFit(blocksVar[blkId][:,:,i],coords),\
                      xrange(blocksVar[blkId].shape[2]))

    def legalCubes(self):
        alreadyPlayed = not emptyIter( \
                            ifilter(lambda x : x == self.nextPlayer, \
                            flatten(self.board)))
        # Did the next player already played ?
        if alreadyPlayed:
            return self.adjToPlayers([self.nextPlayer])
        # Did someone else played ?
        elif not emptyIter(ifilter(lambda x: x != [],flatten(self.board))):
            # Get the cubes adjacent to any player
            return self.adjToPlayers(range(self.nbPlayers))
        # Else, all floor cubes are legal
        else:
            return vstack([array([x,y,0]) for (x,y) in self.xycoords])

    def legalMoves(self):
        uid = self.__uniqueid__()
        if legalMovesDic.has_key(uid):
            return legalMovesDic[uid]
        lc = self.legalCubes()
        L = []
        #duplicates = 0
        for blkId in self.playerBlocks[self.nextPlayer]:
            # Find all the variations that fit
            # and make coords-blkVarId couple
            coordsBlkVarIds = fold(list.__add__, [[(coords,blkVarId) \
                for blkVarId in self.blockVarsThatFit(blkId,coords)]
                for coords in lc])
            # If there are some
            if coordsBlkVarIds != [] and coordsBlkVarIds != None:
                # We will eliminate duplicates
                # For each coords-blkVarId pair, get the cube
                # coordinates on the board
                M = map(lambda (coords,blkVarId): \
                    coords+blockVarWithOrigin(blkId,blkVarId), coordsBlkVarIds)
                N = iter(argsortBlocks(M))
                lastOne = next(N)
                # Add the first coords-blkVarId variation to the big list
                L.append((coordsBlkVarIds[lastOne][0],\
                          blkId,coordsBlkVarIds[lastOne][1]))
                # Go though all the coords-blkVarId variations
                try:
                    while True:
                        nextToLastOne = next(N)
                        # If next one is not the same
                        if not (M[lastOne]==M[nextToLastOne]).all():
                            # Add the next on to the big list
                            L.append((coordsBlkVarIds[nextToLastOne][0],\
                                      blkId,coordsBlkVarIds[nextToLastOne][1]))
                        #else:
                        #    duplicates += 1
                        lastOne = nextToLastOne
                except StopIteration:
                    pass
        #print "%d duplicates" % duplicates
        if L == []:
            L = [None]
        # Add it to the dictionary
        legalMovesDic[uid] = L
        return L

    def legalMovesAsTuple(self):
        """For using UCT"""
        return [(coords[0],coords[1],coords[2],blkId,blkVarId) \
                for coords,blkId,blkVarId in self.legalMoves()]

    def baseScores(self):
        s = zeros(self.nbPlayers,dtype=int16)
        for (x,y) in self.xycoords:
            if self.height([x,y])>0:
                s[self.board[x][y][-1]] += 1
        return s

    def penalty(self):
        return list(sum(map(lambda x : blocks[x].shape[0], \
                        self.playerBlocks[player])) \
                    for player in xrange(self.nbPlayers))

    def finalScores(self):
        return self.baseScores() - self.penalty()

    def isOver(self):
        return self.firstToPass == self.nextPlayer

    def assertValidMove(self,move):
        assert len(move)==3
        coords,blkId,blkVarId = move
        assert len(coords)==3
        assert blkId in self.playerBlocks[self.nextPlayer]
        assert self.doesFit(blocksVar[blkId][:,:,blkVarId],coords)
        return True

    def playMove(self,move):
        assert move == None or (len(move) == 3 and move[0].shape == (3,))
        if self.firstToPass == self.nextPlayer:
            # Game is over !
            return self
        if move == None:
            if self.firstToPass == None:
                self.firstToPass = self.nextPlayer
        else:
            assert self.assertValidMove(move)
            coords,blkId,blkVarId = move
            # Remove the block from the player's stock
            self.playerBlocks[self.nextPlayer].remove(blkId)
            blkWithOrigin = blockVarWithOrigin(blkId,blkVarId)
            # Place the block on the board
            for cube in blkWithOrigin:
                assert cube[2]+coords[2]==self.height([cube[0]+coords[0],cube[1]+coords[1]])
                self.board[cube[0]+coords[0]][cube[1]+coords[1]].append(self.nextPlayer)
            # Break the "passing chain", if necessary
            self.firstToPass = None
        # Update the next player
        self.nextPlayer = (self.nextPlayer+1) % self.nbPlayers
        return self

    def clone(self):
        return GameState(self.settings,\
                         list(map(cp.copy,self.playerBlocks)),\
                         cp.deepcopy(self.board),\
                         nextPlayer=self.nextPlayer,\
                         firstToPass=self.firstToPass)

    def boardToASCII(self, markedCubes=None, zRange=None):
        if zRange == None:
            zRange = xrange(self.boardSize[2])
        if markedCubes == None:
            markedCubes = []
        s = ""
        for z in zRange:
            for y in xrange(self.boardSize[1]):
                for x in xrange(self.boardSize[0]):
                    s += "x" if includesCube(markedCubes,array([x,y,z]))\
                             else ("." if self.height([x,y]) <= z \
                                       else chr(self.board[x][y][z]+65))
                s += "\n"
            s += "\n"
        return s

    def __str__(self):
        s = "Next player is %s\n" % chr(self.nextPlayer+65)
        for player,blocksId in enumerate(self.playerBlocks):
            s += "%s's blocks : %s\n" \
                 % (chr(player+65),\
                    ','.join(map(lambda x : str(x+1),blocksId)))
        s += "\n"+self.boardToASCII()
        return s

    def toASCII(self):
        s = str(self.nextPlayer)+"\n"
        for blocksId in self.playerBlocks:
            s += str(blocksId).replace('[','').replace(']','')+"\n"
        s += "\n"+self.boardToASCII()
        return s

    def showScores(self):
        print "base scores    ", self.baseScores()
        print "penalties    - ", self.penalty()
        print "-------------------------------"
        print "final scores = ", self.finalScores()

    @classmethod
    def fromASCII(cls, string):
        # FIXME guess settings from the text !!
        settings = GameSettings(2)
        lines = string.split('\n')[::-1]
        nextPlayer = int(lines.pop().rstrip())
        playerBlocks = []
        while True:
            l = lines.pop().rstrip()
            if l=="":
                break
            playerBlocks.append(map(int,l.split(',')))
        assert settings.nbPlayers == len(playerBlocks)
        board=[[[] for _ in xrange(settings.boardSize[1])] for _ in xrange(settings.boardSize[0])]
        y = z = 0
        while len(lines) > 0:
            l = lines.pop().rstrip()
            if l=="":
                y = 0
                z += 1
                if z < settings.boardSize[2]:
                    continue
                else:
                    break
            x = 0
            for c in l:
                if c != '.':
                    p = ord(c)-65
                    assert len(board[x][y])==z
                    board[x][y].append(p)
                x += 1
            y += 1
        return GameState(settings,playerBlocks,board,nextPlayer=nextPlayer)

    def save(self,filename):
        with open(filename,'w') as f:
            return f.write(self.toASCII())

    @classmethod
    def load(cls,filename):
        with open(filename,'r') as f:
            return cls.fromASCII(f.read())

def loadLegalMovesDic():
    """ Save/load the legal moves cache """
    with open('legalMovesDic.dat','r') as f:
        return pickle.load(f)

if 'legalMovesDic.dat' in os.listdir('.'):
    legalMovesDic = loadLegalMovesDic()
else:
    legalMovesDic = {}

def saveLegalMovesDic():
    print "Saving moves cache..."
    with open('legalMovesDic.dat','w') as f:
        pickle.dump(legalMovesDic,f)
    print "...done"
