import subprocess
import os
import urllib.request

def compile_and_run_cpp(source_file_path):
    # Check if the source file exists
    if not os.path.exists(source_file_path):
        print("Error: Source file does not exist.")
        return -2

    # Extract the directory and filename without extension
    source_directory, source_filename = os.path.split(os.path.abspath(source_file_path))
    source_filename_no_ext = "".join(os.path.splitext(source_filename)[:-1])

    # Compile the C++ source file to create an executable
    executable_file_path = os.path.join(source_directory, source_filename_no_ext)
    try:
        subprocess.run(['g++', source_file_path, '-o', executable_file_path], check=True)
        print("Compilation successful.")
    except subprocess.CalledProcessError as e:
        print("Compilation failed.")
        return -3

    # Run the compiled executable
    try:
        return subprocess.run([executable_file_path]).returncode
    except subprocess.CalledProcessError as e:
        print("Execution failed.")
        return -4

if compile_and_run_cpp("modules_check.cpp") != 0: # The checker returns 0 when modules are supported!
    urllib.request.urlretrieve("https://raw.githubusercontent.com/gcc-mirror/gcc/master/libstdc%2B%2B-v3/include/precompiled/stdc%2B%2B.h", "import_std.hpp")
    print("std include header successfully recieved.")