from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __init__.py
from norwa_payroll.norwa_payroll import __version__ as version

setup(
	name="norwa_payroll",
	version=version,
	description="Kenya Payroll Component with ERPNext Integration",
	author="Norwa",
	author_email="admin@norwa.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
