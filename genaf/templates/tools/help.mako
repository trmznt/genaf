<%inherit file="rhombus:templates/plainbase.mako" />

<h3>Help for Analysis Tools</h3>

<a name="basic_form"></a>
<h4>Query Parameters</h4>

<dl>

<dt><a name="allele_abs_threshold"></a>
Allele absolute threshold <code>abs_threshold</code></dt>

<dd>The minimum absolute rfu value for each peak to be considered as a real peak. Common values are 50 and 100.</dd>


<dt><a name="allele_rel_threshold"></a>
Allele relative threshold <code>rel_threshold</code></dt>

<dd>The minimum relative rfu against the major peak rfu for each peak to be considered as real peak. Common value is 0.33, but you can change accordingly. The lower the value, the more minor alleles you are likely to get.</dd>

<dt><a name="allele_rel_cutoff"></a>Allele relative cutoff</dt>
<dd>The relative value for cutoff for any minor alleles for deciding whether a sample should be included in the analysis. For example, a cutoff value of 0.95 indicates that if any of the marker in a sample have a minor alleles more than 0.95 relative to the dominant allele, the sample will be excluded from the analysis.<dd>

<dt><a name="sample_qual_threshold"></a>Sample quality threshold</dt>
<dd>This value indicates the minimum number of successfully genotyped locus (marker) relative to the available loci (markers) for a sample to be included in the analysis. For example, a cut of value of 0.25 for 9 markers indicates that the necessary genotyped loci for a marker to be included in the analysis is 3 (round up of 2.25 = 0.25 * 9).</dd>

<dt><a name="marker_qual_threshold"></a>Marker failure cutoff</dt>
<dd>This value indicates the minimum number of successfully genotyped samples of a particular marker relative to the available sample in the analysis set to be included in the analysis.
<dd>

</dl>

<a name="yaml_form"></a>
<h4>YAML Form</h4>

<p>The YAML form uses query text formatted in YAML. The advantage of using a YAML-formatted query
text is that you can copy and paste the query text and save it for future use, or for sharing with other users to get consistent parameters (and consistent results). Also, if you need to perform similar analysis with only a few modification, using YAML-formatted query text is probably more convenient.
</p>

<p>The following is an example showing all possible settings:
<pre>

selector:
  ID:
    - { batch: IDPV }

filter:
  markers: [ MS1,MS10,MS12,MS16,MS20,MS5,MS8,msp1f3,pv3.27 ]
  abs_threshold: 50
  rel_threshold: 0.33
  rel_cutoff: 0
  sample_qual_threshold: 0.1
  marker_qual_threshold: 0.1
  sample_option: A
  peak_type: [binned]
  stutter_ratio: 0.5
  stutter_range: 3.5

differentiator:
  spatial: -1
  temporal: -1

</pre>
</p>

<a name="filtering_process"></a>
<h4>Filtering Process</h4>

<p>Filtering process is performed to obtain a set of samples and markers for the analysis.
The filtering parameters determine how good a sample is being considered to be included in
the analysis, and how good a marker/locus is to be included for the analysis.</p>

<p>The filtering process starts by creating an initial set (or a base set) containing all samples and markers/loci as indicated by the <code>selector</code>,
<code>filter.sample_option</code> and <code>filter.markers</code> in the query. The base set
will then be differentiated based on the differentiatior into base analytical sets. Using the
base markers/loci, the quality of the samples are assessed, and all samples adhering to the sample quality threshold are pooled into filtered sample set. The filtered sample set is then
used to assess the quality of the base markers/loci to obtain those markers that adheres to
marker quality threshold. Using the filtered sample set and filtered marker set, a new
analytical set is produced as filtered analytical sets.
<p>




