# VolSuite

VolSuite is a python-based CLI tool designed for intuitive equity data retrieval and analysis, enabling users to quickly fetch historical ticker data and current option chains via yahoo finance. Additionally supports rolling realized volatility computation and visualization; volatility surface and skew modeling; configurable user settings with session persistence and data import/export capabilities.

## Running commands

VolSuite is a CLI tool, meaning that all user interaction is done through the terminal/command prompt window. In order to perform an action, a line should begin with a base command followed by its necessary arguments and optional flags – a full list of available commands and their arguments can be viewed by typing 'help (\<command\>)'. Commands which retrieve data will require a ticker to be specified by the user when running, this can be done by typing 'ticker \<symbol\>'.

> Note: Flags are optional arguments which can be used to configure the output of some commands. They are formatted as '\<flag\>=\<value\>'.

Upon first running, VolSuite will create a default config.json file in the same directory as the executable. This file can be modified directly by the user or from within the CLI by using the 'config' command.

## Example usage

### Historical price modeling:

Let's say I want to retrieve a list of historial prices of Apple Inc. ($AAPL) over the past year. First I run the following command to connect to the yfinance API and select the ticker 'AAPL':

```
ticker aapl
```

Next, I run the following command to print a table (formatted as a pandas dataframe) of historical summary data for the past year:

```
history 1y
```

Now that I have my dataframe, I want to plot the high and low prices by date. To do so I type the following:

```
plot date high low title=AAPL_High_Low_Prices_1y ylabel=Price_(USD)
```

Where date is my index (x-axis) and everything after is taken as a column to graph or a flag (recognized by a '=' in the argument). Now that I have my graph, I want to export the data for later use. I do so with the following command:

```
export
```

Because no filename was provided, VolSuite automatically generated one for me, 'AAPL_history_1mo.csv'. If I wanted to import the same dataframe in a later session, I could use the import command as follows:

```
import exports/AAPL_history_1mo.csv
```

Whenever a dataframe is loaded, via a command or import, it will be saved to the cache and referenced for any following commands until a new dataframe is loaded. 'import' will always search for the specified path in the same directory as the executable.

### Option chains:

To view the current call option chain expiring 2025-07-18 for $AAPL, I can type:

```
oc 2025-07-18 calls
```

If I want to view puts, I would replace 'calls' with 'puts'.

### Volatility modeling:

To create a plot of rolling close-to-close volatility of $AAPL for the past year, first I run the following:

```
hv close 1y
```

With this dataframe, I can now create my plot by typing:

```
plot date all
```

If I instead wish to view implied volatility data, I can use the following to fetch and plot the current volatility skew for $AAPL for the expiration 2025-07-18:

```
iv skew 2025-07-18
```

And the following to get the current volatility surface, which is also plotted automatically.

```
iv surface
```

> Note: Implied volatilites are currently retrieved from yfinance, and filtered by only referencing OTM options.
