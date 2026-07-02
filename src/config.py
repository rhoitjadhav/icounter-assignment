import os


# DB Connection
SQLALCHEMY_DATABASE_URL = os.getenv(
    "SQLALCHEMY_DATABASE_URL",
    "sqlite:///ip_lookup.db"
    # f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
)


# Providers config
AWS_URL = os.getenv("AWS_URL", "https://ip-ranges.amazonaws.com/ip-ranges.json")
GCP_URL = os.getenv("GCP_URL", "https://www.gstatic.com/ipranges/cloud.json")
AZURE_URL = os.getenv("AZURE_URL", "https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_{date}.json")
CLOUDFLARE_URL = os.getenv("CLOUDFLARE_URL", "https://www.cloudflare.com/ips-v4")
