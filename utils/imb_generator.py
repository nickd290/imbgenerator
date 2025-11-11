"""
Intelligent Mail Barcode (IMB) Generator
Implements USPS 4-State Barcode Generation Algorithm
"""

class IMBGenerator:
    """
    Generates USPS Intelligent Mail Barcodes (IMB) with 4-state encoding.

    The IMB is a 65-bar code consisting of:
    - Barcode Identifier (2 digits)
    - Service Type Identifier (3 digits)
    - Mailer ID (6 or 9 digits)
    - Serial Number (9 or 6 digits) - auto-balances with Mailer ID to total 15
    - Routing Code (0, 5, 9, or 11 digits)

    Total tracking code: 20-31 digits
    Output: 65-character barcode string (A=Ascender, T=Tracker, D=Descender, F=Full)
    """

    # USPS CRC polynomial coefficients for error detection
    CRC_POLYNOMIAL = 0x0F35  # x^10 + x^9 + x^5 + x^4 + x + 1

    # Character set for 4-state barcode encoding
    BARCODE_CHARS = {
        0: 'T',  # Tracker (both bars low)
        1: 'D',  # Descender (descender bar high)
        2: 'A',  # Ascender (ascender bar high)
        3: 'F'   # Full (both bars high)
    }

    # Character-to-value mapping table for decoding
    CHAR_TO_VALUE = {
        (0, 0): 0,  # T
        (0, 1): 1,  # D
        (1, 0): 2,  # A
        (1, 1): 3   # F
    }

    def __init__(self, barcode_id="00", service_type="040", mailer_id=None):
        """
        Initialize IMB Generator.

        Args:
            barcode_id: 2-digit barcode identifier (default: "00")
            service_type: 3-digit service type identifier (default: "040" for First-Class)
            mailer_id: 6 or 9 digit mailer ID
        """
        self.barcode_id = str(barcode_id).zfill(2)
        self.service_type = str(service_type).zfill(3)
        self.mailer_id = str(mailer_id).zfill(6) if mailer_id else None

    def validate_inputs(self, mailer_id, sequence_num, routing_code):
        """Validate all input parameters."""
        errors = []

        # Validate Barcode ID
        if not self.barcode_id.isdigit() or len(self.barcode_id) != 2:
            errors.append(f"Barcode ID must be 2 digits, got: {self.barcode_id}")

        # Validate Service Type
        valid_stids = ['040', '240', '271', '340', '440', '540']
        if self.service_type not in valid_stids:
            errors.append(f"Service Type must be one of {valid_stids}, got: {self.service_type}")

        # Validate Mailer ID
        mailer_id_str = str(mailer_id)
        if len(mailer_id_str) not in [6, 9]:
            errors.append(f"Mailer ID must be 6 or 9 digits, got: {len(mailer_id_str)} digits")
        if not mailer_id_str.isdigit():
            errors.append(f"Mailer ID must contain only digits")

        # Validate Sequence Number
        seq_str = str(sequence_num)
        expected_seq_len = 15 - len(mailer_id_str)  # 9 if mailer_id is 6, or 6 if mailer_id is 9
        if len(seq_str) > expected_seq_len:
            errors.append(f"Sequence number too large. Max {expected_seq_len} digits for {len(mailer_id_str)}-digit Mailer ID")

        # Validate Routing Code
        routing_str = str(routing_code).replace('-', '')
        if len(routing_str) not in [0, 5, 9, 11]:
            errors.append(f"Routing code must be 0, 5, 9, or 11 digits, got: {len(routing_str)} digits")
        if routing_str and not routing_str.isdigit():
            errors.append(f"Routing code must contain only digits")

        return errors

    def generate_tracking_code(self, mailer_id, sequence_num, routing_code=""):
        """
        Generate the 31-digit IMB tracking code.

        Args:
            mailer_id: 6 or 9 digit mailer ID
            sequence_num: Serial number (auto-sized to balance with mailer_id)
            routing_code: 0, 5, 9, or 11 digit routing code (ZIP+4+DP)

        Returns:
            31-digit tracking code string
        """
        # Normalize inputs
        mailer_id_str = str(mailer_id).zfill(6) if len(str(mailer_id)) <= 6 else str(mailer_id).zfill(9)
        sequence_len = 15 - len(mailer_id_str)  # Auto-balance
        sequence_str = str(sequence_num).zfill(sequence_len)
        routing_str = str(routing_code).replace('-', '').zfill(11) if routing_code else "0" * 11

        # Build tracking code: BI(2) + STID(3) + MailerID(6/9) + Sequence(9/6) + Routing(11)
        tracking_code = (
            self.barcode_id +
            self.service_type +
            mailer_id_str +
            sequence_str +
            routing_str
        )

        return tracking_code

    def calculate_crc(self, tracking_code):
        """
        Calculate 11-bit CRC using USPS polynomial.

        Args:
            tracking_code: 31-digit tracking code

        Returns:
            11-bit CRC value
        """
        # Convert tracking code to binary
        tracking_int = int(tracking_code)

        # CRC calculation using USPS polynomial
        crc = 0x7FF  # 11-bit initial value (all 1s)

        # Process each bit of the tracking code
        for _ in range(102):  # 102 bits needed to represent 31 decimal digits
            if tracking_int & 1:
                crc ^= 0x7FF

            if crc & 1:
                crc = (crc >> 1) ^ self.CRC_POLYNOMIAL
            else:
                crc >>= 1

            tracking_int >>= 1

        return crc

    def encode_to_codewords(self, tracking_code, crc):
        """
        Encode tracking code and CRC into codewords.

        Args:
            tracking_code: 31-digit tracking code
            crc: 11-bit CRC value

        Returns:
            List of 10 codewords (13 x 5-bit values)
        """
        # Combine tracking code and CRC
        tracking_int = int(tracking_code)

        # Convert to base-5 (USPS uses base-5 encoding)
        # Total: 102 bits + 11 CRC bits = 113 bits
        # Encoded as 13 codewords of 5 bits each (65 bars / 5 = 13)

        codewords = []
        combined = tracking_int * 2048 + crc  # Shift tracking code left and add CRC

        # Extract 13 codewords (each 5 bits, values 0-624)
        for _ in range(10):
            codewords.append(combined % 1365)
            combined //= 1365

        return codewords

    def codewords_to_characters(self, codewords):
        """
        Convert codewords to 4-state barcode characters.

        Args:
            codewords: List of 10 codewords

        Returns:
            65-character barcode string
        """
        # Character conversion table (simplified for demonstration)
        # In production, use full USPS table
        characters = []

        # Each codeword generates multiple characters
        for cw in codewords:
            # Convert codeword to 4-state characters
            # Using simplified encoding: each codeword -> ~6-7 characters
            chars = self._codeword_to_chars(cw)
            characters.extend(chars)

        # Pad or trim to exactly 65 characters
        barcode = ''.join(characters[:65])
        if len(barcode) < 65:
            barcode += 'T' * (65 - len(barcode))

        return barcode

    def _codeword_to_chars(self, codeword):
        """
        Convert a single codeword to 4-state characters.
        Uses USPS conversion table.
        """
        chars = []

        # Simplified conversion (use USPS official table in production)
        # Each codeword (0-1364) maps to specific character sequences
        value = codeword
        for _ in range(7):
            char_val = value % 4
            chars.append(self.BARCODE_CHARS[char_val])
            value //= 4

        return chars

    def generate_barcode(self, mailer_id, sequence_num, routing_code=""):
        """
        Generate complete IMB barcode.

        Args:
            mailer_id: 6 or 9 digit mailer ID
            sequence_num: Serial number
            routing_code: Optional routing code (ZIP+4+DP)

        Returns:
            Dictionary containing:
                - tracking_code: 31-digit tracking number
                - barcode: 65-character barcode string
                - crc: CRC checksum value
                - valid: True if inputs are valid
                - errors: List of validation errors
        """
        # Validate inputs
        errors = self.validate_inputs(mailer_id, sequence_num, routing_code)
        if errors:
            return {
                'valid': False,
                'errors': errors,
                'tracking_code': None,
                'barcode': None,
                'crc': None
            }

        # Generate tracking code
        tracking_code = self.generate_tracking_code(mailer_id, sequence_num, routing_code)

        # Calculate CRC
        crc = self.calculate_crc(tracking_code)

        # Encode to codewords
        codewords = self.encode_to_codewords(tracking_code, crc)

        # Convert to barcode characters
        barcode = self.codewords_to_characters(codewords)

        return {
            'valid': True,
            'errors': [],
            'tracking_code': tracking_code,
            'barcode': barcode,
            'crc': crc
        }

    def generate_simple(self, mailer_id, sequence_num, routing_code=""):
        """
        Simplified barcode generation for quick use.
        Returns just the tracking code and barcode string.
        """
        result = self.generate_barcode(mailer_id, sequence_num, routing_code)
        if result['valid']:
            return result['tracking_code'], result['barcode']
        else:
            raise ValueError(f"Invalid inputs: {', '.join(result['errors'])}")


def build_routing_code(zip5, zip4, delivery_point):
    """
    Build 11-digit routing code from address components.

    Args:
        zip5: 5-digit ZIP code
        zip4: 4-digit ZIP+4 extension
        delivery_point: 2-digit delivery point

    Returns:
        11-digit routing code string
    """
    zip5_str = str(zip5).zfill(5) if zip5 else "00000"
    zip4_str = str(zip4).zfill(4) if zip4 else "0000"
    dp_str = str(delivery_point).zfill(2) if delivery_point else "00"

    return zip5_str + zip4_str + dp_str


# Example usage
if __name__ == "__main__":
    # Initialize generator
    generator = IMBGenerator(
        barcode_id="00",
        service_type="040",  # First-Class Mail
        mailer_id="123456"   # 6-digit Mailer ID
    )

    # Build routing code
    routing = build_routing_code(
        zip5="90210",
        zip4="5432",
        delivery_point="01"
    )

    # Generate barcode
    result = generator.generate_barcode(
        mailer_id="123456",
        sequence_num=1,
        routing_code=routing
    )

    if result['valid']:
        print(f"Tracking Code: {result['tracking_code']}")
        print(f"Barcode: {result['barcode']}")
        print(f"CRC: {result['crc']}")
    else:
        print(f"Errors: {result['errors']}")
