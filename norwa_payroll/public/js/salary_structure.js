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
                                const incoming = new Set(rows.map(row => row.salary_component));
                                const pruned = [];
                                const seen = new Set();

                                // Keep non-managed rows and de-dup managed ones.
                                existing.forEach(row => {
                                    if (!incoming.has(row.salary_component)) {
                                        pruned.push(row);
                                        return;
                                    }

                                    if (seen.has(row.salary_component)) {
                                        frappe.model.clear_doc(row.doctype, row.name);
                                        return;
                                    }

                                    seen.add(row.salary_component);
                                    pruned.push(row);
                                });

                                frm.doc[fieldname] = pruned;

                                rows.forEach(row => {
                                    const match = pruned.find(item => item.salary_component === row.salary_component);
                                    if (match) {
                                        Object.assign(match, row);
                                        return;
                                    }

                                    const child = frm.add_child(fieldname);
                                    Object.assign(child, row);
                                });

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
