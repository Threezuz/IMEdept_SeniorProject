from dash import Dash, html, dcc, Input, Output, callback
import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
# Load the CSV file
df = pd.read_csv('rfid_data.csv')

# Convert the 'Time' column to datetime
df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S:%d:%m:%Y')

app.layout = html.Div([
    html.Div([
        html.Div([
            dcc.Dropdown(
                df['Tag ID'].unique(),
                df['Tag ID'].unique()[0],
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
        max=len(df['Time'].unique()) - 1,
        step=None,
        id='time-slider',
        value=len(df['Time'].unique()) - 1,
        marks={i: str(time) for i, time in enumerate(sorted(df['Time'].unique()))}
    ), style={'width': '49%', 'padding': '0px 20px 20px 20px'}),

    html.Div([
        dcc.Graph(id='cycle-time-comparison')
    ], style={'width': '100%', 'padding': '0 20'})
])


@callback(
    [Output('indicator-scatter', 'figure'),
     Output('cycle-time-comparison', 'figure')],
    [Input('tag-id-dropdown', 'value'),
     Input('metric-radio', 'value'),
     Input('time-slider', 'value')])
def update_graphs(tag_id, metric, time_index):
    selected_time = sorted(df['Time'].unique())[time_index]
    dff = df[(df['Tag ID'] == tag_id) & (df['Time'] <= selected_time)]

    # Update indicator scatter plot
    scatter_fig = px.scatter(dff, x='Time', y=metric)
    scatter_fig.update_xaxes(title='Time')
    scatter_fig.update_yaxes(title=metric)
    scatter_fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    # Update cycle time comparison plot
    comparison_dff = df[df['Time'] <= selected_time]
    comparison_fig = px.line(comparison_dff, x='Time', y='Cycle Time', color='Tag ID')
    comparison_fig.update_xaxes(title='Time')
    comparison_fig.update_yaxes(title='Cycle Time')
    comparison_fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    return scatter_fig, comparison_fig


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
    Output('time-series', 'figure'),
    [Input('indicator-scatter', 'hoverData'),
     Input('tag-id-dropdown', 'value'),
     Input('metric-radio', 'value')])
def update_time_series(hoverData, tag_id, metric):
    try:
        point_index = hoverData['points'][0]['pointIndex']
        dff = df[df['Tag ID'] == tag_id].iloc[:point_index + 1]
        title = f'Time Series for {tag_id}'
        return create_time_series(dff, metric, title)
    except Exception as e:
        return create_time_series(df[df['Tag ID'] == tag_id], metric, f'Time Series for {tag_id}')


if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)
