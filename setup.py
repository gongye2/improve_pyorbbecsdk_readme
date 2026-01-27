# ******************************************************************************
#  Copyright (c) 2024 Orbbec 3D Technology, Inc
# ******************************************************************************

import os
import shutil
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class PrebuiltExtension(Extension):
    def __init__(self, name, lib_dir=''):
        super().__init__(name, sources=[])  
        self.lib_dir = os.path.abspath(lib_dir)

class CustomBuildExt(build_ext):
    def run(self):
        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        if not os.path.isdir(ext.lib_dir) or not os.listdir(ext.lib_dir):
            raise FileNotFoundError(
                f"Directory '{ext.lib_dir}' is empty or does not exist. "
                "Please compile with CMake first."
            )

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        os.makedirs(extdir, exist_ok=True)
        self.copy_all_files(ext.lib_dir, extdir)

    def copy_all_files(self, source_dir, destination_dir):
        os.makedirs(destination_dir, exist_ok=True)
        for item in os.listdir(source_dir):
            source_path = os.path.join(source_dir, item)
            destination_path = os.path.join(destination_dir, item)

            if os.path.islink(source_path):
                link_target = os.readlink(source_path)
                if os.path.exists(destination_path):
                    os.remove(destination_path)
                os.symlink(link_target, destination_path)
            elif os.path.isdir(source_path):
                self.copy_all_files(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)

setup(
    name='pyorbbecsdk2',
    version='2.0.18',
    author='zhonghong',
    author_email='zhonghong@orbbec.com',
    description='pyorbbecsdk is a python wrapper for the OrbbecSDK',
    long_description=long_description,           
    long_description_content_type="text/markdown",
    ext_modules=[PrebuiltExtension('pyorbbecsdk', 'install/lib')],
    cmdclass={'build_ext': CustomBuildExt},
    zip_safe=False,
)