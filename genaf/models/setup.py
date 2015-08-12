
from rhombus.lib.utils import cout, cerr
from rhombus.models.ek import EK
from rhombus.models.user import Group
from genaf.models.ms import Marker, Panel

def setup(session):
    """ populate database with essential GenAF data, mostly taken from FATools constants """

    EK.bulk_insert( ek_initlist, dbsession=session)

    #get default group, which is system

    adm_group = Group.search('_DataAdm_', dbsession=session)

    # create undefined marker
    marker = Marker( code = 'undefined', species='X' )
    cerr("INFO - marker 'undefined' created.")
    session.add(marker)

    # create ladder marker
    marker = Marker( code =  'ladder', species='X' )
    cerr("INFO - marker 'ladder' created.")
    session.add(marker)

    # create combined marker
    marker = Marker( code = 'combined', species='X' )
    cerr("INFO - marker 'combined' created.")
    session.add(marker)

    # create default panel
    panel = Panel( code = 'undefined', group_id = adm_group.id )
    cerr("INFO - panel 'undefined' created.")
    session.add(panel)


from fatools.lib.const import *

def get_attributes( class_ ):
    return list( getattr(class_, n) for n in dir(class_) if not n.startswith('_'))

ek_initlist = [
    (   '@PEAK-TYPE', 'Peak types',
        get_attributes(peaktype)
        ),
    (   '@CHANNEL-STATUS', 'Channel status',
        get_attributes(channelstatus)
        ),
    (   '@ASSAY-STATUS', 'Assay status',
        get_attributes(assaystatus)
        ),
    (   '@ALIGN-METHOD', 'Ladder alignment method',
        get_attributes(alignmethod)
        ),
    (   '@SCANNING-METHOD', 'Peak scanning method',
        get_attributes(scanningmethod)
        ),
    (   '@ALLELE-METHOD', 'Allele methods',
        get_attributes(allelemethod)
        ),
    (   '@BINNING-METHOD', 'Binning methods',
        get_attributes(binningmethod)
        ),
    (   '@DYE', 'Dye type',
        dyes
        ),
    (   '@SPECIES', 'Species',
        [   ( 'X', 'Undefined' ),
        ]),
    (   '@REGION', 'Region name',
        [   ( '', 'Undefined' ),
        ]),
    (   '@BLOOD-WITHDRAWAL', 'Blood withdrawal method',
        [   'venous', 'capillary',
        ]),
    (   '@BLOOD-STORAGE', 'Blood storage method',
        [   'blood tube', 'EDTA',
        ]),
    (   '@PCR-METHOD', 'PCR detection method',
        []),
]
