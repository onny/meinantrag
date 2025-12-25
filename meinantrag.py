#!/usr/bin/env python3
"""
MeinAntrag - A web application to generate prefilled government requests
"""

import falcon
import json
import requests
from urllib.parse import urlencode, parse_qs
import os
import sys
from jinja2 import Environment, FileSystemLoader
import google.generativeai as genai
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
try:
	from docx import Document
	from docx.shared import Pt, Inches
	from docx.enum.text import WD_ALIGN_PARAGRAPH
	DOCX_AVAILABLE = True
except ImportError:
	DOCX_AVAILABLE = False

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

class GenerateAntragResource:
	def __init__(self):
		# Initialize Gemini API
		api_key = os.environ.get('GOOGLE_GEMINI_API_KEY')
		if api_key:
			genai.configure(api_key=api_key)
			self.model = genai.GenerativeModel('gemini-flash-latest')
		else:
			self.model = None
	
	def _remove_markdown(self, text):
		"""Remove markdown formatting from text"""
		if not text:
			return text
		
		# Remove bold/italic markdown: **text** or *text* or __text__ or _text_
		text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
		text = re.sub(r'\*(.+?)\*', r'\1', text)
		text = re.sub(r'__(.+?)__', r'\1', text)
		text = re.sub(r'_(.+?)_', r'\1', text)
		
		# Remove heading markdown: /Heading or # Heading
		text = re.sub(r'^/\s*', '', text, flags=re.MULTILINE)
		text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
		
		# Remove other markdown elements
		text = re.sub(r'`(.+?)`', r'\1', text)  # Code
		text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # Links
		
		return text.strip()
	
	def _parse_gemini_response(self, text):
		"""Parse the response from Gemini into title, demand, and justification"""
		# Remove markdown formatting first
		text = self._remove_markdown(text)
		
		# Split by "Begründung/Sachverhalt" or similar patterns
		parts = re.split(r'(begründung|sachverhalt|begründung/sachverhalt)', text, maxsplit=1, flags=re.IGNORECASE)
		
		if len(parts) >= 3:
			# We have a split at "Begründung/Sachverhalt"
			before_justification = parts[0].strip()
			justification = parts[2].strip() if len(parts) > 2 else ""
			
			# Remove "Begründung/Sachverhalt" or "Sachverhalt" from the beginning of justification
			justification = re.sub(r'^(begründung\s*/?\s*sachverhalt|sachverhalt|begründung)\s*:?\s*\n?', '', justification, flags=re.IGNORECASE).strip()
		else:
			# Try to split by paragraphs
			paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
			if len(paragraphs) >= 3:
				before_justification = '\n\n'.join(paragraphs[:-1])
				justification = paragraphs[-1]
				# Remove "Begründung/Sachverhalt" or "Sachverhalt" from the beginning
				justification = re.sub(r'^(begründung\s*/?\s*sachverhalt|sachverhalt|begründung)\s*:?\s*\n?', '', justification, flags=re.IGNORECASE).strip()
			else:
				before_justification = text
				justification = ""
		
		# Extract title (first line or first paragraph)
		title_match = re.match(r'^(.+?)(?:\n\n|\n|$)', before_justification)
		if title_match:
			title = title_match.group(1).strip()
			demand = before_justification[len(title):].strip()
		else:
			lines = before_justification.split('\n', 1)
			title = lines[0].strip()
			demand = lines[1].strip() if len(lines) > 1 else ""
		
		# Remove title from demand if it's duplicated
		if demand.startswith(title):
			demand = demand[len(title):].strip()
		
		# Remove markdown from each part
		title = self._remove_markdown(title)
		demand = self._remove_markdown(demand)
		justification = self._remove_markdown(justification)
		
		# Final cleanup: remove any remaining "Sachverhalt" or "Begründung/Sachverhalt" at the start
		justification = re.sub(r'^(begründung\s*/?\s*sachverhalt|sachverhalt|begründung)\s*:?\s*\n?\s*', '', justification, flags=re.IGNORECASE).strip()
		
		return {
			'title': title,
			'demand': demand,
			'justification': justification
		}
	
	def on_post(self, req, resp):
		"""Generate text from user input using Gemini API"""
		try:
			if not self.model:
				resp.status = falcon.HTTP_500
				resp.content_type = 'application/json'
				resp.text = json.dumps({
					'success': False,
					'error': 'Gemini API key not configured'
				})
				return
			
			# Get form data - try multiple methods for Falcon compatibility
			anliegen = ''
			party_id = ''
			
			# Method 1: Try get_param (works for URL-encoded form data)
			anliegen = req.get_param('anliegen', default='') or ''
			party_id = req.get_param('party_id', default='') or ''
			
			# Method 2: If empty, try to read from stream and parse manually
			if not anliegen:
				try:
					# Read the raw body - use bounded_stream if available, otherwise stream
					stream = getattr(req, 'bounded_stream', req.stream)
					raw_body = stream.read().decode('utf-8')
					# Parse URL-encoded data manually
					parsed = parse_qs(raw_body)
					anliegen = parsed.get('anliegen', [''])[0]
					party_id = parsed.get('party_id', [''])[0]
				except Exception as e:
					# Log the exception for debugging
					print(f"Error parsing form data: {e}")
					pass
			
			# Remove any whitespace and check if actually empty
			anliegen = anliegen.strip() if anliegen else ''
			party_id = party_id.strip() if party_id else ''
			
			if not anliegen:
				resp.status = falcon.HTTP_400
				resp.content_type = 'application/json'
				resp.text = json.dumps({
					'success': False,
					'error': 'Anliegen-Feld ist erforderlich'
				})
				return
			
			# Create prompt for Gemini
			prompt = """Erzeuge aus dem folgenden Anliegen-Text je nach Anliegen eine Anfrage oder einen Antrag an die Karlsruher Stadtverwaltung im Namen einer Stadtratsfraktion. 

Der Antrag soll im sachlichen, offiziellen Ton einer Fraktion verfasst sein - KEINE persönliche Anrede, KEINE "ich" oder "wir" Formulierungen. Verwende die dritte Person oder Passiv-Formulierungen.

Struktur:
- Die erste Zeile ist der Antragstitel. Der Titel soll PRÄGNANT, EINFACH und EINPRÄGSAM sein - maximal 8-10 Wörter. Vermeide komplizierte Formulierungen, technische Fachbegriffe oder zu lange Titel. Der Titel soll eine gute Außenwirkung haben und das Anliegen klar und verständlich kommunizieren. Beispiele für gute Titel: "Nachtabsenkung der öffentlichen Straßenbeleuchtung", "Vielfalt in Bewegung – Kulturelle Begleitmaßnahmen World Games 2029", "Prüfung digitaler Zahlungsdienstleister und WERO-Alternative"
- Der zweite Absatz ist der Forderungsteil ("Der Gemeinderat möge beschließen:"). Hier können nach einem kurzen Satz auch Stichpunkte verwendet werden, wenn dies sinnvoll ist.
- Der letzte Teil ist Begründung/Sachverhalt (ohne diesen Titel im Text)

WICHTIG: 
- Verwende KEINE Markdown-Formatierung. Keine **fett**, keine *kursiv*, keine /Überschriften, keine # Hashtags, keine Links oder andere Formatierung. 
- Schreibe nur reinen Text ohne jegliche Markdown-Syntax.
- Sachlicher, offizieller Ton einer Fraktion, keine persönlichen Formulierungen.
- Der Antragstitel muss prägnant, einfach verständlich und einprägsam sein - keine komplizierten Formulierungen!

"""
			prompt += anliegen
			
			# Call Gemini API
			response = self.model.generate_content(prompt)
			generated_text = response.text
			
			# Parse the response
			parsed = self._parse_gemini_response(generated_text)
			
			# Return JSON with the generated text parts
			resp.content_type = 'application/json'
			resp.text = json.dumps({
				'success': True,
				'title': parsed['title'],
				'demand': parsed['demand'],
				'justification': parsed['justification'],
				'party_name': party_id if party_id else ""
			})
			
		except Exception as e:
			import traceback
			traceback.print_exc()
			resp.status = falcon.HTTP_500
			resp.content_type = 'application/json'
			resp.text = json.dumps({
				'success': False,
				'error': str(e)
			})

class GeneratePDFResource:
	def _generate_pdf(self, title, demand, justification, party_name=""):
		"""Generate a PDF that looks like a city council proposal"""
		buffer = BytesIO()
		doc = SimpleDocTemplate(buffer, pagesize=A4,
								rightMargin=2.5*cm, leftMargin=2.5*cm,
								topMargin=2.5*cm, bottomMargin=2.5*cm)
		
		# Container for the 'Flowable' objects
		story = []
		
		# Define styles
		styles = getSampleStyleSheet()
		
		# Custom styles for the document
		title_style = ParagraphStyle(
			'CustomTitle',
			parent=styles['Heading1'],
			fontSize=16,
			textColor='black',
			spaceAfter=30,
			alignment=TA_LEFT,
			fontName='Helvetica-Bold'
		)
		
		heading_style = ParagraphStyle(
			'CustomHeading',
			parent=styles['Heading2'],
			fontSize=12,
			textColor='black',
			spaceAfter=12,
			spaceBefore=20,
			alignment=TA_LEFT,
			fontName='Helvetica-Bold'
		)
		
		body_style = ParagraphStyle(
			'CustomBody',
			parent=styles['Normal'],
			fontSize=11,
			textColor='black',
			spaceAfter=12,
			alignment=TA_JUSTIFY,
			fontName='Helvetica'
		)
		
		# Header with party name if provided
		if party_name:
			party_para = Paragraph(f"<b>Antrag der {party_name}</b>", body_style)
			story.append(party_para)
			story.append(Spacer(1, 0.5*cm))
		
		# Title
		if title:
			title_para = Paragraph(f"<b>{title}</b>", title_style)
			story.append(title_para)
		
		# Demand section
		if demand:
			story.append(Spacer(1, 0.3*cm))
			demand_heading = Paragraph("<b>Der Gemeinderat möge beschließen:</b>", heading_style)
			story.append(demand_heading)
			
			# Process demand text - replace newlines with proper breaks
			demand_lines = demand.split('\n')
			for line in demand_lines:
				if line.strip():
					demand_para = Paragraph(line.strip(), body_style)
					story.append(demand_para)
		
		# Justification section
		if justification:
			story.append(Spacer(1, 0.5*cm))
			justification_heading = Paragraph("<b>Begründung/Sachverhalt</b>", heading_style)
			story.append(justification_heading)
			
			# Process justification text
			justification_lines = justification.split('\n')
			for line in justification_lines:
				if line.strip():
					justification_para = Paragraph(line.strip(), body_style)
					story.append(justification_para)
		
		# Build PDF
		doc.build(story)
		buffer.seek(0)
		return buffer
	
	def on_post(self, req, resp):
		"""Generate PDF from form data"""
		try:
			# Get form data
			title = req.get_param('title', default='') or ''
			demand = req.get_param('demand', default='') or ''
			justification = req.get_param('justification', default='') or ''
			party_name = req.get_param('party_name', default='') or ''
			
			# If empty, try to read from stream
			if not title:
				try:
					stream = getattr(req, 'bounded_stream', req.stream)
					raw_body = stream.read().decode('utf-8')
					parsed = parse_qs(raw_body)
					title = parsed.get('title', [''])[0]
					demand = parsed.get('demand', [''])[0]
					justification = parsed.get('justification', [''])[0]
					party_name = parsed.get('party_name', [''])[0]
				except Exception:
					pass
			
			# Generate PDF
			pdf_buffer = self._generate_pdf(title, demand, justification, party_name)
			
			# Return PDF
			resp.content_type = 'application/pdf'
			resp.set_header('Content-Disposition', 'inline; filename="antrag.pdf"')
			resp.data = pdf_buffer.read()
			
		except Exception as e:
			import traceback
			traceback.print_exc()
			resp.status = falcon.HTTP_500
			resp.content_type = 'application/json'
			resp.text = json.dumps({
				'success': False,
				'error': str(e)
			})

class GenerateWordResource:
	def _generate_word(self, title, demand, justification, party_name=""):
		"""Generate a Word document that looks like a city council proposal"""
		doc = Document()
		
		# Set default font
		style = doc.styles['Normal']
		font = style.font
		font.name = 'Arial'
		font.size = Pt(11)
		
		# Header with party name if provided
		if party_name:
			party_para = doc.add_paragraph(f"Antrag der {party_name}")
			party_para.runs[0].bold = True
			party_para.runs[0].font.size = Pt(11)
			doc.add_paragraph()
		
		# Title
		if title:
			title_para = doc.add_paragraph(title)
			title_para.runs[0].bold = True
			title_para.runs[0].font.size = Pt(16)
			title_para.paragraph_format.space_after = Pt(30)
		
		# Demand section
		if demand:
			doc.add_paragraph()
			demand_heading = doc.add_paragraph("Der Gemeinderat möge beschließen:")
			demand_heading.runs[0].bold = True
			demand_heading.runs[0].font.size = Pt(12)
			demand_heading.paragraph_format.space_before = Pt(20)
			demand_heading.paragraph_format.space_after = Pt(12)
			
			# Process demand text
			demand_lines = demand.split('\n')
			for line in demand_lines:
				if line.strip():
					doc.add_paragraph(line.strip())
		
		# Justification section
		if justification:
			doc.add_paragraph()
			justification_heading = doc.add_paragraph("Begründung/Sachverhalt")
			justification_heading.runs[0].bold = True
			justification_heading.runs[0].font.size = Pt(12)
			justification_heading.paragraph_format.space_before = Pt(20)
			justification_heading.paragraph_format.space_after = Pt(12)
			
			# Process justification text
			justification_lines = justification.split('\n')
			for line in justification_lines:
				if line.strip():
					doc.add_paragraph(line.strip())
		
		# Save to buffer
		buffer = BytesIO()
		doc.save(buffer)
		buffer.seek(0)
		return buffer
	
	def on_post(self, req, resp):
		"""Generate Word document from form data"""
		try:
			if not DOCX_AVAILABLE:
				resp.status = falcon.HTTP_500
				resp.content_type = 'application/json'
				resp.text = json.dumps({
					'success': False,
					'error': 'python-docx not installed'
				})
				return
			
			# Get form data
			title = req.get_param('title', default='') or ''
			demand = req.get_param('demand', default='') or ''
			justification = req.get_param('justification', default='') or ''
			party_name = req.get_param('party_name', default='') or ''
			
			# If empty, try to read from stream
			if not title:
				try:
					stream = getattr(req, 'bounded_stream', req.stream)
					raw_body = stream.read().decode('utf-8')
					parsed = parse_qs(raw_body)
					title = parsed.get('title', [''])[0]
					demand = parsed.get('demand', [''])[0]
					justification = parsed.get('justification', [''])[0]
					party_name = parsed.get('party_name', [''])[0]
				except Exception:
					pass
			
			# Generate Word document
			word_buffer = self._generate_word(title, demand, justification, party_name)
			
			# Return Word document
			resp.content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
			resp.set_header('Content-Disposition', 'attachment; filename="antrag.docx"')
			resp.data = word_buffer.read()
			
		except Exception as e:
			import traceback
			traceback.print_exc()
			resp.status = falcon.HTTP_500
			resp.content_type = 'application/json'
			resp.text = json.dumps({
				'success': False,
				'error': str(e)
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
generate_antrag = GenerateAntragResource()
generate_pdf = GeneratePDFResource()
generate_word = GenerateWordResource()
robots = RobotsResource()
sitemap = SitemapResource()

app.add_route('/', meinantrag)
app.add_route('/impressum', impressum)
app.add_route('/datenschutz', datenschutz)
app.add_route('/api/generate-antrag', generate_antrag)
app.add_route('/api/generate-pdf', generate_pdf)
app.add_route('/api/generate-word', generate_word)
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
