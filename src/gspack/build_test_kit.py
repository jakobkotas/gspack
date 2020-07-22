#     GSPack: Programming Assignment Packager for GradeScope AutoGrader
#     Copyright (C) 2020  Aleksei Sholokhov
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.


import subprocess
import os.path
from pathlib import Path
import types
import shutil
from zipfile import ZipFile
import pickle
import click

DIST_DIR = Path("dist")
TEMPLATES_DIR = Path("templates")
REQUIREMENTS_FILE = "requirements.txt"
RUN_AUTOGRADER_FILE = "run_autograder"
SETUP_FILE = "setup.sh"
RUN_TESTS_FILE = "run_tests.py"
TEST_SUITE_DUMP = "test_suite.dump"
AUTOGRADER_ZIP = "autograder.zip"


def generate_requirements(filepath, output_path):
    process = subprocess.Popen(f"pipreqs --savepath {output_path} {filepath}".split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return process.communicate()


# TODO: fix for new structure of the rubric

def validate_solution(solution_path):
    if not os.path.exists(solution_path):
        raise FileNotFoundError(f"The file {os.path.abspath(solution_path)} does not exists")
    print("Found the solution file:")
    solution_code = open(solution_path, 'r').read()
    print(f"-> {os.path.abspath(solution_path)}")
    solution_module_name = os.path.basename(solution_path)
    solution_module = types.ModuleType(solution_module_name)
    solution_module.__file__ = os.path.abspath(solution_path)
    try:
        mydir = os.getcwd()
        os.chdir(solution_path.parent)
        exec(solution_code, solution_module.__dict__)
        os.chdir(mydir)
    except Exception as e:
        print("Error happened while executing the solution file:")
        print(e)
        return False, None, None
    if not hasattr(solution_module, 'test_suite'):
        print("No test_suite variable defined in the solution file.")
        return False, None, None
    test_suite = solution_module.test_suite
    if type(test_suite) is not dict:
        print(f"test_suite is defined as {type(test_suite)} but it should be dict.")
    print("Found the test suite configuration:")
    for k, v in test_suite.items():
        if not hasattr(solution_module, v["variable_name"]):
            print(f"{k}: variable {v['variable_name']} is set to be checked but it's not defined after the solution finishes its execution.")
        else:
            print(f"-> {k}: ok")
            test_suite[k]["value"] = solution_module.__getattribute__(v["variable_name"])

    if hasattr(solution_module, 'extra_files'):
        extra_files = solution_module.extra_files
        print("Find extra files list:")
        for f in extra_files:
            if os.path.exists(solution_path.parent / f):
                print(f"-> {f}: ok")
            else:
                print(f"-> {f}: can't find {solution_path.parent / f}")
    else:
        extra_files = []

    return True, test_suite, extra_files


# TODO: stratify the logic of this code
def create_solution_archive(solution_path, test_suite, extra_files):
    program_dir = Path(os.path.dirname(__file__))
    solution_dir = Path(solution_path).parent.absolute()
    try:
        os.mkdir(solution_dir / DIST_DIR)
        shutil.copyfile(program_dir / TEMPLATES_DIR / RUN_TESTS_FILE, solution_dir / DIST_DIR / RUN_TESTS_FILE)
        generate_requirements(solution_dir, output_path=solution_dir / DIST_DIR / REQUIREMENTS_FILE)
        shutil.copyfile(program_dir / TEMPLATES_DIR / SETUP_FILE, solution_dir / DIST_DIR / SETUP_FILE)
        shutil.copyfile(program_dir / TEMPLATES_DIR / RUN_AUTOGRADER_FILE, solution_dir / DIST_DIR / RUN_AUTOGRADER_FILE)
        pickle.dump((test_suite, extra_files), open(solution_dir / DIST_DIR / TEST_SUITE_DUMP, "wb"))

        for extra_file in extra_files:
            try:
                shutil.copyfile(solution_dir / extra_file, solution_dir / DIST_DIR / extra_file)
            except FileNotFoundError:
                print(f"File {os.path.abspath(solution_dir / extra_file)} does not exist.")
                return False

        # Zip all files in DIST directory
        zip_archive = ZipFile(solution_dir / AUTOGRADER_ZIP, 'w')
        for f in os.listdir(solution_dir / DIST_DIR):
            zip_archive.write(solution_dir / DIST_DIR / f, arcname=f)
        zip_archive.close()
        print(f"Archive created successfully: \n-> {solution_dir / AUTOGRADER_ZIP}")
    finally:
        if os.path.exists(solution_dir / DIST_DIR):
            shutil.rmtree(solution_dir / DIST_DIR)
    return True


@click.command(
    help="Genreates archive for gradescope autograder"
)
@click.option(
    '--solution',
    type=str,
    help="path to the solution file"
)
def create_autograder_from_console(**kwargs):
    create_autograder(**kwargs)


def create_autograder(solution):
    solution_path = Path(solution).absolute()
    is_valid, test_suite, extra_files = validate_solution(solution_path)
    if is_valid:
        success = create_solution_archive(solution_path, test_suite, extra_files)


if __name__ == "__main__":
    create_autograder(solution_path="../../examples/python101/hw0_solution.py")
