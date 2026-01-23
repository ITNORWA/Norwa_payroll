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
                            const merge_rows = (fieldname, rows) => {
                                if (!rows || !rows.length) {
                                    return;
                                }

                                const existing = frm.doc[fieldname] || [];
                                const components_to_add = rows.map(row => row.salary_component);
                                const new_list = existing.filter(row => !components_to_add.includes(row.salary_component));

                                rows.forEach(row => {
                                    new_list.push(row);
                                });

                                frm.doc[fieldname] = new_list;
                                frm.refresh_field(fieldname);
                            };

                            merge_rows('earnings', r.message.earnings);
                            merge_rows('deductions', r.message.deductions);

                            frappe.msgprint(__("Kenya 2026 Tax Formulas Applied"));
                        }
                    }
                });
            });
        }
    }
});
