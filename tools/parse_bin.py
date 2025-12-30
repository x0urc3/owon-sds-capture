import argparse
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_parser import parse_waveform_data, OwonHeader

def print_parsed_data(header: OwonHeader):
    """Prints the parsed OwonHeader data in a readable format."""
    print("\n--- Parsed Waveform Data ---")
    print(f"Model: {header.model}")
    print(f"Serial: {header.serial}")
    print(f"Trigger Status: {header.trigger_status}")
    print("------------------------------")

    if not header.channels:
        print("No channels found in the data.")
        return

    for i, ch in enumerate(header.channels):
        print(f"--- Channel {i+1} ({ch.name}) ---")
        print(f"  Samples: {ch.samples_file}")
        print(f"  Data Type: {'16-bit' if ch.datatype == 2 else '8-bit'}")
        print(f"  Volts/Div: {ch.volts_div} V")
        print(f"  Time/Div: {ch.time_div} s")
        print(f"  Attenuation: {ch.attenuation}x")
        print(f"  Vertical Offset: {ch.offset_y}")
        print(f"  Frequency: {ch.frequency} Hz")
        print(f"  Period: {ch.period} s")

        if ch.volt_points:
            print(f"  Found {len(ch.volt_points)} data points.")
            # Print first 5 data points as a sample
            print("  Sample Data (Time, Voltage):")
            for j in range(min(5, len(ch.volt_points))):
                time_point = ch.time_points[j]
                volt_point = ch.volt_points[j]
                print(f"    {j}: ({time_point:.6f} s, {volt_point:.4f} V)")
        else:
            print("  No data points found for this channel.")
        print("------------------------------")


def main():
    """Main function to read a file and parse it."""
    # Set up logging to see messages from the parser
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    parser = argparse.ArgumentParser(
        description="Parse an OWON SDS series binary waveform file."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the binary waveform file (.bin)."
    )
    args = parser.parse_args()

    try:
        logging.info(f"Reading binary file: {args.file_path}")
        with open(args.file_path, 'rb') as f:
            raw_data = f.read()
    except FileNotFoundError:
        logging.error(f"Error: File not found at '{args.file_path}'")
        return
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return

    logging.info("Parsing waveform data...")
    parsed_header = parse_waveform_data(raw_data)

    print_parsed_data(parsed_header)

    logging.info("Parsing complete.")


if __name__ == "__main__":
    main()
