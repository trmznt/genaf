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

from fatools.lib.utils import cerr, cout
from fatools.lib.fautil.mixin import ( PanelMixIn, AssayMixIn, ChannelMixIn, MarkerMixIn,
                AlleleSetMixIn, AlleleMixIn, NoteMixIn, AssayNoteMixIn, BinMixIn,
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

    code = Column(types.String(16), nullable=False, unique=True)
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


    def to_dict(self):
        """ return a dictionary """
        d = {}
        d['code'] = self.code
        d['data'] = self.data
        d['remark'] = self.remark
        d['group'] = self.group.name
        d['notes'] = [ n.to_dict for n in self.notes ]
        return d


class PanelNote(Base, PanelNoteMixIn):

    __tablename__ = 'panelnotes'
    id = Column(types.Integer, primary_key=True)
    panel_id = Column(types.Integer, ForeignKey('panels.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)

    panel = relationship(Panel, uselist=False, backref=backref('notes'))
    note = relationship(Note, uselist=False)


class Marker(BaseMixIn, Base, MarkerMixIn):

    __tablename__ = 'markers'

    code = Column(types.String(64), nullable=False, unique=True)
    #species = Column(types.String(32), nullable=False, server_default='X')
    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')
    locus = Column(types.String(16), nullable=False, server_default='')
    repeats = Column(types.Integer, nullable=False, server_default='-1')

    min_size = Column(types.Integer, nullable=False, server_default='0')
    max_size = Column(types.Integer, nullable=False, server_default='0')
    """ range of allele size for this marker """

    related_to_id = Column(types.Integer, ForeignKey('markers.id'),
                          nullable=True)
    related_to = relationship("Marker", uselist=False)
    """ points to related marker """

    z_params = Column(types.String(64), nullable=False, server_default='')
    """ mathematical expression correlating with the related_to marker """

    remark = deferred(Column(types.String(1024), nullable=False, server_default=''))

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
            if callable(session):
                session = session()
            species_id = EK._id(species, dbsession=session)
            q = Marker.query(session).filter( func.lower(Marker.code) == func.lower(code),
                                            Marker.species_id == species_id)
        else:
            q = Marker.query(session).filter( func.lower(Marker.code) == func.lower(code) )
        return q.one()


    def new_bin(self, batch):

        bin = Bin()
        bin.marker_id = self.id
        bin.batch_id = batch.id
        object_session(self).add(bin)
        return bin


    def get_bin(self, batch, recursive=True):

        # bins can be in any of these 3:
        # - hold by respective batch
        # - hold by bin_batch in the respective batch
        # - hold by batch 'server_default'

        session = object_session(self)
        while True:

            bin = Bin.search(marker_id = self.id, batch_id = batch.id, session = session)
            if not recursive:
                return bin
            if bin is not None:
                return bin

            batch = batch.bin_batch
            if batch is None:
                raise RuntimeError('Could not found bins for marker %s' % self.label)



class MarkerNote(Base, MarkerNoteMixIn):

    __tablename__ = 'markernotes'
    id = Column(types.Integer, primary_key=True)
    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Bin(BaseMixIn, Base, BinMixIn):

    __tablename__ = 'bins'
    batch_id = Column(types.Integer, ForeignKey('batches.id'), nullable=False)
    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    z = deferred(Column(NPArray))

    related_to_id = Column(types.Integer, ForeignKey('bins.id'), nullable=True)

    bins = deferred(Column(YAMLCol(8192), nullable=False, server_default=''))
    """ sorted known bins for this markers """

    meta = deferred(Column(YAMLCol(4096), nullable=False, server_default=''))
    """ metadata for this bin """

    remark = deferred(Column(types.String(512)))

    __table_args__ = (  UniqueConstraint( 'batch_id', 'marker_id' ), )


    @staticmethod
    def search(batch_id, marker_id, session):
        try:
            q = Bin.query(session).filter(Bin.batch_id == batch_id,
                    Bin.marker_id == marker_id)
            return q.one()
        except NoResultFound:
            return None



class Assay(BaseMixIn, Base, AssayMixIn):

    __tablename__ = 'assays'

    filename = Column(types.String(128), nullable=False, index=True)
    runtime = Column(types.DateTime, nullable=False)
    rss = Column(types.Float, nullable=False, server_default='-1')
    dp = Column(types.Float, nullable=False, server_default='-1')
    score = Column(types.Float, nullable=False, server_default='-1')
    z = deferred(Column(NPArray))
    ladder_peaks = Column(types.Integer, nullable=False, server_default='-1')

    size_standard = Column(types.String(32), nullable=False, server_default='')
    process_time = Column(types.Integer, nullable=False, server_default='-1')
    """ processing time for this assay in microseconds """

    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                        nullable=False)
    sample = relationship(Sample, uselist=False,
                backref=backref('assays', lazy='dynamic',
                    passive_deletes=True))

    panel_id = Column(types.Integer, ForeignKey('panels.id'), nullable=False)
    panel = relationship(Panel, uselist=False)

    ladder_id = Column(types.Integer,
                        ForeignKey('channels.id', use_alter=True,
                            name = 'fk_ladderchannel'),
                        nullable=True)

    ladder = relationship('Channel', uselist=False,
                primaryjoin = "Assay.ladder_id == Channel.id")

    #status = Column(types.String(32), nullable=False, server_default='')
    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status = EK.proxy('status_id', '@ASSAY-STATUS')

    #method = deferred(Column(types.String(16), nullable=False, server_default=''))
    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@ALIGN-METHOD')

    report = deferred(Column(types.String(512), nullable=False, server_default=''))
    remark = deferred(Column(types.String(1024), nullable=False, server_default=''))

    exclude = deferred(Column(types.String(128), nullable=False, server_default=''))

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
        #return AlleleSet.query(session).join(Channel).join(Assay, Channel.assay_id == Assay.id).filter( Assay.id == self.id )
        return Marker.query(session).join(Channel).join(Assay,
                    Channel.assay_id == Assay.id).filter( Assay.id == self.id )
    markers = property(_get_markers)

    def remove_channels(self):
        sess = object_session(self)
        for channel in self.channels:
            sess.delete(channel)


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
                    backref=backref('channels', lazy='dynamic',
                            passive_deletes=True))

    marker_id = Column(types.Integer, ForeignKey('markers.id'), nullable=False)
    marker = relationship(Marker, uselist=False, backref=backref('channels', lazy='dynamic'))

    #dye = Column(types.String(32), nullable=False)
    dye_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    dye = EK.proxy('dye_id', '@DYE')

    markers = relationship(Marker, secondary='channels_markers', viewonly=True)

    raw_data = deferred(Column(NPArray, nullable=False))
    """ raw data from channel as numpy array, can have empty array to accomodate
        allele data from CSV uploading """

    #status = Column(types.String(32), nullable=False)
    status_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    status = EK.proxy('status_id', '@CHANNEL-STATUS')

    wavelen = Column(types.Integer, nullable=False, server_default='0')
    median = Column(types.Integer, nullable=False, server_default='0')
    mean = Column(types.Float, nullable=False, server_default='0.0')
    std_dev = Column(types.Float, nullable=False, server_default='0.0')
    max_height = Column(types.Integer, nullable=False, server_default='-1')
    min_height = Column(types.Integer, nullable=False, server_default='-1')
    """ basic descriptive statistics for data"""

    data = deferred(Column(NPArray, nullable=False))
    """ data after smoothed using savitzky-golay algorithm and baseline correction
        using top hat morphologic transform
    """

    remark = deferred(Column(types.String(1024), nullable=False, server_default=''))


    def new_alleleset(self, revision=-1):
        return AlleleSet( channel = self, sample = self.assay.sample,
                            marker = self.marker )


    def clear(self):
        sess = object_session(self)
        for alleleset in self.allelesets:
            sess.delete(alleleset)


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

    revision = Column(types.Integer, nullable=False, server_default='0')
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

    #scanning_method = deferred(Column(types.String(32), nullable=False, server_default=''))
    scanning_method_id = deferred(Column(types.Integer, ForeignKey('eks.id'), nullable=False))
    scanning_method = EK.proxy('scanning_method_id', '@SCANNING-METHOD')
    """ method used for scanning and generating this alleleset """

    #calling_method = deferred(Column(types.String(32), nullable=False, server_default=''))
    calling_method_id = deferred(Column(types.Integer, ForeignKey('eks.id'), nullable=False))
    calling_method = EK.proxy('calling_method_id', '@ALLELE-METHOD')
    """ method used for calling this alleleset """

    #binning_method = deferred(Column(types.String(32), nullable=False, server_default=''))
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
                        order_by='Allele.rtime',
                        passive_deletes=True)
                )

    marker_id = Column(types.Integer, ForeignKey('markers.id', ondelete='CASCADE'),
                nullable=False)
    marker = relationship(Marker, uselist=False,
                backref=backref('alleles', cascade='all, delete-orphan',
                    passive_deletes=True))

    abin = Column(types.Integer, nullable=False, server_default='-1')    # adjusted bin
    asize = Column(types.Float, nullable=False, server_default='-1')     # adjusted size
    adelta = Column(types.Float, nullable=False, server_default='-1')    # adjusted delta, abs(abin - asize)
    aheight = Column(types.Float, nullable=False, server_default='-1')   # adjusted height

    bin = Column(types.Integer, nullable=False, server_default='-1')
    size = Column(types.Float, nullable=False, server_default='-1')
    deviation = Column(types.Float, nullable=False, server_default='-1')
    # deviation -> for ladder channel, this is ( z(rtime) - size )**2 or square of residual
    # for marker channel, this depends on the method
    # method cubic-spline, this is avg of deviation of the nearest peaks
    # for local southern, this is (size1 - size2) ** 2

    height = Column(types.Float, nullable=False, server_default='-1')
    area = Column(types.Float, nullable=False, server_default='-1')
    rtime = Column(types.Integer, nullable=False, server_default='-1')
    delta = Column(types.Float, nullable=False, server_default='-1')     # abs(bin - actual size)
    beta = Column(types.Float, nullable=False, server_default='-1')      # area / height
    theta = Column(types.Float, nullable=False, server_default='-1')     # height / width

    #type = Column(types.String(32), nullable=False, server_default='')
    type_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    type = EK.proxy('type_id', '@PEAK-TYPE')

    #method = Column(types.String(32), nullable=False, server_default='')   # binning method
    method_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    method = EK.proxy('method_id', '@BINNING-METHOD')

    brtime = Column(types.Integer, nullable=False, server_default='-1')
    ertime = Column(types.Integer, nullable=False, server_default='-1')
    wrtime = Column(types.Integer, nullable=False, server_default='-1')
    srtime = Column(types.Float, nullable=False, server_default='-1')   # log2( right_area/left_area )
    w25rtime = Column(types.Integer, nullable=False, server_default='-1')
    w50rtime = Column(types.Integer, nullable=False, server_default='-1')
    w75rtime = Column(types.Integer, nullable=False, server_default='-1')
    lshared = Column(types.Boolean, nullable=False, default=False)
    rshared = Column(types.Boolean, nullable=False, default=False)
    """ begin, end, width, symmetrical retention time of this peak and peak quality"""

    qscore = Column(types.Float, nullable=False, server_default='-1')    # calculated in preannotate()
    qcall = Column(types.Float, nullable=False, server_default='-1')     # calculated in call()


    @property
    def channel(self):
        return self.alleleset.channel


    def update(self, obj):

        self._update(obj)


# dataset_table manages relationship between dataset and alleleset
dataset_table = Table('datasets_allelesets', metadata,
    Column('id', types.Integer, Sequence('datasets_alleleset_seqid', optional=True),
        primary_key=True),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    Column('alleleset_id', types.Integer, ForeignKey('allelesets.id'), nullable=False),
    UniqueConstraint( 'dataset_id', 'alleleset_id' ))

dataset_batch_table = Table('datasets_batches', metadata,
    Column('id', types.Integer, Sequence('datasets_batches_seqid', optional=True),
        primary_key=True),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    Column('batch_id', types.Integer, ForeignKey('batches.id'), nullable=False),
    UniqueConstraint( 'dataset_id', 'batch_id' ))


@registered
class DataSet( BaseMixIn, Base ):
    """ DataSet

        DataSet basically performs versioning (snapshot-ing) on a set of allelesets
        by capturing the allele values on spesific samples at a specific time. Although
        optional, it is recommended that a snapshot be associated with a batch to ease
        the data management and versioning.

    """
    __tablename__ = 'datasets'

    uid = Column(types.String(8), nullable=False, unique=True)
    """ universal, stable 8-bytes string-based ID for this dataset """

    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    group = relationship(Group, uselist=False)
    """ primary group where this dataset belongs """

    acl = Column(types.Integer, nullable=False, server_default='0')
    """ access control list for this dataset """

    previous_id = Column(types.Integer, ForeignKey('datasets.id'), nullable=True)
    """ previous dataset """

    number = Column(types.Integer, nullable=False, server_default='1')
    """ order no of this dataset """

    latest = Column(types.Boolean, nullable=False, default=False)
    """ is this the latest dataset for this chain of set? """

    public = Column(types.Boolean, nullable=False, default=False)
    """ whether this dataset is publicly available """

    count = Column( types.Integer, nullable=False )
    """ how many allelesets within this dataset """

    desc = deferred( Column(types.Text(), nullable=False, server_default='') )
    """ any description for this dataset """

    remark = deferred( Column(types.Text(), nullable=False, server_default='') )
    """ any notes or remark for this dataset """

# dbversion_snapshot_table manages relationship between dbversion and snapshot
dbversion_dataset_table = Table('dbversions_datasets', metadata,
    Column('id', types.Integer, Sequence('dbversions_datasets_seqid', optional=True),
        primary_key=True),
    Column('dbversion_id', types.Integer, ForeignKey('dbversions.id'), nullable=False),
    Column('dataset_id', types.Integer, ForeignKey('datasets.id'), nullable=False),
    UniqueConstraint( 'dbversion_id', 'dataset_id' ))


@registered
class DBVersion( BaseMixIn, Base ):
    """ DBVersion

        DBVersion performs database versioning on a set of snapshots. Only the DBA
        or MasterData can create and manage a database version
    """

    __tablename__ = 'dbversions'

    uid = Column( types.String(8), nullable=False, unique=True )
    """ universal, stable 8-bytes string-bbased ID for this database version """

    label = Column( types.String(64), nullable=False, unique=True )
    """ version label """

    desc = Column( types.String(256), nullable=False, server_default='' )
    """ simple description of this label """
