from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HospitalSettings(models.Model):
    _name = "hospital.settings"
    _description = "Hospital - Configuración global"

    hospital_endpoint = fields.Char(string="Hospital Webservice Endpoint", required=True)

    @staticmethod
    def _normalize_endpoint(value):
        """Normalización simple: quitar espacios, quitar slash final, pasar a minúsculas."""
        if not value:
            return ''
        return value.strip().rstrip('/').lower()

    @api.model
    def create(self, vals):
        # normalizar antes de crear para mantener formato consistente
        if 'hospital_endpoint' in vals and vals.get('hospital_endpoint'):
            vals['hospital_endpoint'] = self._normalize_endpoint(vals.get('hospital_endpoint'))
        return super().create(vals)

    def write(self, vals):
        # normalizar al actualizar
        if 'hospital_endpoint' in vals:
            vals['hospital_endpoint'] = self._normalize_endpoint(vals.get('hospital_endpoint'))
        return super().write(vals)

    @api.constrains('hospital_endpoint')
    def _check_endpoint_unique(self):
        """Constraint que evita crear endpoints duplicados (sobre la versión normalizada)."""
        for rec in self:
            norm = self._normalize_endpoint(rec.hospital_endpoint)
            if not norm:
                raise UserError(_("El endpoint no puede estar vacío."))

            # buscar otros registros y comparar su versión normalizada
            others = self.search([('id', '!=', rec.id)])
            for o in others:
                if norm and self._normalize_endpoint(o.hospital_endpoint) == norm:
                    raise UserError(
                        _("Ya existe un endpoint con la misma ruta configurada: %s") % (o.hospital_endpoint or '')
                    )
