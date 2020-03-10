.. highlight:: shell

============
Installation
============


Stable release
--------------

Use pip to install from `PyPI <https://pypi.org/project/geocube/>`__:


Step 1: Install python GDAL version associated with your GDAL version. 

Here is a Linux example with GDAL installed in your system:

  .. code-block:: bash

      export CPLUS_INCLUDE_PATH=/usr/include/gdal
      export C_INCLUDE_PATH=/usr/include/gdal  
      pip install GDAL~=$(gdal-config --version | awk -F'[.]' '{print $1"."$2}').0

Step 2: Install from pip:

  .. code-block:: bash
    
      pip install geocube


2. Use `conda <https://conda.io/en/latest/>`__ with the `conda-forge <https://conda-forge.org/>`__ channel:

  .. code-block:: bash

      conda install -c conda-forge geocube


From source
-----------

The source for geocube can be downloaded from the `GitHub repo`_.

.. code-block:: console

    $ git clone git@github.com:corteva/geocube.git

    $ cd geocube
    $ python setup.py install


.. _GitHub repo: https://github.com/corteva/geocube
