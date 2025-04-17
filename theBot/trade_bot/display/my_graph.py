import plotly.graph_objects as go
import pandas as pd
import os
from trade_bot.utils.enums import TRADE_DIR


class MyGraph:
    __freq = None
    __symbol = None
    __df_candidat = pd.DataFrame()

    def __init__(self, symbol: str):
        self.__symbol = symbol

    def set_candidat(self, df1: pd, freq: str):
        self.__df_candidat = df1
        self.__freq = freq

    def get_chart(self, client_oid, display = True):
        symbol = self.__symbol
        df1 = self.__df_candidat
        period = self.__freq

        # Ensure 'Date' column exists if using DatetimeIndex
        df1['Date'] = df1.index
        symbol = self.__symbol
        fig = go.Figure()

        # Add Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df1['Date'],
            open=df1['open'],
            high=df1['high'],
            low=df1['low'],
            close=df1['close'],
            name="Candlesticks"))

        # Add fill_between effect (Keltner Channel)
        fig.add_trace(go.Scatter(
            x=df1['Date'].tolist() + df1['Date'][::-1].tolist(),  
            y=df1['kcu'].tolist() + df1['kcl'][::-1].tolist(),  
            fill='toself', 
            fillcolor='rgba(255, 182, 193, 0.3)',  # Light pink
            line=dict(color='rgba(255,255,255,0)'),
            name="Keltner band"))

        # Add `kcl` (Keltner lower channel) as a pink line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['kcl'],
            mode='lines',
            line=dict(color='pink', width=2, dash='solid'),  # Dashed blue line
            name="Keltner lower channel"))

        # Add `kcl` (Keltner higher channel) as a pink line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['kcu'],
            mode='lines',
            line=dict(color='pink', width=2, dash='solid'),  # Dashed blue line
            name="Keltner higher channel"))

        # Add `bbu` (Upper Bollinger Band) as a blue line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['bbu'],
            mode='lines',
            line=dict(color='blue', width=2, dash='solid'),  # Dashed blue line
            name="Bollinger Upper Band"))

        # Add `bbm` (medium Bollinger Band) as a blue line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['bbm'],
            mode='lines',
            line=dict(color='blue', width=2, dash='solid'),  # Dashed blue line
            name="Bollinger medium Band"))

        # Add `bbl` (lower Bollinger Band) as a blue line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['bbl'],
            mode='lines',
            line=dict(color='blue', width=2, dash='solid'),  # Dashed blue line
            name="Bollinger lower Band"))

        # Add `hma` (hull mobile) as a black line
        fig.add_trace(go.Scatter(
            x=df1['Date'],
            y=df1['hma'],
            mode='lines',
            line=dict(color='black', width=2, dash='solid'),  # Dashed blue line
            name="Hull mobile"))

        # draw crossing_kcu
        spot_mask = df1['crossing_kcu'] == True
        fig.add_trace(go.Scatter(
            x=df1['Date'][spot_mask],  
            y=df1['kcu'][spot_mask],  
            mode='markers',
            marker=dict(size=8, color='red', symbol='circle'),
            name="Crossing kcu"))

        # draw crossing_kcl
        spot_mask = df1['crossing_kcl'] == True
        fig.add_trace(go.Scatter(
            x=df1['Date'][spot_mask],  
            y=df1['kcl'][spot_mask],  
            mode='markers',
            marker=dict(size=8, color='red', symbol='circle'),
            name="Crossing kcl"))

        # draw touching_bbu
        spot_mask = df1['touching_bbu'] == True
        fig.add_trace(go.Scatter(
            x=df1['Date'][spot_mask],  
            y=df1['bbu'][spot_mask],  
            mode='markers',
            marker=dict(size=8, color='blue', symbol='circle'),
            name="touching bbu"))

        # draw touching_bbl
        spot_mask = df1['touching_bbl'] == True
        fig.add_trace(go.Scatter(
            x=df1['Date'][spot_mask],  
            y=df1['bbl'][spot_mask],  
            mode='markers',
            marker=dict(size=8, color='blue', symbol='circle'),
            name="touching bbl"))

        # draw crossing_hma
        spot_mask = df1['crossing_hma'] == True
        fig.add_trace(go.Scatter(
            x=df1['Date'][spot_mask],  
            y=df1['hma'][spot_mask],  
            mode='markers',
            marker=dict(size=8, color='black', symbol='circle'),
            name="crossing hma"))

        # Layout settings
        fig.update_layout(
            title=f"{symbol} Candlestick Chart {period}",
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            yaxis_title="Price",
            width=900,  # Set width in pixels
            height=800)

        if display: 
            fig.show()
        else:
            output_dir = TRADE_DIR
            os.makedirs(output_dir, exist_ok=True)  # create directory if it doesn't exist
            file_path = os.path.join(output_dir, f"{client_oid}-{symbol}.html")
            fig.write_html(file_path)