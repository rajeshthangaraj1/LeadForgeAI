"""
Country-specific lead generation directory sources.

Structure:
  COUNTRY_SOURCES[country][biz_type] = list of directory URLs to scrape directly.

biz_type values: "B2B", "B2C", "Both"
"Both" urls are included regardless of biz_type.
"""

COUNTRY_SOURCES: dict[str, dict[str, list[str]]] = {

    "UAE": {
        "Both": [
            "https://www.yellowpages.ae/search/",
            "https://www.easyuae.com/en/dubai/",
            "https://emaratfinder.com/categories/en/",
        ],
        "B2B": [
            "https://ae.kompass.com/",
            "https://www.dubaiexporters.com/",
            "https://www.gulfjobseeker.com/employer/",
            "https://www.uaeexporters.net/",
            "https://www.b2bsuppliers.ae/",
            "https://www.tradeareabia.com/",
        ],
        "B2C": [
            "https://www.dubizzle.com/",
            "https://www.opensooq.com/en",
            "https://yalla.com/",
        ],
    },

    "India": {
        "Both": [
            "https://www.justdial.com/",
            "https://www.sulekha.com/",
        ],
        "B2B": [
            "https://www.indiamart.com/",
            "https://www.tradeindia.com/",
            "https://www.exportersindia.com/",
            "https://www.alibaba.com/countrysearch/IN/",
            "https://dir.indiafilings.com/",
            "https://www.yellowpages.co.in/",
        ],
        "B2C": [
            "https://www.sulekha.com/",
            "https://www.urbanclap.com/",
        ],
    },

    "Saudi Arabia": {
        "Both": [
            "https://www.yellowpages.com.sa/",
        ],
        "B2B": [
            "https://sa.kompass.com/",
            "https://www.saudibusiness.com/",
            "https://www.saudiexporter.com/",
            "https://www.tafaseel.com/",
        ],
        "B2C": [
            "https://www.opensooq.com/en",
            "https://haraj.com.sa/",
        ],
    },

    "USA": {
        "Both": [
            "https://www.yellowpages.com/",
            "https://www.manta.com/",
        ],
        "B2B": [
            "https://www.thomasnet.com/",
            "https://www.hoovers.com/",
            "https://clutch.co/",
            "https://www.dnb.com/",
            "https://www.kompass.com/a/usa/",
        ],
        "B2C": [
            "https://www.yelp.com/",
            "https://www.angi.com/",
        ],
    },

    "UK": {
        "Both": [
            "https://www.yell.com/",
        ],
        "B2B": [
            "https://www.kompass.com/a/united-kingdom/",
            "https://www.companieshouse.gov.uk/",
            "https://www.thomasnet.com/",
        ],
        "B2C": [
            "https://www.yell.com/",
            "https://www.checkatrade.com/",
        ],
    },

    "Australia": {
        "Both": [
            "https://www.yellowpages.com.au/",
        ],
        "B2B": [
            "https://www.kompass.com/a/australia/",
            "https://www.truelocal.com.au/",
        ],
        "B2C": [
            "https://www.truelocal.com.au/",
            "https://www.hipages.com.au/",
        ],
    },

    "Qatar": {
        "Both": [
            "https://www.yellowpages.com.qa/",
        ],
        "B2B": [
            "https://qa.kompass.com/",
            "https://www.qatarbusinessdirectory.com/",
        ],
        "B2C": [
            "https://www.opensooq.com/en",
        ],
    },

    "Kuwait": {
        "Both": [
            "https://www.yellowpages.com.kw/",
        ],
        "B2B": [
            "https://kw.kompass.com/",
        ],
        "B2C": [
            "https://www.opensooq.com/en",
        ],
    },

    "Bahrain": {
        "Both": [
            "https://www.yellowpages.com.bh/",
        ],
        "B2B": [
            "https://bh.kompass.com/",
        ],
        "B2C": [
            "https://www.opensooq.com/en",
        ],
    },

    "Oman": {
        "Both": [
            "https://www.yellowpages.com.om/",
        ],
        "B2B": [
            "https://om.kompass.com/",
        ],
        "B2C": [
            "https://www.opensooq.com/en",
        ],
    },

    "Singapore": {
        "Both": [
            "https://www.yellowpages.com.sg/",
        ],
        "B2B": [
            "https://sg.kompass.com/",
            "https://www.sgpbusiness.com/",
        ],
        "B2C": [
            "https://www.carousell.sg/",
        ],
    },

    "Germany": {
        "Both": [
            "https://www.gelbeseiten.de/",
        ],
        "B2B": [
            "https://de.kompass.com/",
            "https://www.wlw.de/",
        ],
        "B2C": [
            "https://www.yelp.de/",
        ],
    },

    "Canada": {
        "Both": [
            "https://www.yellowpages.ca/",
        ],
        "B2B": [
            "https://ca.kompass.com/",
            "https://www.canadianbusiness.com/",
        ],
        "B2C": [
            "https://www.kijiji.ca/",
        ],
    },
}


# All available countries for the UI dropdown
ALL_COUNTRIES = sorted(COUNTRY_SOURCES.keys())


def get_directory_urls(country: str, biz_type: str) -> list[str]:
    """
    Return the combined list of directory URLs for a country + business type.
    Always includes 'Both' URLs. Adds B2B or B2C specific ones based on biz_type.
    """
    sources = COUNTRY_SOURCES.get(country, {})
    urls: list[str] = list(sources.get("Both", []))

    if biz_type in ("B2B", "Both"):
        urls += sources.get("B2B", [])
    if biz_type in ("B2C", "Both"):
        urls += sources.get("B2C", [])

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            result.append(u)
    return result
