
import csv
import json
import os
from dateutil.parser import parse as parse_date
from datetime import date
from io import StringIO

csv_headers = { 'SAMPLE', 'PANEL', 'ASSAY', 'MARKER', 'DYE', 'NEST', 'STANDARD', 'TYPE',
                'COUNTRY', 'ADMINL1', 'ADMINL2', 'ADMINL3', 'ADMINL4', 'COLLECTION_DATE',
                'REMARK', 'CATEGORY', 'INT1', 'INT2', 'STRING1', 'STRING2' }

csv_alleles = { 'ALLELE', 'HEIGHT', 'AREA', 'SIZE' }

default_date = date(1990,1,1)


def check_csv_headers( fieldnames, csv_headers ):

    err_log = []

    # check field names
    if 'SAMPLE' not in fieldnames:
        raise RuntimeError( 'WARNING: SAMPLE not in the header! '
                            'Please check the header of your file and verify that the extension of the file matches '
                            'with the delimiter character used in the file.')

    for fieldname in fieldnames:
        if fieldname not in csv_headers:
            for csv_allele in csv_alleles:
                if fieldname.startswith( csv_allele ):
                    break
            else:
                err_log.append('Header not recognized: %s' % fieldname)
                #raise RuntimeError('CSV headers not recognized: %s' % fieldname)

    return err_log


def row2sample(r):

    if not r.get('COLLECTION_DATE', None):
        collection_date = default_date
    else:
        collection_date = parse_date( r.get('COLLECTION_DATE',''), dayfirst=False,
                default=default_date )

    sample = dict(

        collection_date = collection_date.strftime('%Y/%m/%d'),
        type = r.get('TYPE',''),
        location = (    r.get('COUNTRY', '').strip(),
                        r.get('ADMINL1','').strip(), r.get('ADMINL2','').strip(),
                        r.get('ADMINL3','').strip(), r.get('ADMINL4','').strip() ),
        remark = r.get('REMARK', ''),
        category = int(r.get('CATEGORY','') or 0),
        int1 = int(r.get('INT1','') or 0),
        int2 = int(r.get('INT2','') or 0),
        string1 = r.get('STRING1', '').strip(),
        string2 = r.get('STRING2', '').strip(),

        assays = {}
    )

    return sample


def reader_from_stream( istream, headers, delimiter ):

    reader = csv.DictReader( istream, delimiter = delimiter )
    errlog = check_csv_headers( reader.fieldnames, headers )

    return (reader, errlog)


def csv2dict(istream, with_report=False, delimiter='\t'):

    (reader, errlog) = reader_from_stream( istream, csv_headers, delimiter )
    #log = StringIO() if with_report else None

    return parse_csv( reader, errlog )


def parse_csv( reader, log, sample_func = None, existing_samples = None ):

    counter = 1

    #prepare allele, height, and area
    allele_field = [ x for x in reader.fieldnames if x.startswith('ALLELE') ]
    height_field = [ x for x in reader.fieldnames if x.startswith('HEIGHT') ]
    area_field = [x for x in reader.fieldnames if x.startswith('AREA') ]
    size_field = [x for x in reader.fieldnames if x.startswith('SIZE') ]

    allele_set = list(zip(allele_field, size_field, height_field, area_field))

    samples = existing_samples or {}
    sample_codes = existing_samples.keys() if existing_samples else []

    for row in reader:

        counter += 1
        name = row['SAMPLE']

        if name in samples:
            sample = samples[name]
        else:
            # create new sample
            try:
                sample = row2sample( row )
                if sample_func:
                    sample_func( sample, row )
                samples[name] = sample
                sample_codes.append( name )
            except ValueError as err:
                log.append('Line: %d -- ERROR in sample code: %s with err msg: %s' % (
                        counter, name, str(err)))
                continue
                #raise RuntimeError('ERROR in sample code: %s with err msg: %s' % (
                #        name, str(err)))

        assay_code = row.get('ASSAY', None)
        if assay_code is None:
            continue

        try:
            assay = sample['assays'][assay_code]
        except KeyError:
            assay = dict(
                panel=row['PANEL'],
                nest=row['NEST'],
                size_standard=row['STANDARD'],
                markers = {}
            )
            sample['assays'][assay_code] = assay

        markers = assay['markers']
        marker_name = row['MARKER']
        if marker_name in markers:
            if log:
                log.append( "ERROR: at line %d: duplicate marker name [%s]" %
                        ( counter, marker_name ) )
                return None, log
            else:
                raise RuntimeError('duplicate marker name at line %d!' % counter)

        allele_list = []
        for allele_header, size_header, height_header, area_header in allele_set:
            allele = row[allele_header] or 0
            size = row[size_header] or 0
            height = row[height_header] or 300
            area = row[area_header] or 0
            if int(allele) == 0:
                break
            allele_list.append( (int(allele), float(size), int(height), int(float(area))) )
        markers[marker_name] = dict( dye=row['DYE'], alleles=allele_list )

    return samples, log, sample_codes


def read_dictfile(pathname):
    _, ext = os.path.splitext( pathname )
    if ext == '.json':
        return json.load( open(pathname, 'rt') )
    elif ext == '.yaml':
        return yaml.load( open(pathname, 'rt') )


