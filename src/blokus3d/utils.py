#!/usr/bin/env python
#-*- coding:utf-8 -*-

from numpy.lib.arraysetops import unique
from numpy.random import randint
from itertools import izip, imap, islice
from time import time

fst = lambda x : x[0]
snd = lambda x : x[1]
third = lambda x : x[2]

def top(n,g):
    """Take the n first element from generator g"""
    return islice(g, n)

def repFnc(n, fun, *args, **kwargs):
    """Generator that yields n times a call to function fun"""
    for _ in xrange(n):
        yield fun(*args, **kwargs)

def randomFromList(L):
    return L[randint(len(L))]

def izipWithFun(f, x):
    return izip(imap(f,x),x)

def emptyIter(iterable):
    try:
        next(iterable)
        return False
    except StopIteration:
        return True

def fold(f, iterable):
    first = True
    for e in iterable:
        if first:
            h, first = e, False
        else:
            h = f(h,e)
    return h if not first else None

def concatLists(iterOverLists):
    return fold(list.__add__,iterOverLists)

def notEmptyLine(x):
    return x != ''

def timeLimit(maxSeconds, generator):
    start = time()
    for result in generator:
        ellapsed = time()-start
        if ellapsed > maxSeconds:
            return result
    return None

def bound(x, mini, maxi):
    return mini if x < mini else (maxi if x > maxi else x)

def uniqueIdx(L):
    """
    Find indexes of unique elements in L
    based on their string representation
    (works both for cubes and blocks)
    """
    return list(snd(unique([str(x) for x in L], return_index=True)))

def unik(L):
    return [L[i] for i in uniqueIdx(L)]
