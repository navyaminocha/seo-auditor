from setuptools import setup, find_packages

setup(
    name="verified-seo-agent",
    version="1.0.0",
    description="Verified SEO Audit Agent with TinyFish Integration",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.27.0",
        "pydantic>=2.7.0",
        "beautifulsoup4>=4.12.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "openai>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "audit = seo_agent.cli:main",
        ],
    },
)
