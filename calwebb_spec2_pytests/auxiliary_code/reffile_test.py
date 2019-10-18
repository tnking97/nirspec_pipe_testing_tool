#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 22 12:50:23 2018

@author: gkanarek
"""

import sys, os
from jwst.datamodels import open as dmodel_open
from astropy.io import fits
from astropy.time import Time
from crds.matches import find_match_paths_as_dict as ref_matches
from crds import getrecommendations

# import the subarrays dictionary
sys.path.insert(0, '../../utils')
from utils import subarray_dict as subdict


def check_meta(input_file, match_key, match_val):
    input_val = input_file[match_key.lower()]
    #direct comparison for numeric types; "in" comparison for string types
    if match_val in ["GENERIC", "ALL", "N/A", "ANY"]:
        return True
    if isinstance(input_val, str):
        return input_val in match_val
    return input_val == type(input_val)(match_val) #have to make sure because match_val is always a string

def get_streams(logfile=None):
    """
    Utility function to identify the output streams.
    """
    if logfile is None:
        errstream = sys.stderr
        logstream = sys.stdout
    else:
        errstream = logstream = open(logfile, 'a')
    return logstream, errstream

def load_input_file(path_to_input_file, logstream=None):
    """
    Utility function as a wrapper around dmodel_open.
    """
    if not isinstance(path_to_input_file, str):
        return path_to_input_file
    if logstream is not None:
        print("Loading input file...", file=logstream)
    try:
        input_file = dmodel_open(path_to_input_file)
    except ValueError:
        import pdb; pdb.set_trace()
    
    return input_file
    
    
def get_subarray(fits_file):
    print('Determining subarray')
    # set the subarray according to size
    detector = fits.getval(fits_file, "DETECTOR", 0)
    grating = fits.getval(fits_file, "GRATING", 0)
    substrt1 = fits.getval(fits_file, "substrt1", 0)
    substrt2 = fits.getval(fits_file, "substrt2", 0)
    subsize1 = fits.getval(fits_file, "subsize1", 0)
    subsize2 = fits.getval(fits_file, "subsize2", 0)
    for subarrd_key, subarrd_vals_dir in subdict.subarray_dict.items():
        sst1 = subarrd_vals_dir["substrt1"]
        sst2_dict = subarrd_vals_dir["substrt2"]
        ssz1 = subarrd_vals_dir["subsize1"]
        ssz2 = subarrd_vals_dir["subsize2"]
        # print ("sst1=", sst1, "  sst2_list=", sst2_list, "  ssz1=", ssz1, "  ssz2=", ssz2)
        if substrt1 == sst1 and subsize1 == ssz1 and subsize2 == ssz2:
            for grat, sst2_tuple in sst2_dict.items():
                if grat.lower() == grating.lower():
                    if 'FULL' in subarrd_key:
                        subarrd_key = 'FULL'
                    elif '200A1' in subarrd_key:
                        subarrd_key = 'SUBS200A1'
                    elif '200A2' in subarrd_key:
                        subarrd_key = 'SUBS200A2'
                    elif '200B1' in subarrd_key:
                        subarrd_key = 'SUBS200B1'
                    elif '400A1' in subarrd_key:
                        subarrd_key = 'SUBS400A1'
                    # this part is simply to check that the subarray values are correct
                    # but no values will be changed in the input file
                    if "1" in detector:
                        sst2 = sst2_tuple[0]
                    elif "2" in detector:
                        sst2 = sst2_tuple[1]
                    print("\nSubarray values in input file:", )
                    print("substrt1=", substrt1, " substrt2=", substrt2, " subsize1=", subsize1, " subsize2=", subsize2)
                    print("Subarray values in PTT dictionary:", )
                    print("substrt1=", sst1, " substrt2=", sst2, " subsize1=", ssz1, " subsize2=", ssz2)
                    print("Setting subarray keyword to ", subarrd_key, "\n")
    return subarrd_key


def reffile_test(path_to_input_file, pipeline_step, logfile=None,
                 input_file=None):
    """
    This is a new version of reffile_test which uses crds.matches instead of
    working with the reference file metadata directly. That way, if the rmap
    was updated manually on CRDS (to avoid redelivering files for a minor
    keyword change), this will test the actual match criteria.
    """
    
    logstream, errstream = get_streams(logfile=logfile)
    
    #Convert pipeline step to a header keyword if necessary
    if pipeline_step.upper().startswith("R_"):
        step_key = pipeline_step.upper()
    else:
        if len(pipeline_step) >= 6:
            step_key = "R_" + pipeline_step.upper()[:6]
        else:
            step_key = "R_" + pipeline_step.upper()
    
    #Identify the context
    context = fits.getval(path_to_input_file, "CRDS_CTX")
    
    #Identify the reference file
    try:
        reffile_name = fits.getval(path_to_input_file, step_key)
    except KeyError:
        print("Invalid pipeline step", file=errstream)
        return None
    
    reffile_name = reffile_name.replace('crds://', '')
    
    #Is there a reference file for this step? If not, PASS
    if reffile_name == "N/A":
        print("No reference file for step {}.".format(pipeline_step), file=errstream)
        return ""
    
    #Grab metadata from the input and reference files
    if input_file is None:
        input_file = load_input_file(path_to_input_file, logstream=logstream)
    print("Grabbing CRDS match criteria...", file=logstream)
    try:
        match_criteria = ref_matches(context, reffile_name)[0]
    except ValueError:
        import pdb; pdb.set_trace()
    
    tests = {} #store all the tests in a single dictionary

    # add instrument name in the expected keyword
    match_criteria['META.INSTRUMENT.NAME'] = 'NIRSPEC'

    # make sure that the subarray keyword is correct for the size of the data
    subarray = get_subarray(path_to_input_file)
    match_criteria['META.SUBARRAY.NAME'] = subarray

    #Test whether the recommended reference file was actually selected
    recommended_reffile = getrecommendations(match_criteria,
                                             reftypes=[pipeline_step],
                                             context=context,
                                             fast=True)

    if isinstance(recommended_reffile, str):
        recommended_reffile = os.path.basename(recommended_reffile) #remove path, only want to test filename
        tests['RECOMMENDATION'] = recommended_reffile == reffile_name
    else:
        print('* WARNING: Unable to find recommendation for the reference file:')
        print('        Match criteria determined by pipeline to find reference file: ', match_criteria)
        print('        Recommendation dictionary = ', recommended_reffile)

    #Remove irrelevant match criteria
    del match_criteria['observatory']
    del match_criteria['instrument']
    del match_criteria['filekind']
    
    #Useafter dates require special handling
    if "META.OBSERVATION.DATE" not in match_criteria:
        tests['USEAFTER'] = True
    else:
        input_date = input_file.meta.observation.date
        input_time = input_file.meta.observation.time
        input_obstime = Time(input_date + "T" + input_time)
        ref_date = match_criteria.pop("META.OBSERVATION.DATE")
        ref_time = match_criteria.pop("META.OBSERVATION.TIME")
        ref_useafter = Time(ref_date + "T" + ref_time)
        tests["USEAFTER"] = input_obstime >= ref_useafter
        #Note that this does NOT check whether there is a more recent
        #(but still valid) reference file that could have been selected
    
    #Loop over the rest of the matching criteria
    for criterion, value in match_criteria.items():
        tests[criterion] = check_meta(input_file, criterion, value)
    
    final = all([x or x is None for x in tests.values()])
    
    failures = []
    failmsg = "{}: reffile value {}, input value {}"
    
    #Finally, print out the results of the tests
    print("REFERENCE FILE SELECTION TEST", file=logstream)
    print("  Input file: {}".format(path_to_input_file), file=logstream)
    print("  Pipeline step: {}".format(pipeline_step), file=logstream)
    print("  Header keyword: {}".format(step_key), file=logstream)
    print("  Reference file selected: {}".format(reffile_name), file=logstream)
    print("  **Metadata tests performed:**", file=logstream)
    rescode = {None: "N/A", True: "PASS", False: "FAIL"}
    for meta in sorted(tests):
        result = tests[meta]
        print("    {}: {}".format(meta, rescode[result]), file=logstream)
        if rescode[result] == "FAIL":
            if meta == "USEAFTER":
                ival = input_obstime
                rval = ref_useafter
            else:
                ival = input_file[meta.lower()]
                rval = match_criteria[meta]
            failures.append(failmsg.format(meta, rval, ival))
            print("      Input file value: {}".format(ival), file=logstream)
            print("      Reference file value: {}".format(rval), file=logstream)
    print("  Final result: {}".format(rescode[final]), file=logstream)
    
    #Close the output stream if necessary
    if logfile is not None:
        logstream.close()
    
    return "\n".join(failures)

def create_rfile_test(step, doc_insert):
    """
    A factory to create wrappers for testing correct reference files.
    """
    
    def rfile_test_step(output_hdul):
        output_file = output_hdul[1]
        return reffile_test(output_file, step)
    
    rfile_test_step.__doc__ = """
    This function determines if the reference file for the {} matches the expected one.
    Args:
        output_hdul: output from the output_hdul function

    Returns:
        result: boolean, true if the reference file matches expected value
    """.format(doc_insert)
    
    return rfile_test_step

def check_all_reffiles(path_to_input_file, logfile=None):
    """
    A wrapper around reffile_test to test every reference file in the input
    file's header. A file path may be included to redirect output to a log.
    """
    
    all_steps = list(fits.getval(path_to_input_file, "R_*"))
    
    if logfile is not None: #erase existing log, since we'll be appending later
        with open(logfile, 'w'):
            pass
    
    #Only want to load the input file once
    input_file = load_input_file(path_to_input_file)
    
    failures = {}
    
    for step in all_steps:
        res = reffile_test(path_to_input_file, step, logfile=logfile, 
                           input_file=input_file)
        if res:
            failures[step] = res
        
    return failures

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test to see if the correct '
                                     'reference file was selected for the given'
                                     ' input file(s).')
    parser.add_argument('input_file', nargs='+', help="Paths to one or more input files")
    parser.add_argument('-l', '--log', help="Path to a desired output log file")
    
    args = parser.parse_args()
    
    for input_file in args.input_file:
        check_all_reffiles(input_file, logfile=args.log)
    