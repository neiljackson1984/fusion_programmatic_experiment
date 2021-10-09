from typing import Optional, Sequence, Tuple, Union
from enum import Enum
import enum
import math
import functools
import scipy
import itertools
import warnings
# the above import of scipy requires the user to have taken action to ensure that scipy is available somewhere on the system path,
# for instance by doing "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install scipy
# I would like to automate the management of dependencies like this.  With a "normal" Python project, pipenv would be the logical way to do it,
# but for scripts that are to be loaded by fusion, it is unclear what the best way to manage dependencies is -- maybe some sort of vendoring?


import numpy as np
# I am relying on the installation of scipy to also install numpy.

from numpy.typing import ArrayLike, NDArray
from typing import SupportsFloat
from numpy import ndarray
from numpy import number
from math import sin, cos
import adsk
import adsk.fusion, adsk.core
import unyt
import operator
from .braids.fscad.src.fscad import fscad as fscad

from adsk.fusion import BRepEdge
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt


import unyt
# "C:\Users\Admin\AppData\Local\Autodesk\webdeploy\production\48ac19808c8c18863dd6034eee218407ecc49825\Python\python.exe" -m pip install unyt

unyt.millimeter = unyt.milimeter
# this is a work-around for the problem that unyt misspells the SI
# prefix milli with only a single l.

fusionInternalUnitOfLength = unyt.centimeter

def app()           -> adsk.core.Application   : return adsk.core.Application.get()
def ui()            -> adsk.core.UserInterface : return app().userInterface
def design()        -> adsk.fusion.Design      : return adsk.fusion.Design.cast(app().activeProduct)
def rootComponent() -> adsk.fusion.Component   : return design().rootComponent


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




def castToNDArray(x: Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D], n: Optional[int] = None) -> NDArray:
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

VectorLike = Union[ndarray, adsk.core.Point3D, adsk.core.Vector3D, adsk.core.Point2D, adsk.core.Vector2D]


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