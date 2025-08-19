#!/usr/bin/env python3
"""
Fragify - A web application to generate prefilled FragDenStaat.de request links
"""

import falcon
import json
import requests
from urllib.parse import urlencode
import os
import sys
from jinja2 import Environment, FileSystemLoader

class BaseTemplateResource:
    """Base class for resources that need template rendering"""
    
    def _get_template_dir(self):
        """Get the template directory path, handling both development and installed environments"""
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try development templates first
        dev_template_dir = os.path.join(script_dir, 'templates')
        if os.path.exists(dev_template_dir):
            return dev_template_dir
        
        # Try to find templates relative to the executable
        try:
            # If we're running from a Nix store, look for templates in share/fragify
            if '/nix/store/' in script_dir:
                # Go up from bin to share/fragify/templates
                share_dir = os.path.join(script_dir, '..', 'share', 'fragify', 'templates')
                if os.path.exists(share_dir):
                    return share_dir
                
                # Alternative: look for templates in the same store path
                store_root = script_dir.split('/nix/store/')[1].split('/')[0]
                store_path = f"/nix/store/{store_root}"
                alt_share_dir = os.path.join(store_path, 'share', 'fragify', 'templates')
                if os.path.exists(alt_share_dir):
                    return alt_share_dir
        except Exception:
            pass
        
        # Last resort: try to find any templates directory
        for root, dirs, files in os.walk('/nix/store'):
            if 'templates' in dirs and 'index.html' in os.listdir(os.path.join(root, 'templates')):
                return os.path.join(root, 'templates')
        
        # Fallback to current directory
        return dev_template_dir

class FragifyApp(BaseTemplateResource):
    def __init__(self):
        self.fragdenstaat_api = "https://fragdenstaat.de/api/v1"
        # Setup Jinja2 template environment
        template_dir = self._get_template_dir()
        print(f"Using template directory: {template_dir}")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def on_get(self, req, resp):
        """Serve the main page"""
        template = self.jinja_env.get_template('index.html')
        resp.content_type = 'text/html; charset=utf-8'
        resp.text = template.render()
    
    def on_post(self, req, resp):
        """Handle form submission and generate link"""
        try:
            # Parse form data - use get_param for form fields
            publicbody_id = req.get_param('publicbody_id', default='')
            subject = req.get_param('subject', default='')
            body = req.get_param('body', default='')
            
            # Generate FragDenStaat.de link
            base_url = "https://fragdenstaat.de/anfrage-stellen/"
            if publicbody_id:
                base_url += f"an/{publicbody_id}/"
            
            params = {}
            if subject:
                params['subject'] = subject
            if body:
                params['body'] = body
            
            if params:
                base_url += "?" + urlencode(params)
            
            resp.content_type = 'application/json'
            resp.text = json.dumps({
                'success': True,
                'link': base_url
            })
            
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.content_type = 'application/json'
            resp.text = json.dumps({
                'success': False,
                'error': str(e)
            })

class ImpressumResource(BaseTemplateResource):
    def __init__(self):
        template_dir = self._get_template_dir()
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def on_get(self, req, resp):
        """Serve the Impressum page"""
        template = self.jinja_env.get_template('impressum.html')
        resp.content_type = 'text/html; charset=utf-8'
        resp.text = template.render()

class DatenschutzResource(BaseTemplateResource):
    def __init__(self):
        template_dir = self._get_template_dir()
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
    
    def on_get(self, req, resp):
        """Serve the Datenschutz page"""
        template = self.jinja_env.get_template('datenschutz.html')
        resp.content_type = 'text/html; charset=utf-8'
        resp.text = template.render()

class PublicBodiesResource:
    def __init__(self):
        self.fragdenstaat_api = "https://fragdenstaat.de/api/v1"
    
    def on_get(self, req, resp):
        """API endpoint to search public bodies"""
        try:
            search = req.get_param('search', default='')
            page = req.get_param('page', default=1)
            
            # Build API URL
            url = f"{self.fragdenstaat_api}/publicbody/"
            params = {
                'limit': 20,
                'offset': (int(page) - 1) * 20
            }
            
            if search:
                params['q'] = search
            
            # Make request to FragDenStaat API
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            resp.content_type = 'application/json'
            resp.text = json.dumps(data)
            
        except Exception as e:
            resp.status = falcon.HTTP_500
            resp.content_type = 'application/json'
            resp.text = json.dumps({
                'error': str(e),
                'results': [],
                'next': None
            })

# Create Falcon application
app = falcon.App()

# Add routes
fragify = FragifyApp()
impressum = ImpressumResource()
datenschutz = DatenschutzResource()
publicbodies = PublicBodiesResource()

app.add_route('/', fragify)
app.add_route('/impressum', impressum)
app.add_route('/datenschutz', datenschutz)
app.add_route('/api/publicbodies', publicbodies)

if __name__ == '__main__':
    import wsgiref.simple_server
    
    print("Starting Fragify web application...")
    print("Open your browser and navigate to: http://localhost:8000")
    
    httpd = wsgiref.simple_server.make_server('localhost', 8000, app)
    httpd.serve_forever()
