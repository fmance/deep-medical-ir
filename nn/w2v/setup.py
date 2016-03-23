from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'w2v app',
  ext_modules = cythonize("w2v.pyx"),
)
