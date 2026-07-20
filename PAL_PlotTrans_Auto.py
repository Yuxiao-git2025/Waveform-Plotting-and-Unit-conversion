"""
Read the waveform and station files separately, and plot the original and converted waveforms
(Select them in sequence through the windows one by one)
XA.,Yu   2026/07
"""
from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt
from obspy import read, read_inventory
from tkinter import Tk, filedialog, messagebox
# ============================================================
# User-configurable parameters
# ============================================================
# Response-removal pre-filter corners in Hz:
# (f1, f2, f3, f4)
PRE_FILT = (0.5, 0.8, 20.0, 25.0)

# Stabilization parameter for response deconvolution
WATER_LEVEL = 60

# Output physical quantity:
# "VEL"  -> velocity, m/s
# "DISP" -> displacement, m
# "ACC"  -> acceleration, m/s^2
OUTPUT_UNIT = "DISP"

# ============================================================
# Helper functions
# ============================================================

def choose_file(root, title, filetypes):
    """
    Open a file-selection dialog and return the selected file path.
    Return None if the user cancels the selection.
    """
    filename = filedialog.askopenfilename(
        parent=root,
        title=title,
        filetypes=filetypes,
    )

    if not filename:
        return None

    return Path(filename)

def print_trace_information(st, label):
    """Print summary and detailed stats for every trace."""
    print("\n" + "=" * 60)
    print(label)
    print("=" * 60)
    print(st)

    for index, tr in enumerate(st):
        data = np.asarray(tr.data)

        print("\n" + "-" * 60)
        print(f"Trace index:       {index}")
        print(f"Trace ID:          {tr.id}")
        print(f"Start time:        {tr.stats.starttime}")
        print(f"End time:          {tr.stats.endtime}")
        print(f"Sampling rate:     {tr.stats.sampling_rate} Hz")
        print(f"Number of points:  {tr.stats.npts}")
        print(f"Data type:         {data.dtype}")
        print(f"Minimum value:     {np.min(data):.6e}")
        print(f"Maximum value:     {np.max(data):.6e}")
        print(f"Peak amplitude:    {np.max(np.abs(data)):.6e}")

        print("\nFull stats:")
        print(tr.stats)

def check_response_match(st, inv):
    """
    Verify that every trace has a matching response in StationXML.
    Raise a readable error if no match is found.
    """
    print("\n" + "=" * 60)
    print("Checking StationXML response matching")
    print("=" * 60)

    for tr in st:
        try:
            response = inv.get_response(tr.id, tr.stats.starttime)

            sensitivity = response.instrument_sensitivity

            print(f"\nResponse found for: {tr.id}")

            if sensitivity is not None:
                print(f"Overall sensitivity: {sensitivity.value:.6e}")
                print(f"Input unit:          {sensitivity.input_units}")
                print(f"Output unit:         {sensitivity.output_units}")
            else:
                print("Warning: overall instrument sensitivity is unavailable.")

        except Exception as exc:
            raise RuntimeError(
                "\nNo matching instrument response was found.\n"
                f"Waveform trace ID: {tr.id}\n"
                f"Waveform time:     {tr.stats.starttime}\n\n"
                "Please check whether the following fields match between "
                "the MiniSEED waveform and StationXML file:\n"
                "  - network code\n"
                "  - station code\n"
                "  - location code\n"
                "  - channel code\n"
                "  - channel operational time range\n"
            ) from exc

def validate_pre_filt(st, pre_filt):
    """
    Ensure that the highest pre-filter frequency is below the Nyquist
    frequency for every trace.
    """
    f1, f2, f3, f4 = pre_filt

    if not (0 < f1 < f2 < f3 < f4):
        raise ValueError(
            "PRE_FILT must satisfy: 0 < f1 < f2 < f3 < f4."
        )

    for tr in st:
        nyquist = tr.stats.sampling_rate / 2.0

        if f4 >= nyquist:
            raise ValueError(
                f"\nInvalid PRE_FILT for trace {tr.id}.\n"
                f"Sampling rate: {tr.stats.sampling_rate:.3f} Hz\n"
                f"Nyquist frequency: {nyquist:.3f} Hz\n"
                f"Current highest pre-filter corner: {f4:.3f} Hz\n\n"
                "The fourth pre-filter frequency must be smaller than "
                "the Nyquist frequency. Reduce PRE_FILT accordingly."
            )

def plot_waveforms(st_raw, st_corrected, output_unit):
    """Plot raw counts and response-corrected waveform together."""
    ntr = len(st_raw)

    fig, axes = plt.subplots(
        ntr,
        2,
        figsize=(14, max(4, 3.2 * ntr)),
        squeeze=False,
        sharex=False,
    )

    fig.suptitle(
        f"Raw Waveform and Response-Corrected Waveform ({output_unit})",
        fontsize=14,
        fontweight="bold",
    )

    unit_label = {
        "VEL": "Velocity (m/s)",
        "DISP": "Displacement (m)",
        "ACC": "Acceleration (m/s²)",
    }.get(output_unit, output_unit)

    for i, (tr_raw, tr_corrected) in enumerate(zip(st_raw, st_corrected)):
        time_raw = tr_raw.times()
        time_corrected = tr_corrected.times()

        axes[i, 0].plot(time_raw, tr_raw.data, color="black", linewidth=0.6)
        axes[i, 0].set_title(f"Raw: {tr_raw.id}")
        axes[i, 0].set_xlabel("Time since trace start (s)")
        axes[i, 0].set_ylabel("Amplitude (counts)")
        axes[i, 0].grid(alpha=0.3)

        axes[i, 1].plot(
            time_corrected,
            tr_corrected.data,
            color="tab:blue",
            linewidth=0.6,
        )
        axes[i, 1].set_title(f"Corrected: {tr_corrected.id}")
        axes[i, 1].set_xlabel("Time since trace start (s)")
        axes[i, 1].set_ylabel(unit_label)
        axes[i, 1].grid(alpha=0.3)

    plt.tight_layout()
    plt.show()

# ============================================================
# Main workflow
# ============================================================

def main():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    waveform_file = choose_file(
        root=root,
        title="Select one waveform file",
        filetypes=[
            ("Waveform files", "*.mseed *.miniseed *.msd *.sac"),
            ("MiniSEED files", "*.mseed *.miniseed *.msd"),
            ("SAC files", "*.sac"),
            ("All files", "*.*"),
        ],
    )

    if waveform_file is None:
        print("No waveform file was selected. Program terminated.")
        root.destroy()
        return

    xml_file = choose_file(
        root=root,
        title="Select the corresponding StationXML response file",
        filetypes=[
            ("StationXML files", "*.xml *.stationxml"),
            ("XML files", "*.xml"),
            ("All files", "*.*"),
        ],
    )

    if xml_file is None:
        print("No StationXML file was selected. Program terminated.")
        root.destroy()
        return

    try:
        # ----------------------------------------------------
        # Read waveform and StationXML
        # ----------------------------------------------------
        print(f"\nSelected waveform file:\n{waveform_file.resolve()}")
        print(f"\nSelected StationXML file:\n{xml_file.resolve()}")

        st_raw = read(str(waveform_file))
        inv = read_inventory(str(xml_file))

        print_trace_information(
            st_raw,
            label="RAW WAVEFORM INFORMATION (usually digital counts)",
        )

        # ----------------------------------------------------
        # Validate matching response and pre-filter
        # ----------------------------------------------------
        check_response_match(st_raw, inv)
        validate_pre_filt(st_raw, PRE_FILT)

        # ----------------------------------------------------
        # Copy waveform before modifying data
        # ----------------------------------------------------
        st_corrected = st_raw.copy()

        # Preprocessing before response removal
        st_corrected.detrend("demean")
        st_corrected.detrend("linear")
        st_corrected.taper(
            max_percentage=0.05,
            max_length=5.0,
        )

        # ----------------------------------------------------
        # Remove instrument response
        # ----------------------------------------------------
        print("\n" + "=" * 60)
        print(f"Removing instrument response; output = {OUTPUT_UNIT}")
        print("=" * 60)

        st_corrected.remove_response(
            inventory=inv,
            output=OUTPUT_UNIT,
            pre_filt=PRE_FILT,
            water_level=WATER_LEVEL,
            zero_mean=False,
            taper=False,
        )

        print_trace_information(
            st_corrected,
            label=f"RESPONSE-CORRECTED WAVEFORM INFORMATION ({OUTPUT_UNIT})",
        )

        # ----------------------------------------------------
        # Plot raw and corrected waveforms
        # ----------------------------------------------------
        plot_waveforms(st_raw, st_corrected, OUTPUT_UNIT)

        # ----------------------------------------------------
        # Optional save corrected waveform
        # ----------------------------------------------------
        save_file = messagebox.askyesno(
            title="Save corrected waveform?",
            message=(
                "Do you want to save the response-corrected waveform "
                "as a new MiniSEED file?"
            ),
            parent=root,
        )

        if save_file:
            default_name = (
                f"{waveform_file.stem}_response_removed_{OUTPUT_UNIT}.mseed"
            )

            output_file = filedialog.asksaveasfilename(
                parent=root,
                title="Save response-corrected MiniSEED",
                initialdir=str(waveform_file.parent),
                initialfile=default_name,
                defaultextension=".mseed",
                filetypes=[
                    ("MiniSEED files", "*.mseed"),
                    ("All files", "*.*"),
                ],
            )

            if output_file:
                st_corrected.write(
                    output_file,
                    format="MSEED",
                    encoding="FLOAT64",
                )
                print(f"\nCorrected waveform saved to:\n{output_file}")
            else:
                print("\nSave operation cancelled.")

        else:
            print("\nCorrected waveform was not saved.")

    except Exception as exc:
        error_message = f"Processing failed:\n\n{exc}"
        print("\n" + error_message)
        messagebox.showerror(
            title="Processing Error",
            message=error_message,
            parent=root,
        )

    finally:
        root.destroy()

if __name__ == "__main__":
    main()
