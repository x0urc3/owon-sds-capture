"""
owon-sds-grok
Copyright (C) 2025 Khairulmizam <xource@gmail.com>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import argparse
import logging
import os
import constants

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Control an Owon PDS series oscilloscope.")

    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Increase verbosity. -v for info, -vv for debug, -vvv for pyusb debug.")
    parser.add_argument("--autoset", action="store_true", help="Automatic setting of all control values.")
    parser.add_argument("--self-calibrate", action="store_true", help="Run self-calibration.")
    parser.add_argument("--factory", action="store_true", help="Revert to factory default.")
    parser.add_argument("--trigger", type=str, choices=["force", "50", "0"],
                        help="Trigger actions. 'force' to force a trigger, '50' to set trigger to 50%%, '0' to set trigger to 0.")
    parser.add_argument("--depth", type=str, choices=[m.name for m in constants.MemoryDepth],
                        help="Set acquisition memory depth. If not provided, the device's current setting is used.")
    parser.add_argument("--coupling", nargs=2, metavar=('CHANNEL', 'VALUE'),
                        help="Set channel coupling. CHANNEL is 1 or 2. VALUE is one of " + ", ".join([c.name for c in constants.Coupling]))
    parser.add_argument("--probe", nargs=2, metavar=('CHANNEL', 'VALUE'),
                        help="Set probe attenuation scale. CHANNEL is 1 or 2. VALUE is one of " + ", ".join([p.name for p in constants.ProbeScale]))
    parser.add_argument("--volt-scale", nargs=2, metavar=('CHANNEL', 'VALUE'),
                        help="Set vertical voltage scale (Volt/Div). CHANNEL is 1 or 2. VALUE is one of " + ", ".join([v.name for v in constants.VoltScale]))
    parser.add_argument("--timebase", type=str, choices=[t.name for t in constants.TimeBase],
                        help="Set horizontal timebase scale (Sec/Div).")
    parser.add_argument("--trace-v-pos", nargs=2, metavar=('CHANNEL', 'VALUE'),
                        help="Set trace vertical position. CHANNEL is 1 or 2. VALUE is an integer from -250 to 250.")
    parser.add_argument("--trigger-h-pos", type=int,
                        help="Set trigger horizontal position. VALUE is an integer from -10000 to 10000.")
    parser.add_argument("--acq-mode", type=str, choices=[m.name for m in constants.AcquisitionMode], help="Set acquisition mode.")
    parser.add_argument("--acq-samples", type=str, choices=[s.name for s in constants.AverageSamples], default='SAMPLES_16', help="Set number of samples for Average mode. Used only with --acq-mode AVERAGE. Defaults to SAMPLES_16.")

    # --- Data Acquisition Arguments ---
    acquisition_group = parser.add_argument_group('Data Acquisition', 'Arguments for acquiring waveform data.')
    acquisition_group.add_argument("--get-waveform", action="store_true",
                                   help="Acquire waveform data from the oscilloscope.")
    acquisition_group.add_argument("--output", type=str, metavar='<filename>',
                                   help="Output file to save waveform data. If omitted, a timestamped filename is generated.")
    acquisition_group.add_argument("--format", type=str, choices=['csv', 'bin'], default='csv',
                                   help="Output format for waveform data. 'csv' for processed data, 'bin' for raw data. Defaults to csv.")

    # --- Trigger Configuration Arguments ---
    trigger_group = parser.add_argument_group('Trigger Configuration', 'Arguments for setting up edge or video triggers.')
    trigger_group.add_argument("--trigger-type", nargs=2, metavar=('CHANNEL', 'TYPE'),
                               help="The type of trigger to configure. CHANNEL is 1 or 2. TYPE is 'edge' or 'video'.")
    trigger_group.add_argument("--trigger-mode", type=str, choices=[m.name for m in constants.TriggerMode], default='AUTO',
                               help="Trigger mode (for edge trigger). Defaults to AUTO.")
    trigger_group.add_argument("--trigger-coupling", type=str, choices=[c.name for c in constants.TriggerCoupling], default='DC',
                               help="Trigger coupling (for edge trigger). Defaults to DC.")
    trigger_group.add_argument("--trigger-slope", type=str, choices=[e.name for e in constants.TriggerEdge], default='RISING',
                               help="Trigger slope (for edge trigger). Defaults to RISING.")
    trigger_group.add_argument("--trigger-level", type=int, default=0,
                               help="Trigger level in millivolts (-10000 to 10000) (for edge trigger). Defaults to 0.")
    trigger_group.add_argument("--trigger-alt", action='store_true',
                               help="Use alternate trigger mode (for edge trigger).")
    trigger_group.add_argument("--video-modulation", type=str, choices=[m.name for m in constants.VideoModulation], default='NTSC',
                               help="Video modulation standard (for video trigger). Defaults to NTSC.")
    trigger_group.add_argument("--video-sync", type=str, choices=[s.name for s in constants.VideoSync], default='LINE',
                               help="Video sync type (for video trigger). Defaults to LINE.")
    trigger_group.add_argument("--video-line", type=int,
                               help="Line number for LINE_NO sync type (for video trigger).")

    args = parser.parse_args()

    # Setup logging
    if args.verbose == 1:
        log_level = logging.INFO
    elif args.verbose == 2:
        log_level = logging.DEBUG
    elif args.verbose >= 3:
        log_level = logging.DEBUG
        os.environ['PYUSB_DEBUG'] = 'debug'
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    if args.verbose >= 3:
        logging.info("PyUSB debugging enabled.")

    # Import device and usb after setting up logging and environment
    import usb.core
    from device import SDSDevice
    from data_parser import export_to_csv, export_to_binary

    try:
        with SDSDevice() as device:
            # Handle Waveform Acquisition first as it's a primary action
            if args.get_waveform:
                from datetime import datetime
                import os

                output_filename = args.output
                # Determine correct extension
                ext = args.format

                if not output_filename:
                    output_filename = datetime.now().strftime(f'waveform_%Y%m%d-%H%M%S.{ext}')
                    logging.info(f"Output filename not specified, using {output_filename}")
                else:
                    # Check and fix extension if user provided a filename
                    base, current_ext = os.path.splitext(output_filename)
                    if current_ext.lower().strip('.') != ext:
                        output_filename = f"{base}.{ext}"
                        logging.warning(f"Filename extension corrected for format '{ext}'. New filename: '{output_filename}'")

                if args.format == 'csv':
                    waveform_data = device.get_waveform()
                    if waveform_data and waveform_data.channels:
                        export_to_csv(waveform_data, output_filename)
                    else:
                        logging.error("Could not export CSV: No waveform data was acquired or parsed.")
                elif args.format == 'bin':
                    raw_data = device.get_waveform_raw()
                    if raw_data:
                        export_to_binary(raw_data, output_filename)
                    else:
                        logging.error("Could not export binary: No raw data was acquired.")
                return

            # Handle Trigger Configuration first as it's complex
            if args.trigger_type:
                channel_str, trigger_type = args.trigger_type

                if channel_str not in ['1', '2']:
                    parser.error("Channel for --trigger-type must be 1 or 2.")
                if trigger_type not in ['edge', 'video']:
                    parser.error("Type for --trigger-type must be 'edge' or 'video'.")

                channel = constants.Channel[f"CH{channel_str}"]

                if trigger_type == 'edge':
                    # Validate edge trigger arguments
                    if any([args.video_modulation, args.video_sync, args.video_line]):
                        parser.error("Video arguments cannot be used with --trigger-type 'edge'.")

                    device.set_edge_trigger(
                        channel=channel,
                        mode=constants.TriggerMode[args.trigger_mode],
                        coupling=constants.TriggerCoupling[args.trigger_coupling],
                        edge=constants.TriggerEdge[args.trigger_slope],
                        level=args.trigger_level,
                        is_alt=args.trigger_alt
                    )

                elif trigger_type == 'video':
                    # Validate video trigger arguments
                    if any([args.trigger_mode, args.trigger_coupling, args.trigger_slope, args.trigger_level is not None, args.trigger_alt]):
                        parser.error("Edge trigger arguments cannot be used with --trigger-type 'video'.")

                    device.set_video_trigger(
                        channel=channel,
                        modulation=constants.VideoModulation[args.video_modulation],
                        sync=constants.VideoSync[args.video_sync],
                        line=args.video_line or 1
                    )
                # Return after setting trigger, assuming it's a primary action
                return

            if args.autoset:
                device.autoset()
                return

            if args.self_calibrate:
                device.self_calibrate()
                return

            if args.factory:
                device.factory_reset()
                return

            if args.trigger:
                if args.trigger == "force":
                    device.force_trigger()
                    return
                elif args.trigger == "50":
                    device.set_50pct_trigger()
                elif args.trigger == "0":
                    device.set_0_trigger()

            if args.depth:
                if args.depth not in [c.name for c in constants.MemoryDepth]:
                    parser.error(f"Invalid depth value. Choices are {', '.join([c.name for c in constants.MemoryDepth])}")
                device.set_memory_depth(constants.MemoryDepth[args.depth])

            if args.coupling:
                channel, value = args.coupling
                if int(channel) not in [1, 2]:
                    parser.error("Channel for --coupling must be 1 or 2.")
                if value not in [c.name for c in constants.Coupling]:
                    parser.error(f"Invalid coupling value. Choices are {', '.join([c.name for c in constants.Coupling])}")
                device.set_coupling(constants.Channel[f"CH{channel}"], constants.Coupling[value])

            if args.probe:
                channel, value = args.probe
                if int(channel) not in [1, 2]:
                    parser.error("Channel for --probe must be 1 or 2.")
                if value not in [p.name for p in constants.ProbeScale]:
                    parser.error(f"Invalid probe scale value. Choices are {', '.join([p.name for p in constants.ProbeScale])}")
                device.set_probe_scale(constants.Channel[f"CH{channel}"], constants.ProbeScale[value])

            if args.volt_scale:
                channel, value = args.volt_scale
                if int(channel) not in [1, 2]:
                    parser.error("Channel for --volt-scale must be 1 or 2.")
                if value not in [v.name for v in constants.VoltScale]:
                    parser.error(f"Invalid volt scale value. Choices are {', '.join([v.name for v in constants.VoltScale])}")
                device.set_volt_scale(constants.Channel[f"CH{channel}"], constants.VoltScale[value])

            if args.timebase:
                device.set_time_base(constants.TimeBase[args.timebase])

            if args.trace_v_pos:
                channel, value = args.trace_v_pos
                if int(channel) not in [1, 2]:
                    parser.error("Channel for --trace-v-pos must be 1 or 2.")
                if not -250 <= int(value) <= 250:
                    parser.error("Value for --trace-v-pos must be between -250 and 250.")
                device.set_trace_position(constants.Channel[f"CH{channel}"], int(value))

            if args.trigger_h_pos is not None:
                if not -10000 <= args.trigger_h_pos <= 10000:
                    parser.error("Value for --trigger-h-pos must be between -10000 and 10000.")
                device.set_horizontal_trigger_position(args.trigger_h_pos)

            if args.acq_mode:
                mode = constants.AcquisitionMode[args.acq_mode]
                if mode == constants.AcquisitionMode.AVERAGE:
                    device.set_average_acquisition_mode(constants.AverageSamples[args.acq_samples])
                else:
                    if args.acq_samples:
                        parser.error("Argument --acq-samples can only be used with --acq-mode AVERAGE.")
                    device.set_acquisition_mode(mode)

    except (ConnectionError, ValueError, usb.core.USBError) as e:
        logging.error(f"{e}")
        # Exit with a non-zero status code to indicate failure
        exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()
