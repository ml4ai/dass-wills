""" driver.py --
End to end system to extract will model and output devolution items """

import argparse
import sys, os
import shutil, subprocess

################################################################################
#                                                                              #
#                                  UTILITIES                                   #
#                                                                              #
################################################################################


def cmd_line_invocation():
    desc_text = """This is an end to end system that extracts the Will text extractions json, 
    Will Model, and Will Devolution items given input a Will text file."""

    parser = argparse.ArgumentParser(description=desc_text)
    parser.add_argument(
        "-i",
        "--input-text-file",
        type=str,
        required=True,
        help="Input path to the will text file. Ensure it's a text (.txt) file.",
    )
    parser.add_argument(
        "-o",
        "--output-path",
        type=str,
        required=True,
        help="Output path to store Will extractions json, \
Will Model object, and Will Devolution text file.",
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        required=True,
        help="OPEN AI API KEy.\n",
    )
    args = parser.parse_args()

    return args

################################################################################
#                                                                              #
#                                  Driver Code                                 #
#                                                                              #
################################################################################


def main():
    """This driver code does the following actions:

    - Process the will text and get text extractions json,
    - Process the text extractions json, and get the Will Model object.
    - Process the Will Model, and get the Devolution output."""

    args = cmd_line_invocation()
    input_file = args.input_text_file
    output_path= args.output_path
    key = args.key

    # Paths check
    if not os.path.isfile(input_file):
        print(f"Error: The input file '{input_file}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(output_path):
        print(f"The output directory '{output_path}' does not exist. Creating it now.")
        os.makedirs(output_path) 

    env = os.environ.copy()
    env['OPENAI_API_KEY'] = key

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ## Front End Script Paths
    te_script =  os.path.abspath(os.path.join(base_dir, '..','frontend', 'text2extractions', 'src', 'main.py'))
    te_input_path = os.path.abspath(os.path.join(base_dir, '..','frontend', 'text2extractions', 'input'))
    te_base_path = os.path.abspath(os.path.join(base_dir, '..','frontend', 'text2extractions', 'src'))
    
    ## Backend Script Paths
    backend_base_path = os.path.abspath(os.path.join(base_dir, '..','backend'))
    te_to_wm_script = os.path.abspath(os.path.join(base_dir, '..','backend', 'te_to_wm.py'))
    devolution_script = os.path.abspath(os.path.join(base_dir, '..','backend', 'devolve_will.py'))

    if not os.path.isfile(te_script):
        print(f"Error: The module 'text to extractions' does not exist.")
        sys.exit(1)
    if not os.path.isfile(te_to_wm_script):
        print(f"Error: The module 'text extractions to Will Model' does not exist.")
        sys.exit(1)
    if not os.path.isfile(devolution_script):
        print(f"Error: The module 'Will Model Devulution' does not exist.")
        sys.exit(1)
    
    try:
        shutil.copy(input_file, te_input_path)
    except shutil.SameFileError:
        pass
        

    cmd_te = ['python3', te_script]
    print("... Will Text to TE Module processing.\n")
    p1 = subprocess.Popen(cmd_te, stdout=subprocess.PIPE, stderr=subprocess.PIPE,cwd =te_base_path,env=env)
    for stdout_line in iter(p1.stdout.readline, b''):
        sys.stdout.write(stdout_line.decode())
        sys.stdout.flush()

    stdout1, stderr1 = p1.communicate()

    if p1.returncode == 0:
        print("Will Text to TE Module processed successfully.\n")
    else:
        print(f"Will Text to TE Module failed with return code {p1.returncode}")
        print(f"Error:\n{stderr1.decode('utf-8')}\n")
        sys.exit(1)
    

    will_text_extraction_json= os.path.splitext(os.path.basename(input_file))[0] + '.json'
    
    output_will_text_extraction_json = os.path.abspath(os.path.join(base_dir, '..','frontend', 
    'text2extractions','output', will_text_extraction_json))
    shutil.copy(output_will_text_extraction_json, output_path)
    
    te_json_path= os.path.abspath(os.path.join(output_path,will_text_extraction_json))
    print(f"Text Extraction Json file saved successfully:\n- {te_json_path}")

    wm_obj = os.path.splitext(os.path.basename(input_file))[0] + '.obj'
    wm_obj_path = os.path.abspath(os.path.join(output_path,wm_obj))
    cmd_te_to_wm = ['python3', te_to_wm_script,'-t',te_json_path,'-o',wm_obj_path]
    print("... TE to WM Module processing.\n")
    p2 = subprocess.Popen(cmd_te_to_wm, stdout=subprocess.PIPE, stderr=subprocess.PIPE,cwd =backend_base_path)
    for stdout_line in iter(p2.stdout.readline, b''):
        sys.stdout.write(stdout_line.decode())
        sys.stdout.flush()

    stdout2, stderr2 = p2.communicate()

    if p2.returncode == 0:
        print("TE to WM Module processed successfully.\n")
    else:
        print(f"TE to WM Module failed with return code {p2.returncode}")
        print(f"Error:\n{stderr2.decode('utf-8')}\n")
        sys.exit(1)
    print(f"Will Model file saved successfully:\n- {wm_obj_path}")

    devolution_file = os.path.splitext(os.path.basename(input_file))[0] + '.devolution.json'
    devolution_file_path = os.path.abspath(os.path.join(output_path,devolution_file))
    cmd_devolution = ['python3', devolution_script,'-p',wm_obj_path,'-o',devolution_file_path]
    print("... WM to Devolution Module processing.\n")
    p3 = subprocess.Popen(cmd_devolution, stdout=subprocess.PIPE, stderr=subprocess.PIPE,cwd =backend_base_path,env=env)
    for stdout_line in iter(p3.stdout.readline, b''):
        sys.stdout.write(stdout_line.decode())
        sys.stdout.flush()

    stdout3, stderr3 = p3.communicate()

    if p3.returncode == 0:
        print("WM to Devolution Module processed successfully.\n")
    else:
        print(f"WM to Devolution Module failed with return code {p3.returncode}")
        print(f"Error:\n{stderr3.decode('utf-8')}\n")
        sys.exit(1)
    

if __name__ == "__main__":
    main()
