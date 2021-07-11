import sys
'''
Icon credit:
Icons made by <a href="https://www.flaticon.com/authors/kiranshastry" title="Kiranshastry">Kiranshastry</a> from <a href="https://www.flaticon.com/" title="Flaticon"> www.flaticon.com</a>
Icons made by <a href="https://www.flaticon.com/authors/pixel-perfect" title="Pixel perfect">Pixel perfect</a> from <a href="https://www.flaticon.com/" title="Flaticon"> www.flaticon.com</a>

'''

# TODO: Bug in genome fs when remove multiple items
# TODO: Cannot set max fs in genome list
# TODO: PRI cost via enhance is calculated in the calc_fs method of the model. How does with affect optimizer and other stand alone?
# TODO: Cron blocker
# TODO: MP lock interface
# TODO: Gear widget on enhance for profit items

# TODO: Gears that are freshly loaded ont he for-profit section are still messed up

# TODO: Tooltip
# TODO: Custom gear in compact window
# TODO: issue: accept button not always present in guide overlay
RELEASE_VER = '1.1a9'


if __name__ == "__main__":
    if '-b' in sys.argv:
        from .build_run import convert_ui_files, relative_path_convert
        convert_ui_files(relative_path_convert('Forms'))
    from .start_ui import launch
    launch(RELEASE_VER)
