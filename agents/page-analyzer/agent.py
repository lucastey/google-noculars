from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.cloud import bigquery
from urllib.parse import urlparse
import json
import re
from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup

def analyze_page_structure(url: str) -> Dict[str, Any]:
    """
    Analyzes the DOM structure and layout of a web page.
    
    Args:
        url: The URL of the page to analyze
        
    Returns:
        Dictionary containing page structure analysis
    """
    try:
        # Fetch the page content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page metadata
        metadata = {
            'title': soup.title.string if soup.title else None,
            'meta_description': None,
            'meta_keywords': None,
            'lang': soup.html.get('lang') if soup.html else None,
            'viewport': None
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'description':
                metadata['meta_description'] = meta.get('content')
            elif meta.get('name') == 'keywords':
                metadata['meta_keywords'] = meta.get('content')
            elif meta.get('name') == 'viewport':
                metadata['viewport'] = meta.get('content')
        
        # Analyze DOM structure
        structure = {
            'total_elements': len(soup.find_all()),
            'headings': {
                'h1': len(soup.find_all('h1')),
                'h2': len(soup.find_all('h2')),
                'h3': len(soup.find_all('h3')),
                'h4': len(soup.find_all('h4')),
                'h5': len(soup.find_all('h5')),
                'h6': len(soup.find_all('h6'))
            },
            'images': len(soup.find_all('img')),
            'links': len(soup.find_all('a')),
            'forms': len(soup.find_all('form')),
            'inputs': len(soup.find_all('input')),
            'buttons': len(soup.find_all('button')),
            'divs': len(soup.find_all('div')),
            'spans': len(soup.find_all('span'))
        }
        
        # Analyze layout patterns
        layout = {
            'has_header': bool(soup.find('header') or soup.find(class_=re.compile('header', re.I))),
            'has_footer': bool(soup.find('footer') or soup.find(class_=re.compile('footer', re.I))),
            'has_nav': bool(soup.find('nav') or soup.find(class_=re.compile('nav', re.I))),
            'has_sidebar': bool(soup.find('aside') or soup.find(class_=re.compile('sidebar', re.I))),
            'has_main': bool(soup.find('main') or soup.find(class_=re.compile('main', re.I)))
        }
        
        # Analyze interactive elements
        interactions = {
            'clickable_elements': len(soup.find_all(['a', 'button', 'input[type="button"]', 'input[type="submit"]'])),
            'form_elements': len(soup.find_all(['input', 'select', 'textarea'])),
            'media_elements': len(soup.find_all(['img', 'video', 'audio'])),
            'has_js': bool(soup.find_all('script')),
            'external_scripts': len([s for s in soup.find_all('script') if s.get('src')])
        }
        
        # UX insights
        ux_insights = {
            'content_density': structure['total_elements'] / max(len(soup.get_text().split()), 1),
            'heading_hierarchy': _analyze_heading_hierarchy(structure['headings']),
            'image_optimization': _analyze_images(soup),
            'accessibility_score': _calculate_accessibility_score(soup),
            'mobile_friendly': _check_mobile_friendly(metadata['viewport'])
        }
        
        return {
            'url': url,
            'metadata': metadata,
            'structure': structure,
            'layout': layout,
            'interactions': interactions,
            'ux_insights': ux_insights,
            'timestamp': str(response.headers.get('date', '')),
            'status_code': response.status_code
        }
        
    except Exception as e:
        return {
            'url': url,
            'error': str(e),
            'status': 'failed'
        }

def _analyze_heading_hierarchy(headings: Dict[str, int]) -> Dict[str, Any]:
    """Analyze the heading hierarchy for SEO and accessibility."""
    total_headings = sum(headings.values())
    return {
        'total_headings': total_headings,
        'has_h1': headings['h1'] > 0,
        'multiple_h1': headings['h1'] > 1,
        'hierarchy_score': _calculate_hierarchy_score(headings)
    }

def _analyze_images(soup) -> Dict[str, Any]:
    """Analyze image optimization and accessibility."""
    images = soup.find_all('img')
    images_with_alt = sum(1 for img in images if img.get('alt'))
    
    return {
        'total_images': len(images),
        'images_with_alt': images_with_alt,
        'alt_text_coverage': images_with_alt / max(len(images), 1),
        'lazy_loading': sum(1 for img in images if img.get('loading') == 'lazy')
    }

def _calculate_accessibility_score(soup) -> float:
    """Calculate basic accessibility score."""
    score = 0
    total_checks = 0
    
    # Check for alt text on images
    images = soup.find_all('img')
    if images:
        images_with_alt = sum(1 for img in images if img.get('alt'))
        score += (images_with_alt / len(images)) * 20
        total_checks += 20
    
    # Check for form labels
    forms = soup.find_all('form')
    if forms:
        inputs = soup.find_all('input')
        labels = soup.find_all('label')
        if inputs:
            score += min(len(labels) / len(inputs), 1) * 20
        total_checks += 20
    
    # Check for semantic HTML
    semantic_elements = soup.find_all(['header', 'nav', 'main', 'article', 'section', 'aside', 'footer'])
    if semantic_elements:
        score += min(len(semantic_elements) / 5, 1) * 20
    total_checks += 20
    
    # Check for heading hierarchy
    h1_count = len(soup.find_all('h1'))
    if h1_count == 1:
        score += 20
    elif h1_count > 1:
        score += 10
    total_checks += 20
    
    # Check for language attribute
    if soup.html and soup.html.get('lang'):
        score += 20
    total_checks += 20
    
    return score / max(total_checks, 1) * 100

def _calculate_hierarchy_score(headings: Dict[str, int]) -> float:
    """Calculate heading hierarchy score."""
    if headings['h1'] == 1:
        return 100
    elif headings['h1'] > 1:
        return 70
    elif headings['h1'] == 0 and sum(headings.values()) > 0:
        return 30
    else:
        return 0

def _check_mobile_friendly(viewport: str) -> bool:
    """Check if page has mobile-friendly viewport."""
    if not viewport:
        return False
    return 'width=device-width' in viewport.lower()

def store_analysis_to_bigquery(analysis_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Store the page analysis data to BigQuery.
    
    Args:
        analysis_data: The analysis results from analyze_page_structure
        
    Returns:
        Dictionary containing the storage status
    """
    try:
        client = bigquery.Client()
        dataset_id = 'ux_insights'
        table_id = 'page_analysis'
        
        table_ref = client.dataset(dataset_id).table(table_id)
        
        # Transform data for BigQuery
        metadata = analysis_data.get('metadata', {})
        structure = analysis_data.get('structure', {})
        layout = analysis_data.get('layout', {})
        interactions = analysis_data.get('interactions', {})
        ux_insights = analysis_data.get('ux_insights', {})
        headings = structure.get('headings', {})
        
        row = {
            'url': analysis_data.get('url'),
            'title': metadata.get('title'),
            'meta_description': metadata.get('meta_description'),
            'meta_keywords': metadata.get('meta_keywords'),
            'lang': metadata.get('lang'),
            'viewport': metadata.get('viewport'),
            
            # Structural metrics
            'total_elements': structure.get('total_elements'),
            'images_count': structure.get('images'),
            'links_count': structure.get('links'),
            'forms_count': structure.get('forms'),
            'inputs_count': structure.get('inputs'),
            'buttons_count': structure.get('buttons'),
            'divs_count': structure.get('divs'),
            'spans_count': structure.get('spans'),
            
            # Heading counts
            'h1_count': headings.get('h1'),
            'h2_count': headings.get('h2'),
            'h3_count': headings.get('h3'),
            'h4_count': headings.get('h4'),
            'h5_count': headings.get('h5'),
            'h6_count': headings.get('h6'),
            
            # Layout patterns
            'has_header': layout.get('has_header'),
            'has_footer': layout.get('has_footer'),
            'has_nav': layout.get('has_nav'),
            'has_sidebar': layout.get('has_sidebar'),
            'has_main': layout.get('has_main'),
            
            # Interactive elements
            'clickable_elements': interactions.get('clickable_elements'),
            'form_elements': interactions.get('form_elements'),
            'media_elements': interactions.get('media_elements'),
            'has_js': interactions.get('has_js'),
            'external_scripts': interactions.get('external_scripts'),
            
            # UX insights and scores
            'content_density': ux_insights.get('content_density'),
            'accessibility_score': ux_insights.get('accessibility_score'),
            'mobile_friendly': ux_insights.get('mobile_friendly'),
            'heading_hierarchy_score': ux_insights.get('heading_hierarchy', {}).get('hierarchy_score'),
            'alt_text_coverage': ux_insights.get('image_optimization', {}).get('alt_text_coverage'),
            'lazy_loading_images': ux_insights.get('image_optimization', {}).get('lazy_loading'),
            
            # JSON data for complex structures
            'headings_data': json.dumps(headings),
            'layout_data': json.dumps(layout),
            'interactions_data': json.dumps(interactions),
            'ux_insights_data': json.dumps(ux_insights),
            
            # Metadata
            'status_code': analysis_data.get('status_code')
        }
        
        errors = client.insert_rows_json(table_ref, [row])
        
        if errors:
            return {'status': 'error', 'message': str(errors)}
        else:
            return {'status': 'success', 'message': 'Analysis data stored successfully'}
            
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# Create tool objects
analyze_page_tool = FunctionTool(analyze_page_structure)
store_bigquery_tool = FunctionTool(store_analysis_to_bigquery)

page_analyzer_agent = Agent(
    model='gemini-2.0-flash-001',
    name='page_analyzer_agent',
    description='Analyzes web page structure, layout, and UX patterns for insights.',
    instruction='''You are a specialized Page Analyzer Agent that examines web pages to extract structural and UX insights.

Your main responsibilities:
1. Analyze DOM structure and layout patterns
2. Evaluate accessibility and mobile-friendliness  
3. Assess UX design patterns and user experience elements
4. Store analysis results in BigQuery for further processing
5. Provide actionable insights for UX improvement

When analyzing a page:
- Use the analyze_page_structure tool to get comprehensive page data
- Focus on UX-relevant metrics like accessibility, mobile-friendliness, and interaction patterns
- Store results using store_analysis_to_bigquery for downstream analysis
- Provide clear, actionable recommendations for improvement

Always be thorough but concise in your analysis and recommendations.''',
    tools=[analyze_page_tool, store_bigquery_tool]
)
