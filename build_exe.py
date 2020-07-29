#- * -coding: utf - 8 - * -
"""

@author: ☙ Ryan McConnell ♈♑ rammcconnell@gmail.com ❧

"""
import sys, os, shutil
from datetime import datetime

from .common import relative_path_convert

from .start_ui import RELEASE_VER
import subprocess, numpy
venv = r'C:\ProgramData\Anaconda3\envs\BDO_Enhancement_Tool_venv\Scripts'
pyinstaller = os.path.join(venv, 'pyinstaller.exe')
ISCC = r'C:\Program Files (x86)\Inno Setup 5\ISCC.exe'
UPX = r'C:\Program Files\upx-3.95-win64'

module_name = 'BDO_Enhancement_Tool'

ENTRY_POINT = 'GraveflosEnhancementTool_win32.py'
ICON_PATH = 'favicon.ico'
INSTALL_ICON_PATH = '../install.png'

DEFAULT_OUTPUT_INSTALL_SCRIPT = 'make_installer.iss'
OUTPUT_INSTALL_ICON = 'install.ico'
INSTALL_ICON_OVERLAY = 0.7

icon_sizes = [(256, 256),
               (128, 128),
               (64, 64),
               (48, 48),
               (32, 32),
               (24, 24),
               (16, 16)]


exe_name = 'Setup Graveflo EnhanceTool V' + RELEASE_VER

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def stroke_image(img_, stroke_size=1, stroke_color=(255,255,255)):
    from PIL import Image, ImageFilter
    from .utilities import center_rect, fitAspectRatio

    r, g, b, a = img_.split()
    cont_size = tuple(numpy.array(img_.size) + (stroke_size * 2))

    center = center_rect(img_.size, cont_size)
    #print center

    mask = Image.new("L", cont_size, 0)
    mask.paste(a, center)
    #mask = mask.filter(ImageFilter.BoxBlur(stroke_size))
    for i in range(0, stroke_size):
        mask = mask.filter(ImageFilter.MaxFilter(3))
    #mask = mask.filter(ImageFilter.GaussianBlur(stroke_size))
    #mask = mask.filter(ImageFilter.EDGE_ENHANCE_MORE)
    #mask = mask.filter(ImageFilter.MaxFilter(stroke_size+1))
    def intensity(int):
        if int > 0:
            return 255
        else:
            return 0
    #mask = mask.point(intensity)

    #mask.show()

    backdrop = Image.new('RGB', cont_size, stroke_color)
    backdrop.paste(img_, center, img_)
    #backdrop.format = 'PNG'
    backdrop.putalpha(mask)
    return backdrop

PASTE_POSITION_CENTER = 'center'
def resize_canvas_alpha(img_, canvas_size, paste_pos=(0,0)):
    from PIL import Image, ImageFilter
    from .utilities import center_rect, fitAspectRatio

    if paste_pos == PASTE_POSITION_CENTER:
        paste_pos = center_rect(img_.size, canvas_size)
    r, g, b, a = img_.split()
    mask = Image.new("L", canvas_size, 0)
    mask.paste(a, paste_pos)
    backdrop = Image.new('RGB', canvas_size)
    backdrop.paste(img_, paste_pos, img_)
    backdrop.putalpha(mask)
    return backdrop

def scale_image(img_, aspect_rat=None, width=None, height=None, AA=None):
    from .utilities import center_rect, fitAspectRatio
    from PIL import Image, ImageFilter
    if AA is None:
        AA = Image.LANCZOS
    if aspect_rat is None:
        aspect_rat = img_.size[:]
    dims = numpy.array(fitAspectRatio(aspect_rat, width=width, height=height))
    return img_.resize(tuple(dims.astype(int)), AA)

def copy_print(source, dest, copyf=shutil.copy):
    try:
        copyf(source, dest)
        print('{} -> {}'.format(source, dest))
    except OSError as e:
        print(e)
        print('ERROR: {} -> {}'.format(source, dest))
        input('Press any key to try again... (CTRL+C to cancel program)')
        copy_print(source, dest, copyf=copyf)

def build_iss(path, script_base, swaps=None, output_script_name=DEFAULT_OUTPUT_INSTALL_SCRIPT):
    if swaps is None:
        swaps = {}
    with open(script_base) as f:
        contents = f.read()
        for key,val in swaps.items():
            contents = contents.replace(key, val)

    script_path = os.path.abspath(os.path.join(path, output_script_name))
    with open(script_path, 'w') as f:
        f.write(contents)
    print('Building Installer...')
    try:
        command = [ISCC, script_path]
        print(' '. join(command))
        ret = subprocess.check_call(command, shell=False)
        print('Installer Build Success')
    except subprocess.CalledProcessError as e:
        print(e)
        print('Installer Build Failed')

def build_installer(path, icon=None):
    if icon is None:
        icon = relative_path_convert(ICON_PATH)
    folder_path = os.path.basename(ENTRY_POINT)
    folder_path = folder_path[:folder_path.rfind('.')]
    script_path = relative_path_convert('enhc_inst.iss')
    common_dest = os.path.join(path, folder_path)
    build_iss(path, script_path, {
        '|exename|': str(exe_name),
        '|favicon|': icon,
        '|license|': relative_path_convert('gpl.txt'),
        '|start_ui|': os.path.abspath(common_dest),
        '|outdir|': os.path.abspath(path),
        '|appver|': RELEASE_VER,
        '|scriptname|': ENTRY_POINT[:-3],
        '|modname|':module_name
    })

def build_patch(path, icon=None):
    if icon is None:
        icon = relative_path_convert(ICON_PATH)
    folder_path = os.path.basename(ENTRY_POINT)
    folder_path = folder_path[:folder_path.rfind('.')]
    script_path = relative_path_convert('enhc_inst.iss')
    common_dest = os.path.join(os.path.join(path, 'build'), folder_path)
    build_iss(path, script_path, {
        '|exename|': '{}{}'.format(exe_name,'_patch'),
        '|favicon|': icon,
        '|license|': relative_path_convert('gpl.txt'),
        '|start_ui|': os.path.abspath(common_dest),
        '|outdir|': os.path.abspath(path),
        '|appver|': RELEASE_VER,
        '|scriptname|': ENTRY_POINT[:-3],
        '|modname|':module_name
    }, output_script_name='make_patch.iss')

# Convert UI files to python files
def build_exe(path, upx=False, clean=False, icon_p=None):
    print('Building...')
    my_env = os.environ.copy()
    my_env["PATH"] = "{};{};{};{};{};".format(venv,
                                              venv+r'\Library\mingw-w64\bin',
                                              venv+r'\Library\usr\bin',
                                              venv+r'\Library\bin',
                                              venv+r'\Scripts',) + my_env["PATH"]
    try:
        #import unicodedata
        # '--hidden-import=pkg_resources.py2_warn',
        command = [pyinstaller, '--noconsole', '--noconfirm', '--distpath={}'.format(path),
                   '--icon={}'.format(ICON_PATH),'--hidden-import=unicodedata','--hidden-import=encodings.idna',
                   '{}'.format(ENTRY_POINT)]
        if upx:
            command.insert(5, '--upx-dir={}'.format(UPX))
        if clean:
            command.insert(5, '--clean')
        output = subprocess.check_output(command, env=my_env)
        print('Build Success: ' + str(path))
        folder_path = os.path.basename(ENTRY_POINT)
        folder_path = folder_path[:folder_path.rfind('.')]
        common_dest = os.path.join(path, folder_path)
        mod_embed_path = os.path.join(common_dest, module_name)
        try:
            os.mkdir(mod_embed_path)
        except FileExistsError:
            pass
        copy_print(relative_path_convert('based_settings.json'), os.path.join(mod_embed_path,'settings.json'))
        copy_print(relative_path_convert('based_settings.json'), os.path.join(mod_embed_path, 'settings.json'))
        copy_print(relative_path_convert(ICON_PATH), mod_embed_path)
        copy_print(relative_path_convert('Graveflo.png'), mod_embed_path)
        copy_print(relative_path_convert('title.png'), mod_embed_path)
        copy_print(relative_path_convert('Data'), os.path.join(mod_embed_path, 'Data'), copyf=shutil.copytree)
        images_folder = os.path.join(mod_embed_path, 'Images')
        #try:
        #    os.mkdir(images_folder)
        #except FileExistsError:
        #    pass
        #shutil.copy(relative_path_convert('Images/lens2.png'), os.path.join(images_folder, 'lens2.png'))
        copy_print(relative_path_convert('Images'), images_folder, copyf=shutil.copytree)
        #copy_print(relative_path_convert('Images/items'), os.path.join(images_folder, 'items'),
        #           copyf=shutil.copytree)
        db_folder = os.path.join(mod_embed_path, 'bdo_database')
        try:
            os.mkdir(images_folder)
        except FileExistsError:
            pass
        try:
            os.mkdir(db_folder)
        except FileExistsError:
            pass
        shutil.copy(relative_path_convert('bdo_database/gear.sqlite3'), db_folder)
        try:
            os.mkdir(os.path.join(db_folder, 'tmp_imgs'))
        except FileExistsError:
            pass
        copy_print(relative_path_convert('build'), os.path.join(path, 'build'), copyf=shutil.move)
    except subprocess.CalledProcessError:
        print('Build Failed')

def overlay_inst_icon(input_icon_path, overlay_icon_path, save_path):
    from PIL import Image, ImageFilter

    install_icon = Image.open(overlay_icon_path, 'r')
    favicon = Image.open(input_icon_path, 'r')

    f_w, f_h = favicon.size

    stroked_image = stroke_image(install_icon, stroke_size=2, stroke_color=(0, 0, 0))
    inst_resize = scale_image(stroked_image, width=int(round(f_w * INSTALL_ICON_OVERLAY)))
    fit_stroked = resize_canvas_alpha(inst_resize, favicon.size)
    favicon = Image.alpha_composite(favicon, fit_stroked)

    favicon.save(save_path, sizes=icon_sizes)


def do_build(args):
    upx = '--upx' in args
    clean = '--clean' in args
    patch = '--patch' in args
    debug = '--debug' in args
    patch_only = '--patch-only' in args
    if '--icon' in args:
        icon_p = args[args.index('--icon')+1]
    else:
        icon_p = None
    install = '--noinstall' not in args
    path = relative_path_convert('freeze_' + str(datetime.now().strftime("%m-%d-%y %H %M %S")))
    build_exe(path, upx=upx, icon_p=icon_p)
    if install:
        inst_icon_path = relative_path_convert(os.path.join(path, OUTPUT_INSTALL_ICON))
        if os.path.isfile(INSTALL_ICON_PATH):
            overlay_inst_icon(ICON_PATH, INSTALL_ICON_PATH, inst_icon_path)
        else:
            inst_icon_path = relative_path_convert(ICON_PATH)
        if not patch_only: build_installer(path, icon=inst_icon_path)
        if patch or patch_only: build_patch(path, icon=inst_icon_path)

if __name__ == '__main__':
    do_build(sys.argv[1:])
