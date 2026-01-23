from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __init__.py
__version__ = "0.0.1"

setup(
	name="norwa_payroll",
	version=__version__,
	description="Kenya Payroll Component with ERPNext Integration",
	author="Norwa",
	author_email="admin@norwa.com",
	packages=["norwa_payroll"],
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
