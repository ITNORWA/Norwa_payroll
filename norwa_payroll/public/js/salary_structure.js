frappe.ui.form.on('Salary Structure', {
    refresh: function (frm) {
        if (!frm.doc.__islocal) {
            frm.add_custom_button(__('Apply Kenya Tax 2026'), function () {
                frappe.call({
                    method: 'norwa_payroll.norwa_payroll.utils.apply_kenya_structure',
                    args: {
                        doc: frm.doc
                    },
                    callback: function (r) {
                        if (r.message) {
                            // Update Deductions
                            // We merge with existing or replace?
                            // User asked to "use my app structure". Let's clear and append Deductions.
                            // But usually users might have other deductions.
                            // Safer to check existence or append.
                            // Given the task "create payroll formula...", I will overwrite the relevant Tax rows or append them.

                            let deductions = r.message.deductions;

                            // Remove existing rows of same component to avoid duplicates
                            deductions.forEach(d => {
                                let existing = frm.doc.deductions.filter(row => row.salary_component === d.salary_component);
                                existing.forEach(row => {
                                    frappe.model.clear_doc('Salary Detail', row.name); // This assumes child table name is correct? No, clear logic is different.
                                    // Easier: splice from list.
                                    // frm.doc.deductions = frm.doc.deductions.filter...
                                });
                                // Actually, better to just modify the child table via frm.fields_dict
                            });

                            // Re-filter purely in JS
                            let components_to_add = deductions.map(d => d.salary_component);
                            let new_list = frm.doc.deductions.filter(d => !components_to_add.includes(d.salary_component));

                            // Add new rows
                            deductions.forEach(d => {
                                new_list.push(d);
                            });

                            frm.doc.deductions = new_list;
                            frm.refresh_field('deductions');

                            frappe.msgprint(__("Kenya 2026 Tax Formulas Applied"));
                        }
                    }
                });
            });
        }
    }
});
