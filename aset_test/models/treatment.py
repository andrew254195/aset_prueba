from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HospitalTreatment(models.Model):
    _name = 'hospital.treatment'
    _description = 'Tratamiento'

    code = fields.Char(string="Código de tratamiento", required=True)
    name = fields.Char(string="Nombre del tratamiento", required=True)
    medico_tratante = fields.Char(string="Médico tratante")

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'El código del tratamiento debe ser único.'),
    ]

    @api.constrains('code')
    def _check_code_no_026(self):
        for rec in self:
            if rec.code and '026' in rec.code:
                raise ValidationError(_("El código no puede contener la secuencia '026'."))
