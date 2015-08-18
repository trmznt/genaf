
from datetime import date

from rhombus.models.core import *
from rhombus.models.ek import EK
from rhombus.models.user import User, Group
from rhombus.models.mixin import *
from rhombus.lib.utils import cout, cerr

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func

from fatools.lib.const import *
from fatools.lib.fautil.mixin import ( BatchMixIn, SampleMixIn, NoteMixIn,
                                        BatchNoteMixIn, SampleNoteMixIn )

from genaf.lib import dictfmt


class Location(BaseMixIn, Base):

    __tablename__ = 'locations'

    country_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level1_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level2_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level3_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    level4_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    """ location information """

    country = EK.proxy('country_id', '@REGION')
    level1 = EK.proxy('level1_id', '@REGION')
    level2 = EK.proxy('level2_id', '@REGION')
    level3 = EK.proxy('level3_id', '@REGION')
    level4 = EK.proxy('level4_id', '@REGION')

    latitude = Column(types.Float, nullable=False, default=0)
    """ latitude of location/site """

    longitude = Column(types.Float, nullable=False, default=0)
    """ longitude of location/site """

    altitude = Column(types.Float, nullable=False, default=0)
    """ altitute of location/site """

    notes =  Column(types.String(128), nullable=False, default='')
    """ some notes about the location """

    __table_args__ = ( 
        UniqueConstraint('country_id', 'level1_id', 'level2_id', 'level3_id', 'level4_id'),
        {} )

    @staticmethod
    def search(country, level1='', level2='', level3='', level4='', auto=False, dbsession=None):
        assert dbsession
        country_id = EK._id(country.strip(), dbsession, '@REGION', auto)
        level1_id = EK._id(level1.strip(), dbsession, '@REGION', auto)
        level2_id = EK._id(level2.strip(), dbsession, '@REGION', auto)
        level3_id = EK._id(level3.strip(), dbsession, '@REGION', auto)
        level4_id = EK._id(level4.strip(), dbsession, '@REGION', auto)

        q = Location.query(dbsession).filter(
                and_(Location.country_id == country_id,
                        Location.level1_id == level1_id,
                        Location.level2_id == level2_id,
                        Location.level3_id == level3_id,
                        Location.level4_id == level4_id) )
        r = q.all()
        if len(r) == 0 and auto:
            location = Location( country_id = country_id,
                                level1_id = level1_id,
                                level2_id = level2_id,
                                level3_id = level3_id,
                                level4_id = level4_id )
            dbsession.add( location )
            dbsession.flush()

            return location

        return r[0]


    @staticmethod
    def grep(term, dbsession):
        regions = EK.get_members('@REGION', dbsession).filter( EK.key.contains( term.lower() ) )
        ids = [ r.id for r in regions ]
        return Location.query(dbsession).filter(
            or_( Location.country_id.in_( ids ), Location.level1_id.in_( ids ),
                Location.level2_id.in_( ids ), Location.level3_id.in_( ids ),
                Location.level4_id.in_( ids ) ) )


    def render(self, level=4):
        level = int(level)
        if level < 0:
            return ''
        names = [ self.country ]
        if level >= 1 and self.level1:
            names.append( self.level1 )
        if level >= 2 and self.level2:
            names.append( self.level2 )
        if level >= 3 and self.level3:
            names.append( self.level3 )
        if level >= 4 and self.level4:
            names.append( self.level4 )
        return ' / '.join( names )


    def __repr__(self):
        return '<Location: %s>' % self.render()


    def sample_count(self):
        return self.samples.count()


    @staticmethod
    def from_dict_XXX(d, update=False):
        return Location.search( d['country'], d['adminl1'], d['adminl2'],
                                d['adminl3'], d['adminl4'], auto=True )



class Note(BaseMixIn, Base, NoteMixIn):

    __tablename__ = 'notes'

    text = Column(types.String(1024), nullable=False, default='')
    cat = Column(types.String(32), nullable=False, default='')
    stamp = Column(types.DateTime, nullable=False)



class Batch(BaseMixIn, Base, BatchMixIn):

    __tablename__ = 'batches'

    code = Column(types.String(16), nullable=False, unique=True)
    #assay_provider = Column(types.String(32), nullable=False, default='')
    assay_provider_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)
    description = Column(types.String(1024), nullable=False, default='')
    remark = deferred(Column(types.String(1024), nullable=True))
    data = deferred(Column(YAMLCol(4096), nullable=False, default=''))
    species_id = Column(types.Integer, ForeignKey('eks.id'), nullable=False)
    species = EK.proxy('species_id', '@SPECIES')

    ## GenAF spesific schema
    group_id = Column(types.Integer, ForeignKey('groups.id'), nullable=False)

    ## relationship
    group = relationship(Group, uselist=False, foreign_keys = group_id)

    ## other class variable ##
    sample_class = None


    def update(self, obj):

        self._update(obj)

        if type(obj) == dict:
            if 'group_id' in obj:
                self.group_id = obj['group_id']
            if 'assay_provider_id' in obj:
                self.assay_provider_id = obj['assay_provider_id']
            if 'species_id' in obj:
                self.species_id = obj['species_id']
            if 'data' in obj:
                self.data = obj['data']


    def add_sample(self, sample_code):
        """ return a new Sample with sample_code """

        _Sample = self.get_sample_class()
        sample = _Sample()
        sample.code = sample_code
        sample.batch = self

        return sample


    def search_sample(self, sample_code):
        """ return a single Sample from the current batch with sample_code """
        _Sample = self.get_sample_class()
        try:
            return self.samples.filter( func.lower(_Sample.code) == func.lower(sample_code),
                _Sample.batch_id == self.id ).one()
        except NoResultFound:
            return None


    @staticmethod
    def search(code, session):
        """ provide case-insensitive search for batch code """
        q = Batch.query(session).filter( func.lower(Batch.code) == func.lower(code) )
        return q.one()


    def get_panel(self, panel_code):
        return Panel.search(panel_code, object_session(self))


    def get_marker(self, marker_code, species=None):
        session = object_session(self)
        markers = None  #XXX: Fix me
        raise NotImplementedError()


    @property
    def sample_ids(self):
        """ faster implementation of getting sample ids """
        session = object_session(self)
        _Sample = self.get_sample_class()
        return [ x[0] for x in session.query(_Sample.id).filter(_Sample.batch_id == self.id) ]


    @classmethod
    def set_sample_class(cls, sample_class):
        cerr('BATCH: sample_class set to: %s' % sample_class)
        cls.sample_class = sample_class


    @classmethod
    def get_sample_class(cls):
        if cls.sample_class is None:
            raise RuntimeError('PROG/ERR - sample class need to be set first')
        return cls.sample_class

    @classmethod
    def get_panel_class(cl):
        if cls.sample_class is None:
            raise RuntimeError('PROG/ERR - sample class need to be set first')
        return cls.panel_class


    @staticmethod
    def get_parser_module():
        """ return module that provides CSV/JSON """
        return dictfmt


class BatchNote(Base, BatchNoteMixIn):

    __tablename__ = 'batchnotes'

    id = Column(types.Integer, primary_key=True)
    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)



class Sample(BaseMixIn, Base, SampleMixIn):

    __tablename__ = 'samples'

    code = Column(types.String(64), nullable=False)
    type = Column(types.String(1), default='S')
    altcode = Column(types.String(16), nullable=True)               # custom usage
    category = Column(types.Integer, nullable=False, default=0)     # custom usage
    batch_id = Column(types.Integer, ForeignKey('batches.id', ondelete='CASCADE'),
                nullable=False)
    batch = relationship(Batch, uselist=False,
                backref=backref('samples', lazy='dynamic', passive_deletes=True))
    int1 = Column(types.Integer, nullable=False, default=0)        # custom usage
    int2 = Column(types.Integer, nullable=False, default=0)        # custom usage
    string1 = Column(types.String(16), nullable=False, default='')  # custom usage
    string2 = Column(types.String(16), nullable=False, default='')  # custom usage
    remark = deferred(Column(types.String(1024), nullable=True))

    ## GenAF custom scheme

    polymorphic_type = Column(types.Integer, nullable=False, default=0)

    __mapper_args__ = { 'polymorphic_on': polymorphic_type }

    __table_args__ = (  UniqueConstraint( 'code', 'batch_id' ),
                        UniqueConstraint( 'altcode', 'batch_id')
                    )

    ## GenAF custom schema
 
    shared = Column(types.Boolean, nullable=False, default=False)
    """ whether this particular sample has been shared (viewable/searchable by other
        users), necessary so that individual sample can be shared without all samples
        within a group being shared)
    """

    collection_date = Column(types.Date, nullable=False)
    """ the date of the sample collection """

    location_id = Column(types.Integer, ForeignKey('locations.id'), nullable=False)
    location = relationship(Location, uselist=False,
            backref=backref("samples", lazy='dynamic', passive_deletes=True))
    """ relation to location, with cascading delete """

    latitude = Column(types.Float, nullable=False, default=0)
    """ exact latitude of the sample """

    longitude = Column(types.Float, nullable=False, default=0)
    """ exact longitude of the sample """

    altitude = Column(types.Float, nullable=False, default=0)
    """ exact altitute of the sample """

    comments = deferred( Column(types.Text(), nullable=False, default='') )

    trashed = Column(types.Boolean, nullable=False, default=False)
    """ whether this sample has been marked as deleted """

    markers = []    ## <- what this is for??

    ## other class variables ##
    assay_class = None


    def new_assay(self, raw_data, filename, status, panel=None):
        Assay = self.get_assay_class()
        assay = Assay( raw_data = raw_data, filename = filename )
        if panel is None:
            panel = Panel.search('undefined', object_session(self))
        assay.panel = panel
        assay.sample = self
        assay.status = status
        return assay


    def update(self, obj):

        self._update(obj)

        if type(obj) == dict:
            if 'type' in obj:
                self.type = obj['type']
            if 'collection_date' in obj:
                collection_date = obj['collection_date']
                if type(collection_date) is str:
                    collection_date = date(*[ int(x) for x in collection_date.split('/') ])
                self.collection_date = collection_date
            if 'location' in obj:
                location_code = obj['location']
                location = Location.search(
                                location_code[0], location_code[1],
                                location_code[2], location_code[3], 
                                location_code[4], auto=True, dbsession = object_session(self) )
                cerr('LOCATION: %s' % location)
                self.location = location
            if 'latitude' in obj:
                self.latitute = obj['latitude']
            if 'longitude' in obj:
                self.longitude = obj['longitude']
            if 'altitute' in obj:
                self.altitute = obj['altitude']
            if 'remark' in obj:
                self.remark = obj['remark']
            if 'int1' in obj:
                self.int1 = obj['int1']
            if 'int2' in obj:
                self.int2 = obj['int2']
            if 'string1' in obj:
                self.string1 = obj['string1']
            if 'string2' in obj:
                self.string2 = obj['string2']

        else:

            raise NotImplementedError('PROG/ERR - not implemented yet')


    @staticmethod
    def csv2dict( *args, **kwargs ):
        return dictfmt.csv2dict( *args, **kwargs )

    @classmethod
    def set_assay_class(cls, assay_class):
        cls.assay_class = assay_class

    @classmethod
    def get_assay_class(cls):
        if cls.assay_class is None:
            raise RuntimeError('PROG/ERR - sample class need to be set first')
        return cls.assay_class


class SampleNote(Base, SampleNoteMixIn):

    __tablename__ = 'samplenotes'
    id = Column(types.Integer, primary_key=True)
    sample_id = Column(types.Integer, ForeignKey('samples.id', ondelete='CASCADE'),
                nullable=False)
    note_id = Column(types.Integer, ForeignKey('notes.id', ondelete='CASCADE'),
                nullable=False)





