# handler.py - GenAF database handler

from rhombus.models import handler as rho_handler
from rhombus.lib.utils import cout, cerr, cexit
from genaf.models.sample import *
from genaf.models.ms import *
from fatools.lib.sqlmodels.handler_interface import base_sqlhandler


class DBHandler(rho_handler.DBHandler, base_sqlhandler):

    Marker = Marker
    Batch = Batch
    Location = Location
    Panel = Panel
    Sample = None

    def initdb(self, create_table=True, init_data=True):
        super().initdb(create_table, init_data)
        if init_data:
            from genaf.models.setup import setup
            setup( self.session )
            cerr('[genaf] Database has been initialized.')


    # overriding methods

    def get_batches(self, groups=None):
        
        q = self.Batch.query(self.session)
        q = q.filter( self.Batch.group_id.in_( [ x[1] for x in groups ] ) )

        return q.all()

    # search methods

    def search_location(self, country='', level1='', level2='', level3='', level4='',
                auto=False):
        return self.Location.search(country, level1, level2, level3, level4, auto,
                    dbsession = self.session())


    def get_locations(self):
        return self.Location.query( self.session() ).all()


    @classmethod
    def set_sample_class(cls, sample_class):
        cls.Sample = sample_class
        cls.Batch.set_sample_class( sample_class )

    @classmethod
    def set_assay_class(cls, assay_class):
        cls.Assay = assay_class
        cls.Sample.set_assay_class( assay_class )


DBHandler.set_sample_class( Sample )
DBHandler.set_assay_class( Assay )

