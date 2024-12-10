"""
Core scraper functionality for workforce analytics.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

class BaseScraper(ABC):
    """Base scraper class with common functionality."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging for the scraper."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    def get_job_listings(self) -> List[Dict]:
        """Retrieve job listings from the target site."""
        pass
    
    def _get_page_content(self, url: str, use_playwright: bool = False) -> Optional[str]:
        """
        Fetch page content using either requests or playwright for JS-heavy pages.
        """
        try:
            if use_playwright:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url)
                    content = page.content()
                    browser.close()
                    return content
            
            response = self.session.get(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            response.raise_for_status()
            return response.text
            
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def _parse_html(self, content: str) -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(content, 'html.parser')
    
    @abstractmethod
    def extract_job_details(self, job_element) -> Dict:
        """Extract job details from a job listing element."""
        pass
        
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        return " ".join(text.strip().split())
    
    # Add this to src\scrapers\job_scanner.py, below the BaseScraper class

class JobListingScraper(BaseScraper):
    """Specialized scraper for job listings."""
    
    def __init__(self, base_url: str):
        super().__init__(base_url)
        self.positions_analyzed = 0
        
    def get_job_listings(self) -> List[Dict]:
        """
        Retrieve and parse job listings from the target site.
        """
        try:
            self.logger.info(f"Starting job scan for {self.base_url}")
            content = self._get_page_content(self.base_url, use_playwright=True)
            
            if not content:
                self.logger.error("Failed to retrieve page content")
                return []
                
            soup = self._parse_html(content)
            job_elements = self._find_job_elements(soup)
            
            jobs = []
            for element in job_elements:
                job_data = self.extract_job_details(element)
                if job_data:
                    jobs.append(job_data)
                    self.positions_analyzed += 1
                    
            self.logger.info(f"Successfully analyzed {self.positions_analyzed} positions")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error in get_job_listings: {str(e)}")
            return []
            
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """Find all job listing elements on the page."""
        # This will need to be customized based on the target site's HTML structure
        # For now, using a generic approach
        return soup.find_all('div', class_=['job-listing', 'job-card', 'job-posting'])
        
    def extract_job_details(self, job_element) -> Dict:
        """
        Extract structured data from a job listing element.
        Returns a dictionary of job details.
        """
        try:
            # This is a generic implementation - we'll customize based on target site
            return {
                'title': self.clean_text(job_element.find('h2')),
                'location': self.clean_text(job_element.find(class_='location')),
                'department': self.clean_text(job_element.find(class_='department')),
                'description': self.clean_text(job_element.find(class_='description')),
                'requirements': self.clean_text(job_element.find(class_='requirements')),
                'posting_date': self.clean_text(job_element.find(class_='date')),
                'url': job_element.find('a')['href'] if job_element.find('a') else None
            }
        except Exception as e:
            self.logger.error(f"Error extracting job details: {str(e)}")
            return {}

# Example usage
if __name__ == "__main__":
    # Example implementation
    scraper = JobListingScraper("https://example-job-site.com/careers")
    jobs = scraper.get_job_listings()
    print(f"Found {len(jobs)} job listings")