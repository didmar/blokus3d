"""
Module containing the block definitions
and functions for block manipulation (e.g., rotation)
"""

from numpy.core import vstack
from numpy.core.numeric import lexsort, array, argsort, dot, zeros
from numpy.lib.shape_base import dstack
from numpy.lib.twodim_base import flipud, diag
from numpy.lib.npyio import load
from matplotlib.pylab import flatten
from itertools import ifilter

from blokus3d.utils import third, uniqueIdx

# Sort by increasing z, then y, then x
sortCubes = lambda blk : blk[lexsort(blk.T)]

# Sort by increasing x, then y, then z
sortCubes2 = lambda blk : blk[lexsort(flipud(blk.T))]

# Blocks definition
# The origin cube (0,0,0) is omitted
blocks = [ sortCubes(x) for x in [ \
  array([(1,0,0)]),                 #1 : 2-cube bar \
  array([(1,0,0),(2,0,0)]),         #2 : 3-cube bar \
  array([(1,0,0),(0,0,1)]),         #3 :  \
  array([(1,0,0),(2,0,0),(3,0,0)]), #4 : 4-cube bar \
  array([(1,0,0),(2,0,0),(1,1,0)]), #5 : tetris T-shape \
  array([(1,0,0),(2,0,0),(0,0,1)]), #6 : tetris L-shape \
  array([(1,0,0),(0,0,1),(1,0,1)]), #7 : 2x2 \
  array([(1,0,0),(1,0,1),(2,0,1)]), #8 : tetris S-shape \
  array([(1,0,0),(0,1,0),(0,0,1)]), #9 : axis-shape \
  array([(1,0,0),(1,1,0),(1,1,1)]), #10: \
  array([(0,1,0),(1,1,0),(1,1,1)])] #11: \
]

nbBlocks = len(blocks)

blockNames = ( \
  "2-cube bar", \
  "3-cube bar", \
  "2d axis", \
  "4-cube bar", \
  "tetris T-shape", \
  "tetris L-shape", \
  "2x2", \
  "tetris S-shape", \
  "3d axis", \
  "helix 1", \
  "helix 2")

assert len(blockNames) == nbBlocks

# Relative coordinates of adjacent cubes (except for the one below)
adjacentCoords = array([[1,0,0],[0,1,0],[-1,0,0],[0,-1,0],[0,0,1]])

# Rotation matrices
rotxmat = ( \
diag((1,1,1)), # 0 \
array(((1,0,0),(0,0,1),(0,-1,0))), # 1 (90 deg) \
array(((1,0,0),(0,-1,0),(0,0,-1))), # 2 (180 deg) \
array(((1,0,0),(0,0,-1),(0,1,0))), # 3 (270 deg) \
)
rotymat = ( \
diag((1,1,1)), # 0 \
array(((0,0,-1),(0,1,0),(1,0,0))), # 1 (90 deg) \
array(((-1,0,0),(0,1,0),(0,0,-1))), # 2 (180 deg) \
array(((0,0,-1),(0,1,0),(-1,0,0))), # 3 (270 deg) \
)
rotzmat = ( \
diag((1,1,1)), # 0 \
array(((0,1,0),(-1,0,0),(0,0,1))), # 1 (90 deg) \
array(((-1,0,0),(0,-1,0),(0,0,1))), # 2 (180 deg) \
array(((0,-1,0),(1,0,0),(0,0,1))), # 3 (270 deg) \
)

def rotateBlock(blk, rotx, roty, rotz):
    """ Return the block blk after rotation (rotx,roty,rotz) """
    return dot(dot(dot(blk, rotxmat[rotx]),rotymat[roty]), rotzmat[rotz])

sameBlock = lambda blk1,blk2 : len(blk1)==len(blk2) and (blk1==blk2).all()

def cmpCubesPos(c1,c2):
    for i in xrange(3):
        if c1[i] > c2[i]:
            return +1
        elif c1[i] < c2[i]:
            return -1
    return 0

def argsortBlocks(blocks):
    return argsort(map(flatten, blocks))

# Use the nth cube in the block as the new origin
def changeOrigin(blk, n):
    return sortCubes( \
        ((lambda x : x-x[n])(vstack([[0,0,0],blk]))) \
        [range(n)+range(n+1,blk.shape[0]+1),:] \
    )

def includesCube(blk, cube):
    for c in blk:
        if cmpCubesPos(c,cube) == 0:
            return True
    return False

def blockToASCII(blk, showOrigin=False):
    blkWithOrig = vstack([zeros(3),blk])
    maxi, mini = blkWithOrig.max(0),blkWithOrig.min(0)
    s = ""
    for k in range(int(mini[2]),int(maxi[2])+1):
        for j in range(int(mini[1]),int(maxi[1])+1):
            for i in range(int(mini[0]),int(maxi[0])+1):
                if (blkWithOrig == array([i,j,k])).all(1).any() or i==j==k==0:
                    s += "O" if showOrigin and i==j==k==0 else "#"
                else:
                    s += "."
            s += "\n"
        s += "\n"
    return s

def containsCube(blk, cube):
    return 0 < len(list(ifilter(lambda other : (cube==other).all(), blk)))

def computeBlocksVar():
    """
    Compute all the variations of each block,
    such that blocksVar[k][j][k] is the ith cube
    of the jth variation of the kth block
    """
    _blocksVar = [[] for _ in xrange(nbBlocks)]
    for k in xrange(nbBlocks):
        for rotx in xrange(4):
            for roty in xrange(4):
                for rotz in xrange(4):
                    b = rotateBlock(blocks[k], rotx, roty, rotz)
                    for o in xrange(b.shape[0]+1):
                        _blocksVar[k].append(changeOrigin(b, o))
        uniIdx = uniqueIdx(_blocksVar[k])
        _blocksVar[k] = dstack(_blocksVar[k])
        _blocksVar[k] = _blocksVar[k][:,:,uniIdx]
    return _blocksVar

# XXX Generate the blocksVar cache file if not found
# Saving blocksVar to a file for caching purposes
#blocksVar = computeBlocksVar()
#save('blocksVar.dat',blocksVar)
# Loading blocksVar from cache
blocksVar = load('blocksVar.dat.npy') # blocksVar[i] shape : cubes x coordinates x variations

def blockHeight(blk):
    x = map(third, blk)+[0]
    return max(x)-min(x)+1

def blockVarWithOrigin(blkId, blkVarId):
    return sortCubes(vstack([array([0,0,0]), blocksVar[blkId][:,:,blkVarId]]))

def blockVarToASCII(blkId, blkVarId, showOrigin=False):
    return blockToASCII(blocksVar[blkId][:,:,blkVarId], showOrigin=showOrigin)

