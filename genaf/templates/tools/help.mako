<%inherit file="rhombus:templates/plainbase.mako" />

<h3>Help for Analysis Tools</h3>

<a name="basic_form"></a>
<h4>Basic Form</h4>

<dl>

<dt><a name="allele_abs_threshold"></a>Allele absolute threshold</dt>
<dd>The minimum absolute rfu value for each peak to be considered as a real peak. Common values are 50 and 100.</dd>

<dt><a name="allele_rel_threshold"></a>Allele relative threshold</dt>
<dd>The minimum relative rfu against the major peak rfu for each peak to be considered as real peak. Common value is 0.33, but you can change accordingly. The lower the value, the more minor alleles you are likely to get.</dd>

<dt><a name="allele_rel_cutoff"></a>Allele relative cutoff</dt>
<dd>The relative value for cutoff for any minor alleles for deciding whether a sample should be included in the analysis. For example, a cutoff value of 0.95 indicates that if any of the marker in a sample have a minor alleles more than 0.95 relative to the dominant allele, the sample will be excluded from the analysis.<dd>

<dt><a name="sample_qual_threshold"></a>Sample quality threshold</dt>
<dd>This value indicates the minimum number of successfully genotyped locus (marker) relative to the available loci (markers) for a sample to be included in the analysis. For example, a cut of value of 0.25 for 9 markers indicates that the necessary genotyped loci for a marker to be included in the analysis is 3 (round up of 2.25 = 0.25 * 9).</dd>

<dt><a name="marker_qual_threshold"></a>Marker quality threshold</dt>
<dd>This value indicates the minimum number of successfully genotyped samples of a particular marker relative to the available sample in the analysis set to be included in the analysis.
<dd>

</dl>

<a name="yaml_form"></a>
<h4>YAML Form</h4>

<p>The YAML form uses query text formatted in YAML. The advantage of using a YAML-formatted query
text is that you can just copy and paste the query text for saving or for sharing with other users to get consistent parameters (and consistent results). Also, if you need to perform similar analysis with only a few modification, using YAML-formatted query text is probably more convenient.
</p>

<p>The following is an example showing all possible settings:
<pre>
</pre>
</p>




