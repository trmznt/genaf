
from fatools.lib.analytics import query
from fatools.lib.analytics import selector
from fatools.lib.analytics.sampleset import SampleSet, SampleSetContainer

from rhombus.lib.utils import get_dbhandler

from sqlalchemy import extract
from pandas import DataFrame, pivot_table

from collections import OrderedDict
from itertools import cycle
import yaml


def load_yaml(yaml_text):

    d = yaml.load( yaml_text )
    return load_params( d )


def load_params( d ):
    instances = {}
    for k in d:
        if k == 'selector':
            instances['selector'] = _SELECTOR_CLASS_.from_dict( d[k] )
            print(instances['selector'])
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
            self._sample_sets = super().get_sample_sets(sample_ids)
            differentiator = self._params.get('differentiator', None)
            if differentiator:
                self._sample_sets = differentiator.get_sample_sets( self._sample_sets )
        return self._sample_sets


class FieldBuilder(object):

    def __init__(self, q, dbh):
        self._q = q
        self._dbh = dbh
        self._joined_classes = []


    def _eval_arg(self, arg, field):

        if type(arg) == str:
            if '|' in arg:
                arg = [ x.strip() for x in arg.split('|') ]
            elif ',' in arg:
                arg = [ x.strip() for x in arg.split(',') ]

        if type(arg) == list:
            return field.in_(arg)

        if type(arg) == str:
            arg = arg.strip()

        if type(arg) == str and arg.startswith('!'):
            return field != arg[1:].strip()
        return field == arg


    def _eval_ek_arg(self, arg, field_id):

        if '|' in arg:
            arg = [ x.strip() for x in arg.split('|') ]
        elif ',' in arg:
            arg = [ x.strip() for x in arg.split(',') ]

        if type(arg) == list:
            ek_ids = [ self._dbh.EK._id(x) for x in arg ]
            return field_id.in_( ek_ids )

        arg = arg.strip()

        if arg.startswith('!'):
            return field_id != self._dbh.EK._id( arg[1:].strip() )
        return field_id == self._dbh.EK._id( arg )


    def _add_class(self, class_):
        if class_ not in self._joined_classes:
            self._joined_classes.append(class_)
            self._q = self._q.join(class_)


    def _get_query(self):
        return self._q


    # fields

    def batch(self, arg):
        self._add_class(self._dbh.Batch)
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Batch.code) )


    def code(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.code) )

    def category(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.category) )

    def int1(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.int1) )

    def int2(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.int2) )

    def string1(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.string1) )

    def string2(self, arg):
        self._q = self._q.filter(
            self._eval_arg(arg, self._dbh.Sample.string2) )

    def country(self, arg):
        self._add_class( self._dbh.Location )
        self._q = self._q.filter(
            self._eval_ek_arg(arg, self._dbh.Location.country_id) )

    def adminl1(self, arg):
        self._add_class( self._dbh.Location )
        self._q = self._q.filter(
            self._eval_ek_arg(arg, self._dbh.Location.level1_id) )

    def adminl2(self, arg):
        self._add_class( self._dbh.Location )
        self._q = self._q.filter(
            self._eval_ek_arg(arg, self._dbh.Location.level2_id) )

    def adminl3(self, arg):
        self._add_class( self._dbh.Location )
        self._q = self._q.filter(
            self._eval_ek_arg(arg, self._dbh.Location.level3_id) )

    def adminl4(self, arg):
        self._add_class( self._dbh.Location )
        self._q = self._q.filter(
            self._eval_ek_arg(arg, self._dbh.Location.level4_id) )



class Selector(query.Selector):

    def get_fieldbuilder(self, q, dbh):
        return FieldBuilder(q, dbh)

    def filter_sample(self, spec, dbh, q):
        """ return the query after being built with YAML spec """

        builder = self.get_fieldbuilder(q, dbh)

        print('>>>>> GENAF FILTERING >>>>>>')

        for key in spec:
            if key.startswith('_'):
                continue

            try:
                func = getattr(builder, key)

            except AttributeError:
                raise RuntimeError('ERR: unknown field: %s' % key)

            func( spec[key] )

        return builder._get_query()


    def add_class(self, q, class_list, class_):
        if class_ not in class_list:
            class_list.append(class_)
            return q.join(class_)
        return q


    def eval_ek_arg(self, arg, identifier, dbh):
        if arg[0] == '!':
            return identifier != dbh.EK._id( arg[1:].strip() )
        else:
            return identifier == dbh.EK._id( arg.strip() )


class Filter(query.Filter):
	pass


class Differentiator(object):

    def __init__(self):
        self.spatial = None
        self.temporal = None
        self.int1 = None
        self.int2 = None
        self.string1 = None
        self.string2 = None

        #helpers
        self.location_renderer = None
        self.location_cache = {}

        #handler
        self.dbh = get_dbhandler()


    @staticmethod
    def from_dict(d):
        diff = Differentiator()
        diff.spatial = d['spatial']
        diff.temporal = d['temporal']
        return diff


    def get_sample_sets(self, sample_sets):

        diff_sample_sets = self.do_differentiation( sample_sets )

        return self.generate_sample_sets( diff_sample_sets )


    def do_differentiation(self, sample_sets):
        """ return a dict of { tag: sample_ids } """

        curr_sample_sets = [ (s.label, s.sample_ids) for s in sample_sets ]

        dbh = self.dbh

        new_sample_sets = OrderedDict()

        for (label, sample_ids) in curr_sample_sets:
            q = dbh.session().query( dbh.Sample.id, dbh.Sample.location_id,
                        extract('year', dbh.Sample.collection_date),
                        extract('month', dbh.Sample.collection_date),
                        dbh.Sample.int1, dbh.Sample.int2,
                        dbh.Sample.string1, dbh.Sample.string2
                        ).filter( dbh.Sample.id.in_(sample_ids))

            rows = [
                (int(s_id), self.render_location(loc_id), yr, mo,
                    int1, int2, str1, str2)
                for (s_id, loc_id, yr, mo, int1, int2, str1, str2) in q
            ]

            if not len(rows) > 0:
                continue

            # create tag for each sample
            for (s_id, loc, yr, mo, int1, int2, str1, str2) in rows:
                tag = [ label ]
                if self.spatial >= 0:
                    tag.append( loc )
                if self.temporal > 0:
                    if self.temporal == 1:
                        tag.append( '%d' % yr )
                    elif self.temporal == 2:
                        half = 'H2' if mo >= 6 else 'H1'
                        tag.append( '%d %s' % (yr, half) )
                    elif self.temporal == 3:
                        quarter = 'Q4' if mo >= 9 else ( 'Q3' if mo >= 6
                                        else ('Q2' if mp >= 3 else 'Q1'))
                        tag.append( '%d %s'% (yr, quarter) )
                    else:
                        raise RuntimeError('ERR - unknown temporal setting')
                if self.int1:
                    tag.append( str(int1) )
                if self.int2:
                    tag.append( str(int2) )
                if self.string1:
                    tag.append(str1)
                if self.string2:
                    tag.append(str2)
                tag = tuple(tag)

                try:
                    new_sample_sets[tag].append( s_id )
                except KeyError:
                    new_sample_sets[tag] = [ s_id ]

        return new_sample_sets

        curr_sample_sets = self.do_spatial_differentiation(curr_sample_sets)
        curr_sample_sets = self.do_temporal_differentiation(curr_sample_sets)

        return curr_sample_sets


    def generate_sample_sets(self, sample_set_dict):
        """ given a dict of sample sets, create proper SampleSet """

        colours = cycle(selector.colour_list)
        sample_sets = SampleSetContainer()

        for (tag, sample_ids) in sample_set_dict.items():
            sample_sets.append(
                        SampleSet(label = ' | '.join(tag),
                            colour = next(colours),
                            sample_ids = set(sample_ids))
                    )

        return sample_sets


    def render_location(self, location_id):
        if self.spatial < 0:
            return ''

        try:
            return self.location_cache[location_id]
        except KeyError:
            pass

        location = self.dbh.get_location_by_id(location_id)
        render = location.render(self.spatial)
        self.location_cache[location_id] = render
        return render



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





