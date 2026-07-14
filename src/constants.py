from providers.aws import AWSProvider
from providers.azure import AzureProvider
from providers.cloudflare import CloudflareProvider
from providers.fastly import FastlyProvider
from providers.gcp import GCPProvider

PROVIDERS = [
    AWSProvider,
    AzureProvider,
    CloudflareProvider,
    GCPProvider,
    FastlyProvider,
]
# PROVIDERS = [AzureProvider]
