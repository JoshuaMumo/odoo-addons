from odoo import api, fields, models
from datetime import date
from odoo.exceptions import UserError


class HospitalAppointment(models.Model):
    _name = "hospital.appointment"
    _description = "Hospital Appointment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _rec_name = 'patient_id'

    parent_id = fields.Many2one('hospital.patient', string='Patient')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string="Gender", related='parent_id.gender')
    appointment_time = fields.Date(string='Appointment Time', default=fields.Datetime.now)
    booking_date = fields.Date(string='Booking Date', default=fields.Date.context_today, readonly=True)
    ref = fields.Char(string="Reference", related='parent_id.ref')
    name = fields.Char(string="Appointment Reference", readonly=True, copy=False, default='New')
    days_to_booking_date = fields.Integer(string='No of Days ', compute='_compute_days')
    prescription = fields.Html(string="Prescription")
    pharmacy = fields.Html(string="Pharmacy")
    priority = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Normal'),
        ('4', 'High'),
        ('5', 'Very High')], string='Priority'
    )
    state = fields.Selection([
        ('draft', 'draft'),
        ('in_consultation', 'In Consultation'),
        ('done', 'Done'),
        ('cancel', 'Cancel')], string='State', default='draft', required=True
    )
    doctor_id = fields.Many2one('res.users', string='Doctor')
    pharmacy_line_ids = fields.One2many('appointment.pharmacy.lines', 'appointment_id', string='Pharmacy Lines')

    @api.depends('booking_date', 'appointment_time')
    def _compute_days(self):
        for rec in self:
            today = date.today()
            if rec.booking_date:
                days_difference = (rec.booking_date - today).days
                rec.days_to_booking_date = days_difference
            else:
                rec.days_to_booking_date = 0

    @api.onchange('patient_id')
    def onchange_patient_id(self):
        self.ref = self.patient_id.ref

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hospital.appointment') or 'New'
        return super(HospitalAppointment, self).create(vals)


    def action_in_consultation(self):
        for rec in self:
            rec.state = 'in_consultation'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def object_button(self):
        print("Button Clicked")
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Click successful',
                'type': 'rainbow_man',
            }
        }


class AppointmentPharmacyLines(models.Model):
    _name = "appointment.pharmacy.lines"
    _description = "Appointment Pharmacy Lines"

    product_id = fields.Many2one('product.product', string='Products', required=True)
    price_unit = fields.Float(string='Price', related='product_id.list_price')
    qty = fields.Integer(string='Quantity', default=1)
    appointment_id = fields.Many2one('hospital.appointment', string='Appointment')
