import os
import requests
import json
import time
import socket
import random
import threading
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init
from typing import List, Dict, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

init(autoreset=True)
load_dotenv()
API_KEY = os.getenv('API_KEY')
CSE_ID = os.getenv('CSE_ID')
PROXY_URL = os.getenv('PROXY_URL')

IPS_FILE = "ips.txt"
DOMAINS_FILE = "reversed-domains.txt"
SENTENCES_FILE = "sentences.txt"

class Spinner:
    spinner_cycle = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, message="Loading..."):
        self.stop_running = False
        self.thread = None
        self.message = message

    def start(self):
        def run_spinner():
            idx = 0
            while not self.stop_running:
                print(f"\r{Fore.CYAN}  {self.spinner_cycle[idx % len(self.spinner_cycle)]} {self.message}{Style.RESET_ALL}", end='', flush=True)
                idx += 1
                time.sleep(0.08)
            print('\r' + ' ' * (len(self.message) + 10) + '\r', end='', flush=True)
        self.thread = threading.Thread(target=run_spinner)
        self.thread.start()

    def stop(self):
        self.stop_running = True
        if self.thread:
            self.thread.join()

class ProxyManager:
    def __init__(self, proxy_url: str = None):
        self.proxy_url = proxy_url
        self.proxies = self._setup_proxies()

    def _setup_proxies(self) -> Dict[str, str]:
        if not self.proxy_url:
            return {}
        return {'http': self.proxy_url, 'https': self.proxy_url}

    def get_proxies(self) -> Dict[str, str]:
        return self.proxies

class KeywordGenerator:
    def __init__(self, api_key: str, existing_sentences: Set[str] = None):
        self.api_key = api_key
        self.gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        self.headers = {'Content-Type': 'application/json'}
        self.existing_sentences = existing_sentences or set()

    def _create_prompt(self, count: int, seed: str) -> str:
        return (
            f"Generate at least {count} completely random, unique, unrelated sentences. "
            "Each sentence must be in a different language if possible, and can be in any language in the world. "
            "Each sentence must have more than one word. "
            "Each sentence must be on a new line. "
            "Do not repeat sentences or languages in any request. "
            "No explanations, no numbering, no duplicates. "
            f"Use this random seed for extra randomness: {seed}"
        )

    def generate_keywords(self, count: int) -> List[str]:
        seed = f"{datetime.now().timestamp()}_{random.randint(1000,9999)}"
        prompt = self._create_prompt(count, seed)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 1.5,
                "maxOutputTokens": 100 + count * 20
            }
        }
        spinner = Spinner(f"Requesting {count} random sentences from Gemini AI...")
        spinner.start()
        try:
            response = requests.post(
                f"{self.gemini_url}?key={self.api_key}",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            spinner.stop()
            if response.status_code == 200:
                result = response.json()
                keywords = self._parse_gemini_response(result)
                
                new_keywords = [k for k in keywords if k not in self.existing_sentences]
                skipped_count = len(keywords) - len(new_keywords)
                
                if skipped_count > 0:
                    print(f"  {Fore.YELLOW}⚠ Skipped {skipped_count} duplicate sentences{Style.RESET_ALL}")
                
                if new_keywords:
                    print(f"  {Fore.GREEN}✓ Successfully retrieved {len(new_keywords)} new sentences{Style.RESET_ALL}")
                    self._save_sentences(new_keywords)
                    print(f"  {Fore.BLUE}┌─ Generated Sentences:{Style.RESET_ALL}")
                    for i, k in enumerate(new_keywords, 1):
                        if i == len(new_keywords):
                            print(f"  {Fore.BLUE}└─ {Fore.WHITE}{i:2d}. {k}{Style.RESET_ALL}")
                        else:
                            print(f"  {Fore.BLUE}├─ {Fore.WHITE}{i:2d}. {k}{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.YELLOW}⚠ All generated sentences were duplicates{Style.RESET_ALL}")
                
                return new_keywords
            else:
                print(f"  {Fore.RED}✗ Gemini API Error: {response.status_code}{Style.RESET_ALL}")
                return []
        except Exception as e:
            spinner.stop()
            print(f"  {Fore.RED}✗ Gemini Error: {str(e)}{Style.RESET_ALL}")
            return []

    def _parse_gemini_response(self, result: dict) -> List[str]:
        sentences = []
        seen = set()
        try:
            if 'candidates' in result and result['candidates']:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    text = candidate['content']['parts'][0].get('text', '')
                    lines = text.strip().split('\n')
                    for line in lines:
                        sentence = line.strip()
                        if len(sentence.split()) > 1 and sentence not in seen:
                            seen.add(sentence)
                            sentences.append(sentence)
        except Exception:
            pass
        return sentences

    def _save_sentences(self, sentences: List[str]):
        with open(SENTENCES_FILE, 'a', encoding='utf-8') as f:
            for sentence in sentences:
                f.write(f"{sentence}\n")
        print(f"  {Fore.CYAN}💾 {len(sentences)} sentences saved to: {SENTENCES_FILE}{Style.RESET_ALL}")

class SearchEngine:
    def __init__(self, api_key: str, cse_id: str, existing_ips: Set[str]):
        self.api_key = api_key
        self.cse_id = cse_id
        self.ips: Set[str] = set(existing_ips)

    def search_keyword(self, keyword: str) -> List[str]:
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': self.api_key,
            'cx': self.cse_id,
            'q': keyword,
            'num': 10
        }
        
        display_keyword = keyword[:50] + "..." if len(keyword) > 50 else keyword
        spinner = Spinner(f"Searching: {display_keyword}")
        spinner.start()
        try:
            response = requests.get(url, params=params, timeout=10)
            spinner.stop()
            response.raise_for_status()
            data = response.json()
            urls = [item['link'] for item in data.get('items', []) if 'link' in item]
            new_ips = self._resolve_urls_to_ips(urls)
            if urls:
                print(f"  {Fore.GREEN}✓ Found {len(urls)} URLs → {len(new_ips)} new IPs{Style.RESET_ALL}")
            else:
                print(f"  {Fore.YELLOW}⚠ No results found{Style.RESET_ALL}")
            return new_ips
        except Exception as e:
            spinner.stop()
            print(f"  {Fore.RED}✗ Search failed: {str(e)}{Style.RESET_ALL}")
            return []

    def _resolve_urls_to_ips(self, urls: List[str]) -> List[str]:
        new_ips = []
        for url in urls:
            domain = self._extract_domain(url)
            if domain:
                ip = self._resolve_domain_to_ip(domain)
                if ip and ip not in self.ips:
                    self.ips.add(ip)
                    new_ips.append(ip)
        return new_ips

    @staticmethod
    def _extract_domain(url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if domain else None
        except Exception:
            return None

    @staticmethod
    def _resolve_domain_to_ip(domain: str) -> Optional[str]:
        try:
            ip = socket.gethostbyname(domain)
            return ip
        except Exception:
            return None

class ReverseIPLookup:
    def __init__(self, proxy_manager: ProxyManager = None, result_file: str = None, existing_domains: Set[str] = None):
        self.all_domains: Set[str] = set(existing_domains) if existing_domains else set()
        self.proxy_manager = proxy_manager
        self.result_file = result_file

    def reverse_ip_lookup(self, ip: str) -> List[str]:
        session = requests.Session()
        if self.proxy_manager:
            proxies = self.proxy_manager.get_proxies()
            if proxies:
                session.proxies.update(proxies)
        spinner = Spinner(f"Reverse lookup: {ip}")
        spinner.start()
        try:
            url = f"https://api.reverseipdomain.com/?ip={ip}"
            resp = session.get(url, timeout=20)
            spinner.stop()
            if resp.status_code != 200:
                print(f"  {Fore.RED}✗ {ip} → Failed ({resp.status_code}){Style.RESET_ALL}")
                return []
            data = resp.json()
            domains = data.get("result", [])
            new_domains = []
            for domain in domains:
                if domain not in self.all_domains:
                    self.all_domains.add(domain)
                    new_domains.append(domain)
            if new_domains:
                print(f"  {Fore.GREEN}✓ {ip} → {len(new_domains)} new domains{Style.RESET_ALL}")
                self._save_domains(new_domains)
            else:
                print(f"  {Fore.YELLOW}⚠ {ip} → No new domains{Style.RESET_ALL}")
            return new_domains
        except Exception as e:
            spinner.stop()
            print(f"  {Fore.RED}✗ {ip} → Error: {str(e)}{Style.RESET_ALL}")
            return []

    def _save_domains(self, domains: List[str]):
        if not self.result_file:
            return
        with open(self.result_file, 'a', encoding='utf-8') as f:
            for domain in domains:
                f.write(f"{domain}\n")

    def process_ips(self, ips: List[str]) -> List[str]:
        print(f"  {Fore.CYAN}Processing {len(ips)} IPs with 50 concurrent threads...{Style.RESET_ALL}")
        with ThreadPoolExecutor(max_workers=50) as executor:
            future_to_ip = {executor.submit(self.reverse_ip_lookup, ip): ip for ip in ips}
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    domains = future.result()
                except Exception as exc:
                    print(f"  {Fore.RED}✗ Thread error {ip}: {exc}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}✓ Reverse IP completed. Total unique domains: {len(self.all_domains)}{Style.RESET_ALL}")
        return list(self.all_domains)

def print_header():
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}╔═════════════════════════════════════════════════╗")
    print(f"║           Auto ReverseIP x GeminiAI             ║")
    print(f"║      Github: https://github.com/im-hanzou       ║")
    print(f"╚═════════════════════════════════════════════════╝{Style.RESET_ALL}")

def print_section_header(title: str, icon: str = ""):
    title_with_icon = f"{icon} {title}" if icon else title
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{title_with_icon}{Style.RESET_ALL}")

def print_summary_box(title: str, items: List[tuple]):
    width = 58
    print(f"\n{Fore.MAGENTA}{Style.BRIGHT}┌{'─' * width}┐")
    
    title_padding = (width - len(title) - 2) // 2
    print(f"│{' ' * title_padding}{title}{' ' * (width - len(title) - title_padding)}│")
    print(f"├{'─' * width}┤")
    
    for label, value in items:
        line = f"  {label}: {value}"
        padding = width - len(line) - 1
        print(f"│{line}{' ' * padding}│")
    
    print(f"└{'─' * width}┘{Style.RESET_ALL}")

def validate_environment() -> bool:
    missing = []
    if not API_KEY:
        missing.append("API_KEY")
    if not CSE_ID:
        missing.append("CSE_ID")
    if missing:
        print(f"  {Fore.RED}✗ Missing environment variables: {', '.join(missing)}{Style.RESET_ALL}")
        return False
    print(f"  {Fore.GREEN}✓ Environment variables validated{Style.RESET_ALL}")
    return True

def load_existing(filename: str) -> Set[str]:
    if not os.path.exists(filename):
        return set()
    with open(filename, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f if line.strip())

def save_ips(ips: List[str]):
    with open(IPS_FILE, 'a', encoding='utf-8') as f:
        for ip in ips:
            f.write(f"{ip}\n")
    print(f"  {Fore.GREEN}✓ {len(ips)} IPs saved to: {IPS_FILE}{Style.RESET_ALL}")

def save_domains(domains: List[str]):
    with open(DOMAINS_FILE, 'a', encoding='utf-8') as f:
        for domain in domains:
            f.write(f"{domain}\n")
    print(f"  {Fore.GREEN}✓ {len(domains)} domains saved to: {DOMAINS_FILE}{Style.RESET_ALL}")

def main():
    print_header()
    
    print_section_header("ENVIRONMENT CHECK", "🔧")
    if not validate_environment():
        return
    
    try:
        proxy_manager = ProxyManager(PROXY_URL) if PROXY_URL else None
        if PROXY_URL:
            print(f"  {Fore.CYAN}🌐 Proxy configured: {PROXY_URL}{Style.RESET_ALL}")
        else:
            print(f"  {Fore.YELLOW}⚠ No proxy configured{Style.RESET_ALL}")

        existing_ips = load_existing(IPS_FILE)
        existing_domains = load_existing(DOMAINS_FILE)
        existing_sentences = load_existing(SENTENCES_FILE)
        print(f"  {Fore.BLUE}📄 Loaded {len(existing_ips)} existing IPs{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}📄 Loaded {len(existing_domains)} existing domains{Style.RESET_ALL}")
        print(f"  {Fore.BLUE}📄 Loaded {len(existing_sentences)} existing sentences{Style.RESET_ALL}")

        print_section_header("SENTENCE GENERATION", "🤖")
        keyword_count = random.randint(10, 30)
        print(f"  {Fore.CYAN}🎲 Random sentence count selected: {keyword_count}{Style.RESET_ALL}")

        keyword_generator = KeywordGenerator(API_KEY, existing_sentences)
        keywords = keyword_generator.generate_keywords(keyword_count)
        if not keywords:
            print(f"  {Fore.RED}✗ No new sentences generated. Exiting.{Style.RESET_ALL}")
            return

        print_section_header("KEYWORD SEARCH", "🔍")
        search_engine = SearchEngine(API_KEY, CSE_ID, existing_ips)
        all_new_ips = [] 
        
        for i, keyword in enumerate(keywords, 1):
            print(f"  {Fore.BLUE}[{i:2d}/{len(keywords)}] {Fore.WHITE}{keyword[:60]}{'...' if len(keyword) > 60 else ''}{Style.RESET_ALL}")
            ips = search_engine.search_keyword(keyword)
            truly_new_ips = [ip for ip in ips if ip not in existing_ips and ip not in all_new_ips]
            all_new_ips.extend(truly_new_ips)
            existing_ips.update(truly_new_ips)
            time.sleep(0.2)
        
        if all_new_ips:
            save_ips(all_new_ips)
            print(f"  {Fore.GREEN}✓ Total new IPs to reverse: {len(all_new_ips)}{Style.RESET_ALL}")
            
            print_section_header("REVERSE IP LOOKUP", "🔄")
            reverse_lookup = ReverseIPLookup(proxy_manager, result_file=DOMAINS_FILE, existing_domains=existing_domains)
            final_domains = reverse_lookup.process_ips(all_new_ips)
            new_domains = [d for d in final_domains if d not in existing_domains]
            if new_domains:
                save_domains(new_domains)
            else:
                print(f"  {Fore.YELLOW}⚠ No new domains discovered{Style.RESET_ALL}")
        else:
            print_section_header("REVERSE IP LOOKUP", "🔄")
            print(f"  {Fore.YELLOW}⚠ No new IPs to reverse{Style.RESET_ALL}")
            new_domains = []

        summary_items = [
            ("IPs Found", len(all_new_ips)),
            ("Domains Found", len(new_domains) if all_new_ips else 0),
        ]
        print_summary_box("RESULTS", summary_items)
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 Process completed successfully!{Style.RESET_ALL}\n")
        
    except KeyboardInterrupt:
        print(f"\n  {Fore.YELLOW}⚠ Process cancelled by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n  {Fore.RED}✗ Unexpected error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
