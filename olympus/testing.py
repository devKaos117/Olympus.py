import urllib3
import getpass
import requests
import base64
from requests_ntlm import HttpNtlmAuth

# Option 1: Use requests with requests-ntlm + SSL fixes
username = 'c000000@corp.domain.gov.br'
password = getpass.getpass("Enter proxy password: ")
proxy_url = "http://proxy.domain:9090"

proxies = {
    'http': proxy_url,
    'https': proxy_url  # Note: http for HTTPS proxy
}

# Create session with SSL and connection settings
session = requests.Session()
session.proxies = proxies
session.auth = HttpNtlmAuth(username, password)

# Configure headers
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Connection': 'keep-alive'
})

# Increase timeout and retry
try:
    response = session.get(
        'https://www.google.com',
        timeout=30,
        stream=False
    )
    print(f"Status: {response.status_code}")
    print(response.text[:200])
except requests.exceptions.SSLError:
    print("SSL Error - trying with disabled SSL verification")
    session.verify = False
    response = session.get('https://www.google.com', timeout=30)
    print(f"Status: {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
    print("Trying with basic authentication fallback...")

# Option 2: urllib3 with connection pooling and SSL config
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

username = 'c000000@corp.domain.gov.br'
password = getpass.getpass("Enter proxy password: ")
credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

try:
    # Configure urllib3 with more resilient settings
    proxy = urllib3.ProxyManager(
        proxy_url,
        proxy_headers={
            'Proxy-Authorization': f'Basic {credentials}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Proxy-Connection': 'Keep-Alive'
        },
        timeout=urllib3.Timeout(connect=30, read=30),
        retries=urllib3.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        ),
        cert_reqs='CERT_NONE',  # Disable SSL cert verification
        ca_certs=None
    )
    
    response = proxy.request('GET', 'https://httpbin.org/ip')
    print(f"Status: {response.status}")
    print(response.data.decode('utf-8'))
    
except Exception as e:
    print(f"urllib3 failed: {e}")
    print("Corporate proxy may require NTLM - try requests with NTLM instead")

# Option 3: Debug connection issues
import socket

def test_proxy_connection():
    try:
        # Test basic connectivity to proxy
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex(('proxy.domain', 9090))
        sock.close()
        
        if result == 0:
            print("✓ Proxy server is reachable")
            return True
        else:
            print(f"✗ Cannot connect to proxy server: {result}")
            return False
    except Exception as e:
        print(f"✗ Proxy connection test failed: {e}")
        return False

# Test the connection first
if test_proxy_connection():
    print("Proxy is reachable, trying authenticated request...")
    
    # Try with domain authentication format
    username_variants = [
        'c000000@corp.domain.gov.br',
        'corp\\c000000',  # Windows domain format
        'corp.domain.gov.br\\c000000'  # Full domain format
    ]
    
    for user_format in username_variants:
        print(f"Trying username format: {user_format}")
        try:
            session = requests.Session()
            session.proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            session.auth = HttpNtlmAuth(user_format, password)
            session.verify = False
            session.timeout = 30
            
            response = session.get('https://httpbin.org/ip', timeout=30)
            print(f"✓ Success with {user_format}!")
            print(f"Status: {response.status_code}")
            break
            
        except Exception as e:
            print(f"✗ Failed with {user_format}: {e}")
            continue

# Give up and die