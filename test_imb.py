#!/usr/bin/env python3
"""
Test script for IMB Generator functionality
Run this to verify the IMB generation works correctly
"""

import sys
sys.path.insert(0, '.')

from utils.imb_generator import IMBGenerator, build_routing_code


def test_imb_generation():
    """Test basic IMB generation"""
    print("=" * 60)
    print("IMB Generator - Functionality Test")
    print("=" * 60)
    print()

    # Test 1: Build routing code
    print("Test 1: Building Routing Code")
    print("-" * 60)
    routing = build_routing_code(
        zip5="90210",
        zip4="5432",
        delivery_point="01"
    )
    print(f"  ZIP Code: 90210-5432-01")
    print(f"  Routing Code: {routing}")
    assert len(routing) == 11, "Routing code should be 11 digits"
    assert routing == "90210543201", f"Expected 90210543201, got {routing}"
    print("  ✅ PASS")
    print()

    # Test 2: Initialize IMB Generator
    print("Test 2: Initializing IMB Generator")
    print("-" * 60)
    generator = IMBGenerator(
        barcode_id="00",
        service_type="040",  # First-Class Mail
        mailer_id="123456"   # 6-digit Mailer ID
    )
    print(f"  Barcode ID: {generator.barcode_id}")
    print(f"  Service Type: {generator.service_type}")
    print(f"  Mailer ID: 123456")
    print("  ✅ PASS")
    print()

    # Test 3: Generate tracking code
    print("Test 3: Generating Tracking Code")
    print("-" * 60)
    tracking_code = generator.generate_tracking_code(
        mailer_id="123456",
        sequence_num=1,
        routing_code=routing
    )
    print(f"  Tracking Code: {tracking_code}")
    print(f"  Length: {len(tracking_code)} digits")
    assert len(tracking_code) == 31, "Tracking code should be 31 digits"
    print("  ✅ PASS")
    print()

    # Test 4: Generate complete barcode
    print("Test 4: Generating Complete IMB Barcode")
    print("-" * 60)
    result = generator.generate_barcode(
        mailer_id="123456",
        sequence_num=1,
        routing_code=routing
    )

    if result['valid']:
        print(f"  Tracking Code: {result['tracking_code']}")
        print(f"  Barcode: {result['barcode'][:30]}... (truncated)")
        print(f"  Barcode Length: {len(result['barcode'])} characters")
        print(f"  CRC Checksum: {result['crc']}")
        assert len(result['barcode']) == 65, "Barcode should be 65 characters"
        print("  ✅ PASS")
    else:
        print(f"  ❌ FAIL: {result['errors']}")
        return False
    print()

    # Test 5: Test with 9-digit Mailer ID
    print("Test 5: Testing with 9-digit Mailer ID")
    print("-" * 60)
    result = generator.generate_barcode(
        mailer_id="123456789",
        sequence_num=42,
        routing_code=routing
    )

    if result['valid']:
        print(f"  Tracking Code: {result['tracking_code']}")
        print(f"  Sequence Number: 42")
        assert len(result['tracking_code']) == 31, "Tracking code should be 31 digits"
        print("  ✅ PASS")
    else:
        print(f"  ❌ FAIL: {result['errors']}")
        return False
    print()

    # Test 6: Test validation
    print("Test 6: Testing Input Validation")
    print("-" * 60)
    result = generator.generate_barcode(
        mailer_id="12345",  # Invalid: only 5 digits
        sequence_num=1,
        routing_code=routing
    )

    if not result['valid'] and len(result['errors']) > 0:
        print(f"  Expected Error: {result['errors'][0]}")
        print("  ✅ PASS (validation working)")
    else:
        print("  ❌ FAIL: Should have caught invalid Mailer ID")
        return False
    print()

    # Test 7: Test different service types
    print("Test 7: Testing Different Service Types")
    print("-" * 60)
    service_types = [
        ("040", "First-Class Mail"),
        ("240", "USPS Marketing Mail"),
        ("340", "Periodicals"),
        ("440", "Bound Printed Matter"),
        ("540", "Package Services")
    ]

    for code, name in service_types:
        gen = IMBGenerator(barcode_id="00", service_type=code, mailer_id="123456")
        result = gen.generate_barcode("123456", 1, routing)
        if result['valid']:
            print(f"  {code} ({name}): ✅")
        else:
            print(f"  {code} ({name}): ❌ {result['errors']}")
            return False
    print()

    # Summary
    print("=" * 60)
    print("All Tests Passed! ✅")
    print("=" * 60)
    print()
    print("The IMB Generator is working correctly.")
    print("You can now process mailing lists through the web interface.")
    print()

    return True


def main():
    """Run all tests"""
    try:
        success = test_imb_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED WITH ERROR")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
