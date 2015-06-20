#!/usr/bin/env python
#-*- coding:utf-8 -*-

# XXX if wrong coords are passed, you get 0 variations to choose from and it bugs !

from numpy.core.numeric import array
from numpy.core.fromnumeric import sort
from numpy.lib.arraysetops import unique
from matplotlib.pylab import flatten
from blokus3d.block import blockToASCII, blockVarToASCII, \
                           blockNames, blocks, blocksVar
from blokus3d.move import moveToASCII
from blokus3d.utils import fst, snd, third, unik
from itertools import takewhile

def findMove(gs, askApply=True):
    moves = gs.legalMoves()
    if len(moves)==1:
        print "Only one move possible :\n", moveToASCII(moves[0])
    else:
        ok = False
        while not ok:
            # First, pick a block
            blkId = findBlock(gs,candidates=unique(map(snd,moves)))
            assert blkId != None # since we checked that len(lm) was > 0
            # Filter the moves that have the selected block id
            moves = filter(lambda m : m[1]==blkId, moves)
            # Then, find the coordinates on the board
            coords = findCoords(gs,candidates=unik(map(fst,moves)))
            # Filter the moves that have the selected coordinates
            moves = filter(lambda m : (m[0]==coords).all(), moves)
            # Finally, find its variation
            blkVarId = findVariation(gs,blkId, \
                        candidates=unique(map(third,moves)))
            move = (coords,blkId,blkVarId)
            print "You have selected :\n", moveToASCII(moves[0])
            print "Is this the move you wanted ? [Y/n]"
            if raw_input("") in ["n","N"]:
                # Will start again with all legal moves possibles
                moves = gs.legalMoves()
            else:
                ok = True
    if askApply:
        print "Do you want to play this move over the current gamestate ?",\
              " [Y/n]"
        if raw_input("") not in ["n","N"]:
            gs.playMove(move)
    return move

def findBlock(gs, candidates=None):
    if candidates == None:
        candidates = gs.playerBlocks[gs.nextPlayer]
    if len(candidates)==0:
        return None
    print "Which block ?"
    for blkId in candidates:
        print "%d) %s" % (blkId+1, blockNames[blkId])
        print blockToASCII(blocks[blkId])
    return input("> ")-1

def findCoords(gs, candidates=None):
    if candidates == None:
        candidates=[]
        # List all the possible z-level (heights)
        zRange = list(takewhile(lambda x : x < gs.boardSize[2], \
                 sort(unique(flatten(gs.heightMap())))))
        if zRange==[]:
            print "Board is full, cannot find legal coordinates !"
            return None
    else:
        zRange = sort(unique(map(third,candidates)))
    # Do we have a choice on the z-level ?
    if len(zRange)==1:
        z = zRange[0]
    else:
        print "\n",gs.boardToASCII(markedCubes=candidates)
        # Discard the z height max
        if zRange[-1]==gs.boardSize[2]:
            zRange = zRange[:-1]
        z = -1+input("Which z-level ? (%d-%d)\n> " \
                     % (zRange[0]+1,zRange[-1]+1))
    candidates = filter(lambda c: c[2]==z, candidates)
    if len(candidates)>1:
        # Display the z-level with xy coordinates as letter-number
        print '    '+''.join(chr(97+x) for x in xrange(gs.boardSize[0]))
        print '   +'+'-'*gs.boardSize[0]
        lines = gs.boardToASCII(zRange=[z],markedCubes=candidates)\
                .split('\n')
        for y in xrange(gs.boardSize[1]):
            print '%s |%s' % (str(y+1).zfill(2),lines[y])
        print "\n"
        xy = raw_input("Which xy coordinates ?\n> ")
        return array([ord(xy[0])-97,int(xy[1:])-1,z])
    else:
        return candidates[0]

def findVariation(gs, blkId, candidates=None):
    assert blkId in gs.playerBlocks[gs.nextPlayer]
    # If no candidates are given,
    # then any variation id might be selected
    if candidates == None:
        candidates = range(blocksVar[blkId].shape[2])

    # XXX doesn't work, fix me !!
    #    # Associate each candidate variation id with its height
    #    varHeights = map(lambda blkVarId:
    #                        blockHeight(blocksVar[blkId][:,:,blkVarId]),\
    #                     candidates)
    #    print "varHeights = ",varHeights
    #    hRange = sort(unique(varHeights))
    #    print "hRange = ",hRange
    #    if len(hRange) > 1:
    #        h = input("What height does have the variation ? (%s)\n> " \
    #                  % ','.join(map(str,hRange)))
    #    else:
    #        h = hRange[0]
    #    print "h = ",h
    #    candidates = [candidates[i] for i in find(array(varHeights)==h)]

    if len(candidates) == 1:
        return candidates[0]
    print "Which variation ?"
    for num, blkVarId in enumerate(candidates):
        print "%d) [varId:%d]" % (num+1, blkVarId)
        print blockVarToASCII(blkId, blkVarId, showOrigin=True)
    i = input("> ") - 1
    return candidates[i]

