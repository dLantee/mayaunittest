"""

"""
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
    parser.add_argument('-m', '--maya',
                        help='Maya version',
                        type=int,
                        default=2024)
    parser.add_argument('-mad', '--maya-app-dir',
                        help='Just create a clean MAYA_APP_DIR and exit')
    pargs = parser.parse_args()

    # Locate "mayaunittest" module.
    pass

    # Create clean environment
    pass

    # Run command
    pass



    # mayaunittest = os.path.join(CMT_ROOT_DIR, 'scripts', 'cmt', 'test', 'mayaunittest.py')
    # cmd = [mayapy(pargs.maya), mayaunittest]
    # if not os.path.exists(cmd[0]):
    #     raise RuntimeError('Maya {0} is not installed on this system.'.format(pargs.maya))
    #
    # app_directory = pargs.maya_app_dir
    # maya_app_dir = create_clean_maya_app_dir(app_directory)
    # if app_directory:
    #     return
    # # Create clean prefs
    # os.environ['MAYA_APP_DIR'] = maya_app_dir
    # # Clear out any MAYA_SCRIPT_PATH value so we know we're in a clean env.
    # os.environ['MAYA_SCRIPT_PATH'] = ''
    # # Run the tests in this module.
    # os.environ['MAYA_MODULE_PATH'] = CMT_ROOT_DIR
    # try:
    #     subprocess.check_call(cmd)
    # except subprocess.CalledProcessError:
    #     pass
    # finally:
    #     shutil.rmtree(maya_app_dir)

if __name__ == '__main__':
    main()