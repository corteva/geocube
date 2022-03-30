.. highlight:: shell

============
Installation
============


Stable release
--------------

Use pip to install from `PyPI <https://pypi.org/project/geocube/>`__:


Install from pip:

.. code-block:: bash

    python -m pip install geocube


Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

.. code-block:: bash

    conda config --prepend channels conda-forge
    conda config --set channel_priority strict
    conda create -n geocube_env geocube
    conda activate geocube_env

- `geocube` `conda-forge repository <http://github.com/conda-forge/geocube-feedstock>`__

.. note::
    "... we recommend always installing your packages inside a
    new environment instead of the base environment from
    anaconda/miniconda. Using envs make it easier to
    debug problems with packages and ensure the stability
    of your root env."
    -- https://conda-forge.org/docs/user/tipsandtricks.html

.. warning::
    Avoid using `pip install` with a conda environment. If you encounter
    a python package that isn't in conda-forge, consider submitting a
    recipe: https://github.com/conda-forge/staged-recipes/


From source
-----------

The source for geocube can be installed from the `GitHub repo`_.

.. code-block:: bash

    python -m pip install git+git://github.com/corteva/geocube.git#egg=geocube


To install for local development:

.. code-block:: bash

    git clone git@github.com:corteva/geocube.git
    cd geocube
    python -m pip install -e .[dev]


.. _GitHub repo: https://github.com/corteva/geocube
