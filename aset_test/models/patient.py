from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re

def _normalize_rnc(value):
    return re.sub(r'[\s\-\.\,]', '', (value or ''))

def _is_rnc_valid(value):
    return bool(re.fullmatch(r'\d+', value or ''))
class HospitalPatient(models.Model):
    _name = "hospital.patient"
    _description = "Paciente"
    _rec_name = "display_name"
    _inherit = ['mail.thread']  
    patient_code = fields.Char(
        string="Secuencia",
        readonly=True,
        index=True,
        copy=False,
    )

    name = fields.Char(string="Nombre y Apellido", required=True, tracking=True)
    display_name = fields.Char(string="Nombre para mostrar", compute="_compute_display_name", store=True)

    document_number = fields.Char(string="RNC", tracking=True)

    treatment_ids = fields.Many2many(
        'hospital.treatment',
        'hospital_patient_treatment_rel',
        'patient_id',
        'treatment_id',
        string="Tratamientos realizados",
    )

    fecha_hora_alta = fields.Datetime(string="Fecha hora de alta", readonly=True)
    fecha_hora_actualizacion = fields.Datetime(string="Fecha hora de actualización", readonly=True)

    state = fields.Selection(
        [('draft', 'Borrador'), ('alta', 'Alta'), ('baja', 'Baja')],
        string="Estado",
        default='draft',
        tracking=True,
    )

    _sql_constraints = [
        ('patient_code_unique', 'unique(patient_code)', 'El código de paciente debe ser único.'),
    ]

    @api.depends('name', 'patient_code')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = "%s [%s]" % (rec.name or '', rec.patient_code or '')

    @api.constrains('document_number')
    @api.constrains('document_number')
    def _check_rnc_numeric(self):
        """Solo validar aquí — no escribir campos."""
        for rec in self:
            if rec.document_number:
                raw = _normalize_rnc(rec.document_number)
                if not _is_rnc_valid(raw):
                    raise ValidationError(_("RNC inválido: sólo números permitidos."))

    @api.model
    def create(self, vals):
        # generar secuencia si no viene
        if not vals.get('patient_code'):
            vals['patient_code'] = self.env['ir.sequence'].sudo().next_by_code('hospital.patient.seq') or '/'
        if vals.get('document_number'):
            vals['document_number'] = _normalize_rnc(vals.get('document_number'))
            if not _is_rnc_valid(vals['document_number']):
                raise ValidationError(_("RNC inválido: sólo números permitidos."))
        vals['fecha_hora_actualizacion'] = fields.Datetime.now()
        return super().create(vals)

    def write(self, vals):
        if 'document_number' in vals and vals.get('document_number') is not None:
            vals['document_number'] = _normalize_rnc(vals.get('document_number'))
            if vals['document_number'] and not _is_rnc_valid(vals['document_number']):
                raise ValidationError(_("RNC inválido: sólo números permitidos."))
        vals['fecha_hora_actualizacion'] = fields.Datetime.now()
        res = super().write(vals)
        if 'state' in vals:
            for rec in self:
                if vals.get('state') == 'alta' and not rec.fecha_hora_alta:
                    rec.fecha_hora_alta = fields.Datetime.now()
        return res
    
    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_set_alta(self):
        for rec in self:
            rec.write({'state': 'alta'})
            if not rec.fecha_hora_alta:
                rec.fecha_hora_alta = fields.Datetime.now()

    def action_set_baja(self):
        self.write({'state': 'baja'})

