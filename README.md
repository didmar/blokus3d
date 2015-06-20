AI for the board game Blokus3D
==============================

## Dependencies

- [Matplotlib](http://matplotlib.org/) (packaged as [python-matplotlib](https://packages.debian.org/fr/stable/python-matplotlib) on Debian/Ubuntu)
- For the 3D interface (viewer module), you need [Soya3D](http://home.gna.org/oomadness/en/soya3d/). It is packaged as [python-soya](https://packages.debian.org/fr/stable/python-soya) on Debian/Ubuntu

## Usage

>export PYTHONPATH=$(pwd)/src
>python -m blokus3d

## Game rules

In Blokus3D, players alternatively place their blocks on the board.
The goal is to have the most visible squares visible from above.

Blocks must be placed on top of others, such that there is no empty space between any of their cubes.
Also, there must be an adjacent block of the same color (except during the first turn).
When a player cannot play, he passes. If no one can play anymore, the game is over.
The remaining blocks a player may have will count as a penalty !

## Instructions

- Left click to position a block
- Mouse wheel to pick a different block/rotation
- Hold right click to rotate around the board
- Use dir arrows and page up/down to control camera
- ESC to quit
