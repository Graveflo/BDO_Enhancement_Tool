#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧

"""
import sys, os, shutil
from datetime import datetime
from common import relative_path_convert
from start_ui import RELEASE_VER
import subprocess

pyinstaller = r'C:\ProgramData\Anaconda2\envs\BDO_Enhancement_Tool\Scripts\pyinstaller.exe'
ISCC = r'C:\Program Files (x86)\Inno Setup 5\ISCC.exe'
UPX = r'C:\Program Files\upx-3.95-win64'
icon_path = 'favicon.ico'
entry_point = 'start_ui.py'

exe_name = 'Setup Graveflo EnhanceTool V' + RELEASE_VER

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def copy_print(source, dest, copyf=shutil.copy):
    try:
        copyf(source, dest)
        print '{} -> {}'.format(source, dest)
    except OSError as e:
        print e
        print 'ERROR: {} -> {}'.format(source, dest)
        raw_input('Press any key to try again... (CTRL+C to cancel program)')
        copy_print(source, dest, copyf=copyf)

def build_iss(path, script_base, swaps=None):
    if swaps is None:
        swaps = {}
    with open(script_base) as f:
        contents = f.read()
        for key,val in swaps.iteritems():
            contents = contents.replace(key, val)

    script_path = os.path.abspath(os.path.join(path, 'make_installer.iss'))
    with open(script_path, 'w') as f:
        f.write(contents)
    print 'Building Installer...'
    try:
        command = [ISCC, script_path]
        print ' '. join(command)
        ret = subprocess.check_call(command, shell=False)
        print 'Installer Build Success'
    except subprocess.CalledProcessError as e:
        print e
        print 'Installer Build Failed'


def build_installer(path):
    folder_path = os.path.basename(entry_point)
    folder_path = folder_path[:folder_path.rfind('.')]
    script_path = relative_path_convert('enhc_inst.iss')
    common_dest = os.path.join(path, folder_path)
    build_iss(path, script_path, {
        '|exename|': '{}'.format(exe_name),
        '|favicon|': relative_path_convert(icon_path),
        '|license|': relative_path_convert('gpl.txt'),
        '|start_ui|': os.path.abspath(common_dest),
        '|outdir|': os.path.abspath(path),
        '|appver|': RELEASE_VER
    })


def build_patch(path):
    folder_path = os.path.basename(entry_point)
    folder_path = folder_path[:folder_path.rfind('.')]
    script_path = relative_path_convert('enhc_inst.iss')
    common_dest = os.path.join(os.path.join(path, 'build'), folder_path)
    build_iss(path, script_path, {
        '|exename|': '{}'.format(exe_name) + '_patch',
        '|favicon|': relative_path_convert(icon_path),
        '|license|': relative_path_convert('gpl.txt'),
        '|start_ui|': os.path.abspath(common_dest),
        '|outdir|': os.path.abspath(path),
        '|appver|': RELEASE_VER
    })

# Convert UI files to python files
def build_exe(path, no_upx=True):
    print 'Building...'
    try:
        command = [pyinstaller, '--noconsole', '--noconfirm', '--distpath={}'.format(path),
                   '--icon={}'.format(icon_path),
                   '{}'.format(entry_point)]
        if not no_upx:
            command.insert(5, '--upx-dir={}'.format(UPX))
        output = subprocess.check_output(command)
        print 'Build Success: ' + str(path)
        folder_path = os.path.basename(entry_point)
        folder_path = folder_path[:folder_path.rfind('.')]
        common_dest = os.path.join(path, folder_path)
        copy_print(relative_path_convert(icon_path), common_dest)
        copy_print(relative_path_convert('Graveflo.png'), common_dest)
        copy_print(relative_path_convert('title.png'), common_dest)
        copy_print(relative_path_convert('Data'), os.path.join(common_dest, 'Data'), copyf=shutil.copytree)
        copy_print(relative_path_convert('build'), os.path.join(path, 'build'), copyf=shutil.move)
    except subprocess.CalledProcessError:
        print 'Build Failed'

if __name__ == '__main__':
    no_upx = '--noupx' in sys.argv
    path = 'freeze_' + str(datetime.now().strftime("%m-%d-%y %H %M %S"))
    build_exe(path, no_upx=no_upx)
    build_installer(path)
    build_patch(path)
