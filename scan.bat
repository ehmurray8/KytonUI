@echo off
set /p num_scans="Number of scans: (-1 for continuous) "
set /p start_wave="Starting wavelength (nm): "
set /p end_wave="End wavelength (nm): "
set /p power="Power (dBm): "

python C:/Users/phils/Documents/FbgUI/test_new_setup/test_new_setup.py %num_scans% %start_wave% %end_wave% %power%
