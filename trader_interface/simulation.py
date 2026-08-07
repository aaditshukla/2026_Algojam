# Library Imports
import os
import pandas as pd
from algorithm import Algorithm
import numpy as np
import matplotlib.pyplot as plt
from decimal import Decimal, ROUND_HALF_UP
from matplotlib.gridspec import GridSpec
import math

##############################
# Define constants
##############################
# PRODUCTS AND THEIR INDIVIDUAL BUDGETS IN $AUD
positionLimits = {
    "Fintech Token": 100, 
    "Thrifted Jeans": 800,  
    "UQ Dollar": 650,
    "Sausage Sizzle": 3000,  
    "Bread": 500,    
    "MenuDash": 75000,   
    "Sausage": 5000,   
    "Liferaft Ticket": 1, 
    "Boat Party Ticket": 1000, 
}

# TOTAL DAILY BUDGET IN $AUD
totalDailyBudget = 600000

NO_LOCAL_PNL_INSTRUMENTS = {"Liferaft Ticket"}
##############################

# Trading Engine Class, Controlling Trades Tracking
class TradingEngine:
    def __init__(self, dataFolder='data/'):
        # Init variables
        self.dataFolder = dataFolder
        # Store active positions
        self.positions = {}
        # Position Limits
        self.positionLimits = positionLimits
        # Daily return history of each instrument
        self.returnsHistory = {}
        # Instrument cumulative returns history
        self.cumulativeReturnsHistory = {}
        # Store position as % of limit for graphing
        self.pcPositionHistorys = {}
        # Daily return history of combined instruments
        self.totalReturnHistory = []
        # Cumulative historical value of combined instruments
        self.totalValueHistory = []
        # Total days in simulation
        self.totalDays = 0
        # Track total PNL across all instruments
        self.totalPNL = 0
        # Track pc of total budget used daily
        self.pcTotalBudget = []
        # Setup functions
        self.load_data()
        self.initialize_positions()
        

    # For loading in relevant data from .CSV Files
    def load_data(self):
        self.data = {}
        for file in os.listdir(self.dataFolder):
            if file.endswith('_price_history.csv'):
                instrumentName = file.split('_')[0]
                if instrumentName in positionLimits.keys():
                    filePath = os.path.join(self.dataFolder, file)
                    self.data[instrumentName] = pd.read_csv(filePath)
                else:
                    print(f"No position limit set for {instrumentName}. This dataset will not be loaded.")
        # Ensure that all data have same length of days
        numDays = len(self.data[list(self.data.keys())[0]])
        print(f"Expected number of days: {numDays}")
        for instrument, data in self.data.items():
            if len(data) != numDays:
                print(f"Mismatch found for {instrument}: has {len(data)} days instead of {numDays}")
        print("Continuing with dataset verification...")
        for data in self.data.values():
            # if a dataset has a different number of days, exit
            if len(data) != numDays:
                print("\nError, not all datasets are the same length.\bExiting...")
                exit(1)
        # Otherwise, all data should have the same number of days.
        self.totalDays = numDays
        print("Datasets loaded successfully.")

    # Set initial positions to 0 for each
    def initialize_positions(self):
        for instrument in positionLimits: 
            self.positions[instrument] = 0
            self.returnsHistory[instrument] = []
            self.cumulativeReturnsHistory[instrument] = []
            self.pcPositionHistorys[instrument] = []

    # Helper function to check that a given order is within the daily budget.
    # Also records the total utilisation of the daily budget.
    def notWithinBudget(self, desiredPositions, priceHistory):
        # calc total value of positions
        totVal = 0
        for instrument, history in priceHistory.items():
            pos = desiredPositions[instrument]
            price = history[-1]
            value = abs(pos*price)
            totVal += value
        # if the budget is exceeded
        if totVal > totalDailyBudget:
            print("#########")
            print(f"Over budget by ${totVal-totalDailyBudget}.")
            # display values of each instrument position.
            for instrument, prcHistory in priceHistory.items():
                pos = desiredPositions[instrument]
                price = prcHistory[-1]
                value = abs(pos*price)
                totVal += value
                print(f"{instrument} position value: ${value}.")
            print("#########")
            # record zero as daily position used of budget, as position will be reset to zero
            self.pcTotalBudget.append(0)
            # return true, as desired position not within budget.
            return True
        # within daily budget, so record % usage
        pcBudgetUsage = round(totVal*100/totalDailyBudget,2)
        self.pcTotalBudget.append(pcBudgetUsage)
        # return false, as within the daily budget
        return False

    # Process submitted algorithm
    def run_algorithms(self, algorithmsInstance):
        # Loop through every day of data. day-1 indexing inside the PnL block
        # below is always guarded by `if day != 0`, so day can safely run
        # through totalDays-1 (the final row) without any out-of-range access.
        for day in range(self.totalDays):
            # Get current data history at this point in time
            historicalData = {}
            for instrument, priceData in self.data.items():
                # Fetch all relevant data
                priceHistory = priceData['Price'][:day+1].tolist()
                # Add them to the historicalData store
                historicalData[instrument] = priceHistory     
            # Update the algorithms instance with the new information
            algorithmsInstance.day = day
            algorithmsInstance.data = historicalData
            algorithmsInstance.positions = self.positions
            algorithmsInstance.positionLimits = self.positionLimits
            # Now get the desired positions from the competitors algorithm
            desiredPositions = algorithmsInstance.get_positions()
            
            # Check if the desired positions are within total budget
            if self.notWithinBudget(desiredPositions, historicalData):
                # Set all desired positions to zero
                for instrument in desiredPositions.keys():
                    desiredPositions[instrument] = 0
                print(f"REQUESTED POSIITONS EXCEED DAILY BUDGET OF: ${totalDailyBudget}.")
                print(f"SET ALL DESIRED POSITIONS FOR DAY {day} TO ZERO.")
                
            # Store total return for the day
            dailyReturn = 0
            # Process profit/loss for each instrument:
            for instrument, priceData in self.data.items():
                # Perform desired position quality checks (int and within limits)
                if (type(desiredPositions[instrument]) != type(1) or # not an int
                        abs(desiredPositions[instrument]) > self.positionLimits[instrument] # not within limits
                        ):
                    # Incorrect value provided. Skip
                    print(f"Position given for {instrument} on day {day} invalid.")
                    print(f"Position given was {desiredPositions[instrument]}.")
                    print(f"The limit for this instrument today is: {self.positionLimits[instrument]}")
                    print(f"Setting desired position to zero units.")
                    # Set zero
                    desiredPositions[instrument] = 0
                # Calculate PNL if not day 0
                if day != 0:
                    if instrument in NO_LOCAL_PNL_INSTRUMENTS:
                        instrumentPNL = 0
                    else:
                        existingPosition = self.positions[instrument]
                        currPrice = priceData["Price"][day]
                        lastPrice = priceData["Price"][day-1]
                        instrumentPNL = existingPosition * (currPrice - lastPrice)
                        instrumentPNL = quantize_decimal(instrumentPNL, 2)
                    self.returnsHistory[instrument].append(instrumentPNL)
                    self.cumulativeReturnsHistory[instrument].append(
                        instrumentPNL + self.cumulativeReturnsHistory[instrument][-1]
                    )
                    # add it to the daily return
                    dailyReturn += instrumentPNL
                else:
                    # No trades executed first day
                    self.returnsHistory[instrument].append(0)
                    self.cumulativeReturnsHistory[instrument].append(0)
            # Store positions in historical tracker for graphing
            for instrument, desiredPosition in desiredPositions.items():
                self.pcPositionHistorys[instrument].append(round(desiredPosition*100/self.positionLimits[instrument]))
            # Add the daily return to the tracker
            self.totalReturnHistory.append(dailyReturn)
            # Update total PNL
            self.totalPNL += dailyReturn
            # Display PNL
            print(f"Total PNL @ Day {day}: {self.totalPNL}")
            # Update total Value
            self.totalValueHistory.append(self.totalPNL)
            # Update simluator information
            self.positions = desiredPositions
            

    def plot_returns(self):
        # ── Palette ──────────────────────────────────────────────────────────
        BG          = "#FFFFFF"
        GRID_COLOR  = "#E0E0E0"
        SPINE_COLOR = "#CCCCCC"
        TEXT_COLOR  = "#1A1A2E"
        ACCENT      = "#1565C0"   # total P&L line / budget fill
        ZERO_COLOR  = "#9E9E9E"
        INSTRUMENT_COLORS = [
            "#E53935", "#43A047", "#1E88E5", "#FB8C00",
            "#8E24AA", "#00ACC1", "#D81B60", "#6D4C41",
            "#3949AB", "#00897B",
        ]

        # ── Global style ─────────────────────────────────────────────────────
        plt.rcParams.update({
            "font.family":        "DejaVu Sans",
            "font.size":          9,
            "axes.titlesize":     10,
            "axes.titleweight":   "bold",
            "axes.titlepad":      8,
            "axes.labelsize":     8,
            "axes.labelcolor":    TEXT_COLOR,
            "xtick.labelsize":    8,
            "ytick.labelsize":    8,
            "xtick.color":        TEXT_COLOR,
            "ytick.color":        TEXT_COLOR,
            "legend.fontsize":    7,
            "legend.framealpha":  0.9,
            "legend.edgecolor":   SPINE_COLOR,
        })

        # ── Layout ───────────────────────────────────────────────────────────
        fig = plt.figure(figsize=(18, 10), facecolor=BG)
        gs  = GridSpec(2, 2, figure=fig,
                       hspace=0.45, wspace=0.32,
                       left=0.07, right=0.97, top=0.91, bottom=0.07)

        ax_total  = fig.add_subplot(gs[0, 0])   # top-left:     total cumulative P&L
        ax_indiv  = fig.add_subplot(gs[0, 1])   # top-right:    per-instrument cumulative P&L
        ax_budget = fig.add_subplot(gs[1, 0])   # bottom-left:  budget utilisation
        ax_bar    = fig.add_subplot(gs[1, 1])   # bottom-right: per-instrument P&L bar chart

        # ── Shared axis styling ───────────────────────────────────────────────
        def style_ax(ax):
            ax.set_facecolor(BG)
            ax.grid(True, color=GRID_COLOR, linewidth=0.8, linestyle="-", zorder=0)
            ax.set_axisbelow(True)
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            for spine in ["left", "bottom"]:
                ax.spines[spine].set_color(SPINE_COLOR)
            ax.tick_params(axis="both", color=SPINE_COLOR)
            ax.margins(x=0)

        for ax in [ax_total, ax_indiv, ax_budget, ax_bar]:
            style_ax(ax)

        # ── Print metrics ─────────────────────────────────────────────────────
        print("#" * 50)
        print(f"Total PNL ($): {self.totalPNL}")
        print("#" * 50)
        for instrument, returns in self.cumulativeReturnsHistory.items():
            print(f"{instrument} Returns ($): {returns[-1]}")
        print("#" * 50)

        # ── ax_total — Cumulative P&L ─────────────────────────────────────────
        tv   = [float(v) for v in self.totalValueHistory]
        days = range(len(tv))
        ax_total.plot(tv, color=ACCENT, linewidth=2, zorder=3)
        ax_total.fill_between(days, tv, 0,
                              where=[v >= 0 for v in tv],
                              alpha=0.12, color=ACCENT, zorder=2)
        ax_total.fill_between(days, tv, 0,
                              where=[v < 0 for v in tv],
                              alpha=0.12, color="#E53935", zorder=2)
        ax_total.axhline(0, color=ZERO_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        ax_total.scatter(len(tv) - 1, tv[-1], color=ACCENT, zorder=5, s=55)
        ax_total.annotate(
            f"${tv[-1]:,.2f}",
            xy=(len(tv) - 1, tv[-1]),
            xytext=(-10, 10), textcoords="offset points",
            fontsize=9, fontweight="bold", color=ACCENT, ha="center",
        )
        ax_total.set_title("Cumulative P&L")
        ax_total.set_xlabel("Day")
        ax_total.set_ylabel("$AUD")
        ax_total.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}")
        )

        # ── ax_indiv — Individual Cumulative P&L ──────────────────────────────
        lines_indiv = []
        for (instrument, returns), color in zip(
                self.cumulativeReturnsHistory.items(), INSTRUMENT_COLORS):
            returns = [float(v) for v in returns]
            line, = ax_indiv.plot(returns, label=instrument, color=color,
                                  linewidth=1.4, zorder=3)
            lines_indiv.append(line)
        ax_indiv.axhline(0, color=ZERO_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        legend_indiv = ax_indiv.legend(loc="upper left", ncol=2)
        ax_indiv.set_title("Individual Cumulative P&L")
        ax_indiv.set_xlabel("Day")
        ax_indiv.set_ylabel("$AUD")
        ax_indiv.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"${x:,.0f}")
        )

        # ── ax_budget — Budget Utilisation ───────────────────────────────────
        budget = self.pcTotalBudget
        ax_budget.plot(budget, color=ACCENT, linewidth=1.5, zorder=3)
        ax_budget.fill_between(range(len(budget)), budget,
                               alpha=0.15, color=ACCENT, zorder=2)
        ax_budget.margins(y=0)
        ax_budget.axhline(100, color="#E53935", linewidth=0.8,
                          linestyle="--", zorder=1, alpha=0.6)
        ax_budget.set_title("Daily Budget Utilisation")
        ax_budget.set_xlabel("Day")
        ax_budget.set_ylabel("% of $600K limit")

        # ── ax_bar — Per-instrument P&L bar chart ────────────────────────────
        bar_data = sorted(
            [(inst, float(returns[-1])) for inst, returns in self.cumulativeReturnsHistory.items()],
            key=lambda x: x[1],
        )
        instruments, finals = zip(*bar_data)
        bar_colors = ["#E53935" if v < 0 else "#43A047" for v in finals]
        bars = ax_bar.barh(instruments, finals, color=bar_colors, zorder=3, height=0.6)
        ax_bar.axvline(0, color=ZERO_COLOR, linewidth=0.9, linestyle="--", zorder=1)
        for bar, val in zip(bars, finals):
            x = bar.get_width()
            ax_bar.text(
                x + (max(finals) - min(finals)) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"${val:,.0f}", va="center", ha="left", fontsize=7.5, color=TEXT_COLOR,
            )
        ax_bar.margins(x=0.02, y=0.04)
        ax_bar.set_title("P&L by Instrument")
        ax_bar.set_xlabel("$AUD")
        ax_bar.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"${x:,.0f}"))

        # ── Figure title ──────────────────────────────────────────────────────
        fig.suptitle(
            f"Simulation Results    |    Total P&L: ${float(self.totalPNL):,.2f}",
            fontsize=13, fontweight="bold", color=TEXT_COLOR, y=0.97,
        )

        # ── Legend picking (toggle visibility) ───────────────────────────────
        all_instrument_lines = lines_indiv
        def on_pick(event):
            artist = event.artist
            visible = not artist.get_visible()
            artist.set_visible(visible)
            for line in all_instrument_lines:
                if line.get_label() == artist.get_label():
                    line.set_visible(visible)
            fig.canvas.draw()

        for item in legend_indiv.get_lines():
            item.set_picker(True)
        fig.canvas.mpl_connect("pick_event", on_pick)

        # ── Save & show ───────────────────────────────────────────────────────
        output_dir = "./simulation_results"
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(os.path.join(output_dir, "returns_plot.png"),
                    dpi=300, facecolor=BG, bbox_inches="tight")
        plt.show()
        plt.close(fig)

        

# Function to round a float
def quantize_decimal(value, decimal_places=2):
    # str() first: Decimal() rejects numpy scalar types (e.g. np.int64, which
    # pandas produces for an all-integer price column) even though they
    # behave like plain int/float everywhere else.
    decimal_value = Decimal(str(value))
    if decimal_value % 1 == 0:  # Check if the number is an integer
        return decimal_value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    else:  # For non-integers, round to the specified decimal places
        rounding_format = '1.' + '0' * decimal_places
        return decimal_value.quantize(Decimal(rounding_format), rounding=ROUND_HALF_UP)


if __name__ == "__main__":
    engine = TradingEngine()
    algorithmInstance = Algorithm(engine.positions)
    engine.run_algorithms(algorithmInstance)
    engine.plot_returns()

