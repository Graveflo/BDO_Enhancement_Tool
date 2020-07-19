import sys
'''
Icon credit:
Icons made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon"> www.flaticon.com</a>


'''

if __name__ == "__main__":
    if '-b' in sys.argv:
        from .build_run import convert_ui_files, relative_path_convert

        convert_ui_files(relative_path_convert('Forms'))
        convert_ui_files(relative_path_convert('QtCommon/forms'))
    if '-bexe' in sys.argv:
        from .build_exe import do_build
        do_build(sys.argv[2:])
        sys.exit(0)
    from .start_ui import launch
    launch()
