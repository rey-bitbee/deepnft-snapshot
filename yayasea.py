import httpx
from typing import List, Union
from loguru import logger


def get_listing(collection_name: str, max_pages: int = 100, timeout: float = 30.0, extra_params: Union[dict, None] = None) -> List[int]:
    """
    Fetch all listed token IDs from YaYaSea marketplace for a given collection.

    Args:
        collection_name: Name of the NFT collection (e.g. "GoldenCicada")
        max_pages: Maximum number of pages to fetch (default: 100)
        timeout: Request timeout in seconds (default: 30.0)

    Returns:
        List of token IDs that are currently listed for sale

    Raises:
        httpx.HTTPError: If the API request fails
        ValueError: If max pages reached without completing
    """
    # Pagination parameters
    size = 50  # Number of items per page
    page = 1   # Starting page
    total = 0  # Total listings counter
    token_ids: List[int] = []

    # Fetch all pages until no more listings
    while page <= max_pages:  # Add max pages limit
        logger.info("Fetching page {}...", page)
        url = "https://yayasea.com/api/assets/list"

        # API query parameters
        params = {
            "status": "buyNow",          # Only get items listed for sale
            "order": "PriceLowToHigh",   # Sort by price ascending
            "pageSizes": size,           # Items per page
            "pageNums": page,            # Current page number
            "slug": collection_name,      # Collection name
        }
        if extra_params:
            params.update(extra_params)

        try:
            # Add timeout to prevent hanging requests
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                response_json = response.json()
                rows = response_json["rows"]

                # Break if no more items
                if len(rows) == 0:
                    logger.info("No more listings to fetch in page {}, exiting.", page)
                    break

                # Extract token IDs from response
                for row in rows:
                    token_ids.append(int(row["tokenId"]))

                logger.info("Fetched {} listings in page {}.", len(rows), page)
                total += len(rows)
                page += 1

        except httpx.TimeoutException as e:
            logger.error(f"Request timeout: {str(e)}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise
    else:
        # This block executes if the while loop completes without breaking
        raise ValueError(
            f"Reached maximum number of pages ({max_pages}) without completing. "
            f"Consider increasing max_pages if this is unexpected."
        )

    logger.info("Total {} listings fetched.", total)
    return token_ids
