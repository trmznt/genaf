# ms.py - microsatellite schema
# follows closely the FATools database schema

import numpy, copy, io

#from sqlalchemy import and_, or_, schema, types, MetaData, Sequence, Column, ForeignKey, UniqueConstraint, Table
from sqlalchemy import func
from sqlalchemy.orm import relationship, backref, dynamic_loader, deferred, reconstructor

#from sqlalchemy.orm.collections import column_mapped_collection, attribute_mapped_collection
#from sqlalchemy.orm.interfaces import MapperExtension
#from sqlalchemy.orm.exc import NoResultFound
#from sqlalchemy.orm.session import object_session
#from sqlalchemy.exc import OperationalError, IntegrityError
#from sqlalchemy.ext.associationproxy import association_proxy
#from sqlalchemy.ext.declarative import declared_attr, declarative_base
#from sqlalchemy.sql.functions import current_timestamp


from rhombus.models.core import *
from rhombus.models.ek import EK
from rhombus.models.user import User, Group
from rhombus.models.mixin import *

from fatools.lib.fautil.mixin import ( PanelMixIn, AssayMixIn, ChannelMixIn, MarkerMixIn,
                AlleleSetMixIn, AlleleMixIn, NoteMixIn, AssayNoteMixIn,
                ChannelNoteMixIn, AlleleSetNoteMixIn, PanelNoteMixIn, MarkerNoteMixIn )


from genaf.models.sample import Sample, Batch, Note

class NPArray(types.TypeDecorator):
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        #buf = value.tostring()
        buf = io.BytesIO()
        numpy.save(buf, value)
        return buf.getvalue()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        buf = io.BytesIO(value)
        return numpy.load(buf)
        #return numpy.fromstring(value)

    def copy_value(self, value):
        return copy.deepcopy( value )


class Panel(BaseMixIn, Base, PanelMixIn):

    __tablename__ = 'panels'

    code = Column(types.String(8), nullable=False, unique=True)
    data = Column(YAMLCol(1024), nullable=False)
    remark = deferred(Column(types.String(1024), nullable=True))

    ## GenAF spesific schema

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False, foreign_keys = group_id)


    def update(self, obj):

        self._update(obj)
        session = object_session(self) or self._dbh_session_

        if type(obj) == dict:

            if 'group' in obj:
                with session.no_autoflush:
                    group = Group.search(obj['group'], session)
                    self.group = group

        else:
            raise NotImplementedError()


        # verify that each marker in data exists
        session = object_session(self) or self._dbh_session_
        for m_code in self.data['markers']:
            m = Marker.search(m_code, session)
            if m is None:
                cerr("ERR: can't find marker: %s" % m_code)
                sys.exit(1)


    def sync(self):
        raise NotImplementedError()


    def get_marker(self, marker_code):
        """ return marker instance """
        return Marker.search( marker_code, object_session(self))

    @reconstructor
    def init_data(self):
        if not hasattr(self, '_dyes'):
            self._dyes = {}


    @staticmethod
    def search(code, session):
        """ provide case-insensitive search for marker code """
        q = Panel.query(session).filter( func.lower(Panel.code) == func.lower(code) )
        return q.one()



class PanelNote(Base, PanelNoteMixIn):

    __tablename__ = 'panelnotes'
    id = Column(types.Integer, primary_key=True)
    panel_id = Column(types.Integer, ForeignKey('panels.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Marker(BaseMixIn, Base, MarkerMixIn):

    __tablename__ = 'markers'

    code = Column(types.String(64), nullable=False, unique=True)
    #species = Column(types.String(32), nullable=False, default='X')
    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')
    locus = Column(types.String(16), nullable=False, default='')
    repeats = Column(types.Integer, nullable=False, default=-1)

    min_size = Column(types.Integer, nullable=False, default=0)
    max_size = Column(types.Integer, nullable=False, default=0)
    """ range of allele size for this marker """

    bins = deferred(Column(YAMLCol(2048), nullable=False, default=''))
    """ sorted known bins for this markers """
    
    related_to_id = Column(types.Integer, ForeignKey('markers.id'),
                          nullable=True)
    related_to = relationship("Marker", uselist=False)
    """ points to related marker """
    
    z_params = Column(types.String(64), nullable=False, default='')
    """ mathematical expression correlating with the related_to marker """

    remark = deferred(Column(types.String(1024), nullable=True))

    __table_args__ = ( UniqueConstraint( 'code', 'species_id' ), )

    def update(self, obj):
        
        self._update( obj )
        if type(obj) == dict and 'related_to' in obj:
            related_marker = Marker.search( d['related_to'],
                    session = object_session(self) or self.__dbh_session )
            self.related_to = related_marker


    def sync(self, session):
        """ sync assume that the current instance is not attached to any session """
        db_marker = Marker.search(marker.code, session=session)
        db_marker.update( self )
        return db_marker


    @staticmethod
    def search(code, session):
        """ provide case-insensitive search for marker code """
        if '/' in code:
            species, code = code.split('/')
            species_id = EK._id(species, dbsession=session)
            q = Marker.query(session).filter( func.lower(Marker.code) == func.lower(code),
                                            Marker.species_id == species_id)
        else:
            q = Marker.query(session).filter( func.lower(Marker.code) == func.lower(code) )
        return q.one()


class MarkerNote(Base, MarkerNoteMixIn):

    __tablename__ = 'markernotes'
    id = Column(types.Integer, primary_key=True)
    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Assay(BaseMixIn, Base, AssayMixIn):

    __tablename__ = 'assays'

    filename = Column(types.String(128), nullable=False, index=True)
    runtime = Column(types.DateTime, nullable=False)
    rss = Column(types.Float, nullable=False, default=-1)
    dp = Column(types.Float, nullable=False, default=-1)
    score = Column(types.Float, nullable=False, default=-1)
    z = deferred(Column(NPArray))
    ladder_peaks = Column(types.Integer, nullable=False, default=-1)

    size_standard = Column(types.String(32), nullable=False, default='')

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                        nullable=False)
    sample = relationship(Sample, uselist=False, backref=backref('assays', lazy='dynamic'))

    panel_id = Column(types.Integer, ForeignKey('panels.id'), nullable=False)
    panel = relationship(Panel, uselist=False)

    ladder_id = Column(types.Integer,
                        ForeignKey('channels.id', use_alter=True, name = 'ladderchannel_fk'),
                        nullable=True)

    ladder = relationship('Channel', uselist=False,
                primaryjoin = "Assay.ladder_id == Channel.id")

    #status = Column(types.String(32), nullable=False, default='')
    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status = EK.proxy('status_id', '@ASSAY-STATUS')

    #method = deferred(Column(types.String(16), nullable=False, default=''))
    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@ALIGN-METHOD')

    report = deferred(Column(types.String(512), nullable=False, default=''))
    remark = deferred(Column(types.String(1024), nullable=False, default=''))

    raw_data = deferred(Column(types.Binary(), nullable=False))
    """ raw data for this assay (FSA file content) """

    __table_args__ = (  UniqueConstraint( 'filename', 'panel_id', 'sample_id' ), )

    def new_channel(self, raw_data, data, dye, wavelen, status, median, mean,
            max_height, min_height, std_dev, initial_marker=None, initial_panel=None):
        """ create new channel and added to this assay """
        if not initial_marker:
            initial_marker = Marker.search('undefined', session = object_session(self))
        if not initial_panel:
            initial_panel = Panel.search('undefined', session = object_session(self))
        channel = Channel( raw_data = data, data = data, dye = dye, wavelen = wavelen,
                            status = status, median = median, mean = mean,
                            max_height = max_height, min_height = min_height,
                            std_dev = std_dev )
        channel.assay = self
        channel.marker = initial_marker
        channel.panel = initial_panel

        return channel


    def get_ladder(self):
        """ get ladder channel """
        assert self.ladder_id, "ERR/PROG -  pls make sure ladder_id is not null!"
        session = object_session(self)
        return Channel.get(self.ladder_id, session)


    def _get_markers(self):
        session = object_session(self)
        return AlleleSet.query(session).join(Channel).join(Assay, Channel.assay_id == Assay.id).filter( Assay.id == self.id )
    markers = property(_get_markers)




class AssayNote(Base, AssayNoteMixIn):

    __tablename__ = 'assaynotes'
    id = Column(types.Integer, primary_key=True)
    assay_id = Column(types.Integer, ForeignKey('assays.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Channel(BaseMixIn, Base, ChannelMixIn):

    __tablename__ = 'channels'

    assay_id = Column(types.Integer, ForeignKey('assays.id', ondelete='CASCADE'),
                        nullable=False)
    assay = relationship(Assay, uselist=False, primaryjoin = assay_id == Assay.id, 
                    backref=backref('channels', lazy='dynamic'))

    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    marker = relationship(Marker, uselist=False, backref=backref('channels', lazy='dynamic'))

    #dye = Column(types.String(32), nullable=False)
    dye_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    dye = EK.proxy('dye_id', '@DYE')

    markers = relationship(Marker, secondary='channels_markers', viewonly=True)

    raw_data = deferred(Column(NPArray, nullable=False))
    """ raw data from channel as numpy array, can have empty array to accomodate
        allele data from CSV uploading """

    status = Column(types.String(32), nullable=False)

    wavelen = Column(types.Integer, nullable=False, default=0)
    median = Column(types.Integer, nullable=False, default=0)
    mean = Column(types.Float, nullable=False, default=0.0)
    std_dev = Column(types.Float, nullable=False, default=0.0)
    max_height = Column(types.Integer, nullable=False, default=-1)
    min_height = Column(types.Integer, nullable=False, default=-1)
    """ basic descriptive statistics for data"""
        
    data = deferred(Column(NPArray, nullable=False))
    """ data after smoothed using savitzky-golay algorithm and baseline correction
        using top hat morphologic transform
    """

    remark = deferred(Column(types.String(1024), nullable=True))


    def new_alleleset(self, revision=-1):
        return AlleleSet( channel = self, sample = self.assay.sample,
                            marker = self.marker )


    def clear(self):
        for alleleset in self.allelesets:
            del alleleset


    def get_latest_alleleset(self):
        if self.allelesets.count() < 1:
            raise RuntimeError("ERR - channel does not have alleleset, probably hasn't been scanned!")
        return self.allelesets[-1]



class ChannelNote(Base, ChannelNoteMixIn):

    __tablename__ = 'channelnotes'
    id = Column(types.Integer, primary_key=True)
    channel_id = Column(types.Integer, ForeignKey('channels.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



channels_markers = Table(
    'channels_markers', Base.metadata,
    Column('channel_id', types.Integer, ForeignKey('channels.id')),
    Column('marker_id', types.Integer, ForeignKey('markers.id')),
    UniqueConstraint( 'channel_id', 'marker_id' )
    )
    # unique compound (channel_id, marker_id)



class AlleleSet(BaseMixIn, Base, AlleleSetMixIn):

    __tablename__ = 'allelesets'

    channel_id = Column(types.Integer, ForeignKey('channels.id', ondelete='CASCADE'),
                    nullable=False)
    channel = relationship(Channel, uselist=False,
                backref=backref('allelesets', lazy='dynamic', passive_deletes=True))
    # a channel can have several allele set for different revision numbers

    revision = Column(types.Integer, nullable=False, default=0)
    """ revision number """

    shared = Column(types.Boolean, default=False)
    """ whether this alleleset is viewable/searchable by other users """


    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                    nullable=False)
    sample = relationship(Sample, uselist=False,
                backref=backref('allelesets', lazy='dynamic', passive_deletes=True))
    """ link to sample """

    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    marker = relationship(Marker, uselist=False,
                    backref=backref('allelesets', lazy='dynamic'))
    """ link to marker """

    #scanning_method = deferred(Column(types.String(32), nullable=False, default=''))
    scanning_method_id = deferred(Column(types.Integer, ForeignKey('eks.id'), nullable=False))
    scanning_method = EK.proxy('scanning_method_id', '@SCANNING-METHOD')
    """ method used for scanning and generating this alleleset """

    #calling_method = deferred(Column(types.String(32), nullable=False, default=''))
    calling_method_id = deferred(Column(types.Integer, ForeignKey('eks.id'), nullable=False))
    calling_method = EK.proxy('calling_method_id', '@ALLELE-METHOD')
    """ method used for calling this alleleset """

    #binning_method = deferred(Column(types.String(32), nullable=False, default=''))
    binning_method_id = deferred(Column(types.Integer, ForeignKey('eks.id'), nullable=False))
    binning_method = EK.proxy('binning_method_id', '@BINNING-METHOD')
    """ method used for binning this alleleset """

    __table_args__ = ( UniqueConstraint( 'channel_id', 'revision' ), )


    def new_allele(self, rtime, height, area, brtime, ertime, wrtime, srtime, beta, theta,
                    type, method):
        allele = Allele( rtime = rtime, height = height, area = area,
                    brtime = brtime, ertime = ertime, wrtime = wrtime, srtime = srtime,
                    beta = beta, theta = theta, type = type, method = method )
        allele.alleleset = self

        return allele



class AlleleSetNote(Base, AlleleSetNoteMixIn):

    __tablename__ = 'allelesetnotes'
    id = Column(types.Integer, primary_key=True)
    alleleset_id = Column(types.Integer, ForeignKey('allelesets.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Allele(BaseMixIn, Base, AlleleMixIn):

    __tablename__ = 'alleles'

    alleleset_id = Column(types.Integer, ForeignKey('allelesets.id', ondelete='CASCADE'),
                nullable=False)
    alleleset = relationship(AlleleSet, uselist=False,
                backref=backref('alleles', cascade='all, delete-orphan',
                passive_deletes=True))

    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                nullable=False)
    marker = relationship(Marker, uselist=False,
                backref=backref('alleles', cascade='all, delete-orphan',
                    passive_deletes=True))

    abin = Column(types.Integer, nullable=False, default=-1)    # adjusted bin
    asize = Column(types.Float, nullable=False, default=-1)     # adjusted size
    aheight = Column(types.Float, nullable=False, default=-1)   # adjusted height

    bin = Column(types.Integer, nullable=False, default=-1)
    size = Column(types.Float, nullable=False, default=-1)
    deviation = Column(types.Float, nullable=False, default=-1)
    # deviation -> for ladder channel, this is ( z(rtime) - size )**2 or square of residual
    # for marker channel, this depends on the method
    # method cubic-spline, this is avg of deviation of the nearest peaks
    # for local southern, this is (size1 - size2) ** 2

    height = Column(types.Float, nullable=False, default=-1)
    area = Column(types.Float, nullable=False, default=-1)
    rtime = Column(types.Integer, nullable=False, default=-1)
    delta = Column(types.Float, nullable=False, default=-1)     # bin - actual size 
    beta = Column(types.Float, nullable=False, default=-1)      # area / height
    theta = Column(types.Float, nullable=False, default=-1)     # height / width

    #type = Column(types.String(32), nullable=False, default='')
    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id', '@PEAK-TYPE')

    #method = Column(types.String(32), nullable=False, default='')   # binning method
    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@BINNING-METHOD')

    brtime = Column(types.Integer, nullable=False, default=-1)
    ertime = Column(types.Integer, nullable=False, default=-1)
    wrtime = Column(types.Integer, nullable=False, default=-1)
    srtime = Column(types.Float, nullable=False, default=-1)    # log2( right_area/left_area )
    """ begin, end, width, symmetrical retention time of this peak and peak quality"""

    qscore = Column(types.Float, nullable=False, default=-1)    # calculated in preannotate()
    qcall = Column(types.Float, nullable=False, default=-1)     # calculated in call()


    @property
    def channel(self):
        return self.alleleset.channel

