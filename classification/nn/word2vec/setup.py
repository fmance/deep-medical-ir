from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = 'Word2Vec App',
  ext_modules = cythonize("word2vec.pyx"),
)
