"""
This file contains the functions which will be used to test the wcs_assign step
of the JWST Calibration Pipeline.

Selected keywords are checked to verify that the step ran through successfully.
"""


def create_completed_steps_txtfile(True_steps_suffix_map, step_input_file):
    """
    This function creates the completed steps along with the corresponding suffix of the output file name into a text file.
    Args:
        True_steps_suffix_map: string, full path of where the text file will be written into
        step_input_file: string, name of the input file for the pipeline step

    Returns:
        Nothing. A text file will be created in the pytests directory where all steps will be added
    """
    # name of the text file to collect the step name and suffix
    print ("Map created at: ", True_steps_suffix_map)
    line0 = "# {:<20}".format("Input file: "+step_input_file)
    line1 = "# {:<17} {:<20} {:<20} {:<20}".format("Step", "Added suffix", "Step complition", "Time to run [s]")
    with open(True_steps_suffix_map, "w+") as tf:
        tf.write(line0+"\n")
        tf.write(line1+"\n")


def create_map_from_full_run(full_run_map, step_input_file):
    """
    This function creates the map of fits file names of the intermediary step outputs when running the pipeline in
    a single complete run using the calwebb_spec2.cfg file.
    Args:
        full_run_map: string, full path of where the text file will be written into
        step_input_file: string, name of the input file for the pipeline step

    Returns:
        Nothing. A text file will be created in the pytests directory where all intermediary product files are mapped.
    """

    # list of the steps that produce output fits files (in order of completion)
    pipe_steps = ["assign_wcs", "bkg_subtract", "imprint_subtract", "msa_flagging", "extract_2d", "flat_field",
                  "pathloss", "barshadow", "photom", "resample_spec", "cube_build", "extract_1d"]

    # name of the text file to collect the step name and suffix
    print ("Map created at: ", full_run_map)
    line0 = "# {:<20}".format("Input file: "+step_input_file)
    line1 = "# {:<17} {:<20}".format("Step", "File name")
    with open(full_run_map, "w+") as tf:
        tf.write(line0+"\n")
        tf.write(line1+"\n")
        for stp in pipe_steps:
            line2 = "{:<20} {:<20}".format(stp, "".join((stp, ".fits")))
            tf.write(line2+"\n")




### VERIFICATION FUNCTIONS

def wavstart_exists(output_hdul):
    """
    This function checks that the keyword WAVSTART was added.
    Args:
        outout_hdul: the HDU list of the header keywords

    Returns:
        result: boolean, true if the keyword was indeed added
    """
    result = "WAVSTART" in output_hdul
    return result


def wavend_exists(output_hdul):
    """
    This function checks that the keyword WAVEND was added.
    Args:
        outout_hdul: the HDU list of the header keywords

    Returns:
        result: boolean, true if the keyword was indeed added
    """
    result = "WAVEND" in output_hdul
    return result


def sporder_exists(output_hdul):
    """
    This function checks that the keyword SPORDER was added.
    Args:
        outout_hdul: the HDU list of the header keywords

    Returns:
        result: boolean, true if the keyword was indeed added
    """
    result = "SPORDER" in output_hdul
    return result


def s_wcs_exists(output_hdul):
    """
    This function checks that the keyword S_WCS was added.
    Args:
        outout_hdul: the HDU list of the header keywords

    Returns:
        result: boolean, true if the keyword was indeed added
    """
    result = "S_WCS" in output_hdul
    return result


