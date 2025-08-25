import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SALEOR_API_URL = os.getenv("SALEOR_API_URL")
SALEOR_API_EMAIL = os.getenv("SALEOR_API_EMAIL")
SALEOR_API_PASSWORD = os.getenv("SALEOR_API_PASSWORD")

def get_saleor_auth_token():
    """
    Authenticates with the Saleor GraphQL API to get an access token.
    """
    if not all([SALEOR_API_URL, SALEOR_API_EMAIL, SALEOR_API_PASSWORD]):
        raise ValueError("Saleor API credentials and URL must be set in the .env file.")

    token_create_mutation = '''
    mutation tokenCreate($email: String!, $password: String!) {
      tokenCreate(email: $email, password: $password) {
        token
        errors {
          field
          message
        }
      }
    }
    '''

    variables = {
        "email": SALEOR_API_EMAIL,
        "password": SALEOR_API_PASSWORD
    }

    try:
        response = requests.post(
            SALEOR_API_URL,
            json={"query": token_create_mutation, "variables": variables}
        )
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        
        data = response.json()
        
        if "errors" in data:
            # Handle GraphQL-level errors
            error_messages = [err.get('message', 'Unknown error') for err in data['errors']]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        token_data = data.get("data", {}).get("tokenCreate", {})
        
        if token_data.get("errors"):
            error_messages = [err.get('message', 'Unknown error') for err in token_data["errors"]]
            raise Exception(f"Failed to create token: {', '.join(error_messages)}")
            
        auth_token = token_data.get("token")
        
        if not auth_token:
            raise Exception("Authentication successful, but no token was returned.")
            
        print("Successfully obtained Saleor auth token.")
        return auth_token

    except requests.exceptions.RequestException as e:
        raise Exception(f"An error occurred while connecting to the Saleor API: {e}")
    except Exception as e:
        # Re-raise other exceptions
        raise e

def search_products(auth_token: str, entities: dict) -> list:
    """
    Searches for products in Saleor using extracted entities.
    """
    if not SALEOR_API_URL:
        raise ValueError("Saleor API URL must be set in the .env file.")

    # GraphQL query with filter variable
    graphql_query = '''
    query SearchProducts($filter: ProductFilterInput!, $channel: String = "default-channel") {
      products(first: 5, channel: $channel, filter: $filter) {
        edges {
          node {
            id
            name
            description
            thumbnail {
              url
            }
            isAvailable
            pricing {
              priceRange {
                start {
                  gross {
                    amount
                    currency
                  }
                }
              }
            }
          }
        }
      }
    }
    '''

    # Dynamically build the 'filter' clause using 'search'
    filter_clause = {}
    search_term = entities.get("name") or entities.get("category", "")
    if search_term:
        filter_clause["search"] = search_term
    else:
        # If no search term, return empty list as no products can be found
        return []

    variables = {"filter": filter_clause}

    # No Authorization header for this simple query, as per cURL analysis
    headers = {}

    try:
        response = requests.post(
            SALEOR_API_URL,
            json={"query": graphql_query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            error_messages = [err.get('message', 'Unknown error') for err in data['errors']]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        products = data.get("data", {}).get("products", {}).get("edges", [])
        
        # Flatten the result for easier use
        formatted_products = []
        for edge in products:
            node = edge.get("node", {})
            if not node:
                continue
            
            price_info = node.get("pricing", {}).get("priceRange", {}).get("start", {}).get("gross", {})

            formatted_products.append({
                "id": node.get("id"),
                "name": node.get("name"),
                "description": node.get("description"),
                "thumbnail_url": node.get("thumbnail", {}).get("url"),
                "stock": "Còn hàng" if node.get("isAvailable") else "Hết hàng", # Map boolean to string
                "price": f"{price_info.get('amount')} {price_info.get('currency')}"
            })

        return formatted_products

    except requests.exceptions.RequestException as e:
        raise Exception(f"An error occurred while connecting to the Saleor API: {e}")
    except Exception as e:
        raise e

if __name__ == '__main__':
    # For testing purposes
    try:
        token = get_saleor_auth_token()
        # Test search
        if token:
            # Dummy entities for testing
            test_entities = {"name": "The Dash Cushion"}
            print(f"Searching for products with entities: {test_entities}")
            found_products = search_products(token, test_entities)
            print("Found products:")
            for product in found_products:
                print(product)
    except Exception as e:
        print(f"Error: {e}")


