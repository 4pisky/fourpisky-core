from VOEventLib import VOEvent as voe, Vutil as voe_utils
from astropysics.coords.coordsys import FK5Coordinates 

def get_isotime(v):
    assert isinstance(v, voe.VOEvent)
    try:
        ol = v.WhereWhen.ObsDataLocation.ObservationLocation
        return ol.AstroCoords.Time.TimeInstant.ISOTime
    except:
        return None
    
    
#Simply a wrapper - to avoid "CamelCase" function names.
def get_param_names(v):
    '''
    Grabs the "what" section of a voevent, and produces a list of tuples of group name and param name.
    For a bare param, the group name is the empty string.
    
    NB. This replicates functionality from VOEventLib - but the inbuilt version is broken as of v0.3.
    '''
    list = []
    w = v.What
    if not w: return list
    for p in v.What.Param:
        list.append(('', p.name))
    for g in v.What.Group:
        for p in g.Param:
            list.append((g.name, p.name))
    return list

def pull_FK5_from_WhereWhen(v):
    """Convenience function, converts voevent -> FK5 coords.
    
        WARNING WARNING WARNING:
        Conversion is valid for SWIFT stream - other VO stream formats unchecked.
    """
    ww = voe_utils.getWhereWhen(v)
    
    return FK5Coordinates(ra = ww['longitude'], 
                          dec = ww['latitude'],
                          raerror = ww['positionalError'],
                          decerror = ww['positionalError']
                           )  
    
    