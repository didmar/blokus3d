"""
Moves are triplet: board coordinates, block id and block variation id
"""

from itertools import izip

from blokus3d.block import blockVarWithOrigin, blockVarToASCII

def sameMoves((coords1, blkId1, blkVarId1), (coords2,blkId2,blkVarId2)):
    if blkId1 != blkId2:
        return False
    for (blk1,blk2) in izip(blockVarWithOrigin(blkId1, blkVarId1),\
                            blockVarWithOrigin(blkId2, blkVarId2)):
        if not ((blk1+coords1)==(blk2+coords2)).all():
            return False
    return True

def moveToASCII(move):
    if move == None:
        return "Passing"
    coords, blkId, blkVarId = move
    return "Block %d at height %d, coordinates %c%c, variation [varId=%d]:\n%s"\
           % (blkId+1,coords[2]+1,chr(coords[0]+97),str(coords[1]+1),\
              blkVarId, blockVarToASCII(blkId,blkVarId,showOrigin=True))

def moveIndex(lst,m):
    for i,e in enumerate(lst):
        if (e == None and m == None) or (tuple(e[0]) == tuple(m[0]) and e[1]==m[1] and e[2]==m[2]):
            return i
    return None
