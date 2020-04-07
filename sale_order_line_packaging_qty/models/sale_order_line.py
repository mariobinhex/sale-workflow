# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    product_packaging_qty = fields.Float(
        string="Package quantity",
        compute="_compute_product_packaging_qty",
        inverse="_inverse_product_packaging_qty",
    )

    @api.depends("product_uom_qty", "product_uom", "product_packaging", "product_packaging.qty")
    def _compute_product_packaging_qty(self):
        for sol in self:
            if not sol.product_packaging or sol.product_uom_qty == 0 or sol.product_packaging.qty == 0:
                sol.product_packaging_qty = 0
                continue
            # Consider uom
            if sol.product_id.uom_id != sol.product_uom:
                product_qty = sol.product_uom._compute_quantity(
                    sol.product_uom_qty, sol.product_id.uom_id
                )
            else:
                product_qty = sol.product_uom_qty
            sol.product_packaging_qty = product_qty / sol.product_packaging.qty

    def _inverse_product_packaging_qty(self):
        for sol in self:
            if not sol.product_packaging:
                raise UserError(
                    _(
                        "You must define a package before setting a quantity "
                        "of said package."
                    )
                )
            if sol.product_packaging.qty == 0:
                raise UserError(
                    _("Please select a packaging with a quantity bigger than 0")
                )
            sol.write(
                {
                    "product_uom_qty": sol.product_packaging.qty * sol.product_packaging_qty,
                    "product_uom": sol.product_packaging.product_uom_id.id,
                }
            )

    @api.onchange('product_packaging')
    def _onchange_product_packaging(self):
        if self.product_packaging:
            self.update(
                {
                    "product_packaging_qty": 1,
                    "product_uom_qty": self.product_packaging.qty,
                    "product_uom": self.product_id.uom_id,
                }
            )
        else:
            self.update(
                {
                    "product_packaging_qty": 0,
                }
            )
        return super()._onchange_product_packaging()

    @api.onchange('product_packaging_qty')
    def _onchange_product_packaging_qty(self):
        if self.product_packaging_qty and not self.product_packaging:
            raise UserError(
                _(
                    "You must define a package before setting a quantity "
                    "of said package."
                )
            )
        else:
            self.update(
                {
                    "product_uom_qty": self.product_packaging_qty * self.product_packaging.qty,
                    "product_uom": self.product_id.uom_id,
                }
            )
