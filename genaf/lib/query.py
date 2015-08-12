
from fatools.lib.analytics import query

class Query(query.Query):

    def get_sample_sets(self, sample_ids = None):
        if self._sample_sets is None or sample_ids:
            sample_sets = super().get_sample_sets(sample_ids)
            differentiator = self._params['differentiator']
            self._sample_sets = differentiator.get_sample_sets( sample_sets )
        return self._sample_sets



