#!/usr/bin/env python3
"""
MeinAntrag - A web application to generate prefilled government requests
"""

import falcon
import json
import requests
from urllib.parse import urlencode
import os
import sys
from jinja2 import Environment, FileSystemLoader

SITE_BASE_URL = os.environ.get('MEINANTRAG_BASE_URL', 'http://localhost:8000')

class BaseTemplateResource:
	"""Base class for resources that need template rendering"""
	
	def _get_template_dir(self):
		"""Get the template directory path, handling both development and installed environments"""
		# Allow overriding via environment variable (for packaged deployments)
		env_dir = os.environ.get('MEINANTRAG_TEMPLATES_DIR')
		if env_dir and os.path.exists(env_dir):
			return env_dir

		# Get the directory where this script is located
		script_dir = os.path.dirname(os.path.abspath(__file__))
		
		# Try development templates first
		dev_template_dir = os.path.join(script_dir, 'templates')
		if os.path.exists(dev_template_dir):
			return dev_template_dir
		
		# Try to find templates relative to the executable
		try:
			# If we're running from a Nix store, look for templates in share/meinantrag
			if '/nix/store/' in script_dir:
				# Go up from bin to share/meinantrag/templates
				share_dir = os.path.join(script_dir, '..', 'share', 'meinantrag', 'templates')
				if os.path.exists(share_dir):
					return share_dir
				
				# Alternative: look for templates in the same store path
				store_root = script_dir.split('/nix/store/')[1].split('/')[0]
				store_path = f"/nix/store/{store_root}"
				alt_share_dir = os.path.join(store_path, 'share', 'meinantrag', 'templates')
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

class MeinAntragApp(BaseTemplateResource):
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
		resp.text = template.render(
			meta_title='MeinAntrag – Anfragelinks für FragDenStaat',
			meta_description='Erstelle vorausgefüllte Anfragelinks für FragDenStaat.de, suche Behörden, füge Betreff und Text hinzu und teile den Link.',
			canonical_url=f"{SITE_BASE_URL}/"
		)
	
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
		resp.text = template.render(
			meta_title='Impressum – MeinAntrag',
			meta_description='Impressum für MeinAntrag.',
			canonical_url=f"{SITE_BASE_URL}/impressum",
			noindex=True
		)

class DatenschutzResource(BaseTemplateResource):
	def __init__(self):
		template_dir = self._get_template_dir()
		self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
	
	def on_get(self, req, resp):
		"""Serve the Datenschutz page"""
		template = self.jinja_env.get_template('datenschutz.html')
		resp.content_type = 'text/html; charset=utf-8'
		resp.text = template.render(
			meta_title='Datenschutz – MeinAntrag',
			meta_description='Datenschutzerklärung für MeinAntrag. Keine Cookies, es werden nur Anfragen an die FragDenStaat-API gestellt.',
			canonical_url=f"{SITE_BASE_URL}/datenschutz",
			noindex=True
		)

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

class RobotsResource:
	def on_get(self, req, resp):
		resp.content_type = 'text/plain; charset=utf-8'
		resp.text = f"""User-agent: *
Allow: /
Sitemap: {SITE_BASE_URL}/sitemap.xml
"""

class SitemapResource:
	def on_get(self, req, resp):
		resp.content_type = 'application/xml; charset=utf-8'
		resp.text = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{SITE_BASE_URL}/</loc></url>
  <url><loc>{SITE_BASE_URL}/impressum</loc></url>
  <url><loc>{SITE_BASE_URL}/datenschutz</loc></url>
</urlset>
"""

# Create Falcon application
app = falcon.App()

# Discover static assets directory
STATIC_DIR = os.environ.get('MEINANTRAG_STATIC_DIR')
if not STATIC_DIR:
	# Prefer local assets folder in development (relative to this file)
	script_dir = os.path.dirname(os.path.abspath(__file__))
	candidate = os.path.join(script_dir, 'assets')
	if os.path.isdir(candidate):
		STATIC_DIR = candidate
	else:
		# Try current working directory (useful when running packaged binary from project root)
		cwd_candidate = os.path.join(os.getcwd(), 'assets')
		if os.path.isdir(cwd_candidate):
			STATIC_DIR = cwd_candidate
		else:
			# Fallback to packaged location under share
			STATIC_DIR = os.path.join(script_dir, '..', 'share', 'meinantrag', 'assets')

# Add routes
meinantrag = MeinAntragApp()
impressum = ImpressumResource()
datenschutz = DatenschutzResource()
publicbodies = PublicBodiesResource()
robots = RobotsResource()
sitemap = SitemapResource()

app.add_route('/', meinantrag)
app.add_route('/impressum', impressum)
app.add_route('/datenschutz', datenschutz)
app.add_route('/api/publicbodies', publicbodies)
app.add_route('/robots.txt', robots)
app.add_route('/sitemap.xml', sitemap)

# Static file route
if STATIC_DIR and os.path.isdir(STATIC_DIR):
	app.add_static_route('/static', STATIC_DIR)

if __name__ == '__main__':
	import wsgiref.simple_server
	
	print("Starting MeinAntrag web application...")
	print("Open your browser and navigate to: http://localhost:8000")
	print(f"Serving static assets from: {STATIC_DIR}")
	
	httpd = wsgiref.simple_server.make_server('localhost', 8000, app)
	httpd.serve_forever()
