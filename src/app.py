from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px
import os

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

# Function to read data
def read_data():
    if os.path.exists('tag_data.csv'):
        df = pd.read_csv('tag_data.csv')
        if 'Timestamp' in df.columns:
            try:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%Y-%m-%d %H:%M:%S')
            except ValueError:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
            df.dropna(subset=['Timestamp'], inplace=True)
        return df
    else:
        return pd.DataFrame(columns=["Timestamp", "RFID Tag", "Antenna", "Time Between Stamps"])

# Function to read prediction data
def read_prediction_data():
    if os.path.exists('prediction_results.csv'):
        df = pd.read_csv('prediction_results.csv')
        if 'Date' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %H:%M:%S')
            except ValueError:
                df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df.dropna(subset=['Date'], inplace=True)
        return df
    else:
        return pd.DataFrame(columns=["Image", "Predicted Class", "Date"])

# Initial data read
df = read_data()
prediction_df = read_prediction_data()

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                id='tag-dropdown',
                options=[{'label': tag, 'value': tag} for tag in df['RFID Tag'].unique()],
                value=df['RFID Tag'].unique()[0] if not df.empty else None,
                placeholder="Select an RFID tag",
            ),
        ], style={'width': '49%', 'display': 'inline-block'}),
    ], style={'padding': '10px 5px'}),
    html.Div([
        dcc.Graph(id='time-between-stamps-graph'),
        dcc.Graph(id='cycle-time-graph'),
        dcc.Graph(id='comparison-graph'),
        dcc.Graph(id='prediction-graph'),
    ], style={'display': 'flex', 'flex-direction': 'column'}),
])

@callback(
    Output('tag-dropdown', 'options'),
    Input('tag-dropdown', 'value')
)
def update_dropdown(selected_tag):
    df = read_data()
    return [{'label': tag, 'value': tag} for tag in df['RFID Tag'].unique()]

@callback(
    Output('time-between-stamps-graph', 'figure'),
    Input('tag-dropdown', 'value')
)
def update_time_between_stamps_graph(selected_tag):
    df = read_data()
    if selected_tag:
        df = df[df['RFID Tag'] == selected_tag]
        df['Time Between Stamps'] = df['Time Between Stamps'].astype(float).round(3)
        df['Smoothed Time Between Stamps'] = df['Time Between Stamps'].rolling(window=5).mean()  
        fig = px.line(df, x='Timestamp', y='Smoothed Time Between Stamps', title=f'Time Between Stamps for {selected_tag}')
        fig.update_yaxes(tickformat=".3f")
    else:
        fig = px.line(title='Time Between Stamps')
    return fig

@callback(
    Output('cycle-time-graph', 'figure'),
    Input('tag-dropdown', 'value')
)
def update_cycle_time_graph(selected_tag):
    df = read_data()
    if selected_tag:
        df = df[df['RFID Tag'] == selected_tag]
        df['Cycle Time'] = df['Time Between Stamps'].astype(float).cumsum().round(3)
        fig = px.line(df, x='Timestamp', y='Cycle Time', title=f'Cycle Time for {selected_tag}')
        fig.update_yaxes(tickformat=".3f")
    else:
        fig = px.line(title='Cycle Time')
    return fig

@callback(
    Output('comparison-graph', 'figure'),
    Input('tag-dropdown', 'value')
)
def update_comparison_graph(selected_tag):
    df = read_data()
    if not df.empty:
        df['Time Between Stamps'] = df['Time Between Stamps'].astype(float)
        df['Cycle Time'] = df.groupby('RFID Tag')['Time Between Stamps'].cumsum().round(3)
        fig = px.line(df, x='Timestamp', y='Cycle Time', color='RFID Tag', title='Comparison of Cycle Times')
        fig.update_yaxes(tickformat=".3f")
    else:
        fig = px.line(title='Comparison of Cycle Times')
    return fig

@callback(
    Output('prediction-graph', 'figure'),
    Input('tag-dropdown', 'value')
)
def update_prediction_graph(selected_tag):
    prediction_df = read_prediction_data()
    if not prediction_df.empty:
        fig = px.histogram(prediction_df, x='Date', color='Predicted Class', title='Predicted Class Counts Over Time', nbins=50)
    else:
        fig = px.histogram(title='Predicted Class Counts Over Time')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)
