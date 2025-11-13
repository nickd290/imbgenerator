"""
Address Validation API Integration
Supports USPS Official API, SmartyStreets, and Google Address Validation API
"""

import requests
import os
import xml.etree.ElementTree as ET
from typing import Dict, Optional
import logging

# Set up logger
logger = logging.getLogger(__name__)


class AddressValidator:
    """
    Validates addresses using USPS, SmartyStreets, or Google APIs.
    Returns standardized address components needed for IMB generation.

    All providers are CASS certified and return delivery point data
    required for USPS Intelligent Mail Barcode generation.
    """

    def __init__(self, provider="usps", api_key=None, auth_id=None, auth_token=None, user_id=None):
        """
        Initialize address validator.

        Args:
            provider: "usps", "smartystreets", or "google"
            user_id: USPS User ID (for USPS - deprecated, use OAuth)
            auth_id: Auth ID (for SmartyStreets)
            auth_token: Auth token (for SmartyStreets)
            api_key: API key (for Google)
        """
        self.provider = provider.lower()

        if self.provider == "usps":
            # OAuth 2.0 credentials (modern API)
            self.usps_client_id = os.getenv("USPS_CLIENT_ID")
            self.usps_client_secret = os.getenv("USPS_CLIENT_SECRET")
            self.base_url = "https://apis.usps.com"
            self.oauth_url = "https://apis.usps.com/oauth2/v3/token"

            # Token cache
            self.usps_access_token = None
            self.usps_token_expiry = 0

            # Address validation cache (reduces duplicate API calls)
            self.address_cache = {}

            if not self.usps_client_id or not self.usps_client_secret:
                raise ValueError("USPS OAuth credentials required. Set USPS_CLIENT_ID and USPS_CLIENT_SECRET environment variables.")

        elif self.provider == "smartystreets":
            self.auth_id = auth_id or os.getenv("SMARTYSTREETS_AUTH_ID")
            self.auth_token = auth_token or os.getenv("SMARTYSTREETS_AUTH_TOKEN")
            self.base_url = "https://us-street.api.smartystreets.com/street-address"
            if not self.auth_id or not self.auth_token:
                raise ValueError("SmartyStreets credentials required. Set SMARTYSTREETS_AUTH_ID and SMARTYSTREETS_AUTH_TOKEN.")

        elif self.provider == "google":
            self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
            self.base_url = "https://addressvalidation.googleapis.com/v1:validateAddress"
            if not self.api_key:
                raise ValueError("Google API key is required. Set GOOGLE_MAPS_API_KEY environment variable.")
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'usps', 'smartystreets', or 'google'")

    def _get_usps_oauth_token(self) -> str:
        """
        Get USPS OAuth 2.0 access token (with caching).

        Tokens are cached and reused until they expire (typically 1 hour).
        Automatically refreshes expired tokens.

        Returns:
            str: Valid OAuth access token
        """
        import time

        # Check if cached token is still valid (60 second buffer)
        if self.usps_access_token and time.time() < (self.usps_token_expiry - 60):
            logger.info("Using cached USPS OAuth token")
            return self.usps_access_token

        logger.info("Fetching new USPS OAuth token")

        # Request new token
        payload = {
            'grant_type': 'client_credentials',
            'client_id': self.usps_client_id,
            'client_secret': self.usps_client_secret
        }

        try:
            response = requests.post(
                self.oauth_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(f"OAuth token request failed: {response.status_code} - {response.text}")
                raise Exception(f"USPS OAuth failed: {response.status_code} - {response.text}")

            data = response.json()

            if 'access_token' not in data:
                logger.error(f"No access_token in response: {data}")
                raise Exception("USPS OAuth response missing access_token")

            # Cache token and expiry time
            self.usps_access_token = data['access_token']
            expires_in = data.get('expires_in', 3600)  # Default 1 hour
            self.usps_token_expiry = time.time() + expires_in

            logger.info(f"✓ OAuth token acquired (expires in {expires_in}s)")
            return self.usps_access_token

        except requests.RequestException as e:
            logger.error(f"OAuth request failed: {str(e)}")
            raise Exception(f"Failed to get USPS OAuth token: {str(e)}")

    def validate_address(self, street, city, state, zipcode) -> Dict:
        """
        Validate an address and return standardized components.

        Args:
            street: Street address
            city: City name
            state: State abbreviation
            zipcode: ZIP code

        Returns:
            Dictionary with standardized address components:
                - status: "SUCCESS" or "ERROR"
                - validated_address: Standardized street address
                - validated_city: Standardized city
                - validated_state: State abbreviation
                - validated_zip5: 5-digit ZIP
                - zip_plus4: 4-digit ZIP extension
                - delivery_point: 2-digit delivery point
                - carrier_route: Carrier route (e.g., "C001")
                - dpv_status: Delivery Point Validation status
                - routing_code: 11-digit routing code
                - message: Error or info message
        """
        # Check cache first to avoid duplicate API calls
        cache_key = f"{street}|{city}|{state}|{zipcode}".lower().strip()
        if cache_key in self.address_cache:
            logger.info(f"Address cache hit: {street}, {city}, {state}")
            return self.address_cache[cache_key].copy()

        try:
            if self.provider == "usps":
                result = self._validate_usps(street, city, state, zipcode)
            elif self.provider == "smartystreets":
                result = self._validate_smartystreets(street, city, state, zipcode)
            elif self.provider == "google":
                result = self._validate_google(street, city, state, zipcode)
            else:
                result = None

            # Cache successful validations
            if result and result.get('status') == 'SUCCESS':
                self.address_cache[cache_key] = result.copy()

            return result
        except Exception as e:
            return {
                'status': 'ERROR',
                'validated_address': street,
                'validated_city': city,
                'validated_state': state,
                'validated_zip5': zipcode[:5] if zipcode else '',
                'zip_plus4': '',
                'delivery_point': '',
                'carrier_route': '',
                'dpv_status': 'Error',
                'routing_code': '',
                'message': f"Validation failed: {str(e)}"
            }

    def _validate_usps(self, street, city, state, zipcode) -> Dict:
        """
        Validate using USPS Official API (OAuth 2.0 + JSON).

        Note: USPS API must only be used for shipping/mailing purposes.
        Returns complete address validation with DPV, ZIP+4, and delivery point.
        """
        logger.info(f"USPS OAuth Validation Request - Street: {street}, City: {city}, State: {state}, ZIP: {zipcode}")

        # Get OAuth token
        try:
            access_token = self._get_usps_oauth_token()
        except Exception as e:
            logger.error(f"Failed to get OAuth token: {str(e)}")
            return {
                'status': 'ERROR',
                'validated_address': street,
                'validated_city': city,
                'validated_state': state,
                'validated_zip5': zipcode[:5] if zipcode else '',
                'zip_plus4': '',
                'delivery_point': '',
                'carrier_route': '',
                'dpv_status': 'Error',
                'routing_code': '',
                'message': f'OAuth authentication failed: {str(e)}'
            }

        # Parse ZIP code - handle "12345-6789" or "12345" format
        if zipcode and '-' in zipcode:
            zip5_val = zipcode.split('-')[0]
        else:
            zip5_val = zipcode[:5] if zipcode else ''

        # Build request parameters (filtering out empty values)
        params = {
            'streetAddress': street,
            'city': city or '',
            'state': state,
            'ZIPCode': zip5_val
        }
        # Remove empty parameters
        params = {k: v for k, v in params.items() if v}

        # API endpoint for full address validation with DPV and delivery point
        endpoint = f"{self.base_url}/addresses/v3/address"

        logger.info(f"Calling USPS OAuth API: {endpoint}")
        logger.info(f"Parameters: {params}")

        try:
            response = requests.get(
                endpoint,
                params=params,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Accept': 'application/json'
                },
                timeout=10
            )

            logger.info(f"USPS API Response Status: {response.status_code}")

            # Handle rate limiting (429) with exponential backoff
            if response.status_code == 429:
                retry_after_raw = int(response.headers.get('Retry-After', 60))
                logger.warning(f"USPS API rate limit hit (429). USPS requested wait: {retry_after_raw} seconds")

                # Fail fast if USPS wants us to wait too long (indicates quota exhaustion)
                if retry_after_raw > 60:
                    logger.error(f"USPS API rate limit exceeded with excessive retry delay ({retry_after_raw}s). Failing fast.")
                    return {
                        'status': 'ERROR',
                        'message': f'USPS API rate limit exceeded (retry required in {retry_after_raw}s). Your API quota may be exhausted. Please try again later.',
                        'validated_address': street,
                        'validated_city': city,
                        'validated_state': state,
                        'validated_zip5': '',
                        'zip_plus4': '',
                        'delivery_point': '',
                        'routing_code': '',
                        'carrier_route': '',
                        'dpv_status': 'Error'
                    }

                # Cap retry wait to 60 seconds max (prevent infinite hangs)
                retry_after = min(retry_after_raw, 60)
                logger.warning(f"Waiting {retry_after} seconds before retry...")

                import time
                time.sleep(retry_after)

                # Retry the request once after waiting
                logger.info("Retrying USPS API request after rate limit delay...")
                response = requests.get(
                    endpoint,
                    params=params,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Accept': 'application/json'
                    },
                    timeout=10
                )

                # If still rate limited after retry, return error instead of raising exception
                if response.status_code == 429:
                    logger.error("USPS API still rate limited after retry")
                    return {
                        'status': 'ERROR',
                        'message': 'USPS API rate limit exceeded. Please try again later or reduce batch size.',
                        'validated_address': street,
                        'validated_city': city,
                        'validated_state': state,
                        'validated_zip5': '',
                        'zip_plus4': '',
                        'delivery_point': '',
                        'routing_code': '',
                        'carrier_route': '',
                        'dpv_status': 'Error'
                    }

            # Handle other errors
            if response.status_code >= 300:
                logger.error(f"USPS API error {response.status_code}: {response.text}")
                raise Exception(f"USPS API error {response.status_code}: {response.text}")

            # Parse JSON response
            data = response.json()
            logger.info(f"USPS API Response: {data}")

            # Extract address data
            address = data.get('address', {})
            additional_info = data.get('additionalInfo', {})

            # Check if address was found
            if not address or not address.get('ZIPCode'):
                return {
                    'status': 'ERROR',
                    'validated_address': street,
                    'validated_city': city,
                    'validated_state': state,
                    'validated_zip5': zipcode[:5] if zipcode else '',
                    'zip_plus4': '',
                    'delivery_point': '',
                    'carrier_route': '',
                    'dpv_status': 'Invalid',
                    'routing_code': '',
                    'message': 'Address not found or invalid'
                }

            # Extract validated components
            validated_street = address.get('streetAddress', street)
            validated_city = address.get('city', city)
            validated_state = address.get('state', state)
            zip5 = address.get('ZIPCode', '')
            zip4 = address.get('ZIPPlus4', '')

            # Extract delivery point and carrier route from additionalInfo
            delivery_point = additional_info.get('deliveryPoint', '')
            carrier_route = additional_info.get('carrierRoute', '')

            # DPV confirmation
            dpv_confirmation = additional_info.get('DPVConfirmation', 'N')
            dpv_status = 'Valid' if dpv_confirmation == 'Y' else 'Invalid' if dpv_confirmation == 'N' else 'Uncertain'

            # Build routing code: ZIP5 + ZIP4 + Delivery Point (11 digits total)
            # Ensure each component is properly zero-padded
            zip5 = zip5.zfill(5) if zip5 else "00000"
            zip4 = zip4.zfill(4) if zip4 else "0000"
            delivery_point = delivery_point.zfill(2) if delivery_point else "00"
            routing_code = f"{zip5}{zip4}{delivery_point}"

            result = {
                'status': 'SUCCESS',
                'validated_address': validated_street,
                'validated_city': validated_city,
                'validated_state': validated_state,
                'validated_zip5': zip5,
                'zip_plus4': zip4,
                'delivery_point': delivery_point,
                'carrier_route': carrier_route,
                'dpv_status': dpv_status,
                'routing_code': routing_code,
                'message': 'Address validated successfully via USPS OAuth API'
            }

            # Log success details
            logger.info(f"✅ USPS Validation SUCCESS")
            logger.info(f"   ZIP5: {zip5}")
            logger.info(f"   ZIP4: {zip4}")
            logger.info(f"   DeliveryPoint: '{delivery_point}' (length: {len(delivery_point)})")
            logger.info(f"   CarrierRoute: {carrier_route}")
            logger.info(f"   RoutingCode: {routing_code} (length: {len(routing_code)})")
            logger.info(f"   DPV Status: {dpv_status}")
            return result

        except requests.RequestException as e:
            logger.error(f"USPS API request failed: {str(e)}")
            raise Exception(f"USPS API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process USPS response: {str(e)}")
            raise Exception(f"Failed to process USPS response: {str(e)}")

    def _validate_smartystreets(self, street, city, state, zipcode) -> Dict:
        """Validate using SmartyStreets API (Premium, CASS certified)."""
        params = {
            'auth-id': self.auth_id,
            'auth-token': self.auth_token,
            'street': street,
            'city': city,
            'state': state,
            'zipcode': zipcode,
            'match': 'invalid'  # Return only valid addresses
        }

        response = requests.get(self.base_url, params=params, timeout=10)

        if response.status_code != 200:
            raise Exception(f"SmartyStreets API error: {response.status_code} - {response.text}")

        data = response.json()

        if not data or len(data) == 0:
            return {
                'status': 'ERROR',
                'validated_address': street,
                'validated_city': city,
                'validated_state': state,
                'validated_zip5': zipcode[:5] if zipcode else '',
                'zip_plus4': '',
                'delivery_point': '',
                'carrier_route': '',
                'dpv_status': 'Invalid',
                'routing_code': '',
                'message': 'Address not found or invalid'
            }

        # Extract first result
        result = data[0]
        components = result.get('components', {})
        metadata = result.get('metadata', {})
        delivery_line = result.get('delivery_line_1', '')

        # Extract ZIP+4 and delivery point
        zip5 = components.get('zipcode', '')
        zip4 = components.get('plus4_code', '')
        delivery_point = components.get('delivery_point', '')  # Fixed: delivery_point is in components, not metadata
        carrier_route = metadata.get('carrier_route', '')

        # DPV confirmation
        dpv = metadata.get('dpv_match_code', 'N')
        dpv_status = 'Valid' if dpv == 'Y' else 'Invalid' if dpv == 'N' else 'Uncertain'

        # Build routing code: ZIP5 + ZIP4 + Delivery Point
        # Ensure each component is properly zero-padded
        zip5 = zip5.zfill(5) if zip5 else "00000"
        zip4 = zip4.zfill(4) if zip4 else "0000"
        delivery_point = delivery_point.zfill(2) if delivery_point else "00"
        routing_code = f"{zip5}{zip4}{delivery_point}"

        return {
            'status': 'SUCCESS',
            'validated_address': delivery_line,
            'validated_city': components.get('city_name', city),
            'validated_state': components.get('state_abbreviation', state),
            'validated_zip5': zip5,
            'zip_plus4': zip4,
            'delivery_point': delivery_point,
            'carrier_route': carrier_route,
            'dpv_status': dpv_status,
            'routing_code': routing_code,
            'message': 'Address validated successfully via SmartyStreets'
        }

    def _validate_google(self, street, city, state, zipcode) -> Dict:
        """
        Validate using Google Address Validation API (CASS certified).

        Provides USPS standardized addresses with ZIP+4 and delivery point data.
        Free tier: $200/month (~12,000 addresses), then $17/1,000 lookups.
        """
        # Build request body
        request_body = {
            "address": {
                "regionCode": "US",
                "addressLines": [street],
                "locality": city,
                "administrativeArea": state,
                "postalCode": zipcode
            },
            "enableUspsCass": True  # Enable USPS CASS processing
        }

        headers = {
            'Content-Type': 'application/json'
        }

        params = {
            'key': self.api_key
        }

        response = requests.post(
            self.base_url,
            json=request_body,
            headers=headers,
            params=params,
            timeout=10
        )

        if response.status_code != 200:
            raise Exception(f"Google API error: {response.status_code} - {response.text}")

        data = response.json()

        # Check if address was validated
        result = data.get('result', {})
        verdict = result.get('verdict', {})

        if not verdict.get('hasInferredComponents', False) and not verdict.get('addressComplete', False):
            return {
                'status': 'ERROR',
                'validated_address': street,
                'validated_city': city,
                'validated_state': state,
                'validated_zip5': zipcode[:5] if zipcode else '',
                'zip_plus4': '',
                'delivery_point': '',
                'carrier_route': '',
                'dpv_status': 'Invalid',
                'routing_code': '',
                'message': 'Address not found or invalid'
            }

        # Extract address components
        address_result = result.get('address', {})
        postal_address = address_result.get('postalAddress', {})

        # Get formatted address lines
        address_lines = postal_address.get('addressLines', [])
        validated_address = address_lines[0] if address_lines else street

        validated_city = postal_address.get('locality', city)
        validated_state = postal_address.get('administrativeArea', state)
        postal_code = postal_address.get('postalCode', zipcode)

        # Extract ZIP+4
        zip5 = postal_code[:5] if postal_code else ''
        zip4 = postal_code[6:10] if len(postal_code) > 6 else ''  # Format: "12345-6789"

        # Get USPS data if available
        usps_data = result.get('uspsData', {})
        standardized_address = usps_data.get('standardizedAddress', {})

        # Delivery point from USPS data
        delivery_point = usps_data.get('deliveryPointCheckDigit', '')
        if not delivery_point:
            # Try to extract from postal code extension
            delivery_point = ''

        # Carrier route
        carrier_route = usps_data.get('carrierRoute', '')

        # DPV confirmation
        dpv_confirmation = usps_data.get('dpvConfirmation', 'N')
        dpv_status = 'Valid' if dpv_confirmation == 'Y' else 'Invalid' if dpv_confirmation == 'N' else 'Uncertain'

        # If we have standardized USPS address, use it
        if standardized_address:
            first_address_line = standardized_address.get('firstAddressLine', validated_address)
            if first_address_line:
                validated_address = first_address_line

            # Get more accurate ZIP+4 from USPS data
            zip_code_ext = usps_data.get('zipCodeExtension', zip4)
            if zip_code_ext:
                zip4 = zip_code_ext

        # Build routing code: ZIP5 + ZIP4 + Delivery Point
        # Ensure each component is properly zero-padded
        zip5 = zip5.zfill(5) if zip5 else "00000"
        zip4 = zip4.zfill(4) if zip4 else "0000"
        delivery_point = delivery_point.zfill(2) if delivery_point else "00"
        routing_code = f"{zip5}{zip4}{delivery_point}"

        return {
            'status': 'SUCCESS',
            'validated_address': validated_address,
            'validated_city': validated_city,
            'validated_state': validated_state,
            'validated_zip5': zip5,
            'zip_plus4': zip4,
            'delivery_point': delivery_point,
            'carrier_route': carrier_route,
            'dpv_status': dpv_status,
            'routing_code': routing_code,
            'message': 'Address validated successfully via Google'
        }

    def validate_batch(self, addresses: list) -> list:
        """
        Validate multiple addresses.

        Note: For better performance with large batches, consider implementing
        provider-specific batch APIs (all three providers support batch operations).

        Args:
            addresses: List of dicts with keys: street, city, state, zipcode

        Returns:
            List of validation results
        """
        results = []
        for addr in addresses:
            result = self.validate_address(
                addr.get('street', ''),
                addr.get('city', ''),
                addr.get('state', ''),
                addr.get('zipcode', '')
            )
            results.append(result)
        return results


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Address Validator - API Testing")
    print("=" * 60)
    print()

    # Test address
    test_address = {
        'street': "1600 Amphitheatre Parkway",
        'city': "Mountain View",
        'state': "CA",
        'zipcode': "94043"
    }

    # Test each provider (comment out if you don't have credentials)
    providers = ["usps", "smartystreets", "google"]

    for provider in providers:
        print(f"\nTesting {provider.upper()}:")
        print("-" * 60)
        try:
            validator = AddressValidator(provider=provider)
            result = validator.validate_address(**test_address)

            if result['status'] == 'SUCCESS':
                print(f"✅ Status: {result['status']}")
                print(f"   Address: {result['validated_address']}")
                print(f"   City: {result['validated_city']}, {result['validated_state']}")
                print(f"   ZIP+4: {result['validated_zip5']}-{result['zip_plus4']}")
                print(f"   Delivery Point: {result['delivery_point']}")
                print(f"   Carrier Route: {result['carrier_route']}")
                print(f"   DPV Status: {result['dpv_status']}")
                print(f"   Routing Code: {result['routing_code']}")
            else:
                print(f"❌ Error: {result['message']}")

        except ValueError as e:
            print(f"⚠️  Skipped: {str(e)}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
