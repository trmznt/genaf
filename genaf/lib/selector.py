

from fatools.lib.const import peaktype
from fatools.lib import analytics


class Selector(analytics.Selector):

    def get_sample_sets(self, dbh, sample_ids=None):

        sample_sets = super().get_sample_sets(dbh, sample_ids)

        # now use the differentiatior
        


class Differentiator(object):

    pass
