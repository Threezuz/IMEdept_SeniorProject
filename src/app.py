from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
# Load the first CSV file
df1 = pd.read_csv('rfid_data.csv')
df1['Time'] = pd.to_datetime(df1['Time'], format='%H:%M:%S:%d:%m:%Y')

# Load the second CSV file
df2 = pd.read_csv('prediction_results.csv')
df2['Date'] = pd.to_datetime(df2['Date'])

app.layout = html.Div([
    # Existing layout components for the first set of graphs
    html.Div([
        html.Div([
            dcc.Dropdown(
                df1['Tag ID'].unique(),
                df1['Tag ID'].unique()[0],
                id='tag-id-dropdown'
            ),
        ], style={'width': '49%', 'display': 'inline-block'}),

        html.Div([
            dcc.RadioItems(
                ['TimebetweenReads', 'Cycle Time'],
                'TimebetweenReads',
                id='metric-radio',
                labelStyle={'display': 'inline-block', 'marginTop': '5px'}
            )
        ], style={'width': '49%', 'float': 'right', 'display': 'inline-block'})
    ], style={'padding': '10px 5px'}),

    html.Div([
        dcc.Graph(id='indicator-scatter')
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),

    html.Div([
        dcc.Graph(id='time-series')
    ], style={'display': 'inline-block', 'width': '49%'}),

    html.Div(dcc.Slider(
        min=0,
        max=len(df1['Time'].unique()) - 1,
        step=None,
        id='time-slider',
        value=len(df1['Time'].unique()) - 1,
        marks={i: str(time) for i, time in enumerate(sorted(df1['Time'].unique()))}
    ), style={'width': '49%', 'padding': '0px 20px 20px 20px'}),

    html.Div([
        dcc.Graph(id='cycle-time-comparison')
    ], style={'width': '100%', 'padding': '0 20'}),

    html.Div([
        html.Button("Download CSV", id="btn-download-csv"),
        dcc.Download(id="download-csv")
    ], style={'padding': '10px 5px'}),

    # New layout components for the second set of graphs
    html.Hr(),
    html.H3("Prediction Results"),
    html.Div([
        dcc.Graph(id='predicted-class-scatter')
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),

    html.Div([
        dcc.Graph(id='predicted-class-bar')
    ], style={'display': 'inline-block', 'width': '49%'})
])


@callback(
    [Output('indicator-scatter', 'figure'),
     Output('cycle-time-comparison', 'figure')],
    [Input('tag-id-dropdown', 'value'),
     Input('metric-radio', 'value'),
     Input('time-slider', 'value')])
def update_graphs(tag_id, metric, time_index):
    selected_time = sorted(df1['Time'].unique())[time_index]
    dff = df1[(df1['Tag ID'] == tag_id) & (df1['Time'] <= selected_time)]

    scatter_fig = px.scatter(dff, x='Time', y=metric)
    scatter_fig.update_xaxes(title='Time')
    scatter_fig.update_yaxes(title=metric)
    scatter_fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    comparison_dff = df1[df1['Time'] <= selected_time]
    comparison_fig = px.line(comparison_dff, x='Time', y='Cycle Time', color='Tag ID')
    comparison_fig.update_xaxes(title='Time')
    comparison_fig.update_yaxes(title='Cycle Time')
    comparison_fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return scatter_fig, comparison_fig


@callback(
    Output('time-series', 'figure'),
    [Input('indicator-scatter', 'hoverData'),
     Input('tag-id-dropdown', 'value'),
     Input('metric-radio', 'value')])
def update_time_series(hoverData, tag_id, metric):
    try:
        point_index = hoverData['points'][0]['pointIndex']
        dff = df1[df1['Tag ID'] == tag_id].iloc[:point_index + 1]
        title = f'Time Series for {tag_id}'
        return create_time_series(dff, metric, title)
    except Exception as e:
        return create_time_series(df1[df1['Tag ID'] == tag_id], metric, f'Time Series for {tag_id}')


def create_time_series(dff, metric, title):
    fig = px.scatter(dff, x='Time', y=metric)
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(title=metric)
    fig.add_annotation(x=0, y=0.85, xanchor='left', yanchor='bottom',
                       xref='paper', yref='paper', showarrow=False, align='left',
                       text=title)
    fig.update_layout(height=225, margin={'l': 20, 'b': 30, 'r': 10, 't': 10})
    return fig


@callback(
    Output("download-csv", "data"),
    Input("btn-download-csv", "n_clicks"),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    return dcc.send_data_frame(df1.to_csv, "rfid_data.csv")


@callback(
    Output('predicted-class-scatter', 'figure'),
    Output('predicted-class-bar', 'figure'),
    Input('btn-download-csv', 'n_clicks')  # This can be modified as per need
)
def update_prediction_graphs(n_clicks):
    scatter_fig = px.scatter(df2, x='Date', y='Predicted Class', color='Image')
    scatter_fig.update_layout(title='Predicted Class Scatter Plot')

    bar_fig = px.bar(df2, x='Predicted Class', color='Image')
    bar_fig.update_layout(title='Predicted Class Bar Plot')

    return scatter_fig, bar_fig


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8051)
