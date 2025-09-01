# VolSuite

VolSuite is a python-based CLI tool designed for intuitive equity data retrieval and analysis, enabling users to quickly fetch historical ticker data and current option chains via yahoo finance. Additionally supports rolling realized volatility computation and visualization; volatility surface and skew modeling; configurable user settings with session persistence and data import/export capabilities.

## Running commands

VolSuite is a CLI tool, meaning that all user interaction is done through the terminal/command prompt window. In order to perform an action, a line should begin with a base command followed by its necessary arguments and optional flags – a full list of available commands and their arguments can be viewed by typing 'help (\<command\>)'. Commands which retrieve data will require a ticker to be specified by the user when running, this can be done by typing 'ticker \<symbol\>'.

> Note: Flags are optional arguments which can be used to configure the output of some commands. They are formatted as '--\<flag\>=\<value\>' for parametric flags and '-\<flag\>' for boolean flags.

Upon first running, VolSuite will create a default config.json file in the same directory as the executable. This file can be modified directly by the user or through the CLI by using the 'config' command.

## Installation

### Quick Install:
To install the standalone executable [get the latest release from GitHub](https://github.com/liam-duke/volsuite/releases).

### Developer Setup:
To install and run the source code as a python module:

```
git clone https://github.com/liam-duke/volsuite.git
cd volsuite

# Optional virtual environment setup
python -m venv .venv
source .venv/bin/activate  # MacOS/Linux
.venv\scripts\activate     # Windows

pip install -r requirements.txt
cd src
python -m volsuite.main
```

To build a local executable in with PyInstaller, ensure that you are in the project root folder and:

```
pip install pyinstaller
python build.py
```

The executable can be found in the dist/ folder.

## Example usage

### Historical price modeling:

Let's say I want to retrieve a list of historial prices of Apple Inc. ($AAPL) over the past year. First I run the following command to connect to the yfinance API and select the ticker 'AAPL':

```
ticker aapl
```

Next, I run the following command to print a dataframe of historical summary data for the past year:

```
history 1y
```

Now that I have my dataframe, I want to plot the high and low prices by date. To do so I type the following:

```
plot date high low --title="AAPL High-Low Prices 1y" --ylabel="Price (USD)"
```

Where 'date' is my index and everything after is taken as a column to graph or flag. Now that I have my graph, I want to export the data for later use. I do so with the following command:

```
export
```

Because no filename was provided, VolSuite will automatically generate one for me, 'AAPL_history_1mo.csv'. If I wanted to import the same dataframe in a later session, I could use the import command as follows:

```
import exports/AAPL_history_1mo.csv
```

Whenever a dataframe is loaded, via a command or import, it will be saved to the cache and referenced for any following commands until a new dataframe is loaded either via import or yFinance. 'import' will always search for the specified path in the same directory as the executable.

### Option chain retrieval:

To view the current call option chain for $AAPL with expiry 2025-07-18, I can type:

```
oc 2025-07-18 calls
```

To view puts, I would replace 'calls' with 'puts'.

### Volatility modeling:

To create a plot of rolling close-to-close volatility of $AAPL for the past year, first I run the following:

```
hv close 1y
```

With this dataframe, I can now create my plot by typing:

```
plot date all
```

If I instead wish to view implied volatility data, I can use the following to fetch and plot the current volatility skew of $AAPL options with expiration 2025-07-18:

```
iv skew 2025-07-18
```

And the following to get the current volatility surface, which is also plotted automatically.

```
iv surface
```

> Note: Implied volatilites are currently retrieved from yfinance, and filtered by OTM prices.
