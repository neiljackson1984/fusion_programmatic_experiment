import time
from typing import Iterable, List, Optional, Sequence, Tuple, Union
import math
import itertools
import warnings

# import scipy
# the above import of scipy requires the user to have taken action to ensure
# that scipy is available somewhere on the system path, for instance by doing
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe"
# -m pip install scipy I would like to automate the management of dependencies
# like this.  With a "normal" Python project, pipenv would be the logical way to
# do it, but for scripts that are to be loaded by fusion, it is unclear what the
# best way to manage dependencies is -- maybe some sort of vendoring?

from .highlight import *

import numpy as np
from numpy.core.numerictypes import ScalarType
# I am relying on the installation of scipy to also install numpy.

from numpy.typing import ArrayLike, NDArray
from typing import SupportsFloat
from numpy import ndarray
from numpy import number
from math import sin, cos

from sympy.printing.c import _as_macro_if_defined
import adsk
import adsk.fusion, adsk.core
import unyt
import operator
from .braids.fscad.src.fscad import fscad as fscad

from adsk.fusion import BRepEdge, ChainedCurveOptions, ProfileLoop, SurfaceExtendTypes, TemporaryBRepManager
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt

import pathlib

import unyt
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt


def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent

unyt.millimeter = unyt.milimeter
# this is a work-around for the problem that unyt misspells the SI
# prefix milli with only a single l.

# there is some cognitive dissonance going on to deal simultaneously with the
# "3D.." and "2D..."  terms that appear in the fusion API and the "1D", "2D",
# ... language used by numpy. numpy uses "D"-notation to describe tensor rank
# (sometimes, at least, it seems), whereas the Fusion API uses "2D" and "3D" to
# refer to a 2-dimensional space and 3-dimensional space (but of course Fusion
# (correctly) does things projectively to be able to treat all rigid transforms
# as matrices (and for rational NURBS (to put the 'R' in 'NURBS'), I think).  So
# fusion's '...2D...' and '...3D...' objects are really working with
# 3-dimensional projective and 4-dimensional projective vector spaces,
# respectively.  The wording is not very clean.
#


fusionInternalUnitOfLength = unyt.centimeter

def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent

_brep = None
def temporaryBRepManager() -> adsk.fusion.TemporaryBRepManager:
    # caching the brep is a workaround for a weird bug where an exception from calling a TemporaryBRepManager method
    # and then catching the exception causes TemporaryBRepManager.get() to then throw the same error that was previously
    # thrown and caught. Probably some weird SWIG bug or something.
    global _brep
    if not _brep:
        _brep = adsk.fusion.TemporaryBRepManager.get()
    return _brep


radian = 1
degree = math.pi/180 * radian
centimeter = 1 #fusion's internal native length unit is the centimeter
millimeter = 0.1 * centimeter
zeroLength = 0 
meter = 1000 * millimeter
inch = 25.4 * millimeter
# this is for compatability with expressions copied from featureScript, wherein length is a special type, and I anticipate that
# we will eventually use a similar system of units where we will want a zeroLength.

# we would benefit from having an organized system of physical units.  For now, I am implicitly assuming that all distance units are millimeters.

xHat : NDArray = np.array((1.0,0,0))
yHat : NDArray = np.array((0,1.0,0))
zHat : NDArray = np.array((0,0,1.0))

originPoint3D = adsk.core.Point3D.create(0,0,0)
zeroVector3D = adsk.core.Vector3D.create(0,0,0)

def renderEntityToken(entityToken: str) -> str:
    """trying to make sense of Fusion's entity tokens."""
    # return "\n".join( entityToken.split('/'))
    import base64
    import string
    import zlib
    
    bb = base64.b64decode(entityToken)
    ss = []

    for i in range(len(bb)):
        # try:
        #     s = ba[i:i+1].decode('ascii')
        # except:
        #     s = ba[i:i+1].hex()

        if (
            bb[i] in string.printable.encode('ascii') 
            and not (bb[i] in "\t\r\n\x0b\x0c".encode('ascii'))
            and bb[i] != 255
            and False
        ) :
            s = bb[i:i+1].decode('ascii')
        else:
            s = bb[i:i+1].hex()
        ss.append(s)

    # zlib.decompress(bb[21:])

    return  "".join(ss)
    # + "\n" + "\n".join( 
    #     (
    #         str(len(piece)) + ' ' + piece
    #         for piece in entityToken.split('/')
    #     )
    
    # )
    return entityToken


def norm(v : ndarray) -> number :
    # v is intended to be a rank-one array with real elements
    # being able to specify size and rank (i.e. array 'shape' in numpy parlance) as a type is sorely needed -- actually, it looks like numpy.typing.NDArray comes pretty close.
    # ought to handle zero vectors, or at least throw a meaningful exception
    # according to https://stackoverflow.com/questions/21030391/how-to-normalize-an-array-in-numpy-to-a-unit-vector ,
    # , it is slightly faster to compute the norm as np.sqrt((v*v).sum()) than to call np.linalg.norm()
    return np.sqrt((v*v).sum())

def normalized(v : ndarray) -> ndarray:
    # v is intended to be a rank-one array with real elements
    # being able to specify size and rank (i.e. array 'shape' in numpy parlance) as a type is sorely needed.
    # ought to handle zero vectors, or at least throw a meaningful exception
    # ought to handle the case of complex elements
    # It might improve performance to have a flag to track whether a vector is already normalized, to avoid re-doing the computation unnecessarily.
    return v/norm(v)

normalize = normalized

def rotationMatrix3d(axisOfRotation : ndarray, angleOfRotation : number) -> ndarray:
    # compute normalized axisOfRotation and call it v:
    v = normalized(axisOfRotation)
    projectOnV=np.array(
        [
            [  v[0]*v[0],  v[0]*v[1],  v[0]*v[2]  ],
            [  v[0]*v[1],  v[1]*v[1],  v[1]*v[2]  ],
            [  v[0]*v[2],  v[1]*v[2],  v[2]*v[2]  ]
        ]
    )
    oneMinusProjectOnV=np.array(
        [
            [  1 -v[0]*v[0]  ,    -v[0]*v[1]  ,    -v[0]*v[2]  ],
            [    -v[0]*v[1]  ,  1 -v[1]*v[1]  ,    -v[1]*v[2]  ],
            [    -v[0]*v[2]  ,    -v[1]*v[2]  ,  1 -v[2]*v[2]  ]
        ]
    )
    # I am not sure which is more computationally efficient: 1 -v[0]*v[0]  or v[1]*v[1] + v[2]*v[2] .  
    # They should give the equivalent numerical result due to v being normalized.

    # projectOnV=np.array(
    #     [
    #         [  v[0]**2,  v[0]*v[1],  v[0]*v[2]  ],
    #         [  v[0]*v[1],  v[1]**2,  v[1]*v[2]  ],
    #         [  v[0]*v[2],  v[1]*v[2],  v[2]**2  ]
    #     ]
    # )
    # oneMinusProjectOnV=np.array(
    #     [
    #         [  1 -v[0]**2  ,    -v[0]*v[1]  ,    -v[0]*v[2]  ],
    #         [    -v[0]*v[1]  ,  1 -v[1]**2  ,    -v[1]*v[2]  ],
    #         [    -v[0]*v[2]  ,    -v[1]*v[2]  ,  1 -v[2]**2  ]
    #     ]
    # )

    vCross=np.array(
        [
            [   0     ,  -v[2]  ,   v[1]  ],
            [   v[2]  ,   0     ,  -v[0]  ],
            [  -v[1]  ,   v[0]  ,   0     ]
        ]
    )
    return projectOnV + cos(angleOfRotation) * oneMinusProjectOnV + sin(angleOfRotation) * vCross

def floor(x : SupportsFloat, modulus : SupportsFloat = 1 ) -> SupportsFloat :
    """this is a two-argument version of the floor function that lets you specify a modulus other than 1, if so desired"""
    return math.floor(x/modulus) * modulus 

def mean(*args: ArrayLike) -> ArrayLike:
    # return functools.reduce(operator.add, args)/len(args)
    return sum(args)/len(args)

def vector(*args) -> ndarray:
    return np.array(args)


def partitionEdgeSequenceIntoChains(edges: Sequence[adsk.fusion.BRepEdge]) -> Sequence[Sequence[adsk.fusion.BRepEdge]]:
    """ takes a set of edges.  partitions the edge into subsets, where each subset forms a chain (i.e. the end vertex of one edge is the start vertex of the next, etc.).
        
        This is useful when you have a collection of not-necessarily connected edges, and you want to produce input to one or more calls of adsk.fusion.Features.createPath().
        This function is more stringent than adsk.fusion.Path.create() when it comes to defining a chain.  This function picks out only topological chains, whereas Path.create() 
        would, I think, accept a sequence of edges that simply had coincident sequential endpoints.
    """
    #note: depending on the topological connection between edges, the result will not necessarily be unique. (e.g. in the case of a 'Y' shape, we could join either of the two legs with the base.)
    #it might be good to think about what we should do when edges contains repeated edges.
    # if we were being sophisticated, we might use loop membership to sway us toward one particular parititioning in degenerate cases.
    edgePool : Sequence[adsk.fusion.BRepEdge] = list(edges)
    chains=[]
    while len(edgePool) > 0:
        #start a new chain based on the next member of edgePool
        seedLink = edgePool.pop()
        thisChain : Sequence[adsk.fusion.BRepEdge]  = [seedLink]
        leftVertexOfThisChain = seedLink.startVertex
        rightVertexOfThisChain = seedLink.endVertex
        # we don't pay any attention to the direction of the edge -- we are treating the topology as a non-directed graph.

        # search for links connected on the right
        keepSearchingRightward = True
        while keepSearchingRightward and len(edgePool) > 0:
            #look for the next link to the right
            for i in range(len(edgePool)):
                if edgePool[i].startVertex == rightVertexOfThisChain:
                    newLink = edgePool.pop(i)
                    # add the link to the chain, and update rightVertexOfThisChain 
                    thisChain.append(newLink)
                    rightVertexOfThisChain = newLink.endVertex
                    keepSearchingRightward = True
                    break
                elif edgePool[i].endVertex == rightVertexOfThisChain:
                    newLink = edgePool.pop(i)
                    # add the link to the chain, and update rightVertexOfThisChain 
                    thisChain.append(newLink)
                    rightVertexOfThisChain = newLink.startVertex
                    keepSearchingRightward = True
                    break
                else:
                    keepSearchingRightward = False
        
        # search for links connected on the left
        keepSearchingLeftward = True
        while keepSearchingLeftward and len(edgePool) > 0:
            #look for the next link to the left
            for i in range(len(edgePool)):
                if edgePool[i].startVertex == leftVertexOfThisChain:
                    newLink = edgePool.pop(i)
                    # add the link to the chain, and update leftVertexOfThisChain 
                    # thisChain.append(newLink)
                    thisChain.insert(0,newLink) # inserting at the beginning of the list is not really necessary, but I am arranging things so that thisChain[i] has (at least) one common vertex with thisChain[i+1] for all i, just for the heck of it.
                    leftVertexOfThisChain = newLink.endVertex
                    keepSearchingLeftward = True
                    break
                elif edgePool[i].endVertex == leftVertexOfThisChain:
                    newLink = edgePool.pop(i)
                    # add the link to the chain, and update leftVertexOfThisChain 
                    # thisChain.append(newLink)
                    thisChain.insert(0,newLink)
                    leftVertexOfThisChain = newLink.startVertex
                    keepSearchingLeftward = True
                    break
                else:
                    keepSearchingLeftward = False
        
        chains.append(thisChain)

    return chains



def partitionEdgeSequenceIntoPaths(edges: Sequence[adsk.fusion.BRepEdge]) -> Sequence[adsk.fusion.Path]:
    """takes a set of edges.  partitions the edge into subsets, where each subset forms a chain (i.e. the end vertex of one edge is the start vertex of the next, etc.).
        Then feeds the aforementioned subsets, one by one, into adsk.fusion.Path.create(), to produce a sequence of paths.
        This is useful when you have a collection of not-necessarily connected edges, and you want to produce input to one or more calls of adsk.fusion.Features.createPath().
        This function is more stringent than adsk.fusion.Path.create() when it comes to defining a chain.  This function picks out only topological chains, whereas Path.create() 
        would, I think, accept a sequence of edges that simply had coincident sequential endpoints.
    """

    return tuple(
        map(
            lambda x: 
                adsk.fusion.Path.create(
                    curves=fscad._collection_of(x), 
                    chainOptions=adsk.fusion.ChainedCurveOptions.noChainedCurves
                    # the chainOptions argument tells fusion whether to try to find add add to the path edges or sketch curves other than those specified in curves. 
                    # we are telling fusion not to try to find more edges than those we havve (carefully) specified.
                ),
            partitionEdgeSequenceIntoChains(edges)
        )
    )


VectorLike = Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D, Sequence[number]]

def castToNDArray(x: Union[VectorLike, adsk.core.Matrix3D, adsk.core.Matrix2D], n: Optional[int] = None) -> NDArray:
    #TODO: handle various ranks of NDArray rather than blindly assuming that we have been given a rank-1 array.
    if isinstance(x, np.ndarray):
        returnValue = x
    elif isinstance(x, adsk.core.Point3D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Vector3D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Point2D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Vector2D):
        returnValue =  np.array(x.asArray())
    elif isinstance(x, adsk.core.Matrix3D):
        returnValue =  np.array(
            (
                x.asArray()[0:4],
                x.asArray()[4:8],
                x.asArray()[8:12],
                x.asArray()[12:16],
            )
        )
    elif isinstance(x, adsk.core.Matrix2D):
        returnValue =  np.array(
            (
                x.asArray()[0:3],
                x.asArray()[3:6],
                x.asArray()[6:9],
            )
        )
    else:
        returnValue =  np.array(x)

    if n is not None:
        #pad with zeros as needed to make sure we have at least n elements:
        returnValue = np.append(
            returnValue, 
            (0,)*(n-len(returnValue))
        )
        #take the first n elements, to ensure that we end up with exactly n elements:
        returnValue = returnValue[0:n]
        # this cannot possibly be the most efficient way to do this, 
        # but it has the advantage of being a fairly short line of code.
    return returnValue



def castTo2dArray(x: VectorLike) -> NDArray: 
    return castToNDArray(x,2)

def castTo3dArray(x: VectorLike) -> NDArray: 
    #need to figure out how to use the shape-specificatin facility that I think is part of the NDArray type alias.
    a=castToNDArray(x, 3)
    # I am not sure whether what we should do with Point2D and Vector2D: should we treat them like Point3D and Vector3D that 
    # happen to lie in the xy plane, or should we return the point in projective 3d space that they represent?
    # for now, I am treating them like Point3D and Vector3D that happen to lie in the xy plane.
    #TODO: handle various sizes of NDArray rather than blindly assuming that we have been given a 3-array
    return a

def castTo4dArray(x: VectorLike) -> NDArray: 
    #need to figure out how to use the shape-specificatin facility that I think is part of the NDArray type alias.
    a=castToNDArray(x,4)
    if isinstance(x, (adsk.core.Point3D, adsk.core.Point2D)):
        a[3] = 1


    return a

def castToPoint3D(x: VectorLike) -> adsk.core.Point3D:
    if isinstance(x, adsk.core.Point3D):
        return x.copy()
    else:
        return adsk.core.Point3D.create(*castTo3dArray(x).astype(dtype = float))

def castToVector3D(x: VectorLike) -> adsk.core.Vector3D:
    if isinstance(x, adsk.core.Vector3D):
        return x.copy()
    else:
        return adsk.core.Vector3D.create(*castTo3dArray(x).astype(dtype = float))

# def castToMatrix3D(x: Union[adsk.core.Matrix2D,adsk.core.Matrix3D, np.ndarray[(3,3), np.dtype[ScalarType]] , np.ndarray[(4,4), np.dtype[ScalarType]] ]) -> adsk.core.Matrix3D:
# I do not understand the numpy type hinting system (nor do I have a complet grasp on the type hinting system generally)
def castToMatrix3D(x: Union[adsk.core.Matrix2D,adsk.core.Matrix3D, np.ndarray ]) -> adsk.core.Matrix3D:
    m = castToNDArray(x)
    assert m.shape == (3,3) or m.shape == (4,4)
    # t : np.ndarray[(4,4), np.dtype[ScalarType]] 
    # I do not understand the numpy type hinting system (nor do I have a complet grasp on the type hinting system generally)
    t : np.ndarray

    if m.shape == (4,4):
        t = m
    elif m.shape == (3,3):
        t = np.array(
            (   
                (  m[0][0]  ,  m[0][1]  ,  0.0    ,  m[0][2]   ),
                (  m[1][0]  ,  m[1][1]  ,  0.0    ,  m[1][2]   ),
                (  0.0      ,  0.0      ,  0.0    ,  0.0       ),
                (  m[2][0]  ,  m[2][1]  ,  0.0    ,  m[2][2]   ),
            )
        )
    else:
        raise TypeError() 

    matrix3D : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    result = matrix3D.setWithArray(tuple(t.flatten())); assert result
    return matrix3D


def castToMatrix2D(x: Union[adsk.core.Matrix2D,adsk.core.Matrix3D]) -> adsk.core.Matrix2D:
    # todo: make castToMatrix2D() be able to accept ndarray in the same manner as castToMatrix3D.
    if isinstance(x, adsk.core.Matrix2D):
        return x.copy()
    elif isinstance(x, adsk.core.Matrix3D):
        matrix3D = x
        matrix2D : adsk.core.Matrix3D = adsk.core.Matrix2D.create()
        result = matrix2D.setWithArray(
            (
                matrix3D.getCell(0, 0)  ,  matrix3D.getCell(0, 1)            ,  matrix3D.getCell(0, 3)   ,
                matrix3D.getCell(1, 0)  ,  matrix3D.getCell(1, 1)            ,  matrix3D.getCell(1, 3)   ,

                matrix3D.getCell(3, 0)  ,  matrix3D.getCell(3, 1)            ,  matrix3D.getCell(3, 3)   ,
            )
        )
        assert result
        return matrix2D
    else:
        raise TypeError() 


def arbitraryPerpendicularVector(x : VectorLike) -> adsk.core.Vector3D:
    """ returns a normalized vector perpendicular to the given vector """
    needle = castTo3dArray(x)
    needleHat = normalized(needle)
    candidateDirection = ( yHat if yHat @ needleHat < 0.9 else zHat )
    # Note that candidateDirection is normalized.
    return castToVector3D(
        normalized(
            candidateDirection - ( candidateDirection @ needleHat ) * needleHat
        )
    )
   


# we can think of adsk.core.Vector3D and adsk.core.Point3D as being special
# cases of a 4-element sequence of reals.  Vector3D has the last element being 0
# and Point3D has the last element being 1.  This produces the correct behavior
# when we transform a Vector3D or a Point3D by multiplying by a 4x4 matrix on
# the left.  Therefore, it might make sense to have a castTo4DArray that treats 
# Vector3D and Point3D objects correctly.  

# rectByCorners is a factory function to make an fscad.Rect:
def rectByCorners(corner1 = vector(0,0) * meter, corner2 = vector(1,1) * meter, *args, **kwargs) -> fscad.Rect:
    corner1 = castTo3dArray(corner1)
    corner2 = castTo3dArray(corner2)
    # print('corner1: ' + str(corner1))
    # print('corner2: ' + str(corner2))
    # set the 'x' and 'y' entries to kwargs (overriding any 'x' and 'y' that may have been passed)

    extent = abs(corner2 - corner1)
    minimumCorner = tuple(map(min, corner1, corner2))
    # minimumCorner = map(float, minimumCorner)
    # print('minimumCorner: ' + str(minimumCorner))   
    # print('type(minimumCorner[0]): ' + str(type(minimumCorner[0])))   
    # v = adsk.core.Vector3D.create(minimumCorner[0], minimumCorner[1], minimumCorner[2])
    # v = adsk.core.Vector3D.create(*minimumCorner)

    return fscad.Rect(
        x=extent[0],
        y=extent[1],
        *args,
        **kwargs,
    ).translate(*map(float,minimumCorner))
    # it is very hacky to have to cast to float above, but that
    # is what we have to do to work around Python's lack of
    # automatic type coercion.

def cylinderByStartEndRadius(startPoint : adsk.core.Point3D = adsk.core.Point3D.create(0,0,0), endPoint : adsk.core.Point3D = adsk.core.Point3D.create(0,0,1), radius : float = 1) -> fscad.Cylinder:
    x = fscad.Cylinder(height=endPoint.distanceTo(startPoint),radius=radius)

    # to mimic the behavior of OnShape's fCylinder function, which lets you specify the cylinder's start
    # and end points, I must rotate so as to bring zHat into alignment with self.boreDirection,
    # and translate so as to move the origin to boreBottomCenter.

    t : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    t.setToRotateTo(
        castToVector3D(zHat),
        startPoint.vectorTo(endPoint)
    )
    t.translation = startPoint.asVector()
    x.transform(t)
    return x

def getAllSheetBodiesFromSketch(sketch : adsk.fusion.Sketch) -> Sequence[adsk.fusion.BRepBody]:
    """ returns a sequence of BRepBody, containing one member for each member of sketch.profiles and 
    sheet bodies corresponding to the sketch texts. 
    each body is a sheet body having exactly one face."""
    #TODO: allow control over how we deal with overlapping profiles (which
    #generally happens in the case of nested loops).  For instance, we might
    #want to return only "odd-rank" faces.
    bodies = []

    ## FIRST ATTEMPT - construct the bodies "from scratch" by extracting the primitive entities from sketch.profiles.
    ## foiled due to missing functionality in fusion api.  Also foiled for SketchText objects that SketchText doesn't show up in sketch.profiles.
        # # profile : adsk.fusion.Profile
        # # for profile in sketch.profiles: 
        # #     bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()
        # #     brepLumpDefinition  = bRepBodyDefinition.lumpDefinitions.add()
        # #     brepShellDefinition = brepLumpDefinition.shellDefinitions.add()
        # #     brepFaceDefinition  = brepShellDefinition.faceDefinitions.add(
        # #         surfaceGeometry=profile.plane, 
        # #         isParamReversed=False
        # #         )

        # #     loop: adsk.fusion.ProfileLoop
        # #     for loop in profile.profileLoops:
        # #         bRepLoopDefinition = brepFaceDefinition.loopDefinitions.add()

                
                
        # #         edgeDefinitions = []
        # #         profileCurve : adsk.fusion.ProfileCurve
        # #         for profileCurve in loop.profileCurves:
                    
        # #             # in order to make edgeDefinitions, we need to have vertexDefinitions.
        # #             # There is no good way to construct all the vertexDefinitions (in general) because
        # #             # we some of our vertexDefinitions might need to correspond to the intersection of sketch curves, rather
        # #             # than their endpoints.
        # #             # therefore, we will have to generate a temporary body by means of TemporaryBrepManager::createWireFromCurves() and 
        # #             #  TemporaryBrepManager::createFaceFromPlanarWires()


                    
        # #             edgeDefinition = bRepBodyDefinition.createEdgeDefinitionByCurve(
        # #                 startVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.startVertex.tempId],
        # #                 endVertex= sourceVertexTempIdsToDestinationVertexDefinitions[sourceEdge.endVertex.tempId],
        # #                 modelSpaceCurve=profileCurve.geometry
        # #             )
                    
        # #             edgeDefinitions.append(
        # #                 profileCurve.
        # #             )


        # #         for coEdgeLikeThing in collectionOfSuchThings:
        # #             bRepCoEdgeDefinition = bRepLoopDefinition.bRepCoEdgeDefinitions.add(
        # #                 edgeDefinition= , #construct an edgeDefinition object corresponding to coEdgeLikeThing
        # #                 isOpposedToEdge= # Set the isOpposedToEdge property according to some property of coEdgeLikeThing
        # #             )

        # #     bodies.append(bRepBodyDefinition.createBody())  
    
    # It seems to be prohibitively difficult to construct the bodies "from
    ## scratch" by extracting the primitive geometry from the profiles (because
    ## adsk.fusion.Profile doesn't quite expose enough of the underlying geometry
    ## to reliably handle all cases (for instance: vertices that are formed by
    ## the intersection of two sketch curves, not on the endpoints of the curve.)
    ## Therefore, we will do some fusion feature (probably, Extrude.  could
    ## possibly also use a Patch feature) that takes sketch profiles as input,
    ## and extract the needed geometry from the resultant bodies.

    ## SECOND ATTEMPT -- do a single Extrude feature and pass the collection of profiles as input.
    # foiled due to the fact that the fusion extrude feature 
    # automatically merges adjacent profiles, 
    # but we want to preserve the profiles as is.
        # # extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
        # #     profile= fscad._collection_of(sketch.profiles),
        # #     distance = adsk.core.ValueInput.createByReal(1),
        # #     operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        # # )
        # # bodies += [
        # #     fscad.brep().copy(face)
        # #     for face in extrudeFeature.startFaces
        # # ]


    ## THIRD ATTEMPT -- do one Extrude feature for each profile and each SketchText.
    profile : Union[adsk.fusion.Profile, adsk.fusion.SketchText]
    # Besides SketchText objects and Profile objects, are there any other profile-like objects
    # that can be contained in a sketch that we should think about handling?
    for profile in itertools.chain(sketch.profiles, sketch.sketchTexts): 
        # this extrude feature throws an exception in the case where profile is
        # a sketchtext such that profile.text == '', or even where profile.text
        # == ' ' (i.e. cases where the sketch text does not produce any "ink").
        # Precisely what is wrong with extruding an empty region?  It simply
        # yields an empty body. There's nothing ambiguous or problematic about
        # it. This seems to me no reason for the software to get all hoo-hooed.
        # how can we handle this situation gracefully.  Obviously, the correct
        # outcome is to add no items to bodies on this pass through the loop.
        # the question is not so much how to handle  the situation -- that's
        # easy - just don't attempt the extrusion operation and don't add
        # anything to bodies. the real question is how do we detect an "empty"
        # (i.e. zero ink) sketch-text. options:
        # - try the extrusion and look for exceptions.  The problem is that I am
        #   not sure this is a very specific test (although it is sensitive).
        # - inspect profile.boundingBox.  Unfortunately, in the case of a zero
        #   ink sketch text, the bounding box does not have any zero dimensions
        #   (small - 10 microns, perhaps, but not reliably zero)
        # - inspect len(profile.asCurves() ) (winner)
        
        if isinstance(profile, adsk.fusion.SketchText) and len(profile.asCurves()) == 0: continue
        
        extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
            profile= profile,
            distance = adsk.core.ValueInput.createByReal(-1),
            # it is important that this be negative 1 so that the faces have normals 
            # pointing in the same direction as the sketch's normal.
            operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        


        bodies += [
            fscad.brep().copy(face)
            for face in extrudeFeature.startFaces
        ]
        # In the case where profile is a single SketchProfile, I expect that
        # extrudeFeature.startFaces will always have just one face.  However,
        # this will not generally be true for the case where profile is a
        # SketchText. 
        
        extrudeFeature.deleteMe()


    return bodies


def getAllSheetBodiesFromSketchGroupedByRank(sketch : adsk.fusion.Sketch) -> Sequence[Sequence[adsk.fusion.BRepBody]]:
    """ returns a sequence of sequence BRepBody, containing (collectively) one
    member for each member of sketch.profiles and sheet bodies corresponding to
    the sketch texts. each body is a sheet body having exactly one face.
    returnValue[i] contains precisely the sheets of rank i. Inasmuch as the
    rank-finding algorithm relies on Fusion's ability to give us non-overlapping
    profiles, the logic herein might break down in the case of sketchtext
    objects combined with other skethc geometry, because Fusion deals with the
    profiles corresponding to the sketchtext as separate from the profiles
    corresponding to all non-sketchtext geometry. 
    For now, we might just neglect sketchtext altogether.
    """

    # the below algorithm is NOT the most efficient, because it does not make use
    # of Fusion's automatic built-in plane-partitioning.  Fusion has already figured out the
    # topology of the regions in the sketch - I merely need to query Fusion's graph.

    bodies = []

    profileIndicesGroupedByRank : Sequence[Sequence[int]] = []
    # profilesGroupedByRank : Sequence[Sequence[adsk.fusion.Profile]] = []

    ## do one Extrude feature for each profile and each SketchText.
    r : int = 0
    profiles : Sequence[adsk.fusion.Profile] = list(sketch.profiles)
    sheetBodies : Sequence[Sequence[adsk.fusion.BRepBody]] = []
    outerBrepLoops : Sequence[Sequence[adsk.fusion.BRepLoop]] = []
    innerBrepLoops : Sequence[Sequence[adsk.fusion.BRepLoop]] = []
    # we are going to deal in sequences of sheetBodies rather than sheetBodies
    # to handle cases where the sheetBodies are disjoint (which we shouldn't get due
    # to fusion's abbhorence of disjoint bodies, but nevertheless seems prudent)

    # the indices in profiles correspond with the indices in sheetBodies
    # # and with the indices in outerLoops;
    # sheetBodies[i] is the (tuple of) sheet body generated by profiles[i].
    # outerLoops[i] is the (tuple of) outer BRepLoops of the faces of the bodies in sheetBodies[i].
    # innerLoops[i] is the (tuple of) inner BRepLoops of the faces of the bodies in sheetBodies[i].
    # our categorizing operation will work with indices.

    for profile in profiles:
        extrudeFeature = sketch.parentComponent.features.extrudeFeatures.addSimple(
            profile= profile,
            distance = adsk.core.ValueInput.createByReal(-1),
            # it is important that this be negative 1 so that the faces have normals 
            # pointing in the same direction as the sketch's normal.
            operation = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        )
        bodies = tuple(
            fscad.brep().copy(face)
            for face in extrudeFeature.startFaces
        )
        innerBrepLoopsOfFacesOfBodies : Sequence[adsk.fusion.BRepLoop] = tuple(
            brepLoop 
            for body in bodies
            for face in body.faces
            for brepLoop in face.loops
            if not brepLoop.isOuter
        )
        outerBrepLoopsOfFacesOfBodies : Sequence[adsk.fusion.BRepLoop] = tuple(
            brepLoop 
            for body in bodies
            for face in body.faces
            for brepLoop in face.loops
            if brepLoop.isOuter
        )
        sheetBodies.append(bodies)
        innerBrepLoops.append(innerBrepLoopsOfFacesOfBodies)
        outerBrepLoops.append(outerBrepLoopsOfFacesOfBodies)
        # I expect that extrudeFeature.startFaces will always have just one
        # face, but I am dealing in a sequence of bodies rather than a single
        # body just to cover all possibilities.
        
        extrudeFeature.deleteMe()

    
    maxrank=100 
    #maxrank is mainly to prevent ridiculous runaways during debugging

    remainingProfileIndices = set(range(len(profiles)))

    while remainingProfileIndices and r <= maxrank:
        # find the set of profiles p such that the outer loop of p does not 
        # coincide (except perhaps by osculation)
        # with any of the inner loops of any of the other profiles.
        # this is the set of rank r profiles.  Move these profiles out of remainingProfiles
        # and deposit them in profilesGroupedByRank[r].
        profileIndicesOfRankR = set()
        candidateProfileIndex : int
        for candidateProfileIndex in remainingProfileIndices:
            candidateProfile = profiles[candidateProfileIndex]
            candidateSheetBodies = sheetBodies[candidateProfileIndex]
            outerBrepLoopsOfCandidateSheetBodies = outerBrepLoops[candidateProfileIndex]
            innerBrepLoopsOfCandidateSheetBodies = innerBrepLoops[candidateProfileIndex]
            outerEdgesOfCandidateSheetBodies = tuple(
                edge
                for brepLoop in outerBrepLoops[candidateProfileIndex]
                for edge in brepLoop.edges
            )
            innerEdgesOfCandidateSheetBodies = tuple(
                edge
                for brepLoop in innerBrepLoops[candidateProfileIndex]
                for edge in brepLoop.edges
            )


            outerLoopOfCandidateProfileCoincidesWithAnInnerLoopOfSomeOtherProfile : bool = False
            # we assume, as a hypothesis to be disproven, that
            # outerLoopOfCandidateProfile has no coincidence with any of the
            # inner loops of any other profile.

            # outerLoopOfCandidateProfile : adsk.fusion.ProfileLoop = next(filter(lambda profileLoop: profileLoop.isOuter, candidateProfile.profileLoops))
            # # we are counting on Fusion's promise that each profile will have
            # # exactly one outer loop. look through the inner loops of all other
            # # profiles in remainingProfiles.  if outerLoopOfCandidateProfile
            # # coincides (in the appropriate sense) with any of the inner loops,
            # # then we know it is not a rank r profile.  If it coincides with
            # # none, than we know it is.
            #
            # innerLoop : adsk.fusion.ProfileLoop
            # for innerLoop in (
            #     profileLoop
            #     for i in remainingProfileIndices 
            #     for profileLoop in profiles[i].profileLoops
            #     if (
            #         (not profileLoop.isOuter) 
            #         and (i != candidateProfileIndex) 
            #         # and (i not in profileIndicesOfRankR)
            #     )
            # ):
            #     # for our purposes, we can consider two profileLoops to be
            #     # coincident when, and only when, the intersection of the set of
            #     # sketchEntities of profileCurves of loops A and B,
            #     # respectively, is non-empty. ( actually NO -- this doesn't
            #     # quite do it in all cases. )
            #     if fscad._find_coincident_edges_on_body(
            #         body=
            #     ):
            #         outerLoopOfCandidateProfileCoincidesWithAnInnerLoopOfSomeOtherProfile = True
            #         break
            
            otherSheetBody : adsk.fusion.BrepBody
            for otherSheetBody in (
                body
                for i in remainingProfileIndices
                for body in sheetBodies[i] 
                if (
                    (i != candidateProfileIndex)
                    # and (i not in profileIndicesOfRankR)
                )
            ):
                if fscad._find_coincident_edges_on_body(
                    body=otherSheetBody,
                    selectors=outerEdgesOfCandidateSheetBodies
                ):
                    #note we are actually searching all edges of the other sheet bodies rather
                    # than only the inner edges of the other sheet bodies, but that should suffice
                    #  for our purposes.
                    # This whole searching process could probably be greatly optimized.
                    outerLoopOfCandidateProfileCoincidesWithAnInnerLoopOfSomeOtherProfile = True
                    break


            if not outerLoopOfCandidateProfileCoincidesWithAnInnerLoopOfSomeOtherProfile:
                profileIndicesOfRankR.add(candidateProfileIndex)
        # remainingProfileIndices = [
        #     i for i in remainingProfileIndices 
        #     if i not in profileIndicesOfRankR
        # ]
        remainingProfileIndices -= profileIndicesOfRankR
        profileIndicesGroupedByRank.append(profileIndicesOfRankR)
        r += 1 
    
    
    sheetBodiesGroupedByRank : Sequence[Sequence[adsk.fusion.BRepBody]] = tuple(
        tuple( 
            sheetBody  
            for i in profileIndicesGroupedByRank[r] 
            for sheetBody in sheetBodies[i]  
        )
        for r in range(len(profileIndicesGroupedByRank))
    )

    return sheetBodiesGroupedByRank

def getAllSheetBodiesFromSvgGroupedByRank(pathOfSVGFile, 
    svgNativeLengthUnit : float = 1 * millimeter,
    transform : Optional[adsk.core.Matrix3D] = None
) -> Sequence[Sequence[adsk.fusion.BRepBody]]:
    
    #
    # Fusion seems to be looking at the current pixel size (i.e. dependent
    # on the computer monitor and display settings currently in use,
    # perhaps) in order to decide what the svg native unit means (see
    # https://knowledge.autodesk.com/support/fusion-360/troubleshooting/caas/sfdcarticles/sfdcarticles/SVG-file-imports-with-a-wrong-scale-into-Fusion-360.html).
    # This seems ass-backward to me; choose an interpretation and stick with
    # it, but perhaps the svg format does not, in its standard incarnation,
    # specify the physical meaning of the native units in the svg file.  At
    # the moment in my tests, I am observing that fusion interprets the svg
    # native unit to mean about 0.0264583 centimeters, which is very nearly
    # (and, internally nominally, probably exactly) 96 svg units per inch.
    # This is a common dpi for monitors. I am not sure if there is anything
    # Fusion is picking up from my particular operating-system settings to
    # arrive at this "96" number -- Fusion might be making a blind
    # hard-coded assumption (which would, in my opinion, be preferrable to
    # Fusion dynamically deciding on the meaning of native SVG units based
    # on current monitor/operating-system-display settings.
    #
    # In the case of the svg files generated by Inkscape that I have
    # observed, Inkscape seems to ascribe a meaning of 1 millimeter to the
    # native SVG unit (regardless of the setting of the
    # "inkscape:document-units" or the "units" properties within the
    # "sodipodi:namedview" xml element in the svg file), but it is not
    # obvious to me how widely this assumption applies -- does the SVG
    # standard specify that the native SVG length unit means 1 millimeter,
    # or provide a standard way to specify such a meaning within the svg
    # file?  At any rate, for my purposes here, it suffices to assume that
    # the native SVG length unit is 1 millimeter.
    #
    
    nativeSVGLengthUnitAssumedByFusion = (1/96) * inch
    pathOfSVGFile = pathlib.Path(pathOfSVGFile).resolve()
    tempOccurrence = rootComponent().occurrences.addNewComponent(adsk.core.Matrix3D.create())
    mainTempComponent = tempOccurrence.component
    mainTempComponent.name = "getAllSheetBodiesFromSvgGroupedByRank-mainTempComponent"
    sketch = mainTempComponent.sketches.add(mainTempComponent.xYConstructionPlane)
    sketch.importSVG(
        pathOfSVGFile.as_posix(),
        scale =  svgNativeLengthUnit/nativeSVGLengthUnitAssumedByFusion, 
        xPosition= 0, 
        yPosition= 0
    )
    # the xPosition and yPosition arguments to Sketch::importSVG() seem to have no effect.
    timestamps : List[float] = []
    timestamps.append(time.time())
    allSheetBodiesFromSketchGroupedByRank = getAllSheetBodiesFromSketchGroupedByRank(sketch)
    timestamps.append(time.time())
    print(f"time to to get all sheet bodies from sketch: {timestamps[-1] - timestamps[-2]} seconds.")
    tempOccurrence.deleteMe()
    if transform is not None:
        for sheetBodyRankGroup in allSheetBodiesFromSketchGroupedByRank:
            for sheetBody in sheetBodyRankGroup:
                result : bool = temporaryBRepManager().transform(sheetBody, transform); assert result
    return allSheetBodiesFromSketchGroupedByRank

def captureEntityTokens(occurrence : adsk.fusion.Occurrence):
    return {
        'occurrence': occurrence.entityToken,
        'component': occurrence.component.entityToken,
        'bodies' : [
            {
                'body'  : body.entityToken,
                'faces' : [face.entityToken for face in body.faces],
                'edges' : [edge.entityToken for edge in body.edges]
            }
            for body in occurrence.bRepBodies
        ]
    }
 
def translation(v: VectorLike) -> adsk.core.Matrix3D:
    # this is a convenience function that encapsulates the annoyance
    # of having to create the matrix, then assign its translation in twq separate steps.
    t : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    # result :bool = t.setWithCoordinateSystem(
    #     origin= castToPoint3D(v),
    #     xAxis = adsk.core.Vector3D.create(1,0,0),
    #     yAxis = adsk.core.Vector3D.create(0,1,0),
    #     zAxis = adsk.core.Vector3D.create(0,0,1),
    # ); assert result
    t.translation = castToVector3D(v)
    return t

def rotation(
    angle : float,
    axis: VectorLike = (0,0,1),
    origin: VectorLike = (0,0,0)
) -> adsk.core.Matrix3D:
    # a convenience function to make it easier to use the fusion Matrix3D class
    t : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    result :bool = t.setToRotation(
        angle= angle,
        axis = castToVector3D(axis),
        origin = castToPoint3D(origin)
    ); assert result
    return t

def rigidTransform3D(
    xDirection : Optional[VectorLike] = None, 
    yDirection : Optional[VectorLike] = None, 
    zDirection : Optional[VectorLike] = None, 
    origin : Optional[VectorLike] = None 
) -> adsk.core.Matrix3D :
    '''this is a factory for producing an adsk.core.Matrix3D that is guaranteed
    to be a rigid transform . This function is flexible (no pun intended) in the
    combination of basis directions that can be specified.  
    You are free to omit the origin, in which case we will assume (0,0,0). Only
    the direction, not the magnitude, of the direction arguments is meaningful.
    If you give all three direction vectors, only two of them are taken into
    account -- the third is ignored. If you give two direction vectors, the
    missing third is constructed according to the right-hand rule. If you give
    one direction vector, you have not fully specified the transform, but we
    will choose an arbitrary perpendicular vector to serve as one of the missing
    direction vectors.


    This function is an imporvement on the built-in factory-function,
    adsk.core.Matrix3D.create(), in that the built-in function does not
    guarantee to return a rigid transform, and the built-in function requires
    all three basis directions to specified, which is redundant when the
    transform is assumed to be rigid (which means the basis directions will be
    mutually pairwise perpendicular).  The built-in factory function is geared
    towards specifying arbitrary values for all of the top 3 rows of the 4x4
    matrix, whereas for our factory function, the upper-left 3x3 submatrix,
    being a rigid rotation, represents only 3 degrees of freedom, not 9.
    '''

    if origin is None: 
        origin=adsk.core.Point3D.create(0,0,0)
    else:
        origin = castToPoint3D(origin)
    

    # to form the rotational part of the transform, take the first two non-None direction vectors.
    givenDirections = [xDirection, yDirection, zDirection]
    # indicesOfNoneDirections = tuple(i for  i, x in enumerate(givenDirections) if x is None)
    # indicesOfNonNoneDirections = tuple(i for  i, x in enumerate(givenDirections) if x is not None)
    
    indicesOfNoneDirections : Sequence[int] = []
    indicesOfNonNoneDirections : Sequence[int] = [] 
    basisVectors : Sequence[Optional[adsk.core.Vector3D]] = []
    for i in range(len(givenDirections)):
        if (
            (givenDirections[i] is None )
            or 
            (len(indicesOfNonNoneDirections) == 2)
            #this ensures that we ignore the third slot in the case
            # that the first two slots were non-None.
        ):
            # the 
            indicesOfNoneDirections.append(i)
            thisVectorAsOptionalVector3D = None
        else:
            indicesOfNonNoneDirections.append(i)
            thisVectorAsOptionalVector3D = castToVector3D(givenDirections[i])
        basisVectors.append(thisVectorAsOptionalVector3D)

    numberOfNoneDirections = len(indicesOfNoneDirections)
    # numberOfNoneDirections will be 1,2, or 3 -- it is guaranteed not to be 0
    # due to our discarding of the third slot if the first two slots are
    # occupied, above.



    if numberOfNoneDirections == 1:
        #fill in the "empty" slot:
        indexOfTheEmptySlot = indicesOfNoneDirections[0]
        indexOfTheFirstNonEmptySlot = indicesOfNonNoneDirections[0]
        indexOfTheSecondNonEmptySlot = indicesOfNonNoneDirections[1]
        #------------------------------------------------------------------------------------------------------
        #  cases:            ||  derived quantities:
        #  ------------------||-----------------------------------------------------------------------------
        #                    ||  indicesOfNonNoneDirections  | fill the       |  then, redefine the second 
        #                    ||                              | empty slot     |  originally-nonempty slot 
        #  indexOfEmptySlot  ||                              |                |  to ensure perpendicularity (if needed)
        # -------------------||------------------------------|----------------|-----------------------------
        #  0                 ||  1,2                         | v0 := v1 X v2  |  v2 := v0 X v1
        #  1                 ||  0,2                         | v1 := v2 X v0  |  v2 := v0 X v1
        #  2                 ||  0,1                         | v2 := v0 X v1  |  v1 := v2 X v0

        basisVectors[indexOfTheEmptySlot] = (
                basisVectors[ (indexOfTheEmptySlot + 1) % 3 ].crossProduct(
                    basisVectors[(indexOfTheEmptySlot + 2) % 3 ]
                )
            )    
        
        if not basisVectors[indexOfTheFirstNonEmptySlot].isPerpendicularTo(basisVectors[indexOfTheSecondNonEmptySlot]):
            warnings.warn("rigidTransform3D has received two non-perpendicular vectors as arguments -- we are coercing the result to be fully perpendicular.") 
            basisVectors[indexOfTheSecondNonEmptySlot] = (
                    basisVectors[ (indexOfTheSecondNonEmptySlot + 1) % 3 ].crossProduct(
                        basisVectors[(indexOfTheSecondNonEmptySlot + 2) % 3 ]
                    )
                )    
        # we might want to force (or at least verify) that vectors in the two slots are perpendicular to one another.
    elif numberOfNoneDirections == 2:
        raise Exception(" rigidTransform3D()'s ability to construct a transform based on only a single direction basis vector has not yet been implemented.")
        pass
        #todo: pick an arbitrary vector perpendicular to the one given vector.
        #if we get here, it means that numberOfNoneDirections is 1, 2, or 3
        # if numberOfNoneDirections == 1:
        #     indicesOfDirectionsToOverwrite = list(indicesOfNoneDirections)
        #     givenDirections[indicesOfNoneDirections[0]] = 
        # elif numberOfNoneDirections == 2:
        #     indicesOfDirectionsToOverwrite = list(indicesOfNoneDirections)
        # else: # elif numberOfNoneDirections == 3:
        #     givenDirections[0] = xHat
        #     givenDirections[1] = yHat
        #     givenDirections[2] = zHat

    for x in basisVectors: x.normalize()
    returnValue : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    returnValue.setWithCoordinateSystem(origin, *basisVectors)
    return returnValue


def evExtremeSkewerPointsOfBodies(*bodies : adsk.fusion.BRepBody,  axis: adsk.core.InfiniteLine3D) -> Tuple[adsk.core.Point3D]:
    """ returns a tuple of Point3D representing the minimum and maximum points,
    respectively, along axis, of the intersection of bodies with the axis.  If
    the axis does not intersect any of the bodies, then the returned tuple is
    empty """
    # strategy: iterate through all faces of all bodies in bodies.  For each,
    # compute the intersection point(s) of that face with axis,
    # axis.intersectWithSurface(face.geometry), and then using
    # face.evaluator.isParameterOnFace() to pick out only those intersection
    # points that are actually on the face.  Then, of all the intersection
    # points, find the minimum and maximum with respect to the direction of
    # axis.
    intersectionPoints : Sequence[adsk.core.Point3D] = []
    bodyIndex = 0
    for body in bodies:
        face : adsk.fusion.BRepFace
        faceIndex = 0
        for face in body.faces:
            candidateIntersectionPoint : adsk.core.Point3D
            for candidateIntersectionPoint in axis.intersectWithSurface(face.geometry):
                # print(f"bodyIndex: {bodyIndex}, faceIndex: {faceIndex}, " + 'type(candidateIntersectionPoint): ' + str(type(candidateIntersectionPoint)))
                if face.evaluator.isParameterOnFace(face.evaluator.getParameterAtPoint(candidateIntersectionPoint)[1]):
                    intersectionPoints.append(candidateIntersectionPoint)
                    # print("is on face")
            faceIndex += 1
        bodyIndex += 1
    if len(intersectionPoints) == 0:
        return tuple()
    else:
        intersectionPoints.sort(key= lambda p: p.asVector().dotProduct(axis.direction))
        return (intersectionPoints[0], intersectionPoints[-1])


def toProperFractionString(x: SupportsFloat, denominator : int) -> str:
    denominator = abs(denominator)   
    numerator : int = round(x*denominator)
    # gcd : int = greatestCommonDivisor(numerator, denominator)
    gcd : int = np.gcd(numerator, denominator)
    # print(f"{type(numerator)}, {type(denominator)}, {type(gcd)}")
    numerator = int( numerator / gcd )
    denominator = int( denominator / gcd )

    # print(f"{type(numerator)}, {type(denominator)}")
    returnValue = f"{numerator}/{denominator}"

    # attempt to convert returnValue to one of the special unicode codepoints for fractions:
    returnValue = {
        "1/9"  : "\u2151",
        "1/10" : "\u2152",
        "1/3"  : "\u2153",
        "2/3"  : "\u2154",
        "1/5"  : "\u2155",
        "2/5"  : "\u2156",
        "3/5"  : "\u2157",
        "4/5"  : "\u2158",
        "1/6"  : "\u2159",
        "5/6"  : "\u215a",
        "1/8"  : "\u215b",
        "3/8"  : "\u215c",
        "5/8"  : "\u215d",
        "7/8"  : "\u215e",
        "1/4"  : "\u00bc",
        "1/2"  : "\u00bd",
        "3/4"  : "\u00be",
    }.get(returnValue, returnValue)

    return returnValue


# def extremeBoundPointsOfBodies(*bodies : adsk.fusion.BRepBody,  direction: adsk.core.Vector3D) -> Tuple[adsk.core.Point3D]:
#     pass


def import_step_file(pathOfFileToImport : str, name : str ="import") -> fscad.Component:
    """Imports the given step file as a new Component

    Args:
        pathOfFileToImport: The path of the step file to be imported
        name: The name of the component

    Returns: A new Component containing the contents of the imported file.
    """
    # import_options = app().importManager.createFusionArchiveImportOptions(filename)
    import_options = app().importManager.createSTEPImportOptions(pathOfFileToImport)
    document = app().importManager.importToNewDocument(import_options)
    imported_root = document.products[0].rootComponent

    bodies = []

    for body in imported_root.bRepBodies:
        bodies.append(fscad.brep().copy(body))
    for occurrence in imported_root.allOccurrences:
        for body in occurrence.bRepBodies:
            bodies.append(fscad.brep().copy(body))

    document.close(saveChanges=False)

    return fscad.BRepComponent(*bodies, name=name)

from .highlight import *
def changeSurfaceOfSheetBody(
    sheetBody : adsk.fusion.BRepBody, 
    # destinationSurface : adsk.core.Surface, 
    destinationFace : adsk.fusion.BRepFace 
    # we are doing destiantion face instead of destination surface in order to
    # be able to have a bounded surface evaluator
    # (adsk.fusion.BRepFace::evaluator is a bounded evaluator whereas
    # adsk.core.Surface::evaluator can be unbounded.) we assume sheetBody lies
    # on the xy plane, and we are pretending that the parameter space of the
    # sheetBody's face(s) is the xy plane rather than the weird scaled,
    # translated transform that fusion seems to use internally (and
    # counterintuitvely) for planes (I think that internall in Fusion, a plane
    # (and probably any surface), carries along a transform, but that the API
    # DOES NOT EXPOSE this transform (at least not directly), which means we
    # have to go to great lengths to re-compute the hidden transform (that's
    # what planeParameterSpaceToModelSpaceTransform() is all about) that the API
    # really ought to expose in the first place.

) -> Optional[adsk.fusion.BRepBody]:
    """
        sheetBody is assumed to consist of one or more faces all having the same
        underlying surface. We return a new sheet body wherein the surface has
        been replaced with destinationSurface (but all the curves and vertices
        are the same in the parameter space of the surface.
    """
    destinationSurface : adsk.core.Surface = destinationFace.geometry
    destinationSurfaceEvaluator : adsk.core.SurfaceEvaluator = destinationFace.evaluator
    # destinationSurfaceEvaluator : adsk.core.SurfaceEvaluator = destinationSurface.evaluator

    bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()
    
    


    vertexDefinitions : Sequence[adsk.fusion.BRepVertexDefinition] = []
    vertex : adsk.fusion.BRepVertex
    for vertex in sheetBody.vertices:
        # compute/construct transformedPosition
        transformedPosition : adsk.core.Point3D
        
        # identify a face, a loop, a coEdge, and an edge such that vertex is
        # used by edge, which is used by coEdge, which belongs to loop,
        # which belongs to face.
        face : adsk.fusion.BRepFace
        loop : adsk.fusion.BRepLoop
        coEdge : adsk.fusion.BRepCoEdge
        edge : adsk.fusion.BRepEdge

        edge = vertex.edges[0]
        coEdge = edge.coEdges[0]
        brepLoop = coEdge.loop
        face = brepLoop.face
        
        # pToM = planeParameterSpaceToModelSpaceTransform(face.geometry)
        pToM = planeParameterSpaceToModelSpaceTransform(face)
        # it is vitally important that we pass face and not face.geometry to
        # planeParameterSpaceToModelSpaceTransform() because, as is discussed in
        # the comments in  planeParameterSpaceToModelSpaceTransform(), we cannot
        # generally trust that face.evaluator() will represent the same
        # transform as face.geometry.evalutor()

        #We are now, and in the use of pToM below, very definitely assuming that
        # the surface lies on the xy plane.
        result : bool
        parameter : adsk.core.Point2D
        # result, parameter = face.geometry.evaluator.getParameterAtPoint(vertex.geometry)
        result, parameter = face.evaluator.getParameterAtPoint(vertex.geometry); assert result
        #actually, I think face.evaluator and     face.geometry.evaluator will work equally well for doing the parametrAtPoint() operation.
        parameterPrime = parameter.copy(); result = parameterPrime.transformBy(castToMatrix2D(pToM)); assert result
        # parameterPrime is what parameter would be if Fusion parameterized planes "correctly" (i.e. no scaling).

        result, transformedPosition = destinationSurfaceEvaluator.getPointAtParameter(parameterPrime); assert result
        vertexDefinitions.append(bRepBodyDefinition.createVertexDefinition(position=transformedPosition))

    edgeDefinitions : Sequence[adsk.fusion.BRepEdgeDefinition] = []
    edge : adsk.fusion.BRepEdge
    for edge in sheetBody.edges:
        coEdge : adsk.fusion.BRepCoEdge
        coEdge = edge.coEdges[0]
        coEdge.geometry
        # result : Sequence[adsk.core.Curve3D] 
        # pToM = planeParameterSpaceToModelSpaceTransform(coEdge.loop.face.geometry)
        pToM = planeParameterSpaceToModelSpaceTransform(coEdge.loop.face)
        # it is vitally important that we pass face and not face.geometry to
        # planeParameterSpaceToModelSpaceTransform() because, as is discussed in
        # the comments in  planeParameterSpaceToModelSpaceTransform(), we cannot
        # generally trust that face.evaluator() will represent the same
        # transform as face.geometry.evalutor()

        parameterCurve : adsk.core.Curve2D = coEdge.geometry
        # primedParameterCurve = parameterCurve.copy()
        # oops, Curve2D does not have a copy() method, nor any other obvious way to clone it,
        # and yet Curve2D's transform() method is mutating.  Damn you, Fusion.
        primedParameterCurve : adsk.core.Curve2D = coEdge.geometry
        assert primedParameterCurve is not parameterCurve
        # hopefully we get a fresh anonymous Curve2D every time we call coEdge.geometry
        result = primedParameterCurve.transformBy(castToMatrix2D(pToM)); assert result
        
        
        result : adsk.core.ObjectCollection = destinationSurfaceEvaluator.getModelCurveFromParametricCurve(   primedParameterCurve   )
        if not (result.count == 1 and isinstance(result[0], adsk.core.Curve3D)):
            print(f"oops, result.count is {result.count} and isinstance(result[0], adsk.core.Curve3D) is {isinstance(result[0], adsk.core.Curve3D)}")
            assert False
        assert result.count == 1 and isinstance(result[0], adsk.core.Curve3D)
        # god help us if result does not contain exactly one curve3D object.
        transformedCurve3D : adsk.core.Curve3D = result[0]

        # print(f"edge {_edge_index_within_body(edge)}: isParamReversed: {edge.isParamReversed}.  isTolerant: {edge.isTolerant}")
        edgeDefinitions.append(
            bRepBodyDefinition.createEdgeDefinitionByCurve(
                startVertex = vertexDefinitions[_vertex_index_within_body(edge.startVertex)],
                endVertex = vertexDefinitions[_vertex_index_within_body(edge.endVertex)],
                modelSpaceCurve = transformedCurve3D,
            )
        )


    lump : adsk.fusion.BRepLump
    indexOfLumpWithinBody = 0
    for lump in sheetBody.lumps:
        lumpDefinition : adsk.fusion.BRepLumpDefinition = bRepBodyDefinition.lumpDefinitions.add()
        shell : adsk.fusion.BRepShell
        indexOfShellWithinLump = 0
        for shell in lump.shells:
            shellDefinition : adsk.fusion.BRepShellDefinition = lumpDefinition.shellDefinitions.add()
            face : adsk.fusion.BRepFace
            indexOfFaceWithinShell = 0
            for face in shell.faces:
                faceDefinition : adsk.fusion.BRepFaceDefinition = shellDefinition.faceDefinitions.add(
                    surfaceGeometry = destinationSurface, 
                    isParamReversed = face.isParamReversed
                )
                loop : adsk.fusion.BRepLoop
                indexOfLoopWithinFace = 0
                for loop in face.loops:
                    loopDefinition : adsk.fusion.BRepLoopDefinition = faceDefinition.loopDefinitions.add()
                    coEdge : adsk.fusion.BRepCoEdge
                    indexOfCoedgeWithinLoop = 0
                    for coEdge in loop.coEdges:
                        coEdgeDefinition : adsk.fusion.BRepCoEdgeDefinition = loopDefinition.bRepCoEdgeDefinitions.add(
                            # edgeDefinition=edgeDefinitions[_edge_index_within_body(edge)],
                            ###  OOPS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  god damn it.  There went half a day, at least.
                            edgeDefinition=edgeDefinitions[_edge_index_within_body(coEdge.edge)],
                            isOpposedToEdge=coEdge.isOpposedToEdge
                        )
                        indexOfCoedgeWithinLoop += 1
                    indexOfLoopWithinFace += 1
                indexOfFaceWithinShell += 1
            indexOfShellWithinLump += 1
        indexOfLumpWithinBody += 1

    bRepBodyDefinition.doFullHealing = False
    morphedSheetBody : adsk.fusion.BRepBody = bRepBodyDefinition.createBody()
    
    # print(
    #     "bRepBodyDefinition.outcomeInfo: " 
    #     + "\n".join( 
    #         x
    #         for x in bRepBodyDefinition.outcomeInfo
    #     )
    # )
    
    ##region highlighting
    ## from .design1 import makeHighlightParams
    ##this is a temporary hack during debugging
    #for vertexDefinitionIndex, vertexDefinition in enumerate( vertexDefinitions ) :
    #    highlight(
    #        vertexDefinition.position,
    #        **makeHighlightParams(f"vertex definition {vertexDefinitionIndex}")
    #    )
    #  
    #for edgeDefinitionIndex, edgeDefinition in enumerate( edgeDefinitions ) :
    #    highlight(
    #        edgeDefinition.modelSpaceCurve,
    #        **makeHighlightParams(f"edge definition {edgeDefinitionIndex}")
    #    )
    ##endregion highlighting 


    if morphedSheetBody is None:
        print("oops. morphedSheetBody creation failed.")
    assert morphedSheetBody is not None

    return morphedSheetBody

def changeSurfaceOfSheetBodies(
    sheetBodies : Iterable[adsk.fusion.BRepBody], 
    # destinationSurface : adsk.core.Surface,
    destinationFace : adsk.fusion.BRepFace 
    # we are doing destiantion face instead of destination surface -- see
    # comment in changeSurfaceOfSheetBody() 
) -> Sequence[adsk.fusion.BRepBody]:
    returnValue : Sequence[adsk.fusion.BRepBody] = []
    sheetBody : adsk.fusion.BRepBody
    for sheetBody in sheetBodies:
        morphedSheetBody = changeSurfaceOfSheetBody(sheetBody, destinationFace)
        if morphedSheetBody is not None:
            returnValue.append(morphedSheetBody)
    return returnValue

def _edge_index_within_body(edge : adsk.fusion.BRepEdge) -> int:
    return fscad._edge_index(edge)

def _vertex_index_within_body(vertex: adsk.fusion.BRepVertex) -> int:
    for i, candidate_vertex in enumerate(vertex.body.vertices):
        if candidate_vertex == vertex:
            return i
    assert False
#=================================


def wrapSheetBodiesAroundCylinder(
    sheetBodies : Iterable[adsk.fusion.BRepBody], 
    cylinderOrigin :  VectorLike,    
    cylinderAxisDirection : VectorLike,
    wrappingRadius : float,
    rootRadius : Optional[float] = None
    # destinationFace : adsk.fusion.BRepFace 
    # we are doing destination face instead of destination surface -- see
    # comment in changeSurfaceOfSheetBody() 
) -> Sequence[adsk.fusion.BRepBody]:
    """
    The rootRadius is the radius of cylinder on which we perform a preliminary
    wrapping (so we imagine) of the sheetBodies in order to determine the
    geometry within (angle, length) space. We then draw the geometry on a
    cylinder of the specified radius such that the shapes in (angle, length)
    space are unaltered. In other words, we will stretch the geometry in one
    direction (that which corresponds to the cylinder's circumferential
    direction) by a factor of radius/rootRadius.
    """
    #region comments_and_discussion
    # this is very nearly the same as changeSurfaceOfSheetBodies, except that we
    # re-parameterize the bounded direction so that the result is as if the
    # range of the cylinder's bounded parameter were 2*Pi*radius, rather than
    # 2*Pi (which it seems, and which we assume, is always the range of the
    # bounded parameter of a cylinder
    #
    # we assume that all cylinders always exhibit the following behavior (i.e.
    # the u direction is unbounded in both directions and the p direction is
    # periodic with the principal interval being (-Pi, Pi) pRange :
    # adsk.core.BoundingBox2D = destinationSurface.evaluator.parametricRange()
    # uRange = (pRange.minPoint.x, pRange.maxPoint.x) vRange =
    # (pRange.minPoint.y, pRange.maxPoint.y) print(f"uRange: {uRange}\nvRange:
    # {vRange}")
    # #
    # # uRange: (0.0, 0.0)
    # # vRange: (-3.141592653589793, 3.141592653589793)
    # #
    # skewScalingTransform : adsk.core.Matrix3D = adsk.core.Matrix3D.create()
    #
    # for a bounded evaluator, the u parameter means radians (yes, that's right,
    # the parameter that controls the position along the axis of the cylinder is
    # ALSO in radians.
    #
    # for sheetBody in sheetBodies: result : result = fscad.brep().transform(
    #     body=fscad.brep().copy(sheetBody), transform=
    #     )
    # Based on the fact that the only method provided by fscad to achieve
    # non-uniform scaling relies on fusion features rather than the built-in
    # fusion function to transform by matrix3d, and also based on comments in
    # fscad to this effect, I am assuming that non-uniform scaling cannot
    # reliably be achieved by a simple transform by a Matrix3D.  (But it could
    # be that fscad wants to allow non-uniform scaling even when the transform
    # would be nonsingular (collapsing one of the dimensions to zero).  It may
    # be that simple transforming by Matrix3D works as long as the MAtrix3D is
    # singular.  At any rate, for now, I will do my nonuniform scaling in the
    # canoncial fscad way: by means of the fscad "Scale" class.
    #endregion comments_and_discussion

    cylinderLength = 20 * inch
    #TODO: compute the length intelligently.  We must ensure (I think) that the
    #length of the cylinder is longer than anything we want to wrap around it

    #TODO: allow the user to specify which direction in the sheetSpace will be
    # aligned with the axis of the cylinder and/or project the cylinder's axis
    # onto sheetSpace (in our case, the xy plane) to determine the alignment.
    

    cylinderForWrapping = cylinderByStartEndRadius(
        startPoint = castToPoint3D(castTo3dArray(cylinderOrigin) - castTo3dArray(cylinderAxisDirection) * cylinderLength/2),
        endPoint = castToPoint3D(castTo3dArray(cylinderOrigin) + castTo3dArray(cylinderAxisDirection) * cylinderLength/2),
        radius=wrappingRadius
    )

    # cylinderForWrapping.name = "cylinder for wrapping"
    # cylinderForWrapping.create_occurrence().isLightBulbOn = False
    
    destinationFace = cylinderForWrapping.side.brep
    destinationSurface : adsk.core.Surface = destinationFace.geometry
    assert destinationFace.geometry.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType


    # print(f"destinationSurface.evaluator.getParamAnomaly(): {destinationSurface.evaluator.getParamAnomaly()}")
    # pRange : adsk.core.BoundingBox2D = destinationSurface.evaluator.parametricRange()
    # uRange = (pRange.minPoint.x, pRange.maxPoint.x)
    # vRange = (pRange.minPoint.y, pRange.maxPoint.y)
    # print(f"uRange: {uRange}\nvRange: {vRange}")
    #
    # print(f"cylinderForWrapping.side.brep.evaluator.getParamAnomaly(): {cylinderForWrapping.side.brep.evaluator.getParamAnomaly()}")
    # pRange : adsk.core.BoundingBox2D = cylinderForWrapping.side.brep.evaluator.parametricRange()
    # uRange = (pRange.minPoint.x, pRange.maxPoint.x)
    # vRange = (pRange.minPoint.y, pRange.maxPoint.y)
    # print(f"uRange: {uRange}\nvRange: {vRange}")
    #
    # xRange = (supportFscadComponent.min().x, supportFscadComponent.max().x)
    # yRange = (supportFscadComponent.min().y, supportFscadComponent.max().y)



    unscaledSheetBodiesFscadComponent = fscad.BRepComponent(*sheetBodies)

    # scaledSheetBodiesFscadComponent = unscaledSheetBodiesFscadComponent.copy().scale(
    #         sx = 1/destinationSurface.radius,
    #         sy = 1/destinationSurface.radius,
    #         sz = 1/destinationSurface.radius,
    #     )

    scaledSheetBodiesFscadComponent = fscad.Scale(
            unscaledSheetBodiesFscadComponent,
            sx = 1/wrappingRadius,
            sy = 1/rootRadius,
            sz = 1/wrappingRadius,
        )


    scaledSheetBodies = (           
            fscadBody.brep
            for fscadBody in scaledSheetBodiesFscadComponent.bodies
        )

    # scaledSheetBodiesFscadComponent.name = "scaled sheet bodies"
    # scaledSheetBodiesFscadComponent.create_occurrence()

    # print(
    #     f"scaledSheetBodiesFscadComponent has "
    #     + f"xRange {(scaledSheetBodiesFscadComponent.min().x,scaledSheetBodiesFscadComponent.max().x)} "
    #     + f"and yRange {(scaledSheetBodiesFscadComponent.min().y,scaledSheetBodiesFscadComponent.max().y)}"
    # )

    return changeSurfaceOfSheetBodies(
        sheetBodies=scaledSheetBodies,
        destinationFace=destinationFace
    )




#==============================

# def planeParameterSpaceToModelSpaceTransform(plane : adsk.core.Plane) -> adsk.core.Matrix3D:
def planeParameterSpaceToModelSpaceTransform(arg : Union[adsk.core.Plane, adsk.core.SurfaceEvaluator, adsk.fusion.BRepFace] ) -> adsk.core.Matrix3D:
    
    planarSurfaceEvaluator : adsk.core.SurfaceEvaluator
    if isinstance(arg, adsk.core.Plane):
        planarSurfaceEvaluator = arg.evaluator
    elif isinstance(arg, adsk.core.SurfaceEvaluator):
        planarSurfaceEvaluator = arg
    elif isinstance(arg, adsk.fusion.BRepFace) and isinstance(arg.geometry, adsk.core.Plane):
        planarSurfaceEvaluator = arg.evaluator
    # elif isinstance(arg, adsk.fusion.BRepFace) and not isinstance(arg.geometry, adsk.core.Plane):
    #     planarSurfaceEvaluator = arg.evaluator
    #     # we are taking our chances here and hoping that the surface is close enough to a plane.
    else:
        raise TypeError(f" type(arg): {type(arg)}.   " + ( f"type(arg.geometry): {type(arg.geometry)}  "  if isinstance(arg, adsk.fusion.BRepFace) else "") )


    t : adsk.core.Matrix3D

    #in the following description, I imagine that all vectors are three-dimensional vectors (the 
    # Point2D and Vector2D objects are implicitly turned into 3D vectors by adding 0 as the third coordinate doing castTo3dArray()
    # and we think of 3d vectors of having a 4th parameter that (for our purposes here), is 0 for direction-like and 1 for position-like.
    # we want t to satisfy the following conditions:
    
    result, value = planarSurfaceEvaluator.getPointAtParameter(adsk.core.Point2D.create(0,0)); assert result
    root = castTo4dArray(value)
    # what a convoluted way of dealing with what is essentially an exception! --
    # have we no nullable objects? (we do have them) have we no first-class
    # Exceptions? (we do have them).  For Christ's sake, a function whose name
    # starts with "getPoint..." has no business returning anything other than a
    # point.
    #
    #  the above definition of root should be equivalent to doing root =
    # castTo4dArray(plane.origin)
    
    result, value = planarSurfaceEvaluator.getPointAtParameter(adsk.core.Point2D.create(1,0)); assert result
    a    = castTo4dArray(value)

    result, value = planarSurfaceEvaluator.getPointAtParameter(adsk.core.Point2D.create(0,1)); assert result
    b    = castTo4dArray(value)



    # t @ (1,0,0,0) == plane.evaluator.getPointAtParameter(1,0) - plane.origin == a - root
    # t @ (0,1,0,0) == plane.evaluator.getPointAtParameter(0,1) - plane.origin == b - root
    # t @ (0,0,1,0) == plane.evaluator.getPointAtParameter(0,1) - plane.origin == (a - root) X (b - root)  (where the cross product is done as if these were 3-dimensional directions (which they are)) (I am not concerned with scaling)
    # t @ (0,0,0,1) == plane.origin                                            == root
    #  And I think it is safe to assume that plane.origin is always equal to plane.evaluator.getPointAtParameter(0,0)
    
    # the reason that we need to take the surfaceEvaluator as opposed to a surface (from which we could get surface.evaluator) is
    # that, as I have discovered in my tests, at least in the case of planes,
    # the planeParameterSpaceToModelSpaceTransform generated by (probably internally, carried around as a property)
    # face.evaluator is NOT the same GENERALLY as face.geometry.evluator (I have observed scale differences).
    # The intended use for this planeParameterSpaceToModelSpaceTransform() function is to facilitate 
    # redefining a face with a different underlying surface (i.e. all parameter space geometry remains unaltered -- only the surface changes).
    # but the parameter space in which, for instance, coEdge.geometry (a 2d curve in the parameter space of the face) lives is that 
    # defined by face.evaluator (NOT necessarily the same as that defined by face.geometry.evaluator).

    column0 = a - root
    column1 = b - root
    column2 = castTo4dArray(np.cross(castTo3dArray(column0), castTo3dArray(column1)))
    column3 = root
    t = np.column_stack((column0, column1, column2, column3))

    # print(f"t: \n{t}")

    return castToMatrix3D(t)


def offsetSheetBodyUsingTheExtendTechnique(sheetBody : adsk.fusion.BRepBody, offset: float) -> Sequence[adsk.fusion.BRepBody]:
    # This function is intended to operate on planar sheet bodies (i.e. a BRepBody consisting of a single open face)

    # The strategy herein relies on Fusion's "Extend" feature which only works
    # with NON-NEGATIVE VALUES of OFFSET.  DAMNIT!  This is probably why fscad
    # resorts to using sketches to do offsetting.
    returnBodies : Sequence[adsk.fusion.BRepBody] = []
    # offsetedSheetBodies = tuple(
    #     fscadBody.brep
    #     for sheetBody in sheetBodies
    #     for face in fscad.BRepComponent(sheetBody).faces
    #     for fscadBody in fscad.OffsetEdges(face=face, edges=face.edges, offset = offset).bodies
    # )
    # unfortunately, fscad's OffsetEdges() class is not quite ready for prime time.

    tempOccurrence = fscad.root().occurrences.addNewComponent(adsk.core.Matrix3D.create())
    mainTempComponent = tempOccurrence.component
    mainTempComponent.name = "temp-offsetSheetBodyUsingTheExtendTechnique"

    sheetBodyPersisted : adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(sheetBody)

    extendFeatureInput : adsk.fusion.ExtendFeatureInput = mainTempComponent.features.extendFeatures.createInput(
        edges= fscad._collection_of(sheetBodyPersisted.edges),
        distance = adsk.core.ValueInput.createByReal(offset),
        extendType = adsk.fusion.SurfaceExtendTypes.NaturalSurfaceExtendType,
        isChainingEnabled = False
    )

    try:
        extendFeature : adsk.fusion.ExtendFeature = mainTempComponent.features.extendFeatures.add(extendFeatureInput)
    except Exception as e:
        print(f"In offsetSheetBodyUsingTheExtendTechnique (with offset {offset}), creation of the extrude feature failed with error: {e}")
    else:
        returnBodies.extend( temporaryBRepManager().copy(bRepBody) for bRepBody in extendFeature.bodies )

    tempOccurrence.deleteMe()
    return tuple(returnBodies)


def offsetSheetBodyUsingTheExtrusionTechnique(sheetBody : adsk.fusion.BRepBody, offset : float) -> Sequence[adsk.fusion.BRepBody]:
    returnBodies : Sequence[adsk.fusion.BRepBody] = []

    tempOccurrence = fscad.root().occurrences.addNewComponent(adsk.core.Matrix3D.create())
    mainTempComponent = tempOccurrence.component
    mainTempComponent.name = "temp-offsetSheetBodyUsingTheExtrusionTechnique"

    extrusionDistance = 1
    extrusionTaperAngle = math.atan(offset/extrusionDistance)

    print(f"extrusionDistance: {extrusionDistance}")
    print(f"extrusionTaperAngle: {extrusionTaperAngle}")

    sheetBodyPersisted : adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(sheetBody)
    

    extrudeFeatureInput : adsk.fusion.ExtrudeFeatureInput = mainTempComponent.features.extrudeFeatures.createInput(
        profile= fscad._collection_of(sheetBodyPersisted.faces), 
        operation= adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    

    result : bool = extrudeFeatureInput.setOneSideExtent(
        # extent = 
        adsk.fusion.DistanceExtentDefinition.create(distance= adsk.core.ValueInput.createByReal(extrusionDistance)),
        
        # direction = 
        adsk.fusion.ExtentDirections.PositiveExtentDirection ,
        
        # taperAngle = 
        adsk.core.ValueInput.createByReal(extrusionTaperAngle)
    ); assert result

    extrudeFeatureInput.startExtent = adsk.fusion.OffsetStartDefinition.create(offset=adsk.core.ValueInput.createByReal(-extrusionDistance))
    extrudeFeatureInput.isSolid = True


    try:
        extrudeFeature : adsk.fusion.ExtrudeFeature = mainTempComponent.features.extrudeFeatures.add(extrudeFeatureInput)
    except Exception as e:
        print(f"In offsetSheetBodyUsingTheExtrusionTechnique (with offset {offset}), creation of the extrude feature failed with error: {e}")
    else:
        assert extrudeFeature.endFaces.count == 1
        # at the moment, I am assuming that there is onle one end face (based on
        #the assumption that sheetBody only contianed one face). I am making
        #this assumption mainly because TemporaryBRepManager().copy() does not
        #provide a convenient way to copy multiple connected faces as a single
        #new body. This should be sufficient for the present application,
        #although a todo item is to handle the case where sheetBody contains
        #multiple faces (the extrude feature should handle multiple connected
        #faces just fine -- it's just a matter of collecting the end faces into
        #a single sheet body here below.
        returnBodies.append(temporaryBRepManager().copy(extrudeFeature.endFaces[0]))

    # tempOccurrence.deleteMe()
    return tuple(returnBodies)

#region abandoned_offset_function
# def offsetSheetBodyUsingTheSketchTechnique(sheetBody : adsk.fusion.BRepBody, offset : float) -> Sequence[adsk.fusion.BRepBody]:
#     returnBodies : Sequence[adsk.fusion.BRepBody] = []

#     tempOccurrence = fscad.root().occurrences.addNewComponent(adsk.core.Matrix3D.create())
#     mainTempComponent = tempOccurrence.component
#     mainTempComponent.name = "temp-offsetSheetBodyUsingTheExtrusionTechnique"

#     sheetBodyPersisted : adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(sheetBody)
    
#     sketchProfileLoopsDefiningOffsetLoops : list[adsk.fusion.ProfileLoop] = []
#     sheetBodiesDefiningOffsetLoops : list[adsk.fusion.ProfileLoop] = []
#     face : adsk.fusion.BRepFace = sheetBodyPersisted.faces[0]
#     loop : adsk.fusion.BRepLoop
#     for loop in face.loops:
#         sketch : adsk.fusion.Sketch = mainTempComponent.sketches.add(face)
#         edge : adsk.fusion.BRepEdge
#         sketchEntitiesBeforeOffsetting : list[adsk.fusion.SketchEntity] = []
#         for edge in loop.edges:
#             newSketchEntities = sketch.include(edge)
#             assert newSketchEntities.count != 0
#             sketchEntitiesBeforeOffsetting.extend(newSketchEntities)
#         offsetCurves : Sequence[adsk.fusion.SketchCurve] = sketch.offset(
#             # curves =fscad._collection_of(sketchEntitiesBeforeOffsetting),
#             curves = sketch.sketchCurves,
#             directionPoint = face.pointOnFace,
#             offset = - offset
#         )

#         # delete the original sketch curves:
#         for sketchEntity in sketchEntitiesBeforeOffsetting: 
#             result : bool = sketchEntity.deleteMe(); assert result
        
#         # at this point, the sketch should hafve exactly one profile, namely the offset curves.
#         assert sketch.profiles.count == 1
#         assert sketch.profiles[0].profileLoops.count == 1
#         sketchProfileLoopsDefiningOffsetLoops.append(sketch.profiles[0].profileLoops[0])
#         wireBody : adsk.fusion.BRepBody
#         result : bool
#         wireBody, result = temporaryBRepManager().createWireFromCurves
#         assert result

#     bRepBodyDefinition : adsk.fusion.BRepBodyDefinition = adsk.fusion.BRepBodyDefinition.create()

#     # tempOccurrence.deleteMe()
#     return tuple(returnBodies)
#endregion abandoned_offset_function        


def offsetSheetBodyUsingTheWireTechnique(
    sheetBody : adsk.fusion.BRepBody, 
    offset : float,
    offsetCornerType : Optional[adsk.fusion.OffsetCornerTypes] = None
) -> Sequence[adsk.fusion.BRepBody]:
    if offsetCornerType is None: offsetCornerType = adsk.fusion.OffsetCornerTypes.CircularOffsetCornerType
    
    returnBodies : Sequence[adsk.fusion.BRepBody] = []
    # print(f"offsetting with offset {offset}")
    assert sheetBody.faces.count == 1

    offsetWireBodies : list[adsk.fusion.BRepBody] = []
    face : adsk.fusion.BRepFace = sheetBody.faces[0]
    loop : adsk.fusion.BRepLoop
    for loop in face.loops:
        unOffsetWireBody : adsk.fusion.BRepBody
        edgeMap : Sequence[adsk.fusion.BRepEdge]

        unOffsetWireBody, edgeMap = temporaryBRepManager().createWireFromCurves(
            curves = [
                edge.geometry
                for edge in loop.edges
            ],
            allowSelfIntersections=False
        )
        assert unOffsetWireBody.wires.count == 1
        unOffsetWire : adsk.fusion.BRepWire = unOffsetWireBody.wires[0]

        # a loop is, by definition, oriented so that when we are standing on the
        # surface so that our sense of "up" is in the direction of the face
        # normal, as we walk along the loop in the positive direction of the
        # loop, the face will be on our left.
        wireDirectionMatchesLoopDirection : bool

        # find a pair of coEdges (surceCoEdge, destinationCoEdge) such that
        # sourcCoEdge is a coEdge from the original loop and destinationCoEdge
        # is the CORRESPONDING coEdge from the newly-created wire.
        
        sampleEdgeIndex = 0
        sourceEdge : adsk.fusion.BRepEdge = loop.edges[sampleEdgeIndex]
        destinationEdge : adsk.fusion.BRepEdge = edgeMap[sampleEdgeIndex]
        
        candidateSourceCoEdges : Sequence[adsk.fusion.BRepCoEdge] = tuple(filter( lambda coEdge: coEdge.loop == loop,  sourceEdge.coEdges ))
        assert len(candidateSourceCoEdges) == 1
        sourceCoEdge = candidateSourceCoEdges[0]

        candidateDestinationCoEdges : Sequence[adsk.fusion.BRepCoEdge] = destinationEdge.coEdges
        assert len(candidateDestinationCoEdges) == 1
        destinationCoEdge = candidateDestinationCoEdges[0]

        # the above assertions are just sanity checks to make sure we are not
        # dealing with an edge that is used by more than one coEdge (not that
        # there is anything inherently wrong about that, but
        # TemporaryBRepManager::createWireFromCurves() only tells us about
        # correspondence between edges, not coEdges (which would be more useful,
        # I think)).  Since we are dealing with one loop of a face, we probably 
        # will not see multiple coedges using the same edge.

        #TODO: to more thoroughly  handle the case where some edges are used by
        # multiple coedges, we might iterate through all edge indexes until we
        # find a valid pair of coEdges. In practice, I suspect this will be
        # entirely moot because in any case where we might have multiple coedges
        # of the loop using the same edge, Fusion will have thrown a tantrum
        # long before we get here.
        sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = sourceCoEdge.isOpposedToEdge ^ sourceCoEdge.edge.isParamReversed
        destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = destinationCoEdge.isOpposedToEdge ^ destinationCoEdge.edge.isParamReversed

        # I am assuming that in the process of running
        # TemporaryBRepManager::createWireFromCurves() , the direction of the
        # underlying geometry did not change.

        # the underlying geometry (the Curve3D) object has a sense of direction.
        # the edge has a sense of direction (either same or opposed to that of
        # underlying geometry) the coEdge has a sense of direction (either same
        # or opposed to that of the edge)

        # Note the CoEdge::isParamReversed property tells us about the
        # relationship between the co-edge's geometry property (which is a
        # curve2D - in the paramater space of the face's surface). this property
        # is not of interest to us here.

        wireDirectionMatchesLoopDirection = sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge == destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge
        
        # print(f"wireDirectionMatchesLoopDirection: {wireDirectionMatchesLoopDirection}")
        # print(
        #     f"sourceCoEdge.isOpposedToEdge, sourceCoEdge.edge.isParamReversed, destinationCoEdge.isOpposedToEdge, destinationCoEdge.edge.isParamReversed: "
        #     + "".join(
        #         map(
        #             lambda x: str(int(x)), 
        #             (sourceCoEdge.isOpposedToEdge, sourceCoEdge.edge.isParamReversed, destinationCoEdge.isOpposedToEdge, destinationCoEdge.edge.isParamReversed)
        #         )
        #     )
        # )

        offsetWireBody : adsk.fusion.BRepBody
        result, planeNormal = face.evaluator.getNormalAtPoint(face.pointOnFace); assert result
        
        

        offsetWireBody = unOffsetWire.offsetPlanarWire(
            planeNormal = planeNormal,

            distance = offset * (1 if wireDirectionMatchesLoopDirection else -1), 
            #may have to evaluate loop/coedge/parameter reversal to know the correct sign for offset.

            # cornerType = adsk.fusion.OffsetCornerTypes.CircularOffsetCornerType
            cornerType = offsetCornerType
        )

        offsetWireBodies.append(offsetWireBody)
    
    highlight(
        [ 
            edge 
            for body in offsetWireBodies
            for edge in body.edges
        ],
        **makeHighlightParams(f"offsetWireBodies", show=False)
    )

    result : Optional[adsk.fusion.BRepBody] = temporaryBRepManager().createFaceFromPlanarWires(wireBodies=offsetWireBodies)
    if result is not None:
        returnBodies.append(result)
    return tuple(returnBodies)



def offsetSheetBodies(
    sheetBodies : Iterable[adsk.fusion.BRepBody], 
    offset: float,
    offsetCornerType : Optional[adsk.fusion.OffsetCornerTypes] = None
) -> Sequence[adsk.fusion.BRepBody]:
    # offsetCornerType only has an effect in the case where we implement this function using 
    # offsetSheetBodyUsingTheWireTechnique.
    
    # This function is intended to operate on planar sheet bodies (i.e. a BRepBody consisting of a single open face)
    # we basically assume that the sheet bodies lie on the xy plane.
    returnBodies : Sequence[adsk.fusion.BRepBody] = []

    for sheetBody in sheetBodies:  
        #TODO check for success and warn or raise exception in case of failure.
        
        returnBodies.extend(
            offsetSheetBodyUsingTheWireTechnique(
                sheetBody=sheetBody, 
                offset=offset,
                offsetCornerType = offsetCornerType
            )
        )
    return tuple(returnBodies)

def loftBetweenSheets(sheetBodies : Sequence[adsk.fusion.BRepBody]) -> Sequence[adsk.fusion.BRepBody]:
    # at the moment, I assume that sheetBodies contains exactly two members,
    # each of which is a BRepBody consisting of a single face, and each face
    # having the same number of loops, with the loop indices in "correspondence"
    # between the two sheets (i.e. we are going to loft loop i of (the face of)
    # sheetBodies[j] to loop i of (the face of) sheetBodies[j+1]). a tuple of
    # the solid bodies created (which should generally contaion exactly one
    # element).
    returnBodies : Sequence[adsk.fusion.BRepBody] = []

    assert len(sheetBodies) >= 2

    tempOccurrence = rootComponent().occurrences.addNewComponent(adsk.core.Matrix3D.create())
    mainTempComponent = tempOccurrence.component
    mainTempComponent.name = "loftBetweenSheets-mainTempComponent"

    i = 0
    startSheetBody = sheetBodies[i]
    endSheetBody   = sheetBodies[i+1]

    startSheetPersisted : adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(startSheetBody)
    endSheetPersisted   : adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(endSheetBody)
    assert startSheetPersisted.faces.count == 1
    assert endSheetPersisted.faces.count == 1


    startFace : adsk.fusion.BRepFace = startSheetPersisted.faces[0]
    endFace : adsk.fusion.BRepFace = endSheetPersisted.faces[0]
    assert startFace.loops.count == endFace.loops.count

    # loftFeatureInput : adsk.fusion.LoftFeatureInput = mainTempComponent.features.loftFeatures.createInput(operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    # startLoftSection : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( startFace )
    # endLoftSection   : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( endFace   )
    # loftFeatureInput.isSolid = False # this seems to make no difference -- we seemn to almost always get sheet bodies rather than solids.
    # loftFeature : adsk.fusion.LoftFeature = fscad.root().features.loftFeatures.add(loftFeatureInput)
    # returnBodies.extend( temporaryBRepManager().copy(body) for body in loftFeature.bodies )
    # # The loft feature, when operating on faces, seems to ignore inner loops.
    # # Therefore, we must pass something other than faces as loftFeature input, and we must go loop-by-loop.
    
    sidewallBodies : Sequence[adsk.fusion.BRepBody] = []
    for loopIndex in range(startFace.loops.count):
        # We are trusting that the loop index is analogous in the startFace and endFace.
        startLoop : adsk.fusion.BRepLoop = startFace.loops[loopIndex]
        sampleEdgeIndex = 0
        startSampleEdge : adsk.fusion.BRepEdge = startLoop.edges[sampleEdgeIndex]
        candidateStartCoEdges : Sequence[adsk.fusion.BRepCoEdge] = tuple(filter( lambda coEdge: coEdge.loop == startLoop,  startSampleEdge.coEdges ))
        assert len(candidateStartCoEdges) == 1
        startSampleCoEdge = candidateStartCoEdges[0]
        startSampleCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = startSampleCoEdge.isOpposedToEdge ^ startSampleCoEdge.edge.isParamReversed
        startReferencePoint = (startSampleEdge.endVertex.geometry  if startSampleCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge else startSampleEdge.startVertex.geometry )
        highlight(startReferencePoint,**makeHighlightParams(f"startReferencePoint", show=False))
        highlight(startSampleEdge,**makeHighlightParams(f"startSampleEdge", show=False))

        endLoop   : adsk.fusion.BRepLoop = endFace.loops[loopIndex]
        endSampleEdge : adsk.fusion.BRepEdge = endLoop.edges[sampleEdgeIndex]
        candidateEndCoEdges : Sequence[adsk.fusion.BRepCoEdge] = tuple(filter( lambda coEdge: coEdge.loop == endLoop,  endSampleEdge.coEdges ))
        assert len(candidateEndCoEdges) == 1
        endSampleCoEdge = candidateEndCoEdges[0]
        endSampleCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = endSampleCoEdge.isOpposedToEdge ^ endSampleCoEdge.edge.isParamReversed
        endReferencePoint = (endSampleEdge.endVertex.geometry  if endSampleCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge else endSampleEdge.startVertex.geometry )
        highlight(endReferencePoint,**makeHighlightParams(f"endReferencePoint", show=False))
        highlight(endSampleEdge,**makeHighlightParams(f"endSampleEdge", show=False))

        guideWireBody : adsk.fusion.BRepBody
        guideWireBody, _ = temporaryBRepManager().createWireFromCurves(
            curves = [adsk.core.Line3D.create(startPoint= startReferencePoint, endPoint= endReferencePoint)],
            allowSelfIntersections=False
        )
        assert guideWireBody.edges.count == 1
        highlight(guideWireBody.edges,**makeHighlightParams(f"guideWire", show=False))
  
        
        
        # highlight(
        #     startLoop.edges,
        #     **makeHighlightParams(f"start loop {loopIndex}")
        # )

        # highlight(
        #     endLoop.edges,
        #     **makeHighlightParams(f"end loop {loopIndex}")
        # )



        # startPath : adsk.fusion.Path = adsk.fusion.Path.create(curves = startLoop.edges[0]   , chainOptions = adsk.fusion.ChainedCurveOptions.noChainedCurves)
        # for edgeIndex in range(1, startLoop.edges.count): startPath.addCurves(startLoop.edges[edgeIndex], chainOptions = adsk.fusion.ChainedCurveOptions.noChainedCurves)

        # endPath : adsk.fusion.Path = adsk.fusion.Path.create(curves = endLoop.edges[0]   , chainOptions = adsk.fusion.ChainedCurveOptions.noChainedCurves)
        # for edgeIndex in range(1, endLoop.edges.count): startPath.addCurves(endLoop.edges[edgeIndex], chainOptions = adsk.fusion.ChainedCurveOptions.noChainedCurves)

        startPath : adsk.fusion.Path = mainTempComponent.features.createPath(curve= fscad._collection_of(startLoop.edges), isChain=False)
        endPath   : adsk.fusion.Path = mainTempComponent.features.createPath(curve= fscad._collection_of(endLoop.edges),   isChain=False)
        #curiously, adsk.fusion.Path.create(curves= fscad._collection_of(startLoop.edges), chainOptions = adsk.fusion.ChainedCurveOptions.noChainedCurves)
        # would throw an error, saying something about path being empty.  However, mainTempComponent.features.createPath() worked as desired.
        # This difference might have something to do with persisted vs. transient bodies.

        assert startPath.isClosed
        assert endPath.isClosed

        # highlight(
        #     startPath,
        #     **makeHighlightParams(f"startPath {loopIndex}")
        # )

        # highlight(
        #     endPath,
        #     **makeHighlightParams(f"endPath {loopIndex}")
        # )


        #TODO : Refactor to get rid of pyramid-of-doom below:
        
        succesfullyCreatedSidewallBodies : bool = False

        if not succesfullyCreatedSidewallBodies:
            loftFeature : adsk.fusion.LoftFeature
            loftFeatureInput : adsk.fusion.LoftFeatureInput = mainTempComponent.features.loftFeatures.createInput(operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            startLoftSection : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( startPath )
            endLoftSection   : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( endPath )
            loftFeatureInput.isSolid = False # this seems to make no difference -- we seemn to almost always get sheet bodies rather than solids.
            
            try:
                loftFeature = fscad.root().features.loftFeatures.add(loftFeatureInput)
            except Exception as e:
                print(f"loftBetweenSheets encountered error while attempting to construct sidewalls using the loft technique without a rail: {e}")
                loftFeature = None
            else:
                sidewallBodies.extend( loftFeature.bodies )
                succesfullyCreatedSidewallBodies = True        
        
        if not succesfullyCreatedSidewallBodies :
            print("attempting loft again, this time with guide rail.")
            
            
            guideWireBodyPersisted : adsk.fusion.BRepBody = mainTempComponent.bRepBodies.add(guideWireBody)
            assert guideWireBodyPersisted.edges.count == 1  
            highlight(guideWireBody.edges,**makeHighlightParams(f"guideWire-had to use it", show=False))


            loftFeatureInput : adsk.fusion.LoftFeatureInput = mainTempComponent.features.loftFeatures.createInput(operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
            startLoftSection : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( startPath )
            endLoftSection   : adsk.fusion.LoftSection = loftFeatureInput.loftSections.add( endPath )
            loftFeatureInput.isSolid = False # this seems to make no difference -- we seemn to almost always get sheet bodies rather than solids.
            loftCenterLineOrRail : adsk.fusion.LoftCenterLineOrRail = loftFeatureInput.centerLineOrRails.addRail(guideWireBodyPersisted.edges[0])
            try:
                loftFeature = fscad.root().features.loftFeatures.add(loftFeatureInput)
            except Exception as e:
                print(f"loftBetweenSheets encountered error while attempting to construct sidewalls using the loft technique with a rail: {e}")
                loftFeature = None
            else: 
                sidewallBodies.extend( loftFeature.bodies )
                succesfullyCreatedSidewallBodies = True  

        if not succesfullyCreatedSidewallBodies:
            print("resorting to ruled surface for sidewall body.")
            #compute the sidewalls as ruled surfaces.
            startWireBody  : adsk.fusion.BRepBody
            startEdgeMap   : Sequence[adsk.fusion.BRepEdge]
            startWireBody, startEdgeMap = temporaryBRepManager().createWireFromCurves(
                curves = [
                    edge.geometry
                    for edge in startLoop.edges
                ],
                allowSelfIntersections=False
            )
            assert startWireBody.wires.count == 1
            startWire : adsk.fusion.BRepWire = startWireBody.wires[0]
            # start:
            sampleEdgeIndex = 0
            sourceEdge : adsk.fusion.BRepEdge = startLoop.edges[sampleEdgeIndex]
            destinationEdge : adsk.fusion.BRepEdge = startEdgeMap[sampleEdgeIndex]

            candidateSourceCoEdges : Sequence[adsk.fusion.BRepCoEdge] = tuple(filter( lambda coEdge: coEdge.loop == startLoop,  sourceEdge.coEdges ))
            assert len(candidateSourceCoEdges) == 1
            sourceCoEdge = candidateSourceCoEdges[0]

            candidateDestinationCoEdges : Sequence[adsk.fusion.BRepCoEdge] = destinationEdge.coEdges
            assert len(candidateDestinationCoEdges) == 1
            destinationCoEdge = candidateDestinationCoEdges[0]
            sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = sourceCoEdge.isOpposedToEdge ^ sourceCoEdge.edge.isParamReversed
            destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = destinationCoEdge.isOpposedToEdge ^ destinationCoEdge.edge.isParamReversed
            startWireDirectionMatchesStartLoopDirection : bool = sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge == destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge
            print(f"startWireDirectionMatchesStartLoopDirection: {startWireDirectionMatchesStartLoopDirection}")
            startStartPoint = (sourceEdge.endVertex.geometry  if sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge else sourceEdge.startVertex.geometry )

            endWireBody  : adsk.fusion.BRepBody
            endEdgeMap   : Sequence[adsk.fusion.BRepEdge]
            endWireBody, endEdgeMap = temporaryBRepManager().createWireFromCurves(
                curves = [
                    edge.geometry
                    for edge in endLoop.edges
                ],
                allowSelfIntersections=False
            )
            assert endWireBody.wires.count == 1
            endWire : adsk.fusion.BRepWire = endWireBody.wires[0]
            # end:
            sampleEdgeIndex = 0
            sourceEdge : adsk.fusion.BRepEdge = endLoop.edges[sampleEdgeIndex]
            destinationEdge : adsk.fusion.BRepEdge = endEdgeMap[sampleEdgeIndex]

            candidateSourceCoEdges : Sequence[adsk.fusion.BRepCoEdge] = tuple(filter( lambda coEdge: coEdge.loop == endLoop,  sourceEdge.coEdges ))
            assert len(candidateSourceCoEdges) == 1
            sourceCoEdge = candidateSourceCoEdges[0]

            candidateDestinationCoEdges : Sequence[adsk.fusion.BRepCoEdge] = destinationEdge.coEdges
            assert len(candidateDestinationCoEdges) == 1
            destinationCoEdge = candidateDestinationCoEdges[0]
            sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = sourceCoEdge.isOpposedToEdge ^ sourceCoEdge.edge.isParamReversed
            destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge = destinationCoEdge.isOpposedToEdge ^ destinationCoEdge.edge.isParamReversed
            endWireDirectionMatchesEndLoopDirection : bool = sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge == destinationCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge
            print(f"endWireDirectionMatchesEndLoopDirection: {endWireDirectionMatchesEndLoopDirection}")
            endStartPoint = (sourceEdge.endVertex.geometry  if sourceCoEdgeIsOpposedToUnderlyingGeometryOfItsEdge else sourceEdge.startVertex.geometry )

            highlight(startWire.edges,**makeHighlightParams(f"startWire", show=False))
            highlight(startStartPoint,**makeHighlightParams(f"startStartPoint", show=False))


            highlight(endWire.edges,**makeHighlightParams(f"endWire", show=False))
            highlight(endStartPoint,**makeHighlightParams(f"endStartPoint", show=False))


            # WRAP THIS IN ATRY LOOP
            #  BOOKMARK 2021-11-22-0954
            # attmept to construct the sidewalls using a ruled surface
            sidewallBody : adsk.fusion.BRepBody = temporaryBRepManager().createRuledSurface(
                sectionOne = startWire,
                sectionTwo = endWire
            )
            sidewallPersistedBody: adsk.fusion.BRepBody  = mainTempComponent.bRepBodies.add(sidewallBody)

            sidewallBodies.append(sidewallPersistedBody)



    boundaryFillFeatureInput : adsk.fusion.BoundaryFillFeatureInput = mainTempComponent.features.boundaryFillFeatures.createInput(
        tools= fscad._collection_of( sidewallBodies + [startSheetPersisted, endSheetPersisted]) , 
        operation=adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )

    bRepCell : adsk.fusion.BRepCell
    for bRepCell in boundaryFillFeatureInput.bRepCells: 
        bRepCell.isSelected = True

    boundaryFillFeature : adsk.fusion.BoundaryFillFeature = mainTempComponent.features.boundaryFillFeatures.add(boundaryFillFeatureInput)
    returnBodies.extend( temporaryBRepManager().copy(body) for body in boundaryFillFeature.bodies )

    # we might consider using a ruled surface (as created with TemporaryBRepManager::createRuledSurface(), 
    # NOT with the ruled surface feature, which does not allow you to create an arbitrary ruled surface
    # because it only lets youn specify one of the "rails".) instead of a loft.


    tempOccurrence.deleteMe()
    return tuple(returnBodies)



def extrudeDraftAndWrapSheetbodiesAroundCylinder(
    sheetBodies : Iterable[adsk.fusion.BRepBody], 
    cylinderOrigin :  VectorLike,    
    cylinderAxisDirection : VectorLike,
    wrappingRadiusStart : float,
    wrappingRadiusEnd: float,
    draftAngle: float,
    rootRadius : Optional[float] = None,
    offsetCornerType : Optional[adsk.fusion.OffsetCornerTypes] = None
) -> Sequence[adsk.fusion.BRepBody]:
    # the name of this function is admittedly terrible. this function takes a
    # set of sheet bodies, assumed to lie on the xy plane.  We then do the
    # equivalent of extruding these sheet bodies, with draft, and then
    # transforming the resulting solid into cylindrical coordinates.  (TODO: make this explanation clearer)
    # I am going to call this operation "Edification" for lack of a better word.
    returnBodies : Sequence[adsk.fusion.BRepBody] = []


    for sheetBody in sheetBodies:
        #we are assuming that each sheetBody has a single face (and that the wrapped version of the sheet body will also have a single face)
        flatSheetAtStart = sheetBody
        fscad.BRepComponent(flatSheetAtStart,name="flatSheetAtStart").create_occurrence().isLightBulbOn = False


        flatSheetsAtEnd = offsetSheetBodies( 
            sheetBodies = [flatSheetAtStart], 
            offset = math.tan(draftAngle) * (wrappingRadiusEnd - wrappingRadiusStart),
            offsetCornerType = offsetCornerType
        )
        assert len(flatSheetsAtEnd) == 1
        flatSheetAtEnd = flatSheetsAtEnd[0]
        fscad.BRepComponent(flatSheetAtEnd,name="flatSheetAtEnd").create_occurrence().isLightBulbOn = False


        wrappedSheetsAtStart = wrapSheetBodiesAroundCylinder(
            sheetBodies    = (flatSheetAtStart, ),
            wrappingRadius = wrappingRadiusStart,
            cylinderOrigin =cylinderOrigin ,
            cylinderAxisDirection=cylinderAxisDirection ,
            rootRadius = rootRadius
        )
        assert len(wrappedSheetsAtStart) == 1
        wrappedSheetAtStart = wrappedSheetsAtStart[0]
        fscad.BRepComponent(wrappedSheetAtStart,name="wrappedSheetAtStart").create_occurrence().isLightBulbOn = False


        wrappedSheetsAtEnd = wrapSheetBodiesAroundCylinder(
            sheetBodies    = (flatSheetAtEnd, ),
            wrappingRadius = wrappingRadiusEnd,
            cylinderOrigin =cylinderOrigin ,
            cylinderAxisDirection=cylinderAxisDirection ,
            rootRadius = rootRadius
        )
        assert len(wrappedSheetsAtEnd) == 1
        wrappedSheetAtEnd = wrappedSheetsAtEnd[0]
        fscad.BRepComponent(wrappedSheetAtEnd,name="wrappedSheetAtEnd").create_occurrence().isLightBulbOn = False

        returnBodies.extend(loftBetweenSheets((wrappedSheetAtStart, wrappedSheetAtEnd)))



    return tuple(returnBodies)
