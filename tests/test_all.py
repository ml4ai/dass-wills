import json, sys, os, subprocess, shutil, time

TOTAL_TESTS = 3

def main():
    time_start = time.time()
    if len(sys.argv) <2:
        print("Test format: python3 test_all.py OPENAI_API_KEY")
    
    key = sys.argv[1]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    tests_passed = 0
    test_driver_script =  os.path.abspath(os.path.join(base_dir, 'test_driver.py')) 
    if not os.path.isfile(test_driver_script):
            print(f"Error: The driver module does not exist.")
            sys.exit(1)

    print("\n==============================\n")

    for i in range(TOTAL_TESTS):
        test_no = i + 1
        test_folder_name = f"test{test_no}"
        print(f"Processing test: {test_no}")
        test_folder_path = os.path.abspath(os.path.join(base_dir, test_folder_name)) 
        if not os.path.isdir(test_folder_path):
            print(f"Error: The test folder {test_folder_path} does not exist.")
            continue

        cmd_run_test_driver = ['python3', test_driver_script,key,test_folder_path]
        process = subprocess.Popen(cmd_run_test_driver, stdout=subprocess.PIPE, stderr=subprocess.PIPE,cwd = base_dir)
        stdout, stderr = process.communicate()
        print("Test output below:\n",stdout.decode())
        if process.returncode == 0:
            print(f"Test {test_no} passed successfully.")
            tests_passed+=1
        else:
            print(f"Test {test_no} failed.")
        print("\n==============================\n")

    time_taken = round(time.time() - time_start,2)
    print(f"{tests_passed}/{TOTAL_TESTS} tests passed successfully.")
    print(f"Total time taken: {time_taken}s")

    output_path = os.path.abspath(os.path.join(base_dir, 'output_test'))
    if  os.path.isdir(output_path):
        shutil.rmtree(output_path)

if __name__ == "__main__":
    main()
