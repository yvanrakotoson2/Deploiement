# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    adv_payment_ids = fields.Many2many('account.payment', string="Advance Payment", copy=False)
    adv_payment_count = fields.Integer(string="Advance Payment Count", compute="_count_adv_payment_ids")

    @api.depends('adv_payment_ids')
    def _count_adv_payment_ids(self):
        for order in self:
            order.adv_payment_count = len(order.adv_payment_ids)

    def action_view_adv_payments(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_payments_payable').read()[0]
        action['domain'] = [('id', 'in', self.adv_payment_ids.ids)]
        action['context'] = {'create': False,}
        return action

    def btn_advance_payment(self):
        self.ensure_one()
        return {'name': _("Advance Payment"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'account.payment',
                'target': 'new',
                'view_id': self.env.ref('eq_purchase_advance_payment.view_purchase_advance_account_payment_form').id,
                'context': {
                    "default_payment_type": "outbound",
                    "default_partner_type": "supplier",
                    "default_partner_id": self.partner_id.id,
                    "default_amount": self.amount_total - sum(self.adv_payment_ids.mapped("amount")),
                    "default_currency_id": self.currency_id.id,
                    "default_ref": self.name,
                    "active_id": self.id,
                    "active_model": "purchase.order",
                },
            }

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)

        if (
            self.env.context.get("active_model") == "purchase.order"
            and self.env.context.get('active_id')
        ):
            purchase = self.env["purchase.order"].browse(
                self.env.context["active_id"]
            )

            purchase.write({
                "adv_payment_ids": [
                    (4, payment.id) for payment in payments
                ]
            })

        return payments