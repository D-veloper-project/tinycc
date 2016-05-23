"""
tinycc compiler
===============

tinycc (or tcc) is a small, fast C compiler capable of producing DLLs that can
be loaded via ctypes.

*__version__* is the package version.

*TCC_VERSION* is the compiler version.

*TCC* is the full path to the tcc.exe executable, wrapped in quotes so that
it can be used as part of an os.system command even when it contains spaces.
:func:`find_tcc_path` returns the path without quotes.

Usage example::

    import os
    from tinycc import TCC

    source = "hello.c"
    COMPILE = TCC + " -shared -rdynamic -Wall %(source)s -o %(target)s"
    target = os.path.splitext(source)[0] + ".dll"  # replace .c with .dll
    command = COMPILE%{"source": source, "target": target}
    status = os.system(command)
    if status != 0 or not os.path.exists(target):
        raise RuntimeError("compile failed.  File is in %r"%source)

or more simply, use :func:`compile`::

    from tinycc import compile
    dll_path = compile("hello.c")

Use :func:`data_files` to gather the data files required for bundling tinycc
in a py2exe package.  This places the compiler in the tinycc-data directory
beside the library.zip generated by py2exe.  The following should appear in
the setup.py for the py2exe build::

    import tinycc

    data_files = []
    ...
    data_files.extend(tinycc.data_files())
    ...
    setup(
        ...
        data_files = data_files,
        ...
        )

Note: if you have put tcc.exe somewhere unusual (i.e., not in the tinycc
package and not in tinycc-data next to the py2exe generated library or exe),
then you can set the environment variable TCC_ROOT to the directory
containing tcc.exe.
"""

__version__ = "1.0"
TCC_VERSION = "0.9.26"  # compiler version returned by tcc -v

def compile(source, target=None):
    """
    Compile *source* into target, returning the path to target.

    If *target* is not specified, replace the source extension with ".dll"
    and use that as the target. This function does not check that source
    ends with ".c".
    """
    import os

    if target is None:
        target = os.path.splitext(source)[0] + ".dll"
    COMPILE = TCC + " -shared -rdynamic -Wall %(source)s -o $(target)s"
    command = COMPILE%{"source": source, "target": target}
    status = os.system(command)
    if status != 0 or not os.path.exists(target):
        raise RuntimeError("compile failed.  File is in %r"%source)
    return target


def data_files():
    """
    Return the data files required to run tcc.

    The format is a list of (directory, [files...]) pairs which can be
    used directly in setup.py::

        data_files = []
        data_files.extend(tinycc.data_files())
        ...
        setup(...,
              data_files=data_files,
              ...)
    """
    from os.path import dirname, join as joinpath
    import os
    from glob import glob

    ROOT = dirname(find_tcc_path())
    def _find_files(path, patterns):
        target = joinpath('tinycc-data', path) if path else 'tinycc-data'
        files = []
        for pattern in patterns.split(','):
            files.extend(glob(joinpath(ROOT, path, pattern)))
        return (target, files)
    result = []
    result.append(_find_files('include', '*.h'))
    for path, dirs, _ in os.walk(joinpath(ROOT, 'include')):
        relative_path = path[len(ROOT)+1:]
        for d in dirs:
            result.append(_find_files(joinpath(relative_path, d), '*.h'))
    result.append(_find_files('lib', '*'))
    result.append(_find_files('libtcc', '*'))
    result.append(_find_files('', '*.exe,*.dll'))
    return result


def find_tcc_path():
    """
    Return the path to the tcc executable.
    """
    import sys
    from os import environ
    from os.path import join as joinpath, dirname, realpath, exists
    EXE = 'tcc.exe'

    # Look for the TCC_PATH environment variable
    KEY = 'TCC_ROOT'
    if KEY in environ:
        path = joinpath(environ[KEY], EXE)
        if not exists(path):
            raise RuntimeError("%s %r does not contain %s"
                               % (KEY, environ[KEY], EXE))
        return path

    # Check in the tinycc package
    path = joinpath(dirname(realpath(__file__)), EXE)
    if exists(path):
        return path

    # Check next to exe/zip file
    path = joinpath(realpath(dirname(sys.executable, 'tinycc-data', EXE)))
    if exists(path):
        return path

    raise ImportError("Could not locate tcc.exe")


TCC = '"%s"' % find_tcc_path()
