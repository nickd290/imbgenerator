"""
File Processing Utilities
Handles CSV and Excel file uploads, parsing, and export
"""

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional


class FileProcessor:
    """
    Processes mailing list files (CSV, Excel) for IMB generation.
    """

    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

    # Common column name variations for address fields
    ADDRESS_PATTERNS = {
        'street': ['street', 'address', 'address1', 'addr', 'street_address', 'address_line_1', 'line1'],
        'city': ['city', 'town', 'municipality'],
        'state': ['state', 'st', 'province', 'region'],
        'zip': ['zip', 'zipcode', 'zip_code', 'postal', 'postal_code', 'postcode'],
        'zip4': ['zip4', 'zip_4', 'plus4', 'plus_4', 'zip+4', 'zipplus4']
    }

    def __init__(self, upload_folder='uploads'):
        """Initialize file processor."""
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)

    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def load_file(self, filepath: str) -> pd.DataFrame:
        """
        Load CSV or Excel file into DataFrame.

        Args:
            filepath: Path to the file

        Returns:
            pandas DataFrame

        Raises:
            ValueError: If file format is not supported
        """
        ext = filepath.rsplit('.', 1)[1].lower()

        if ext == 'csv':
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    return df
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not read CSV file with any supported encoding")

        elif ext in ['xlsx', 'xls']:
            # Read Excel with dtype=str to prevent NaN type inference issues
            # keep_default_na=False prevents empty cells from becoming NaN
            df = pd.read_excel(filepath, dtype=str, keep_default_na=False)
            # Replace any remaining empty strings with None for consistency
            df = df.replace('', None)
            return df

        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def detect_address_columns(self, df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """
        Auto-detect address-related columns.
        Prioritizes exact matches over partial matches to handle extra columns correctly.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary mapping field types to detected column names:
                {'street': 'Address', 'city': 'City', 'state': 'ST', 'zip': 'ZIP'}
        """
        detected = {
            'street': None,
            'city': None,
            'state': None,
            'zip': None,
            'zip4': None  # Optional field
        }

        # Normalize column names for comparison
        columns_lower = {col: col.lower().replace('_', '').replace(' ', '') for col in df.columns}

        # Try exact matches first (highest priority)
        for field_type, patterns in self.ADDRESS_PATTERNS.items():
            for col, col_normalized in columns_lower.items():
                for pattern in patterns:
                    pattern_normalized = pattern.replace('_', '')
                    # Exact match
                    if col_normalized == pattern_normalized:
                        detected[field_type] = col
                        break
                if detected[field_type]:
                    break

        # Try partial matches for any still undetected fields
        for field_type, patterns in self.ADDRESS_PATTERNS.items():
            if detected[field_type]:  # Skip if already found
                continue
            for col, col_normalized in columns_lower.items():
                for pattern in patterns:
                    pattern_normalized = pattern.replace('_', '')
                    # Partial match (contains pattern)
                    if pattern_normalized in col_normalized:
                        detected[field_type] = col
                        break
                if detected[field_type]:
                    break

        return detected

    def preview_data(self, df: pd.DataFrame, num_rows: int = 10) -> Dict:
        """
        Generate preview of uploaded data.

        Args:
            df: DataFrame to preview
            num_rows: Number of rows to include

        Returns:
            Dictionary with preview data and metadata
        """
        # Get preview data and replace NaN with None for valid JSON
        preview_df = df.head(num_rows)
        preview_df = preview_df.where(pd.notnull(preview_df), None)

        return {
            'columns': list(df.columns),
            'num_rows': len(df),
            'num_columns': len(df.columns),
            'preview': preview_df.to_dict('records'),
            'detected_columns': self.detect_address_columns(df)
        }

    def validate_mapping(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> Tuple[bool, List[str]]:
        """
        Validate that mapped columns exist in DataFrame.

        Args:
            df: DataFrame to validate against
            column_mapping: Dictionary mapping field types to column names

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        required_fields = ['street', 'city', 'state', 'zip']

        for field in required_fields:
            col_name = column_mapping.get(field)
            if not col_name:
                errors.append(f"Missing mapping for required field: {field}")
            elif col_name not in df.columns:
                errors.append(f"Mapped column '{col_name}' not found in file")

        return len(errors) == 0, errors

    def prepare_for_processing(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Prepare DataFrame for IMB processing.

        Args:
            df: Original DataFrame
            column_mapping: Mapping of field types to column names
                          Can include optional 'zip4' field

        Returns:
            DataFrame with standardized column names and ready for processing
        """
        # Create a copy to avoid modifying original
        df_processed = df.copy()

        # Add standardized columns with proper NaN handling
        # First replace NaN with empty string, then convert to string
        for field in ['street', 'city', 'state', 'zip']:
            col_name = column_mapping[field]
            df_processed[f'_{field}'] = df_processed[col_name].fillna('').astype(str)

        # Handle optional ZIP+4 column
        if column_mapping.get('zip4'):
            zip4_col = column_mapping['zip4']
            df_processed['_zip4'] = df_processed[zip4_col].fillna('').astype(str).str.strip()

            # Concatenate ZIP5 and ZIP+4 when ZIP+4 is available
            # Format: "12345-6789" or just "12345" if ZIP+4 is empty
            df_processed['_zip'] = df_processed.apply(
                lambda row: f"{row['_zip'].strip()}-{row['_zip4']}"
                            if row['_zip4'] and row['_zip4'].strip()
                            else row['_zip'].strip(),
                axis=1
            )

        # Clean up data
        df_processed['_street'] = df_processed['_street'].str.strip()
        df_processed['_city'] = df_processed['_city'].str.strip()
        df_processed['_state'] = df_processed['_state'].str.strip().str.upper()
        df_processed['_zip'] = df_processed['_zip'].str.strip()

        # Remove rows with missing critical data
        df_processed = df_processed[
            (df_processed['_street'] != '') &
            (df_processed['_city'] != '') &
            (df_processed['_state'] != '') &
            (df_processed['_zip'] != '')
        ]

        return df_processed

    def add_imb_columns(self, df: pd.DataFrame, results: List[Dict]) -> pd.DataFrame:
        """
        Add IMB generation results to DataFrame.

        Args:
            df: Original DataFrame
            results: List of result dictionaries from IMB processing

        Returns:
            DataFrame with IMB columns added
        """
        # Create a copy
        df_with_imb = df.copy()

        # Extract result fields
        result_fields = [
            'validated_address',
            'validated_city',
            'validated_state',
            'validated_zip5',
            'zip_plus4',
            'delivery_point',
            'routing_code',
            'carrier_route',
            'dpv_status',
            'imb_tracking_code',
            'imb_barcode',
            'sequence_number',
            'validation_status',
            'validation_message'
        ]

        # Initialize new columns
        for field in result_fields:
            df_with_imb[field] = [r.get(field, '') for r in results]

        return df_with_imb

    def export_to_csv(self, df: pd.DataFrame, original_filename: str, output_folder: str = None) -> str:
        """
        Export DataFrame to CSV with timestamped filename.

        Args:
            df: DataFrame to export
            original_filename: Original uploaded filename
            output_folder: Output directory (defaults to upload_folder)

        Returns:
            Path to exported file
        """
        if output_folder is None:
            output_folder = self.upload_folder

        # Generate output filename
        base_name = os.path.splitext(original_filename)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"{base_name}_IMB_{timestamp}.csv"
        output_path = os.path.join(output_folder, output_filename)

        # Export to CSV
        df.to_csv(output_path, index=False, encoding='utf-8')

        return output_path

    def export_errors(self, df: pd.DataFrame, original_filename: str, output_folder: str = None) -> str:
        """
        Export only failed/error rows to separate CSV.

        Args:
            df: DataFrame with validation_status column
            original_filename: Original uploaded filename
            output_folder: Output directory

        Returns:
            Path to error file
        """
        if output_folder is None:
            output_folder = self.upload_folder

        # Filter error rows
        error_df = df[df['validation_status'] == 'ERROR'].copy()

        if len(error_df) == 0:
            return None

        # Generate error filename
        base_name = os.path.splitext(original_filename)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        error_filename = f"{base_name}_ERRORS_{timestamp}.csv"
        error_path = os.path.join(output_folder, error_filename)

        # Export errors
        error_df.to_csv(error_path, index=False, encoding='utf-8')

        return error_path

    def get_processing_summary(self, df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics from processed DataFrame.

        Args:
            df: DataFrame with validation_status column

        Returns:
            Dictionary with summary stats
        """
        total = len(df)
        successful = len(df[df['validation_status'] == 'SUCCESS'])
        failed = len(df[df['validation_status'] == 'ERROR'])

        # DPV status breakdown
        dpv_valid = len(df[df['dpv_status'] == 'Valid'])
        dpv_invalid = len(df[df['dpv_status'] == 'Invalid'])
        dpv_uncertain = len(df[df['dpv_status'] == 'Uncertain'])

        return {
            'total_records': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
            'dpv_valid': dpv_valid,
            'dpv_invalid': dpv_invalid,
            'dpv_uncertain': dpv_uncertain,
            'api_calls': total  # One API call per record
        }


# Example usage
if __name__ == "__main__":
    processor = FileProcessor()

    # Test file loading
    # df = processor.load_file('sample_mailing_list.csv')
    # preview = processor.preview_data(df)
    # print(f"Detected columns: {preview['detected_columns']}")
