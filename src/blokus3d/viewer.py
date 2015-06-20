#!/usr/bin/env python
#-*- coding:utf-8 -*-
# 3D viewer using the Soya lib

# XXX show controls using a text message
# XXX show remaining blocks
# XXX show the Z limit by drawing something on top of the cube
# XXX no freezing while AI is thinking

import sys, math, soya.cube, soya.sdlconst
from numpy.core.fromnumeric import argmin
from numpy.core import vstack
from numpy.core.numeric import array
from numpy.linalg import norm
from itertools import imap

from blokus3d.block import sortCubes2
from blokus3d.gamestate import blockVarWithOrigin
from blokus3d.utils import bound

white = soya.Material()
white.diffuse = (1.0, 1.0, 1.0, 1.0)
red = soya.Material()
red.diffuse = (1.0, 0.0, 0.0, 1.0)
green = soya.Material()
green.diffuse = (0.0, 1.0, 0.0, 1.0)

class SelectionPerformed(Exception):
    def __init__(self,move):
        self.move = move

class Cursor(soya.Body):

    def __init__(self, parent, cursorModel, gameSettings, legalMoves):
        soya.Body.__init__(self, parent, None)
        # set viewpoint azimuth and elevation
        self.alpha, self.beta = 0, math.pi/4
        self.cursorModel = cursorModel
        self.radius = gameSettings.boardSize[2]+2
        self.legalMoves = legalMoves
        self.viewOnly = (self.cursorModel == None) and (self.legalMoves == None)
        # Compute all possible block placement
        if self.legalMoves != None:
            self.cubeToBlk, self.cubeCenters = Cursor.computeAllBlockPlacements(legalMoves)
        # for camera movement
        self.rightClicking = False
        self.selectedVariant = 0
        self.selectedMove = None
        self.cursorCubes = []
        self.previouslySelectedCube = None
        # Camera stuff
        self.boardCenter = soya.Point()
        x = 0.5*(gameSettings.boardSize[0]-1)
        y = 1
        z = 0.5*(gameSettings.boardSize[1]-1)
        self.boardCenter.set_xyz(x, y, z)
        self.camera = soya.Camera(self.parent)
        self.camera.fov = 90.0
        self.updateCamera()
        soya.set_root_widget(self.camera)

    def begin_round(self):
        soya.Body.begin_round(self)
        # Processes the events
        for event in soya.MAIN_LOOP.events:
            self.handleEvent(event)
        self.updateCamera()

    def handleEvent(self, event):
        if event[0] == soya.sdlconst.QUIT:
            raise Exception
        elif event[0] == soya.sdlconst.MOUSEMOTION:
            if self.rightClicking:
                dx,dz = event[3],event[4] # mouse cursor movement
                self.alpha -= dx*0.02
                self.beta  -= dz*0.02
            elif not self.viewOnly:
                cube2dPositions = []
                for cubeCenter in self.cubeCenters:
                    cube3dPos = soya.Point(self.parent,cubeCenter[0],cubeCenter[1],cubeCenter[2])
                    cube2dPositions.append(self.camera.coord3d_to_2d(cube3dPos))
                cube2dPositions = vstack(cube2dPositions)
                i = argmin(map(norm, \
                            cube2dPositions - array([event[1],event[2]])))
                self.selectedCube = self.cubeToBlk.keys()[i]
                if self.selectedCube != self.previouslySelectedCube:
                    self.updateCursor()
                    self.previouslySelectedCube = self.selectedCube
        elif event[0] == soya.sdlconst.MOUSEBUTTONDOWN:
            if event[1] == soya.sdlconst.BUTTON_WHEELDOWN:
                self.selectedVariant += 1
                self.updateCursor()
            elif event[1] == soya.sdlconst.BUTTON_WHEELUP:
                self.selectedVariant -= 1
                self.updateCursor()
            elif event[1] == soya.sdlconst.BUTTON_RIGHT:
                self.rightClicking = True
            elif event[1] == soya.sdlconst.BUTTON_LEFT and not self.viewOnly:
                raise SelectionPerformed(self.selectedMove)
        elif event[0] == soya.sdlconst.MOUSEBUTTONUP:
            if event[1] == soya.sdlconst.BUTTON_RIGHT:
                self.rightClicking = False
        elif event[0] == soya.sdlconst.KEYDOWN:
            if event[1] == soya.sdlconst.K_LEFT:
                self.alpha += 0.1
            elif event[1] == soya.sdlconst.K_RIGHT:
                self.alpha -= 0.1
            elif event[1] == soya.sdlconst.K_DOWN:
                self.beta -= 0.1
            elif event[1] == soya.sdlconst.K_UP:
                self.beta += 0.1
            elif event[1] == soya.sdlconst.K_PAGEUP:
                self.radius = max(self.radius - 0.5, 0.01)
            elif event[1] == soya.sdlconst.K_PAGEDOWN:
                self.radius = min(self.radius + 0.5, 20.0)
            elif event[1] == soya.sdlconst.K_ESCAPE:
                raise Exception

    def updateCamera(self):
        global radius
        self.beta = bound(self.beta,0,math.pi/2-0.1)
        radius = bound(self.radius,2,10)
        xp, zp = math.cos(self.alpha)*radius, math.sin(self.alpha)*radius
        yp = self.boardCenter.y + radius * math.sin(self.beta)
        xp = self.boardCenter.x + xp * math.cos(self.beta)
        zp = self.boardCenter.z + zp * math.cos(self.beta)
        self.camera.set_xyz(xp, yp, zp)
        self.camera.look_at(self.boardCenter)

    def updateCursor(self):
        if self.selectedCube == None:
            return
        variants = self.cubeToBlk[self.selectedCube]
        self.selectedMove = variants[self.selectedVariant % len(variants)]
        coords, blkId, blkVarId = self.selectedMove
        # Destroy previous cursor block, if necessary
        for cube in self.cursorCubes:
            self.parent.remove(cube)
        self.cursorCubes = []
        # Create cubes to show the selected block
        for cube in imap(tuple, coords+blockVarWithOrigin(blkId,blkVarId)):
            c = soya.Body(self.parent, self.cursorModel)
            c.set_xyz(cube[0],cube[2],cube[1])
            self.cursorCubes.append(c)

    @classmethod
    def computeAllBlockPlacements(cls, legalMoves):
        cubeToBlk = {} # cube coords -> (blkId, blkVar)
        for coords, blkId, blkVarId in legalMoves:
            for cube in imap(tuple, coords+blockVarWithOrigin(blkId,blkVarId)):
                if not cubeToBlk.has_key(cube):
                    cubeToBlk[cube] = []
                cubeToBlk[cube].append( (coords,blkId,blkVarId) )
        # If their is a cube higher than another, move its entries to the lower cube
        S = reversed(sortCubes2(array(cubeToBlk.keys())))
        lastOne = tuple(next(S))
        try:
            while True:
                nextToLastOne = tuple(next(S))
                # Same xy coordinates ?
                if lastOne[0]==nextToLastOne[0] and lastOne[1]==nextToLastOne[1] :
                    # nextToLastOne has smaller z
                    L = cubeToBlk.pop(lastOne)
                    cubeToBlk[nextToLastOne].extend( L )
                lastOne = nextToLastOne
        except StopIteration:
            pass
        # Compute the center of each cube key in the soya world frame
        cubeCenters = vstack([array([c[0],c[2],c[1]]) for c in cubeToBlk.keys()])
        return cubeToBlk, cubeCenters


def findMove3d(gs, viewOnly=False):

    if not viewOnly:
        legalMoves = gs.legalMoves()
        if legalMoves==[None]:
            print "Passing"
            return None

    assert gs.nbPlayers == 2
    playerMaterials = [red,green] # TODO a changer quand on aura plus de 2 joueurs
    soya.init(title='Blokus 3D',quiet=True)
    # Creates the scene
    scene = soya.World()

    # Create the 3d representation of the board
    for x,y in gs.xycoords:
        col = gs.board[x][y]
        for z in xrange(len(col)):
            cube = soya.Body(scene, soya.cube.Cube(None, playerMaterials[col[z]]).to_model())
            cube.set_xyz(x, z, y)
        floor = soya.World(scene)
        s=0.9
        soya.Face(floor,\
                   [soya.Vertex(floor, x+0.5*s, -0.5*s, y+0.5*s, 1.0*s, 1.0*s),\
                    soya.Vertex(floor, x+0.5*s, -0.5*s, y-0.5*s, 0.0,   1.0*s),\
                    soya.Vertex(floor, x-0.5*s, -0.5*s, y-0.5*s, 0.0,   0.0),\
                    soya.Vertex(floor, x-0.5*s, -0.5*s, y+0.5*s, 1.0*s, 0.0),\
                   ], white)

    if viewOnly:
        Cursor(scene, None, gs.settings, None)
    else:
        # Create a translucent material of the player's color
        # to represent the current selection
        cursorMat = soya.Material()
        pm = playerMaterials[gs.nextPlayer]
        cursorMat.diffuse = (pm.diffuse[0], \
                             pm.diffuse[1], \
                             pm.diffuse[2], \
                             0.5)
        cursorModel = soya.cube.Cube(None, cursorMat).to_model()
        Cursor(scene, cursorModel, gs.settings, legalMoves)

    # Adds a light
    light = soya.Light(scene)
    light.set_xyz(gs.boardSize[0]/2, gs.boardSize[2]+1, gs.boardSize[1]/2)
    light.ambient = (0.5, 0.5, 0.5, 0.5)

    # Run a loop, until some move is selected
    try:
        soya.MainLoop(scene).main_loop()
    except SelectionPerformed as sp:
        return sp.move
    except Exception as e:
        print "Exiting", e
        sys.exit()
