import json, sys, os, subprocess, shutil, time, pprint


def convert_devolution_to_truth_file(devolution):
        ground_truth = {}
        for directive in devolution:
            rule_text_d = devolution[directive]['rule_applied_text']            
            rule_applied_d = int(devolution[directive]['rule_applied_id'])
            for asset_d in devolution[directive]:
                if asset_d not in ground_truth:
                    if asset_d not in ['rule_applied_text', 'rule_applied_id']:
                        ground_truth[asset_d] = {"beneficiares": {}, 
                        "rule_id": rule_applied_d,
                        "rule_applied_text": rule_text_d
                        }
                    
                        for beneficiary_d in devolution[directive][asset_d]:
                            ground_truth[asset_d]["beneficiares"][beneficiary_d] = devolution[directive][asset_d][beneficiary_d]
        return ground_truth

def check_division (devolution, ground_truth):
    for asset_g in ground_truth:
        asset_found = False
        rule_text_g = ground_truth[asset_g]['rule_applied_text']
        rule_applied_g = int(ground_truth[asset_g]['rule_id'])
        print(f"Testing rule: {rule_text_g}")
        for beneficiary_g in ground_truth[asset_g]['beneficiares']:
            beneficiar_found = False
            division_b_g = ground_truth[asset_g]['beneficiares'][beneficiary_g]
            for directive in devolution:
                rule_text_d = devolution[directive]['rule_applied_text']
                rule_applied_d = int(devolution[directive]['rule_applied_id'])
                for asset_d in devolution[directive]:
                    if asset_d == asset_g:
                        asset_found  = True
                        for beneficiary_d in devolution[directive][asset_d]:
                            if beneficiary_g == beneficiary_d:
                                beneficiar_found = True
                                division_b_d = devolution[directive][asset_d][beneficiary_d]
                                division_b_d = round(division_b_d,4)
                                 ### checking if ground truth division equals devolution output division
                                try:
                                    assert (division_b_d == division_b_g)
                                except AssertionError as error:
                                         print(f"Division of asset '{asset_g}' to '{beneficiary_g}' incorrect.")
                                         print(f"Expected a value of {division_b_g}, but instead found {division_b_d}.")
                                         return False
                                ### checking if rule applied is correct
                                try:
                                    assert (rule_applied_g == rule_applied_d)
                                except AssertionError as error:
                                         print(f"Division of asset '{asset_g}' to '{beneficiary_g}' with incorrect rule.")
                                         print(f"Expected a rule'{rule_text_g}', but instead found '{rule_text_d}'.")
                                         return False
            if not beneficiar_found:
                print(f"Beneficiary {beneficiary_g} for {asset_g} not found in devolution")
                return False

        if not asset_found :
            print(f"Asset {asset_g} not found in devolution")
            return False
    return True

def main():
    time_start = time.time()
    

    if len(sys.argv) <3:
        print("Test format: python3 test_driver.py OPENAI_API_KEY test_folder")
    key = sys.argv[1]
    test_folder = sys.argv[2]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    driver_script =  os.path.abspath(os.path.join(base_dir, '..', 'src', 'driver.py')) 
    if not os.path.isfile(driver_script):
            print(f"Error: The driver module does not exist.")
            sys.exit(1)
    input_test_file = os.path.abspath(os.path.join(test_folder, 'will.txt'))
    input_ground_truth = os.path.abspath(os.path.join(test_folder, 'ground_truth.json'))
    base_dir = os.path.dirname(os.path.abspath(__file__))
    base_name = os.path.basename(test_folder)
    output_path = os.path.abspath(os.path.join(base_dir, f'output_test_{base_name}'))
    people_db_path =os.path.abspath(os.path.join(test_folder, 'people_db.json'))
    
    ## deleting output path to remove previous files
    if  os.path.isdir(output_path):
        shutil.rmtree(output_path)
        os.makedirs(output_path)

    if not os.path.isfile(input_test_file):
            print(f"Error: The test file does not exist.")
            sys.exit(1)
    # if not os.path.isfile(input_ground_truth):
    #         print(f"Error: The ground truth file does not exist.")
    #         sys.exit(1)
    if not os.path.isfile(people_db_path):
            people_db_path = None
    if people_db_path:
        cmd_run_driver = ['python3', driver_script,'-i',input_test_file,'-o',output_path, '-k',key, '-d',people_db_path ]
    else:
        cmd_run_driver = ['python3', driver_script,'-i',input_test_file,'-o',output_path, '-k',key]
    process = subprocess.Popen(cmd_run_driver, stdout=subprocess.PIPE, stderr=subprocess.PIPE,cwd = base_dir)
    stdout, stderr = process.communicate()
    print(stdout.decode())
    if process.returncode != 0:
        print(f"Driver module failed with error code: {process.returncode}")
        if  os.path.isdir(output_path):
            shutil.rmtree(output_path)
        print(f"Error:\n{stdout.decode()}\n")
        print()
        sys.exit(1)


    devolution_file_path =   None
    for file in os.listdir(output_path):
        if file.endswith("devolution.json"):
            devolution_file_path = os.path.abspath(os.path.join(output_path,file )) 

    if not os.path.isfile(devolution_file_path):
            print(f"Error: The devolution file does not exist.")
            if  os.path.isdir(output_path):
                shutil.rmtree(output_path)
            sys.exit(1)

    with open(devolution_file_path, 'r') as file:
        devolution_data = json.load(file)
    # with open(input_ground_truth, 'r') as file:
    #     GT_data = json.load(file)
    g_truth = None
    if len(devolution_data) >= 1:
        
        g_truth = convert_devolution_to_truth_file(devolution_data)

        if len(g_truth):  
            with open(input_ground_truth, 'w') as file:
                json.dump(g_truth, file, indent=4) 
    if not g_truth:
        sys.exit(1)
    print("Test Passed Successfully.")
    time_taken = round(time.time() - time_start,2)
    print(f"Time taken: {time_taken}s")
    shutil.rmtree(output_path)

if __name__ == "__main__":
    main()
