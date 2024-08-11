from odoo import api, fields, models, _


class TenderBid(models.Model):
    _name = "tender.bid"
    _description = "Tender Bid"

    name = fields.Char(string="Bid Reference", copy=False)
    tender_id = fields.Many2one('tender.management', string="Tender")
    tender_user = fields.Many2one('res.users', string="Purchase Representative", related='tender_id.tender_user')
    ref = fields.Char(string="Reference", readonly=True, related='tender_id.ref')
    partner_id = fields.Many2one('res.partner', string="Vendor")
    date_created = fields.Date(string='Start Date', related='tender_id.date_created')
    date_bid_to_end = fields.Date(string='End Date', related='tender_id.date_bid_to_end')
    days_to_deadline = fields.Integer(string='Days To Deadline', related='tender_id.days_to_deadline')
    bid_management_line_ids = fields.One2many('bid.management.line', 'bid_management_id',
                                              string='Bid Management Line')
    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('submit', 'SUBMITTED'),
        ('approve', 'APPROVE'),
        ('approved', 'IN PROGRESS'),
        ('done', 'DONE'),
        ('cancel', 'CANCEL')], string='State', default='draft', required=True)

    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('tender.bid') or _('New')

        # Create the bid record
        bid = super(TenderBid, self).create(vals)

        # Auto-populate bid_management_line_ids from tender_management_line_ids
        if bid.tender_id:
            for line in bid.tender_id.tender_management_line_ids:
                self.env['bid.management.line'].create({
                    'tender_management_line_id': line.id,
                    'bid_management_id': bid.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'qty': line.qty,
                    'description': line.description,
                })
        return bid

    def change_state(self, new_state):
        for rec in self:
            rec.state = new_state

    def action_approve(self):
        self.change_state('approve')

    def action_done(self):
        self.change_state('done')

    def action_cancel(self):
        self.change_state('cancel')

    def action_draft(self):
        self.change_state('draft')

    def action_approved(self):
        self.change_state('approved')

    def action_submit(self):
        self.change_state('submit')


class BidManagementLine(models.Model):
    _name = 'bid.management.line'
    _description = "Bid Management Line"

    tender_management_line_id = fields.Many2one('tender.management.line', string='Tender Management Line')
    product_id = fields.Many2one('product.product', string='Products', related='tender_management_line_id.product_id')
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unit of Measure',
        store=True, readonly=True,
        # related='product_id.product_uom_id'
    )
    product_quantity = fields.Many2one(
        comodel_name='uom.uom',
        string='Product Quantity',
        store=True, readonly=True,
    )
    price_unit = fields.Float(string='Price', related='product_id.list_price', readonly=False)
    qty = fields.Integer(string='Quantity', related='tender_management_line_id.qty')
    default_code = fields.Char(related='product_id.default_code', string='Code')
    description = fields.Char(string='Description')
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.company.currency_id)
    bid_management_id = fields.Many2one('tender.bid', string='Bid Management')

    @api.depends('qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            line.price_total = line.qty * line.price_unit
