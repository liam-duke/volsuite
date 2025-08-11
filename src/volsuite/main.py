from datetime import datetime
from pathlib import Path
from rich.console import Console
import cmd
import json
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

from volsuite.utils.config import DEFAULT_CONFIG, init_config
from volsuite.utils.decorators import (
    catch_network_error,
    requires_ticker,
    requires_min_args,
)
from volsuite.utils.dicts import VALID_PERIODS, VALID_INTERVALS
from volsuite.utils.functions import (
    get_base_path,
    parse_line,
    is_date,
    console_error,
    type_eval,
)
from volsuite.utils.volatility import hv, iv_skew, iv_surface, plot_iv_surface


BASE_PATH = get_base_path()
CONFIG_PATH = BASE_PATH / "config.json"

version = "0.10"
console = Console()
config = init_config(CONFIG_PATH)

# Verify existence of default ticker if specified on startup
if config["default_ticker"]:
    if yf.Ticker(config["default_ticker"]).history(period="1d").empty:
        console.print(
            f"[red]Error: Unable to fetch data for symbol '{config["default_ticker"]}' from yfinance API. Check your connection and/or that the symbol exists."
        )

# Load pandas configuration settings
pd.set_option(
    "display.max_rows",
    None if int(config["display_max_rows"]) == 0 else int(config["display_max_rows"]),
)
pd.set_option(
    "display.max_colwidth",
    (
        None
        if int(config["display_max_colwidth"]) == 0
        else int(config["display_max_colwidth"])
    ),
)


class MainCLI(cmd.Cmd):
    """
    Main CLI class which stores all session data and available commands.
    """

    intro = f"Welcome to VolSuite v{version}. Enter 'ticker <symbol>' or 'help' to get started."

    def __init__(self):
        super().__init__()
        self._ticker = (
            None
            if not config["default_ticker"]
            else yf.Ticker(config["default_ticker"])
        )
        self._last_output = None

    def console_output(self, df: pd.DataFrame):
        """
        Custom print to console function for dataframes which caches output for export later on.

        Args:
            df: Dataframe object to be printed.
        """

        # Remove whitespace and capitalization from column titles of dataframes for easier access when plotting
        if isinstance(df, pd.DataFrame):
            df = df.rename(columns=lambda x: x.replace(" ", "").lower())

        # Cache dataframe
        self._last_output = df

        # Print dataframe
        print()
        console.print(df)
        print()

    @property
    def prompt(self):  # type: ignore
        """
        Custom prompt message to indicate current date, time and ticker if specified.
        """
        return (
            f"[{datetime.now().strftime('%H:%M:%S')}] {self._ticker.ticker} > "
            if self._ticker
            else f"[{datetime.now().strftime('%H:%M:%S')}] > "
        )

    def default(self, line):
        """
        Custom unknown command message.
        """
        console.print(
            f"[red]Error: '{line}' is not a recognized command. Type 'help' for a list of available commands."
        )

    def do_config(self, line):
        """
        View, edit or reset the configuration file to default.
        Usage:
        config (<setting>) (<value>)
        config reset
        """
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return
        global config

        if not args:
            console.print(config)
            return

        setting = args[0]

        if setting in config:
            if len(args) > 1:
                value = type_eval(args[1])
                config[setting] = value
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f, indent=2)
                config = init_config(CONFIG_PATH)

                pd.set_option(
                    "display.max_rows",
                    (
                        None
                        if int(config["display_max_rows"]) == 0
                        else int(config["display_max_rows"])
                    ),
                )
                pd.set_option(
                    "display.max_colwidth",
                    (
                        None
                        if int(config["display_max_colwidth"]) == 0
                        else int(config["display_max_colwidth"])
                    ),
                )

                console.print(f"'{setting}' is now set to: '{value}'")

            else:
                console.print(f"'{setting}' is currently set to: '{config[setting]}'")

        elif setting == "reset":
            with open(CONFIG_PATH, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
            config = init_config(CONFIG_PATH)

            pd.set_option(
                "display.max_rows",
                (
                    None
                    if int(config["display_max_rows"]) == 0
                    else int(config["display_max_rows"])
                ),
            )
            pd.set_option(
                "display.max_colwidth",
                (
                    None
                    if int(config["display_max_colwidth"]) == 0
                    else int(config["display_max_colwidth"])
                ),
            )

            console.print(f"Configuration file has been reset to default settings.")

        else:
            console.print(
                f"[red]Error: {args[0]} is not recognized as a configurable variable."
            )

    def do_quit(self, line):
        """
        Quit CLI.
        Usage:
        quit
        """
        exit(0)

    def do_last(self, line):
        """
        Print last cached DataFrame.
        Usage:
        last
        """
        console.print(self._last_output)
        print()

    def do_export(self, filename):
        """
        Save the last printed DataFrame to a CSV file inside the export folder. Builds a default filename if none provided.
        Usage: export (<filename>)
        """
        # Load dataframe from cache
        df = self._last_output

        if df is None:
            console.print("[red]Error: No cached data to export.")
            return

        # Build default filename if none provided
        if not filename:
            filename = (
                f"{df.attrs['ticker']}_{df.attrs['datatype']}_{df.attrs['period']}"
            )

        # Build filename with extension and get export path
        filename = Path(filename).with_suffix(".csv")
        export_path = BASE_PATH / str(config["export_folder"])

        # Build the base path for the file
        filepath = export_path / filename

        # Create the export directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Save dataframe to CSV
        try:
            df.to_csv(filepath, index=False)
            console.print(f"[green]DataFrame successfully saved to '{filepath}'.")
        except Exception as e:
            console_error(e)

    def do_import(self, filepath):
        """
        Load external csv to last output cache.
        Usage:
        import <filepath>
        """
        try:
            df = pd.read_csv(filepath)
            self._last_output = df
            console.print(
                f"[green]Successfully loaded '{filepath}' into cache as last output."
            )

        except OSError:
            console.print(f"[red]Error: No such file or directory '{filepath}'.")

    @catch_network_error
    def do_ticker(self, line):
        """
        Set ticker for current section or view if none provided.
        Usage:
        ticker (<symbol>)
        """
        # No ticker specified, default print current ticker
        if line == "":
            console.print(
                f"Current ticker is set to: [purple]${self._ticker.ticker if self._ticker else None}[/purple]."
            )

        # Ticker specified, download and update if available
        else:
            line = line.upper()
            console.print(f"Downloading ticker symbol [purple]'${line}'[/purple]...")
            if yf.Ticker(line).history(period="1d", interval="1m").empty:
                console.print(
                    f"[red]Error: Unable to fetch data for symbol '{config["default_ticker"]}' from yfinance API. Check your connection and/or that the symbol exists."
                )
            else:
                console.print(
                    f"[green]Ticker symbol '[purple]${line}[/purple]' successfully loaded."
                )
            self._ticker = yf.Ticker(line)

    @requires_ticker
    @catch_network_error
    def do_news(self, line):
        """
        Print recent news for specified ticker.
        Usage:
        news
        """
        news = self._ticker.news
        print()
        for article in news:
            content = article["content"]
            title = content["title"]
            provider = content["provider"]["displayName"]
            summary = content["summary"]
            url = content["canonicalUrl"]["url"]
            console.print(f"[bold]{provider} — {title}[/bold]\n{summary}\n{url}")
            print()

    @requires_ticker
    @requires_min_args(1)
    @catch_network_error
    def do_history(self, line):
        """
        Print historical summary data given a specified time period.
        Usage:
        history <time_period> (<time_interval>)
        history <startdate> <enddate>
        """
        command = "history"
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return

        # Handle time period
        if args[0] in VALID_PERIODS:
            # Time interval also provided
            if len(args) > 1:
                if args[1] in VALID_INTERVALS:
                    df = self._ticker.history(
                        period=args[0], interval=args[1]
                    ).reset_index()
                    # Metadata for export
                    df.attrs["period"] = f"{args[0]}_{args[1]}"
                else:
                    console.print(
                        f"[red]Error: Invalid time interval '{args[1]}'. Use {VALID_INTERVALS}."
                    )
                    return
            # Time interval not provided
            else:
                df = self._ticker.history(period=args[0]).reset_index()

                # Metadata for export
                df.attrs["period"] = f"{args[0]}"

        # Handle date interval
        elif is_date(args[0]):
            # End date provided
            if len(args) > 1:
                try:
                    df = self._ticker.history(start=args[0], end=args[1]).reset_index()
                    df.attrs["period"] = f"{args[0]}_{args[1]}"
                except ValueError as e:
                    console_error(e)
                    return
            # No end date provided
            else:
                console.print(
                    f"[red]Error: Missing end date. Use date format '%Y-%m-%d'."
                )
                return
        # No valid time period or date
        else:
            console.print(
                f"[red]Error: '{args[0]}' is not recognized as a valid time period or date. Use {VALID_PERIODS} or date format '$Y-$m-$d'."
            )
            return

        # Include metadata
        df.attrs["ticker"] = self._ticker.ticker
        df.attrs["datatype"] = command

        # Print data
        self.console_output(df)

    @requires_ticker
    @catch_network_error
    def do_oc(self, line):
        """
        Print the call or put options chain for a given expiration date. Displays available expirations if none provided.
        Usage:
        oc <expiration date> calls|puts
        """
        command = "oc"
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return

        if args:
            expiration = args[0]
        else:
            expiration = ""

        # Handle expiration date
        try:
            chain = self._ticker.option_chain(expiration)

            # Handle option type
            if len(args) > 1:
                if args[1] == "calls":
                    df = chain.calls
                elif args[1] == "puts":
                    df = chain.puts
                else:
                    console.print(
                        f"[red]Error: Unknown option type '{args[1]}'. Use 'calls' or 'puts'."
                    )
                    return

            # Option type not specified
            else:
                console.print("[red]Error: Missing option type. Use 'calls' or 'puts'.")
                return

            # Include metadata
            df.attrs["ticker"] = self._ticker.ticker
            df.attrs["period"] = expiration
            df.attrs["datatype"] = f"{command}_{args[0]}"

            # Print data
            self.console_output(df)

        # Catch invalid date format and print available expirations
        except ValueError as e:
            console_error(e)
            return

    @requires_ticker
    @requires_min_args(2)
    @catch_network_error
    def do_hv(self, line):
        """
        Print historical rolling volatility model given a specified method and time period.
        Usage:
        hv <method> <startdate enddate>
        hv <method> <time period>
        """
        command = "hv"
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return
        method = args[0]

        # Time period in period format
        if args[1] in VALID_PERIODS:
            period = args[1]

        # Time period in startdate enddate format
        elif is_date(args[1]):
            if len(args) > 2:
                period = (args[1], args[2])
            else:
                console.print(
                    f"[red]Error: Missing end date. Use date format '%Y-%m-%d'."
                )
                return

        # Catch invalid time period
        else:
            console.print(
                f"[red]Error: '{args[1]}' is not recognized as a valid time period or date. Use {VALID_PERIODS} or date format '$Y-$m-$d'."
            )
            return

        # Get hv data
        try:
            hv_df, hv_realized = hv(
                self._ticker, method, period, config["hv_rolling_windows"]
            )
        except ValueError as e:
            console_error(e)
            return

        # Include metadata in DataFrame
        hv_df.attrs["ticker"] = self._ticker.ticker
        hv_df.attrs["period"] = (
            f"{period[0]}" if args[1] in VALID_PERIODS else f"{period[0]}_{period[1]}"
        )
        hv_df.attrs["datatype"] = command

        # Print data
        self.console_output(hv_df)
        console.print(f"Realized Volatility: {hv_realized}\n")

    @requires_ticker
    @requires_min_args(1)
    @catch_network_error
    def do_iv(self, line):
        """
        Print current implied volatility surface data or skew for a given expiration date.
        Usage:
        iv <surface|skew> (expiration)
        Flags:
        --res <int>     : resolution of volatility surface plot.
        --range <float> : percent range around spot price for strikes of volatility surface plot.
        --cmap <str>    : colormap of volatility surface plot.
        """
        command = "iv"
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return
        subcmd = args[0]

        expiration = args[1] if len(args) > 1 else ""

        if subcmd == "surface":
            # Handle Flags
            try:
                res = int(flags.get("--res", config["iv_surface_res"]))
                strike_range = float(flags.get("--range", config["iv_surface_range"]))
                cmap = str(flags.get("--cmap", config["iv_surface_cmap"]))
            except Exception as e:
                console_error(e)
                return

            try:
                # Get IV surface dataframe
                df = iv_surface(self._ticker)
                self.console_output(df)
                plot_iv_surface(df, self._ticker, strike_range, res, cmap)
            except ValueError as e:
                console_error(e)

                # Clear plot figure on error to prevent ghost plots
                plt.clf()
                plt.close()
                return

        elif subcmd == "skew":
            try:
                # Fetch and print IV skew dataframe
                df = iv_skew(self._ticker, expiration)
                self.console_output(df)

                # Plot IV skew dataframe automatically
                plt.figure(figsize=(10, 5))
                ax = plt.gca()

                ax.plot(df["strike"], df["impliedVolatility"])
                ax.set_xlabel("Strike")
                ax.set_ylabel("Implied Volatility")
                ax.set_title(f"{self._ticker.ticker} Volatility Skew {expiration}")

                plt.tight_layout()
                plt.show()

            except ValueError as e:
                console_error(e)

                # Clear plot figure on error to prevent ghost plots
                plt.clf()
                plt.close()
                return

        # Invalid subcmd
        else:
            console.print(
                f"[red]Error: '{subcmd}' is not recognized as a valid sub-command. Use 'skew' or 'surface'."
            )
            return

    @requires_min_args(1)
    def do_plot(self, line):
        """
        Plot the specified or all columns of the last output if it is a DataFrame against a specified index.
        Usage:
        plot <index> <column(s)| all>
        Flags:
        --title <str>   : title of plot
        --style <str>   : style of plot (https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html)
        --xlabel <str>  : label of x-axis
        --ylabel <str>  : label of y-axis
        -grid           : enable background grid
        -legend         : enable legend (automatically enabled when plotting two or more columns)
        """

        df = self._last_output
        try:
            args, flags = parse_line(line)
        except ValueError as e:
            console_error(e)
            return

        index = args[0]
        args.remove(index)

        # Check that last output is a dataframe / exists
        if not isinstance(df, pd.DataFrame):
            console.print(f"[red]Error: Last output '{df}' is not a DataFrame.")
            return

        # Check that dataframe is not empty
        if df.empty:
            console.print(f"[red]Error: DataFrame '{df}' is empty, cannot plot.")
            return

        # Handle plot style
        try:
            style = str(flags.get("--style", config["plot_style"]))
            plt.style.use(style)
        except (ValueError, OSError) as e:
            console_error(e)
            return

        plt.figure(figsize=(10, 5))
        ax = plt.gca()

        # Check existence of specified index
        try:
            series = df[index]
        except KeyError as e:
            console.print(f"[red]Error: Index {e} not found in DataFrame")
            # Clear plot figure
            plt.clf()
            plt.close()
            return

        # Plot all columns if 'all'
        if args[0] == "all":
            columns = list(df.columns[df.columns != index])
        else:
            columns = args

        # Plot columns
        for column in columns:
            try:
                ax.plot(series, df[column], label=column)
            except KeyError as e:
                console.print(f"[red]Error: Column {e} not found in DataFrame.")
                # Clear plot figure
                plt.clf()
                plt.close()
                return

        if pd.api.types.is_datetime64_any_dtype(series):
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            ax.xaxis.set_major_formatter(
                mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())
            )

        if len(df) > 20:
            plt.xticks(rotation=45, ha="right")

        # Handle flags
        try:
            title = str(flags.get("--title", f"{self._ticker.ticker} {columns}"))
            xlabel = str(flags.get("--xlabel", index.title()))
            ylabel = str(flags.get("--ylabel", ""))
            grid = flags.get("-grid", config["plot_grid"])
            legend = flags.get("-legend", config["plot_legend"])
        except ValueError as e:
            console_error(e)
            return

        if legend:
            plt.legend()
        ax.grid(grid)
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    MainCLI().cmdloop()
