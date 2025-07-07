# Volatility computation and plotting related functions

from datetime import date, datetime
from scipy.interpolate import griddata
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


def hv(ticker: yf.Ticker, method: str, timeperiod, windows: list):
    """
    Calculate historical realized volatility over a given time interval.

    Args:
        ticker: yf.Ticker object to fetch data from.
        method: Method of realized volatility calculation (close, garman-klass, parkinson).
        timeperiod: Time period in string format or startdate enddate format as a tuple.
        windows: List of rolling windows through which to compute realized volatility.

    Returns:
        A dataframe of the rolling realized volatility calculations for each day in the specified time period.
        A float representing the realized volatility over the entire period.

    Raises:
        ValueError: An unexpected method is taken in by the function.
    """

    # Fetch price data
    if isinstance(timeperiod, tuple):
        df = ticker.history(start=timeperiod[0], end=timeperiod[1])
        period = f"{timeperiod[0]}_{timeperiod[1]}"
    else:
        df = ticker.history(period=timeperiod)
        period = timeperiod

    df = df.dropna()
    hv_df = pd.DataFrame(index=df.index)

    # Rolling Close-to-Close volatility
    if method == "close":
        log_returns = np.log(df["Close"] / df["Close"].shift(1)).dropna()

        # Rolling vol
        for w in windows:
            hv_df[f"{w}d_close"] = log_returns.rolling(window=w).std(ddof=0) * np.sqrt(
                252
            )

        # Realized vol over entire period
        hv_realized = log_returns.std(ddof=0) * np.sqrt(252)

    # Rolling Parkinson volatility
    elif method == "parkinson":
        log_hl = np.log(df["High"] / df["Low"])

        for w in windows:
            parkinson_var = (1 / (4 * np.log(2))) * (log_hl**2).rolling(window=w).mean()
            hv_df[f"{w}d_parkinson"] = np.sqrt(parkinson_var) * np.sqrt(252)

        hv_realized = np.sqrt((1 / (4 * np.log(2))) * (log_hl**2).mean()) * np.sqrt(252)

    # Rolling Garman-Klass volatility
    elif method == "gk":
        log_hl = np.log(df["High"] / df["Low"])
        log_co = np.log(df["Close"] / df["Open"])
        gk_var = 0.5 * log_hl**2 - (2 * np.log(2) - 1) * log_co**2

        for w in windows:
            hv_df[f"{w}d_gk"] = np.sqrt(gk_var.rolling(window=w).mean()) * np.sqrt(252)

        hv_realized = np.sqrt(gk_var.mean()) * np.sqrt(252)

    else:
        raise ValueError(
            f"'{method}' is not recognized as a valid method. Use 'close', 'parkinson' or 'gk'"
        )

    # Include metadata for export
    hv_df.attrs["ticker"] = ticker.ticker
    hv_df.attrs["period"] = period
    hv_df.attrs["datatype"] = f"hv_{method}"

    return hv_df.reset_index(), hv_realized


def iv_skew(ticker: yf.Ticker, expiration: str = ""):
    """
    Create implied volatility skew for a given ticker and expiration. Computes skew with OTM options (puts below strike, calls above strike).

    Parameters:
        ticker: yf.Ticker object to fetch data from.
        expiration: Date of option expiration.

    Returns:
        A dataframe of implied volatilities at each strike for the given expiration.
    """

    # Fetch option chains
    calls = ticker.option_chain(expiration).calls
    puts = ticker.option_chain(expiration).puts

    # Filter for OTM options
    otm_calls = calls[calls["inTheMoney"] == False]
    otm_puts = puts[puts["inTheMoney"] == False]

    # Build skew dataframe
    iv_df = pd.concat(
        [
            otm_puts[["strike", "impliedVolatility"]].copy(),
            otm_calls[["strike", "impliedVolatility"]].copy(),
        ]
    )
    iv_df = iv_df.dropna()

    # Include metadata in dataframe for export
    iv_df.attrs["ticker"] = ticker.ticker
    iv_df.attrs["period"] = expiration
    iv_df.attrs["datatype"] = "iv_skew"

    return iv_df


def iv_surface(ticker: yf.Ticker):
    """
    Create implied volatility surface dataframe for a given ticker using otm ivs provided by yfinance.

    Parameters:
        ticker: yf.Ticker object to fetch data from.

    Returns:
        A dataframe of implied volatilites for each strike at every expiration available.
    """

    # Get expirations and today's date for time to expiry
    expirations = ticker.options
    current_date = pd.Timestamp(datetime.today())

    options = []

    for expiration in expirations:
        chain = ticker.option_chain(expiration)

        for df in [chain.puts, chain.calls]:
            otm = df[~df["inTheMoney"]].copy()
            otm = otm[["strike", "impliedVolatility"]].rename(
                columns={"impliedVolatility": "impliedvolatility"}
            )
            otm["expiration"] = expiration
            otm["dte"] = (pd.to_datetime(expiration) - current_date).days
            otm["spot"] = ticker.fast_info["lastPrice"]
            options.append(otm)

    # Concatenate all expiration data
    iv_surface_df = pd.concat(options, ignore_index=True)

    # Create moneyness column
    iv_surface_df["moneyness"] = iv_surface_df["strike"] / iv_surface_df["spot"]

    # Include metadata for export
    iv_surface_df.attrs["ticker"] = ticker.ticker
    iv_surface_df.attrs["period"] = str(date.today())
    iv_surface_df.attrs["datatype"] = "iv_surface"

    return iv_surface_df


def plot_iv_surface(
    iv_surface_df: pd.DataFrame,
    ticker: yf.Ticker,
    strike_range: float,
    res: int,
    cmap: str,
):
    """
    Plot implied volatility surface for a given volatility surface dataframe, ticker and percent range for moneyness.

    Parameters:
        iv_surface_df: Dataframe of implied volatilities for each strike at every expiration.
        ticker: yf.Ticker object to fetch data from.
        strike_range: Percent range of values above and below spot price to plot. (0.2 -> min strike = 80% of spot, max strike = 120% of spot).
        res: Resolution of surface, represents length of square meshgrid.
        cmap: Colormap to use for surface plotting.
    """

    # Get spot price from dataframe
    spot = iv_surface_df["spot"].iloc[0]

    # Filter iv surface df by strike range
    lower_strike = spot * (1 - strike_range)
    upper_strike = spot * (1 + strike_range)
    iv_surface_df_filtered = iv_surface_df[
        (iv_surface_df["strike"] >= lower_strike)
        & (iv_surface_df["strike"] <= upper_strike)
    ]

    x = iv_surface_df_filtered["strike"].values
    y = iv_surface_df_filtered["dte"].values
    z = iv_surface_df_filtered["impliedvolatility"].values

    # Organize data into meshgrid
    xi = np.linspace(x.min(), x.max(), res + 1)
    yi = np.linspace(y.min(), y.max(), res + 1)
    XI, YI = np.meshgrid(xi, yi)

    # Interpolate iv on the grid
    ZI = griddata((x, y), z, (XI, YI), method="linear")

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    surf = ax.plot_surface(XI, YI, ZI, cmap=cmap, edgecolor=None)

    # Label axes and plot
    ax.set_xlabel("Strike")
    ax.set_ylabel("Time to Maturity (Days)")
    ax.set_zlabel("Implied Volatility")
    ax.set_title(f"{ticker.ticker} Implied Volatility Surface")

    fig.colorbar(surf, shrink=0.5, aspect=10)

    plt.show()
