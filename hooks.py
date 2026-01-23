app_name = "norwa_payroll"
app_title = "Norwa Payroll"
app_publisher = "Norwa"
app_description = "Kenya Payroll Integration"
app_email = "admin@norwa.com"
app_license = "mit"

# Frappe App Hooks
# Includes in <head>
# ------------------

# include js in doctype views
doctype_js = {
    "Salary Structure": "public/js/salary_structure.js"
}

# Setup Hooks
after_install = "norwa_payroll.utils.setup_payroll"
after_migrate = "norwa_payroll.utils.setup_payroll"
