"%PYTHON%" setup.py install
"%PYTHON%" setup.py --version > __conda_version__.txt
if errorlevel 1 exit 1
