import argparse
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd

marker = ['s', 'o', '^', 'D', 'v', '*']
color = ['blue', 'red', 'green', 'yellow', 'purple', 'orange']


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

        parser.add_argument(
            '-d', '--dev-split',
            type=bool,
            default=True,
            help='Whether to generate separate figures for deviations.'
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
    inset_x_max = args.inset_temp

    # Import style information
    plt.style.use('./style.mplstyle')

    # Generate Plot (fig, ax) and Inset (ax_inset)
    fig, ax = plt.subplots(
        figsize=(5, 3.5)
    )

    inset_bounds = (0.50, 0.10, 0.45, 0.40)
    ax_inset = ax.inset_axes(inset_bounds)

    inset_x_min, inset_y_min = 0, 0

    # Plot Data & Determine Maximum
    max_temperature = 0
    max_heat_capacity = 0
    inset_max_heat_capacity = 0
    i = 0
    for label, df in all_data.items():
        # Plot the Heat Capacity
        add_heat_capacity_plot(ax, ax_inset, label, df['Measured Temperature'], df['Measured Heat Capacity'],
                               df['Smoothed Temperature'], df['Smoothed Heat Capacity'], m=marker[i], c=color[i])
        # Determine Maxima
        if df['Measured Temperature'].max() > max_temperature:
            max_temperature = df['Measured Temperature'].max()
        if df['Measured Heat Capacity'].max() > max_heat_capacity:
            max_heat_capacity = df['Measured Heat Capacity'].max()
        if df['Measured Heat Capacity'][
            :index_of_max(df['Measured Temperature'], inset_x_max)].max() > inset_max_heat_capacity:
            inset_max_heat_capacity = df['Measured Heat Capacity'][
                :index_of_max(df['Measured Temperature'], inset_x_max)].max()
        i += 1

    # Format the Figure
    inset_y_max = inset_max_heat_capacity * y_pad
    format_figure(ax, ax_inset, 0, max_temperature * x_pad, 0, max_heat_capacity * y_pad, inset_x_min, inset_x_max,
                  inset_y_min, inset_y_max, r"$T\mathrm{/K}$",
                  r"$C_{p,\mathrm{m}}\mathrm{\,(J\cdot K^{-1}\!\!\cdot mol^{-1})}$")

    # Save the Figure and Close
    plt.savefig(
        f'{output_dir}/heat_capacity.jpg',
        pil_kwargs={'quality': 100, 'subsampling': 0}
    )
    print(f"Figure saved to: {args.output_dir}/heat_capacity.jpg")

    plt.close(fig)


def add_heat_capacity_plot(ax, ax_inset, label, measured_temperature, measured_heat_capacity, smoothed_temperature,
                           smoothed_heat_capacity, m='s', c='blue'):
    ax.plot(measured_temperature, measured_heat_capacity,
            zorder=5,
            clip_on=False,
            label=fr"$\mathrm{{{label}}}$",
            marker=m,
            color=c
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
                  marker=m,
                  color=c
                  )
    ax_inset.plot(smoothed_temperature, smoothed_heat_capacity,
                  linestyle='-',
                  linewidth=0.7,
                  color='black',
                  marker='None',
                  zorder=2
                  )


def generate_deviations_figures(all_data, args):
    output_dir = args.output_dir
    x_pad = args.x_padding
    y_pad = args.y_padding
    inset_x_max = args.inset_temp
    dev_split = args.dev_split

    # Import Style Information
    plt.style.use('./style.mplstyle')

    if dev_split:
        i = 0
        for label, df in all_data.items():
            fig, ax = plt.subplots(
                figsize=(5, 3.5)
            )

            inset_bounds = (0.50, 0.10, 0.40, 0.40)
            ax_inset = ax.inset_axes(inset_bounds)

            inset_x_min, inset_min_deviation = 0, 0
            max_temperature = df['Measured Temperature'].max() * x_pad
            min_deviation = df['Fit Deviations'].min() * y_pad
            max_deviation = df['Fit Deviations'].max() * y_pad
            inset_max_deviation = df['Fit Deviations'][
                                      :index_of_max(df['Measured Temperature'], inset_x_max)].max() * y_pad
            inset_min_deviation = df['Fit Deviations'][
                                      :index_of_max(df['Measured Temperature'], inset_x_max)].min() * y_pad

            y_lower_bound = -((max_deviation - df['Fit Deviations'][
                index_of_min(df['Measured Temperature'],
                             max_temperature * 0.5):].min()) / 0.4 - max_deviation)

            if min_deviation > y_lower_bound:
                min_deviation = y_lower_bound

            add_deviations_plot(ax, ax_inset, label, df['Measured Temperature'], df['Fit Deviations'], m=marker[i],
                                c=color[i])

            format_figure(ax, ax_inset, 0, max_temperature, min_deviation, max_deviation, inset_x_min,
                          inset_x_max, inset_min_deviation, inset_max_deviation, r"$T\mathrm{/K}$",
                          r"$C_{p,\mathrm{m}}\mathrm{\,(J\cdot K^{-1}\!\!\cdot mol^{-1})}$")

            add_center_line(ax, ax_inset, 0, max_temperature * x_pad, 0, inset_x_max)

            ax.legend(
                loc='upper right',
                bbox_to_anchor=(0.95, 0.95),
                frameon=False,
                fontsize=8
            )

            plt.savefig(
                f'{output_dir}/deviations_{i}.jpg',
                pil_kwargs={'quality': 100, 'subsampling': 0}
            )
            print(f"Figure saved to: {output_dir}/deviations_{i}.jpg")

            plt.close(fig)

            i += 1


    else:
        # Generate Plot (fig, ax) and Inset (ax_inset)
        fig, ax = plt.subplots(
            figsize=(5, 3.5)
        )

        inset_bounds = (0.50, 0.10, 0.40, 0.40)
        ax_inset = ax.inset_axes(inset_bounds)

        inset_x_min, inset_min_deviation = 0, 0

        # Plot Data & Determine Minima & Maximum
        max_temperature = 0
        min_deviation = 0
        max_deviation = 0
        inset_max_deviation = 0
        y_min = 0
        i = 0
        for label, df in all_data.items():
            # Plot the Heat Capacity
            add_deviations_plot(ax, ax_inset, label, df['Measured Temperature'], df['Fit Deviations'], m=marker[i],
                                c=color[i])
            # Determine Maxima
            if df['Measured Temperature'].max() > max_temperature:
                max_temperature = df['Measured Temperature'].max()
            if df['Fit Deviations'].max() > max_deviation:
                max_deviation = df['Fit Deviations'].max()
            if df['Fit Deviations'][
                :index_of_max(df['Measured Temperature'], inset_x_max)].max() > inset_max_deviation:
                inset_max_deviation = df['Fit Deviations'][
                    :index_of_max(df['Measured Temperature'], inset_x_max)].max()

            # Determine Minima
            if df['Fit Deviations'].min() < min_deviation:
                min_deviation = df['Fit Deviations'].min()
            if df['Fit Deviations'][
                :index_of_max(df['Measured Temperature'], inset_x_max)].min() * y_pad < inset_min_deviation:
                inset_min_deviation = df['Fit Deviations'][
                                          :index_of_max(df['Measured Temperature'], inset_x_max)].min() * y_pad

            if (-((max_deviation * y_pad - df['Fit Deviations'][
                index_of_min(df['Measured Temperature'],
                             max_temperature * 0.5):].min()) / 0.4 - max_deviation * y_pad)) < y_min:
                y_min = -((max_deviation * y_pad - df['Fit Deviations'][
                    index_of_min(df['Measured Temperature'],
                                 max_temperature * 0.5):].min()) / 0.4 - max_deviation * y_pad)

            # Iterate through Data, Markers, and Colours
            i += 1

        # Format the Figure
        if y_min > min_deviation:
            y_min = min_deviation * y_pad

        inset_y_max = inset_max_deviation * y_pad
        format_figure(ax, ax_inset, 0, max_temperature * x_pad, y_min, max_deviation * y_pad, inset_x_min,
                      inset_x_max, inset_min_deviation, inset_y_max, r"$T\mathrm{/K}$",
                      r"$C_{p,\mathrm{m}}\mathrm{\,(J\cdot K^{-1}\!\!\cdot mol^{-1})}$")

        add_center_line(ax, ax_inset, 0, max_temperature * x_pad, 0, inset_x_max)

        # Reframe Legend
        ax.legend(
            loc='upper right',
            bbox_to_anchor=(0.95, 0.95),
            frameon=False,
            fontsize=8
        )

        # Save the Figure and Close
        plt.savefig(
            f'{output_dir}/deviations.jpg',
            pil_kwargs={'quality': 100, 'subsampling': 0}
        )
        print(f"Figure saved to: {output_dir}/deviations.jpg")

        plt.close(fig)


def add_deviations_plot(ax, ax_inset, label, measured_temperature, fit_deviations, m='s', c='blue'):
    ax.plot(measured_temperature, fit_deviations,
            zorder=5,
            clip_on=False,
            label=fr"$\mathrm{{{label}}}$",
            marker=m,
            color=c
            )
    ax_inset.plot(measured_temperature, fit_deviations,
                  zorder=5,
                  clip_on=True,
                  marker=m,
                  color=c
                  )


def add_center_line(ax, ax_inset, x_min, x_max, inset_x_min, inset_x_max):
    ax.plot([x_min, x_max], [0, 0],
            linestyle='-',
            linewidth=0.7,
            color='black',
            marker='None',
            zorder=2
            )
    ax_inset.plot([inset_x_min, inset_x_max], [0, 0],
                  linestyle='-',
                  linewidth=0.7,
                  color='black',
                  marker='None',
                  zorder=2
                  )


def format_figure(ax, ax_inset, x_min, x_max, y_min, y_max, inset_x_min, inset_x_max, inset_y_min, inset_y_max, x_label,
                  y_label):
    # Set Plot Limits
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(
        bottom=y_min,
        top=y_max
    )

    # Set Inset Limits
    ax_inset.set_xlim(inset_x_min, inset_x_max)
    ax_inset.set_ylim(
        bottom=inset_y_min,
        top=inset_y_max
    )

    # Set Number of Major Ticks
    ax.xaxis.set_major_locator(ticker.MaxNLocator(7))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(7))

    # Remove Ticks Overlapping with Spines
    remove_overlapping_ticks(ax, x_min, x_max, y_min, y_max)

    # Generate Legend & Axis Labels
    ax.legend(
        loc='upper left',
        bbox_to_anchor=(0.05, 0.95),
        frameon=False,
        fontsize=8
    )

    ax.set_xlabel(rf'{x_label}')
    ax.set_ylabel(rf'{y_label}')

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
    ax_inset.xaxis.set_major_locator(ticker.MaxNLocator(int(inset_x_max / 2 + 1)))
    ax_inset.yaxis.set_major_locator(ticker.MaxNLocator(5))

    # Remove Inset Ticks Overlapping with Spines
    remove_overlapping_ticks(ax_inset, inset_x_min, inset_x_max, inset_y_min, inset_y_max,
                             keep_x_zero=True,
                             keep_y_max=True
                             )


def remove_overlapping_ticks(ax, x_min, x_max, y_min, y_max, keep_x_zero=False, keep_y_max=False):
    x_locs = ax.get_xticks()
    x_ticks = ax.xaxis.get_major_ticks()

    if len(x_locs) == len(x_ticks):
        for loc, tick in zip(x_locs, x_ticks):
            if np.isclose(loc, x_min):
                if not keep_x_zero:
                    tick.tick1line.set_visible(False)
                    tick.tick2line.set_visible(False)
            elif np.isclose(loc, x_max):
                tick.tick1line.set_visible(False)
                tick.tick2line.set_visible(False)

    y_locs = ax.get_yticks()
    y_ticks = ax.yaxis.get_major_ticks()

    if len(y_locs) == len(y_ticks):
        for loc, tick in zip(y_locs, y_ticks):
            if np.isclose(loc, y_max):
                if not keep_y_max:
                    tick.tick1line.set_visible(False)
                    tick.tick2line.set_visible(False)
            elif np.isclose(loc, y_min):
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


def index_of_min(arr, target):
    min_val = float('inf')
    min_idx = -1

    for idx, val in enumerate(arr):
        if target < val < min_val:
            min_val = val
            min_idx = idx

    return min_idx


def main():
    args = parse_input()

    try:
        all_data = read_excel_file(args.input)

        generate_heat_capacity_figure(all_data, args)

        generate_deviations_figures(all_data, args)

    except Exception as e:
        print(e)
        exit(1)

    exit(0)


if __name__ == '__main__':
    main()
