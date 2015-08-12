<%inherit file="rhombus:templates/base.mako" />

<h1>Sample Data Verification</h1>

<p>Your sample data file has been saved temporarily.</p>


<a href="${request.route_url('genaf.batch-action',
            _query = { '_method': 'verify-sample-info',
                        'batch_id': batch.id,
                        '_path': path,
                    })}"><button class="btn btn-info">Verify</button></a>

%if errlog:
<p>Below is the log from the parsing process:</p>

${errlog | n}

%endif

