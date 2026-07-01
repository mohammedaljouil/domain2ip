import dns.resolver
import concurrent.futures
from functools import lru_cache
import sys

# Speed settings
DEFAULT_DNS = "1.1.1.1"    # Faster than 8.8.8.8 in many regions
TIMEOUT = 2.0              # seconds – enough for most DNS queries

def _query_record(domain, rdtype, dns_server):
    """Query a single record type on its own resolver instance (thread-safe)."""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [dns_server]
    resolver.lifetime = TIMEOUT
    try:
        answers = resolver.resolve(domain, rdtype)
        return [str(r) for r in answers]
    except Exception:
        return []   # no records of this type

@lru_cache(maxsize=512)
def resolve_domain_cached(domain, dns_server=DEFAULT_DNS):
    """
    Return IPv4 + IPv6 addresses, using parallel A/AAAA queries and a cache.
    The cache stores results per (domain, dns_server) pair.
    """
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(_query_record, domain, "A", dns_server)
        future_aaaa = executor.submit(_query_record, domain, "AAAA", dns_server)
        a_records = future_a.result()
        aaaa_records = future_aaaa.result()
    return a_records, aaaa_records

if __name__ == "__main__":
    if len(sys.argv) > 1:
        domain = sys.argv[1]
    else:
        domain = input("Enter domain: ").strip()

    dns_server = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_DNS

    a, aaaa = resolve_domain_cached(domain, dns_server)
    all_ips = a + aaaa

    if all_ips:
        print(f"IP addresses for {domain} (via {dns_server}):")
        for ip in all_ips:
            print(ip)
    else:
        print(f"No A or AAAA records found for '{domain}' (DNS: {dns_server}).")