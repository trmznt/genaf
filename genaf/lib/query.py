
from fatools.lib.analytics import query


def load_yaml(yaml_text):

    d = yaml.load( yaml_text )
    return load_params( d )


def load_params( d ):
    instances = {}
    for k in d:
        if k == 'selector':
            instances['selector'] = _SELECTOR_CLASS_.from_dict( d[k] )
        elif k == 'filter':
            instances['filter'] = _FILTER_CLASS_.from_dict( d[k] )
        elif k == 'differentiator':
        	instances['differentiator'] = _DIFFERENTIATOR_CLASS_.from_dict( d[k] )
        else:
            raise RuntimeError()

    return instances


class Query(query.Query):

    def get_sample_sets(self, sample_ids = None):
        if self._sample_sets is None or sample_ids:
            sample_sets = super().get_sample_sets(sample_ids)
            differentiator = self._params['differentiator']
            self._sample_sets = differentiator.get_sample_sets( sample_sets )
        return self._sample_sets


class Selector(query.Selector):
	pass

class Filter(query.Filter):
	pass

class Differentiator(object):

	def __init__(self):
		pass

	@staticmethod
	def from_dict(d):
		return Differentiator()

	def get_sample_sets(self, sample_sets):
		return sample_sets

_SELECTOR_CLASS_ = Selector
_FILTER_CLASS_ = Filter
_DIFFERENTIATOR_CLASS_ = Differentiator


def set_query_class( selector_class=None, filter_class=None, differentiator_class=None ):
	global _SELECTOR_CLASS_, _FILTER_CLASS_, _DIFFERENTIATOR_CLASS_
	if selector_class:
		_SELECTOR_CLASS_ = selector_class
	if filter_class:
		_FILTER_CLASS_ = filter_class
	if differentiator_class:
		_DIFFERENTIATOR_CLASS_ = differentiator_class





