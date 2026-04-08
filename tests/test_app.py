import io
import unittest
from unittest.mock import patch

import app as coordinator_app


class CoordinatorAppTests(unittest.TestCase):
    def setUp(self):
        coordinator_app.app.config['TESTING'] = True
        self.client = coordinator_app.app.test_client()

    def test_index_includes_shared_frontend_config(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('id="app-config"', html)
        self.assertIn('static/app.js', html)
        self.assertNotIn('const TIME_VALUES =', html)

    def test_preview_validation_error_includes_person_name(self):
        response = self.client.post('/preview', json={
            'is_pm': False,
            'people': [
                {'name': 'Smith J', 'ranges': [{'start': '11:15', 'end': '11:45'}]},
                {'name': 'Doe A', 'ranges': [{'start': '13:27', 'end': '14:00'}]},
            ],
            'room_data': {},
        })

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn('Doe A', payload['error'])
        self.assertIn('15-minute times between 11:00 and 16:45', payload['error'])

    @patch('app.render_preview', return_value=io.BytesIO(b'preview'))
    def test_preview_accepts_quarter_hour_ranges(self, mock_render_preview):
        response = self.client.post('/preview', json={
            'is_pm': False,
            'people': [{'name': 'Smith J', 'ranges': [{'start': '11:15', 'end': '11:45'}]}],
            'room_data': {},
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'image/png')
        mock_render_preview.assert_called_once()

    @patch('app.build_xlsx', return_value=io.BytesIO(b'xlsx'))
    def test_export_accepts_quarter_hour_ranges(self, mock_build_xlsx):
        response = self.client.post('/export', json={
            'people': [{'name': 'Smith J', 'ranges': [{'start': '14:15', 'end': '15:45'}]}],
            'room_data': {},
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        mock_build_xlsx.assert_called_once()


if __name__ == '__main__':
    unittest.main()
