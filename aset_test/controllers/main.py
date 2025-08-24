# controllers/main.py
from odoo import http
from odoo.http import request, Response
import json
import logging
from urllib.parse import urlparse

_logger = logging.getLogger(__name__)

class HospitalPatientController(http.Controller):

    @http.route(['/<path:req_path>'], type='http', auth='public', methods=['GET'], csrf=False)
    def paciente_consulta_dynamic(self, req_path, **kw):
        Settings = request.env['hospital.settings'].sudo()
        settings_recs = Settings.search([])
        configured_paths = []
        for s in settings_recs:
            raw = (s.hospital_endpoint or '').strip()
            if not raw:
                continue
            if raw.lower().startswith('http'):
                try:
                    parsed = urlparse(raw)
                    path = (parsed.path or '').strip('/')
                except Exception:
                    path = raw.strip('/').lower()
            else:
                path = raw.strip('/')
            if path:
                configured_paths.append(path.lower())

        if not configured_paths:
            return Response(json.dumps({'error': 'Endpoint no configurado en Ajustes (Hospital).'}, ensure_ascii=False),
                            status=503, content_type='application/json; charset=utf-8')

        req_path_norm = req_path.strip('/').lower()

        best_match = None
        best_len = -1
        for cp in configured_paths:
            if req_path_norm == cp or req_path_norm.startswith(cp + '/'):
                if len(cp) > best_len:
                    best_match = cp
                    best_len = len(cp)

        if not best_match:
            _logger.info("Ruta no autorizada: req_path=%s configured_paths=%s", req_path_norm, configured_paths)
            return Response(json.dumps({'error': 'Endpoint no autorizado para esta ruta.'}, ensure_ascii=False),
                            status=404, content_type='application/json; charset=utf-8')

        rest = req_path_norm[len(best_match):].lstrip('/')
        if not rest:
            return Response(json.dumps({'error': 'Falta secuencia en la URL. Debe ser: <endpoint>/<secuencia>'}, ensure_ascii=False),
                            status=400, content_type='application/json; charset=utf-8')

        # extraemos la secuencia tal y como viene (sin normalizar aún)
        secuencia_raw = rest.split('/')[0].strip()
        if not secuencia_raw:
            return Response(json.dumps({'error': 'Secuencia inválida.'}, ensure_ascii=False),
                            status=400, content_type='application/json; charset=utf-8')

        # BÚSQUEDA CASE-INSENSITIVE:
        Patient = request.env['hospital.patient'].sudo()
        candidates = Patient.search([('patient_code', 'ilike', secuencia_raw)], limit=10)

        paciente = None
        for rec in candidates:
            if rec.patient_code and rec.patient_code.lower() == secuencia_raw.lower():
                paciente = rec
                break

        if not paciente and candidates:
            paciente = candidates[0]

        if not paciente:
            return Response(json.dumps({'error': 'Paciente no encontrado', 'seq': secuencia_raw}, ensure_ascii=False),
                            status=404, content_type='application/json; charset=utf-8')

        payload = {
            'seq': paciente.patient_code or '',
            'name': paciente.name or '',
            'rnc': paciente.document_number or '',
            'state': paciente.state or '',
        }
        _logger.debug("Respuesta paciente encontrada: seq=%s matched_endpoint=%s", secuencia_raw, best_match)
        return Response(json.dumps(payload, ensure_ascii=False),
                        status=200, content_type='application/json; charset=utf-8')
