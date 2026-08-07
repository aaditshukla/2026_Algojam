import numpy as np

# Custom trading Algorithm
class Algorithm():

    # FUNCTION TO SETUP ALGORITHM CLASS
    def __init__(self, positions):
        self.data = {}  # Historical data of all instruments
        self.positionLimits = {}    # Initialise position limits
        self.day = 0     # Initialise the current day as 0
        self.positions = positions   # Initialise the current positions
        
    def get_current_price(self, instrument):
        """
        Helper function to fetch current price of an instrument.
        """
        return self.data[instrument][-1]
    
    # RETURN DESIRED POSITIONS IN DICT FORM
    def get_positions(self):
        # Get current position
        currentPositions = self.positions
        # Get position limits
        positionLimits = self.positionLimits
        
        # Declare a store for desired positions
        desiredPositions = {}
        # Loop through all the instruments you can take positions on.
        for instrument, positionLimit in positionLimits.items():
            # For each instrument initilise desired position to zero
            desiredPositions[instrument] = 0

        # IMPLEMENT CODE HERE TO DECIDE WHAT POSITIONS YOU WANT 
        #######################################################################
        # Display the current trading day
        print("Starting Algorithm for Day:", self.day)
        
        
        # Trade thrifted jeans and the sausage sizzle
        trade_instruments = ["Thrifted Jeans", "Sausage Sizzle"]
        
        # Display the prices of instruments I want to trade
        for ins in trade_instruments:
            print(f"{ins}: ${self.get_current_price(ins)}")
        
        # If its 10th day or more, then trade
        if self.day >= 10:
            for ins in trade_instruments:
                # if price has gone down, buy
                todays_price = self.data[ins][-1]
                yesterdays_price = self.data[ins][-2]
                if yesterdays_price > todays_price:
                    desiredPositions[ins] = positionLimits[ins]
                else: # else, short
                    desiredPositions[ins] = -positionLimits[ins]
                    
                    
        # Display the end of trading day
        print("Ending Algorithm for Day:", self.day, "\n")
        #######################################################################
        # Return the desired positions
        return desiredPositions
