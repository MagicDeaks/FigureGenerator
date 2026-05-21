import argparse
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd


def parse_input():
    try:
        parser = argparse.ArgumentParser(
            description="Automated pipeline to process Excel data into publication-ready figures."
        )

        parser.add_argument(
            '-i', '--input',
            required=True,
            type=str,
            help='Path to input Excel file.'
        )

        parser.add_argument(
            '-o', '--output-dir',
            type=str,
            default='./figures',
            help='Path to output directory.'
        )

        parser.add_argument(
            '-x', '--x-padding',
            type=float,
            default=1.05,
            help='Padding for x-axes.'
        )

        parser.add_argument(
            '-y', '--y-padding',
            type=float,
            default=1.1,
            help='Padding for y-axes.'
        )

        parser.add_argument(
            '-t', '--inset-temp',
            type=float,
            default=14.7,
            help='Maximum temperature of the inset.'
        )

        args = parser.parse_args()

        print(f"Loading data from: {args.input}")
        print(f"Output directory: {args.output_dir}")

        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)

        return args
    except Exception as e:
        print(e)
        exit(1)


def read_excel_file(path):
    with pd.ExcelFile(path, engine='openpyxl') as xls:
        sheet_names = xls.sheet_names
        print(f"Detected sheets: {sheet_names}")

        all_data = {}

        for sheet in sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet)
            all_data[sheet] = df

        return all_data


def generate_heat_capacity_figure(all_data, args):
    output_dir = args.output_dir
    x_pad = args.x_padding
    y_pad = args.y_padding
    inset_xmax = args.inset_temp

    # Import style information
    plt.style.use('./style.mplstyle')

    # Generate Plot (fig, ax) and Inset (ax_inset)
    fig, ax = plt.subplots(
        figsize=(5, 3.5)
    )

    inset_bounds = (0.50, 0.10, 0.45, 0.40)
    ax_inset = ax.inset_axes(inset_bounds)

    inset_xmin, inset_ymin = 0, 0

    # Plot Data & Determine Maximum
    max_temperature = 0
    max_heat_capacity = 0
    inset_max_heat_capacity = 0
    i = 0
    marker = 's'
    color = 'blue'
    for label, df in all_data.items():
        # Use a Different Shape & Colour for each Dataset
        match i:
            case 1:
                marker = 'o'
                color = 'red'
            case 2:
                marker = '^'
                color = 'green'
            case 3:
                marker = 'D'
                color = 'yellow'
            case 4:
                marker = 'v'
                color = 'purple'
            case 5:
                marker = '*'
                color = 'orange'
        # Plot the Heat Capacity
        add_heat_capacity_plot(ax, ax_inset, label, df['Measured Temperature'], df['Measured Heat Capacity'],
                               df['Smoothed Temperature'], df['Smoothed Heat Capacity'], marker=marker, color=color)
        # Determine Maxima
        if df['Measured Temperature'].max() > max_temperature:
            max_temperature = df['Measured Temperature'].max()
        if df['Measured Heat Capacity'].max() > max_heat_capacity:
            max_heat_capacity = df['Measured Heat Capacity'].max()
        if df['Measured Heat Capacity'][
            :index_of_max(df['Measured Temperature'], inset_xmax)].max() > inset_max_heat_capacity:
            inset_max_heat_capacity = df['Measured Heat Capacity'][
                :index_of_max(df['Measured Temperature'], inset_xmax)].max()
        i += 1

    # Set Plot Limits
    ax.set_xlim(0, max_temperature * x_pad)
    ax.set_ylim(
        bottom=0,
        top=max_heat_capacity * y_pad
    )

    # Set Inset Limits
    inset_ymax = inset_max_heat_capacity * y_pad
    ax_inset.set_xlim(inset_xmin, inset_xmax)
    ax_inset.set_ylim(
        bottom=inset_ymin,
        top=inset_ymax
    )

    # Set Number of Major Ticks
    ax.xaxis.set_major_locator(ticker.MaxNLocator(7))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(7))

    # Remove Ticks Overlapping with Spines
    remove_overlapping_ticks(ax, 0, max_temperature * x_pad, 0, max_heat_capacity * y_pad)

    # Generate Legend & Axis Labels
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(0.05, 0.95),
        frameon=False,
        fontsize=8
    )

    ax.set_xlabel(r'$T\mathrm{/K}$')
    ax.set_ylabel(r'$C_{p,\mathrm{m}}\mathrm{\,(J\cdot K^{-1}\!\!\cdot mol^{-1})}$')

    # Refactor Inset Spines & Ticks
    ax_inset.yaxis.tick_right()
    ax_inset.yaxis.set_label_position('right')

    ax_inset.spines['top'].set_visible(False)
    ax_inset.spines['left'].set_visible(False)

    ax_inset.tick_params(
        axis='both',
        which='both',
        direction='in',
        top=False,
        left=False,
        right=True,
        bottom=True,
        labelsize=8
    )

    # Set Number of Inset Major Ticks
    ax_inset.xaxis.set_major_locator(ticker.MaxNLocator(int(inset_xmax / 2 + 1)))
    ax_inset.yaxis.set_major_locator(ticker.MaxNLocator(5))

    # Remove Inset Ticks Overlapping with Spines
    remove_overlapping_ticks(ax_inset, inset_xmin, inset_xmax, inset_ymin, inset_ymax,
                             keep_x_zero=True,
                             keep_y_max=True
                             )

    # Save the Figure and Close
    plt.savefig(
        f'{output_dir}/heat_capacity.jpg',
        pil_kwargs={'quality': 100, 'subsampling': 0}
    )

    plt.close(fig)


def add_heat_capacity_plot(ax, ax_inset, label, measured_temperature, measured_heat_capacity, smoothed_temperature,
                           smoothed_heat_capacity, marker='s', color='blue'):
    ax.plot(measured_temperature, measured_heat_capacity,
            zorder=5,
            clip_on=False,
            label=fr"$\mathrm{{{label}}}$",
            marker=marker,
            color=color
            )
    ax.plot(smoothed_temperature, smoothed_heat_capacity,
            linestyle='-',
            linewidth=0.7,
            color='black',
            marker='None',
            zorder=2
            )
    ax_inset.plot(measured_temperature, measured_heat_capacity,
                  zorder=5,
                  clip_on=True,
                  marker=marker,
                  color=color
                  )
    ax_inset.plot(smoothed_temperature, smoothed_heat_capacity,
                  linestyle='-',
                  linewidth=0.7,
                  color='black',
                  marker='None',
                  zorder=2
                  )


def remove_overlapping_ticks(ax, xmin, xmax, ymin, ymax, keep_x_zero=False, keep_y_max=False):
    x_locs = ax.get_xticks()
    x_ticks = ax.xaxis.get_major_ticks()

    if len(x_locs) == len(x_ticks):
        for loc, tick in zip(x_locs, x_ticks):
            if np.isclose(loc, xmin):
                if not keep_x_zero:
                    tick.tick1line.set_visible(False)
                    tick.tick2line.set_visible(False)
            elif np.isclose(loc, xmax):
                tick.tick1line.set_visible(False)
                tick.tick2line.set_visible(False)

    y_locs = ax.get_yticks()
    y_ticks = ax.yaxis.get_major_ticks()

    if len(y_locs) == len(y_ticks):
        for loc, tick in zip(y_locs, y_ticks):
            if np.isclose(loc, ymax):
                if not keep_y_max:
                    tick.tick1line.set_visible(False)
                    tick.tick2line.set_visible(False)
            elif np.isclose(loc, ymin):
                tick.tick1line.set_visible(False)
                tick.tick2line.set_visible(False)


def index_of_max(arr, target):
    max_val = float('-inf')
    max_idx = -1

    for idx, val in enumerate(arr):
        if target > val > max_val:
            max_val = val
            max_idx = idx

    return max_idx


def main():
    args = parse_input()

    try:
        all_data = read_excel_file(args.input)

        generate_heat_capacity_figure(all_data, args)

        print(f"Figure saved to: {args.output_dir}/heat_capacity.jpg")

    except Exception as e:
        print(e)
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
